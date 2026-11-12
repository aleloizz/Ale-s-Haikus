"""API JSON dell'applicazione.

Tutte le scritture richiedono JSON, token CSRF (gestito in ``app.py``) e
validazione esplicita dei campi. I like sono memorizzati lato server con un
vincolo di unicità, non nella sessione firmata.
"""
import logging
import re
from functools import wraps

from flask import Blueprint, g, jsonify, request
from sqlalchemy import case
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from config.constants import (
    ALLOWED_POEM_TYPES,
    MAX_ANALYZE_CHARS,
    MAX_AUTHOR_LENGTH,
    MAX_BACHECA_PAGE,
    MAX_BACHECA_PER_PAGE,
    MAX_FILTER_LENGTH,
    MAX_POEM_CHARS,
    MAX_POEM_LINES,
    MAX_TITLE_LENGTH,
    SCHEMI_POESIA,
)
from extensions import limiter
from models.poem import Poem, PoemLike, db
from services.poetry_analyzer import analizza_poesia_completa, verifica_metrica
from utils.poem_type import (
    normalize_poem_type,
    normalize_recognized_poem_type,
    validate_selected_poem_type,
)
from utils.security import get_client_fingerprint, get_voter_key
from utils.text_processing import sanitize_user_text

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ValidationError(ValueError):
    """Errore di validazione con tipo macchina e stato HTTP."""

    def __init__(self, message, error_type="invalid_input", status=400):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status = status


def require_json(f):
    """Richiede ``application/json`` e un oggetto JSON nel corpo."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Content-Type application/json richiesto",
                    }
                ),
                400,
            )
        try:
            data = request.get_json(force=False, silent=False)
        except HTTPException:
            # Lascia passare 413/415 verso gli handler applicativi.
            raise
        except Exception:
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "JSON non valido nel corpo della richiesta",
                    }
                ),
                400,
            )
        if not isinstance(data, dict):
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Il corpo JSON deve essere un oggetto",
                    }
                ),
                400,
            )
        return f(*args, **kwargs)

    return wrapper


def _error_response(error: ValidationError, **extra):
    payload = {
        "error": True,
        "error_type": error.error_type,
        "message": error.message,
    }
    payload.update(extra)
    return jsonify(payload), error.status


def _clean_text(value, field_name, max_chars, max_lines=None) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"Campo {field_name} non valido")
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"Campo {field_name} mancante o vuoto")
    if _CONTROL_CHAR_RE.search(cleaned):
        raise ValidationError(f"Campo {field_name} contiene caratteri non ammessi")
    if len(cleaned) > max_chars:
        raise ValidationError(
            f"Campo {field_name} troppo lungo (max {max_chars} caratteri).",
            error_type="too_long",
        )
    if max_lines is not None and len(cleaned.splitlines()) > max_lines:
        raise ValidationError(
            f"Troppi versi (max {max_lines}).",
            error_type="too_many_lines",
        )
    return cleaned


def _parse_selected_type(value):
    """Valida il tipo scelto dall'utente; ``None`` se assente."""
    try:
        return validate_selected_poem_type(value)
    except ValueError as exc:
        raise ValidationError(
            "Tipo di poesia non valido", error_type="invalid_poem_type"
        ) from exc


def _effective_poem_type(selected_type, analysis) -> str:
    if selected_type:
        return selected_type
    return normalize_recognized_poem_type(analysis.get("tipo_riconosciuto"))


def _log_security_event(event: str, **fields):
    """Log compatto di eventi di sicurezza, senza PII in chiaro."""
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info("security_event=%s %s", event, details)


def format_poem_type_label(raw_type: str | None, default: str = "poesia") -> str:
    """Normalizza una tipologia per uso testuale/UI (non per logica interna)."""
    value = str(raw_type or "")
    for ch in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00a0"):
        value = value.replace(ch, " ")
    value = value.replace("_", " ")
    value = " ".join(value.split())
    return value or default


def calculate_rhyme_status_for_verses(analyzed_scheme, expected_scheme, num_verses):
    """Calcola lo stato delle rime per ogni verso (valid/invalid)."""
    if not expected_scheme:
        return ["valid"] * num_verses

    expected_string = "".join(expected_scheme)
    if len(analyzed_scheme or "") != len(expected_string):
        return ["invalid"] * num_verses

    return [
        "valid" if analyzed_scheme[i] == expected_string[i] else "invalid"
        for i in range(num_verses)
    ]


def validate_rhyme_pattern(
    analyzed_scheme, expected_scheme, analisi_rime=None, poem_type: str = None
):
    """Valida se lo schema rime analizzato corrisponde a quello atteso."""
    if not expected_scheme:
        return True, []

    expected_string = "".join(expected_scheme)
    analyzed_string = analyzed_scheme or ""
    poem_type = (poem_type or "").lower() if poem_type else None

    if poem_type == "sonetto" and len(analyzed_string) == 14:
        prefix8 = analyzed_string[:8]
        if prefix8 in ("ABBAABBA", "ABABABAB"):
            suffix6 = analyzed_string[8:14]
            if suffix6 and set(suffix6) <= set("CDE") and 2 <= len(set(suffix6)) <= 3:
                from collections import Counter

                if all(v >= 2 for v in Counter(suffix6).values()):
                    return True, []

    if analyzed_string == expected_string:
        return True, []

    errors = []
    if len(analyzed_scheme or "") != len(expected_string):
        errors.append(
            f"Schema ha {len(analyzed_scheme or '')} rime invece di {len(expected_string)}"
        )
    else:
        for i, (actual, expected) in enumerate(
            zip(analyzed_scheme, expected_string)
        ):
            if actual != expected:
                sound_info = ""
                if (
                    analisi_rime
                    and "suoni_finali" in analisi_rime
                    and i < len(analisi_rime["suoni_finali"])
                ):
                    current_sound = analisi_rime["suoni_finali"][i]
                    expected_verses = []
                    expected_sounds = []
                    for j, letter in enumerate(expected_string):
                        if (
                            j != i
                            and letter == expected
                            and j < len(analisi_rime["suoni_finali"])
                        ):
                            expected_verses.append(j + 1)
                            expected_sounds.append(
                                analisi_rime["suoni_finali"][j]
                            )
                    if expected_verses:
                        if len(expected_verses) == 1:
                            sound_info = (
                                f" (suono '{current_sound}' non rima con verso "
                                f"{expected_verses[0]}: '{expected_sounds[0]}')"
                            )
                        else:
                            sound_info = (
                                f" (suono '{current_sound}' dovrebbe rimare con "
                                f"versi {', '.join(map(str, expected_verses))}: "
                                f"{', '.join(repr(s) for s in expected_sounds)})"
                            )
                    else:
                        sound_info = f" (suono '{current_sound}')"

                errors.append(
                    f"Verso {i + 1}: rima '{actual}' invece di '{expected}'{sound_info}"
                )

    return False, errors


def get_expected_rhyme_scheme(tipo_poesia):
    """Restituisce lo schema rime atteso per un tipo di poesia."""
    if tipo_poesia in SCHEMI_POESIA and "rima" in SCHEMI_POESIA[tipo_poesia]:
        if SCHEMI_POESIA[tipo_poesia]["rima"]:
            return SCHEMI_POESIA[tipo_poesia]["rima"]

    schemi_attesi = {
        "sonetto": ["ABBA", "ABBA", "CDC", "DCD"],
        "quartina": ["ABAB"],
        "terzina_dantesca": ["ABA"],
        "limerick": ["AABBA"],
        "ballad": ["ABCB"],
        "clerihew": ["AABB"],
        "stornello": ["ABA"],
        "distico": ["AA"],
    }
    return schemi_attesi.get(tipo_poesia, [])


def convert_rhyme_scheme_to_frontend(schema_string, tipo_poesia):
    """Converte lo schema rime da stringa al formato array del frontend."""
    if not schema_string or not schema_string.strip():
        return []

    if tipo_poesia in SCHEMI_POESIA and "rima" in SCHEMI_POESIA[tipo_poesia]:
        if SCHEMI_POESIA[tipo_poesia]["rima"]:
            return SCHEMI_POESIA[tipo_poesia]["rima"]

    schema = schema_string.strip()
    if len(schema) == 14:
        return [schema[0:4], schema[4:8], schema[8:11], schema[11:14]]
    if len(schema) in (3, 4, 5):
        return [schema]

    return [schema[i : i + 4] for i in range(0, len(schema), 4)] or [schema]


def get_syllable_pattern(tipo_poesia):
    """Restituisce il pattern di sillabe per un tipo di poesia."""
    patterns = {
        "haiku": [5, 7, 5],
        "tanka": [5, 7, 5, 7, 7],
        "katauta": [5, 7, 7],
        "choka": [5, 7, 5, 7, 5, 7, 5, 7, 7],
        "sedoka": [5, 7, 7, 5, 7, 7],
        "sonetto": [11] * 14,
        "quartina": [11] * 4,
        "stornello": [5, 11, 11],
        "ottava_rima": [11] * 8,
        "terzina_dantesca": [11, 11, 11],
        "limerick": [8, 8, 5, 5, 8],
        "ballad": [8, 6, 8, 6],
        "clerihew": [8, 8, 8, 8],
        "cinquain": [2, 4, 6, 8, 2],
        "sestina": [11] * 6,
        "distico": [11, 11],
        "versi_liberi": [],
    }
    return patterns.get(tipo_poesia, [])


def get_target_sillabe(tipo_poesia, indice_verso):
    pattern = get_syllable_pattern(tipo_poesia)
    if pattern and indice_verso < len(pattern):
        return pattern[indice_verso]
    return None


@api_bp.route("/analyze", methods=["POST"])
@require_json
@limiter.limit("20 per minute")
def api_analizza():
    """Analizza una poesia senza salvarla."""
    try:
        data = request.get_json() or {}
        testo = _clean_text(
            data.get("text"), "text", MAX_ANALYZE_CHARS, MAX_POEM_LINES
        )
        if _HTML_TAG_RE.search(testo):
            raise ValidationError(
                "Il testo contiene caratteri non ammessi.", "invalid_input"
            )

        selected_type = _parse_selected_type(
            data.get("type") or data.get("poem_type") or data.get("tipo")
        )
        use_tolerance = data.get("use_tolerance") is True

        analisi = analizza_poesia_completa(testo, use_tolerance=use_tolerance)
        if "errore" in analisi:
            logger.warning(
                "analysis_failed error=%s request_id=%s",
                analisi.get("errore"),
                getattr(g, "request_id", "-"),
            )
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Errore durante l'analisi del testo.",
                    }
                ),
                500,
            )

        tipo_poesia = _effective_poem_type(
            selected_type, analisi
        )
        pattern = get_syllable_pattern(tipo_poesia)
        num_versi = len(analisi.get("versi", []))

        if tipo_poesia != "versi_liberi" and pattern:
            if num_versi != len(pattern):
                error_type = (
                    "too_few_verses"
                    if num_versi < len(pattern)
                    else "too_many_verses"
                )
                verb = "corta" if num_versi < len(pattern) else "lunga"
                return (
                    jsonify(
                        {
                            "error": True,
                            "error_type": error_type,
                            "poem_type": tipo_poesia,
                            "pattern": pattern,
                            "required": len(pattern),
                            "received": num_versi,
                            "message": (
                                f"Poesia troppo {verb}! Un {tipo_poesia} "
                                f"richiede {len(pattern)} versi."
                            ),
                        }
                    ),
                    400,
                )

        results = []
        schema = (analisi.get("analisi_rime") or {}).get("schema") or []
        syllable_counts = analisi.get("sillabe_per_verso") or []
        for i, verso in enumerate(analisi.get("versi", [])):
            syllables = (
                syllable_counts[i] if i < len(syllable_counts) else 0
            )
            target = get_target_sillabe(tipo_poesia, i)
            rhyme = schema[i] if i < len(schema) and schema[i] != "-" else None
            item = {
                "verse": i + 1,
                "text": verso,
                "syllables": syllables,
                "target": target,
                "correct": syllables == target if target else True,
            }
            if rhyme or tipo_poesia == "versi_liberi":
                item["rhyme"] = rhyme
            results.append(item)

        expected_scheme = get_expected_rhyme_scheme(tipo_poesia)
        if expected_scheme:
            scheme_for_frontend = expected_scheme
        else:
            scheme_for_frontend = convert_rhyme_scheme_to_frontend(
                analisi.get("schema_rime"), tipo_poesia
            )

        rhyme_valid, rhyme_errors = validate_rhyme_pattern(
            analisi.get("schema_rime"),
            expected_scheme,
            analisi.get("analisi_rime", {}),
            poem_type=tipo_poesia,
        )
        rhyme_status = calculate_rhyme_status_for_verses(
            analisi.get("schema_rime"), expected_scheme, num_versi
        )

        return jsonify(
            {
                "poem_type": tipo_poesia,
                "pattern": pattern or [],
                "results": results,
                "valid": all(result["correct"] for result in results),
                "rhyme_analysis": {
                    "scheme": scheme_for_frontend,
                    "details": analisi.get("analisi_rime", {}),
                    "valid": rhyme_valid,
                    "errors": rhyme_errors,
                    "verse_status": rhyme_status,
                },
                "total_syllables": analisi.get("sillabe_totali", 0),
                "total_verses": analisi.get("num_versi", 0),
                "valid_structure": analisi.get("rispetta_metrica", False),
                "metadata": analisi.get("dettagli_metrica", {}),
                "error": False,
                "parsing_version": "modular_v1.1",
            }
        )

    except ValidationError as exc:
        return _error_response(exc)
    except Exception:
        logger.exception(
            "analyze_unhandled_error request_id=%s",
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Errore interno durante l'analisi.",
                }
            ),
            500,
        )


def _publish_poem(data, text_key, author_key, title_key):
    """Logica comune di pubblicazione con validazione e metriche."""
    testo_raw = _clean_text(
        data.get(text_key), text_key, MAX_POEM_CHARS, MAX_POEM_LINES
    )
    autore_raw = _clean_text(
        data.get(author_key), author_key, MAX_AUTHOR_LENGTH
    )
    titolo_raw = data.get(title_key)
    if titolo_raw is not None and not isinstance(titolo_raw, str):
        raise ValidationError("Campo titolo non valido")

    selected_type = _parse_selected_type(
        data.get("poem_type") or data.get("tipo") or data.get("type")
    )
    use_tolerance = data.get("use_tolerance") is True

    testo = sanitize_user_text(testo_raw)
    autore = sanitize_user_text(autore_raw)
    titolo = sanitize_user_text((titolo_raw or "").strip())
    if not testo.strip():
        raise ValidationError("Il testo della poesia è vuoto dopo la sanificazione.")
    if not autore.strip():
        raise ValidationError("L'autore è vuoto dopo la sanificazione.")
    if len(titolo) > MAX_TITLE_LENGTH:
        raise ValidationError(
            f"Titolo troppo lungo (max {MAX_TITLE_LENGTH} caratteri).",
            error_type="too_long",
        )
    if not titolo:
        titolo = sanitize_user_text(
            f"{format_poem_type_label(selected_type or 'poesia')} senza titolo"
        )

    analisi = analizza_poesia_completa(testo, use_tolerance=use_tolerance)
    if "errore" in analisi:
        raise ValidationError(
            "Errore durante l'analisi del testo.", "analysis_error", 400
        )

    if selected_type:
        is_valid = verifica_metrica(
            selected_type,
            analisi.get("num_versi", 0),
            analisi.get("sillabe_per_verso", []),
            analisi.get("schema_rime", ""),
            use_tolerance=use_tolerance,
        )
    else:
        is_valid = bool(analisi.get("rispetta_metrica", False))

    effective_type = _effective_poem_type(selected_type, analisi)
    if not is_valid:
        expected_info = get_syllable_pattern(effective_type) or None
        details = [
            f"Tipo: {format_poem_type_label(effective_type, default='sconosciuto')}",
            f"Tolleranza attiva: {'sì' if use_tolerance else 'no'}",
        ]
        if expected_info:
            details.append(f"Pattern atteso: {expected_info}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": (
                        "Pubblicazione non consentita: la poesia non rispetta "
                        "i vincoli metrici della tipologia scelta."
                    ),
                    "details": details,
                }
            ),
            400,
        )

    poesia = Poem.create_from_analysis(
        titolo,
        testo,
        autore,
        analisi,
        poem_type_override=selected_type,
    )
    db.session.add(poesia)
    db.session.commit()

    _log_security_event(
        "poem_published",
        poem_id=poesia.id,
        poem_type=poesia.poem_type,
        author_len=len(autore),
        text_len=len(testo),
        client=get_client_fingerprint(),
        request_id=getattr(g, "request_id", "-"),
    )

    return (
        jsonify(
            {
                "success": True,
                "message": "Poesia pubblicata con successo!",
                "id": poesia.id,
                "poem_type": poesia.poem_type,
                "analisi": analisi,
            }
        ),
        201,
    )


@api_bp.route("/poems", methods=["POST"])
@require_json
@limiter.limit("5 per minute")
def api_create_poem():
    """Crea una poesia (alias con campi inglesi)."""
    try:
        return _publish_poem(
            request.get_json() or {}, "text", "author", "title"
        )
    except ValidationError as exc:
        return _error_response(exc)
    except Exception:
        db.session.rollback()
        logger.exception(
            "publish_unhandled_error request_id=%s",
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Errore interno durante la pubblicazione.",
                }
            ),
            500,
        )


@api_bp.route("/pubblica", methods=["POST"])
@require_json
@limiter.limit("5 per minute")
def api_pubblica():
    """Crea una poesia (alias con campi italiani)."""
    try:
        return _publish_poem(
            request.get_json() or {}, "testo", "autore", "titolo"
        )
    except ValidationError as exc:
        return _error_response(exc)
    except Exception:
        db.session.rollback()
        logger.exception(
            "publish_unhandled_error request_id=%s",
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Errore interno durante la pubblicazione.",
                }
            ),
            500,
        )


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")


@api_bp.route("/bacheca", methods=["GET"])
@limiter.limit("60 per minute")
def api_bacheca():
    """Restituisce la bacheca paginata con filtri validati."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        page = max(1, min(page if page is not None else 1, MAX_BACHECA_PAGE))
        per_page = max(
            1,
            min(per_page if per_page is not None else 10, MAX_BACHECA_PER_PAGE),
        )

        tipo_raw = (request.args.get("tipo") or "").strip()[:MAX_FILTER_LENGTH]
        autore = (request.args.get("autore") or "").strip()[:MAX_FILTER_LENGTH]
        solo_valide = (request.args.get("solo_valide") or "").lower() == "true"

        query = Poem.query

        if tipo_raw:
            tipo = normalize_poem_type(tipo_raw)
            if tipo not in ALLOWED_POEM_TYPES:
                raise ValidationError(
                    "Tipo di poesia non valido", "invalid_poem_type"
                )
            query = query.filter(Poem.poem_type == tipo)

        if autore:
            query = query.filter(
                Poem.author.ilike(f"%{_escape_like(autore)}%", escape="\\")
            )

        if solo_valide:
            query = query.filter(Poem.is_valid.is_(True))

        paginated = query.order_by(Poem.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "poesie": [poem.to_dict() for poem in paginated.items],
                "total": paginated.total,
                "pages": paginated.pages,
                "current_page": page,
                "per_page": per_page,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev,
            }
        )
    except ValidationError as exc:
        return _error_response(exc)
    except Exception:
        logger.exception(
            "bacheca_api_error request_id=%s",
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Errore interno nel recupero delle poesie.",
                }
            ),
            500,
        )


@api_bp.route("/poesia/<int:poesia_id>", methods=["GET"])
@limiter.limit("120 per minute")
def api_poesia_dettaglio(poesia_id):
    poem = db.session.get(Poem, poesia_id)
    if poem is None:
        return jsonify({"error": True, "message": "Risorsa non trovata"}), 404
    return jsonify(poem.to_dict())


def _get_poem_or_404(poem_id):
    poem = db.session.get(Poem, poem_id)
    if poem is None:
        return None, (
            jsonify({"success": False, "error": "Poesia non trovata"}),
            404,
        )
    return poem, None


@api_bp.route("/poems/<int:poem_id>/like", methods=["POST"])
@require_json
@limiter.limit("30 per minute")
def api_like_poem(poem_id):
    """Registra un like idempotente per (poesia, votante)."""
    poem, error = _get_poem_or_404(poem_id)
    if error:
        return error

    voter_key = get_voter_key()
    existing = PoemLike.query.filter_by(
        poem_id=poem_id, voter_key=voter_key
    ).first()
    if existing:
        return jsonify(
            {
                "success": True,
                "likes": poem.likes or 0,
                "liked": True,
                "already_liked": True,
                "message": "Hai già messo like a questa poesia.",
            }
        )

    try:
        db.session.add(PoemLike(poem_id=poem_id, voter_key=voter_key))
        db.session.query(Poem).filter(Poem.id == poem_id).update(
            {Poem.likes: db.func.coalesce(Poem.likes, 0) + 1},
            synchronize_session=False,
        )
        db.session.commit()
    except IntegrityError:
        # Due richieste concorrenti: il vincolo unico ha già registrato il like.
        db.session.rollback()
        poem = db.session.get(Poem, poem_id)
        return jsonify(
            {
                "success": True,
                "likes": (poem.likes if poem else 0) or 0,
                "liked": True,
                "already_liked": True,
                "message": "Hai già messo like a questa poesia.",
            }
        )
    except Exception:
        db.session.rollback()
        logger.exception(
            "like_unhandled_error poem_id=%s request_id=%s",
            poem_id,
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {"success": False, "error": "Errore interno nel dare like."}
            ),
            500,
        )

    poem = db.session.get(Poem, poem_id)
    _log_security_event(
        "poem_liked",
        poem_id=poem_id,
        voter=voter_key[:12],
        client=get_client_fingerprint(),
        request_id=getattr(g, "request_id", "-"),
    )
    return jsonify(
        {
            "success": True,
            "likes": (poem.likes if poem else 0) or 0,
            "liked": True,
            "message": "Like aggiunto con successo!",
        }
    )


@api_bp.route("/poems/<int:poem_id>/unlike", methods=["POST"])
@require_json
@limiter.limit("30 per minute")
def api_unlike_poem(poem_id):
    poem, error = _get_poem_or_404(poem_id)
    if error:
        return error

    voter_key = get_voter_key()
    try:
        deleted = PoemLike.query.filter_by(
            poem_id=poem_id, voter_key=voter_key
        ).delete(synchronize_session=False)
        if deleted:
            db.session.query(Poem).filter(Poem.id == poem_id).update(
                {
                    Poem.likes: case(
                        (db.func.coalesce(Poem.likes, 0) > 0, Poem.likes - 1),
                        else_=0,
                    )
                },
                synchronize_session=False,
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception(
            "unlike_unhandled_error poem_id=%s request_id=%s",
            poem_id,
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {"success": False, "error": "Errore interno nel rimuovere like."}
            ),
            500,
        )

    poem = db.session.get(Poem, poem_id)
    return jsonify(
        {
            "success": True,
            "likes": (poem.likes if poem else 0) or 0,
            "liked": False,
            "message": "Like rimosso!" if deleted else "Nessun like da rimuovere.",
        }
    )


@api_bp.route("/poems/<int:poem_id>/like/status", methods=["GET"])
@limiter.limit("120 per minute")
def api_like_status(poem_id):
    poem, error = _get_poem_or_404(poem_id)
    if error:
        return error

    voter_key = get_voter_key()
    liked = (
        PoemLike.query.filter_by(poem_id=poem_id, voter_key=voter_key).first()
        is not None
    )
    return jsonify(
        {"success": True, "liked": liked, "likes": poem.likes or 0}
    )


@api_bp.route("/stats", methods=["GET"])
@limiter.limit("120 per minute")
def api_stats():
    try:
        total_poems = Poem.query.count()
        valid_poems = Poem.query.filter(Poem.is_valid.is_(True)).count()
        authors_count = db.session.query(Poem.author).distinct().count()
        poems_by_type = (
            db.session.query(Poem.poem_type, db.func.count(Poem.id))
            .filter(Poem.poem_type.isnot(None))
            .group_by(Poem.poem_type)
            .all()
        )
        return jsonify(
            {
                "total_poems": total_poems,
                "valid_poems": valid_poems,
                "total_authors": authors_count,
                "poems_by_type": dict(poems_by_type),
                "success_rate": round(
                    (valid_poems / total_poems * 100) if total_poems else 0, 2
                ),
            }
        )
    except Exception:
        logger.exception(
            "stats_unhandled_error request_id=%s",
            getattr(g, "request_id", "-"),
        )
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Errore interno nel recupero delle statistiche.",
                }
            ),
            500,
        )
