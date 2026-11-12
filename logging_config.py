"""Logging strutturato con request id, senza dipendenze esterne."""
import hashlib
import hmac
import json
import logging
import sys
from datetime import datetime, timezone

from flask import current_app, g, has_request_context, request


def _client_fingerprint() -> str | None:
    """IP pseudonimo nei log: nessun indirizzo in chiaro."""
    try:
        remote_addr = request.remote_addr
        if not remote_addr:
            return None
        secret = (current_app.config.get("SECRET_KEY") or "missing-secret").encode(
            "utf-8"
        )
        return hmac.new(
            secret, remote_addr.encode("utf-8", errors="replace"), hashlib.sha256
        ).hexdigest()[:16]
    except Exception:
        return None


class JsonFormatter(logging.Formatter):
    """Formatta i record come righe JSON, adatte a Docker/Cloudflare Logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if has_request_context():
            payload.update(
                {
                    "request_id": getattr(g, "request_id", None),
                    "method": request.method,
                    "path": request.path,
                    "client": _client_fingerprint(),
                }
            )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(app) -> None:
    """Configura il logger dell'app e quello root (utile per Gunicorn)."""
    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if app.config.get("LOG_JSON"):
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
    app.logger.propagate = False
