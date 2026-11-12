"""Primitive di sicurezza applicativa: CSRF, origin check e chiavi like."""
import hashlib
import hmac
import secrets
from urllib.parse import urlsplit

from flask import current_app, jsonify, request, session

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
_CSRF_SESSION_KEY = "_csrf_token"


def get_client_ip() -> str:
    """IP del client, già risolto da ProxyFix quando configurato."""
    return request.remote_addr or "unknown"


def get_csrf_token() -> str:
    """Restituisce (creando se necessario) il token CSRF legato alla sessione."""
    token = session.get(_CSRF_SESSION_KEY)
    if not isinstance(token, str) or not token:
        token = secrets.token_urlsafe(32)
        session[_CSRF_SESSION_KEY] = token
    return token


def _csrf_failure(message: str):
    current_app.logger.warning(
        "csrf_rejected path=%s method=%s client=%s",
        request.path,
        request.method,
        get_client_fingerprint(),
    )
    if request.path.startswith("/api/"):
        return jsonify({"error": True, "message": message}), 403
    return message, 403


def csrf_protect():
    """before_request: verifica il synchronizer token per i metodi unsafe."""
    if not current_app.config.get("CSRF_ENABLED", True):
        return None
    if request.method in SAFE_METHODS:
        return None
    if request.path == "/healthz":
        return None

    expected = session.get(_CSRF_SESSION_KEY)
    supplied = request.headers.get("X-CSRF-Token")
    if not supplied:
        supplied = request.form.get("csrf_token")

    if (
        not isinstance(expected, str)
        or not isinstance(supplied, str)
        or not expected
        or not supplied
        or not hmac.compare_digest(expected, supplied)
    ):
        return _csrf_failure("CSRF token mancante o non valido")
    return None


def origin_protect():
    """before_request: blocca POST cross-origin quando il browser invia Origin/Referer.

    Il token CSRF è la difesa principale; questo controllo aggiuntivo intercetta
    richieste cross-site che dovessero riuscire a presentare un token valido.
    """
    if request.method in SAFE_METHODS:
        return None

    source = request.headers.get("Origin")
    if not source:
        source = request.headers.get("Referer")
    if not source:
        return None

    parsed = urlsplit(source)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return _csrf_failure("Origine della richiesta non valida")

    if parsed.netloc.lower() != request.host.lower():
        return _csrf_failure("Origine della richiesta non consentita")

    return None


def get_voter_key() -> str:
    """Chiave pseudonima e stabile per deduplicare i like senza salvare PII.

    Combina IP e User-Agent con HMAC-SHA256. Il valore memorizzato non permette
    di risalire direttamente a IP o browser.
    """
    secret = current_app.config.get("SECRET_KEY") or "missing-secret"
    user_agent = request.headers.get("User-Agent", "")[:256]
    raw = f"{get_client_ip()}|{user_agent}".encode("utf-8", errors="replace")
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def get_client_fingerprint() -> str:
    """Identificatore pseudonimo del client per i log di sicurezza.

    Non memorizza l'IP in chiaro: usa HMAC-SHA256 troncato, utile solo per
    correlare eventi ripetuti dello stesso client.
    """
    secret = current_app.config.get("SECRET_KEY") or "missing-secret"
    raw = get_client_ip().encode("utf-8", errors="replace")
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()[:16]
