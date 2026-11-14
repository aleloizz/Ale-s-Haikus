"""Normalizzazione e validazione delle tipologie poetiche.

La tipologia è un valore controllato dall'utente che finisce in HTML, URL e
filtri di database. Qui viene ridotta a uno slug canonico e, per i valori
selezionati dall'utente, accettata solo se presente nell'allowlist.
"""
import re

from config.constants import (
    ALLOWED_POEM_TYPES,
    MAX_POEM_TYPE_LENGTH,
    POEM_TYPE_ALIASES,
)

_SLUG_RE = re.compile(r"^[a-z0-9_]+$")


def normalize_poem_type(value) -> str:
    """Riporta un valore grezzo a minuscolo, senza spazi esterni e con alias risolti."""
    if not isinstance(value, str):
        return ""
    normalized = value.strip().lower()
    return POEM_TYPE_ALIASES.get(normalized, normalized)


def validate_selected_poem_type(value):
    """Valida un tipo scelto dall'utente.

    Ritorna lo slug canonico se valido, ``None`` se il valore è assente.
    Solleva ``ValueError`` se il valore è presente ma non ammesso.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Tipo di poesia non valido")

    raw = value.strip()
    if not raw:
        return None

    normalized = normalize_poem_type(raw)
    if (
        len(normalized) > MAX_POEM_TYPE_LENGTH
        or not _SLUG_RE.fullmatch(normalized)
        or normalized not in ALLOWED_POEM_TYPES
    ):
        raise ValueError("Tipo di poesia non valido")
    return normalized


def normalize_recognized_poem_type(value) -> str:
    """Normalizza un tipo prodotto dall'analizzatore.

    L'analizzatore può produrre etichette legacy (es. "distico (rima baciata)").
    I valori non riconosciuti vengono ridotti a ``versi_liberi``: è l'unico
    fallback che appartiene all'allowlist e che quindi può essere salvato senza
    introdurre etichette arbitrarie nel database o nell'interfaccia.
    """
    normalized = normalize_poem_type(value)
    if normalized in ALLOWED_POEM_TYPES:
        return normalized
    return "versi_liberi"
