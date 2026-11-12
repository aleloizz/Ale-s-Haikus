"""
Ale's Haikus - Webapp di analisi poetica.

Factory applicativa unica. Le scelte di sicurezza (proxy, CSRF, CSP, host
fidati, logging) sono centralizzate qui e valgono per tutte le route.
"""
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape as xml_escape

from flask import (
    Flask,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import text
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.middleware.proxy_fix import ProxyFix

from config.app_config import config
from extensions import limiter
from logging_config import configure_logging
from models.poem import db
from routes.api import api_bp
from routes.web import web_bp
from services.syllable_analyzer import conta_sillabe
from utils.security import csrf_protect, get_csrf_token, origin_protect
from utils.text_processing import BLEACH_AVAILABLE

try:
    from flask_compress import Compress
except ImportError:  # pragma: no cover - dipendenza opzionale
    Compress = None


_CONFIG_ALIASES = {
    "dev": "development",
    "prod": "production",
    "test": "testing",
}


def _resolve_config_name(config_name=None) -> str:
    """Risolve il nome configurazione senza mai cadere su development."""
    name = (
        config_name
        or os.environ.get("APP_CONFIG")
        or os.environ.get("FLASK_ENV")
        or "production"
    )
    name = _CONFIG_ALIASES.get(str(name).strip().lower(), str(name).strip().lower())
    return name if name in config else "production"


def _request_id() -> str:
    """Request id fornito dal proxy se ragionevole, altrimenti generato."""
    supplied = (request.headers.get("X-Request-ID") or "").strip()
    if supplied and len(supplied) <= 64 and all(
        ch.isalnum() or ch in "-_." for ch in supplied
    ):
        return supplied
    return uuid.uuid4().hex


def _is_api_request() -> bool:
    return request.path.startswith("/api/")


def current_base_url() -> str:
    """Base URL canonica configurata, mai derivata dall'header Host."""
    from flask import current_app

    return (current_app.config.get("CANONICAL_BASE_URL") or "").rstrip("/")


def create_app(config_name=None):
    """Crea e configura l'applicazione Flask."""
    config_name = _resolve_config_name(config_name)
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config[config_name])
    app.config["APP_CONFIG_NAME"] = config_name

    # --- Fail-fast dei requisiti di produzione ---------------------------
    if config_name == "production":
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key or secret_key.startswith("dev-secret-key"):
            raise RuntimeError(
                "SECRET_KEY non impostata correttamente per la produzione."
            )
        if len(secret_key) < 32:
            raise RuntimeError(
                "SECRET_KEY troppo corta: usare almeno 32 caratteri casuali."
            )

        database_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        if not database_uri:
            raise RuntimeError(
                "DATABASE_URL non impostata: la produzione richiede PostgreSQL."
            )
        if not database_uri.startswith(
            ("postgresql://", "postgresql+psycopg2://")
        ):
            raise RuntimeError(
                "DATABASE_URL deve puntare a PostgreSQL in produzione."
            )

        if not BLEACH_AVAILABLE:
            raise RuntimeError(
                "bleach non è importabile: la sanificazione fail-closed è "
                "obbligatoria in produzione."
            )

        if not app.config.get("TRUSTED_HOSTS"):
            raise RuntimeError(
                "TRUSTED_HOSTS non configurato: rifiuto di avviarsi senza "
                "validazione dell'header Host."
            )
        canonical = app.config.get("CANONICAL_BASE_URL") or ""
        if not canonical.startswith("https://"):
            raise RuntimeError(
                "CANONICAL_BASE_URL deve essere un URL https in produzione."
            )

        if not app.config.get("CSRF_ENABLED", True):
            raise RuntimeError("CSRF_ENABLED non può essere disattivato in produzione.")
        if not app.config.get("RATELIMIT_ENABLED", True):
            raise RuntimeError(
                "RATELIMIT_ENABLED non può essere disattivato in produzione."
            )
        if not app.config.get("SESSION_COOKIE_SECURE", False):
            raise RuntimeError(
                "SESSION_COOKIE_SECURE deve essere true in produzione."
            )
        if not app.config.get("SESSION_COOKIE_HTTPONLY", True):
            raise RuntimeError(
                "SESSION_COOKIE_HTTPONLY deve essere true in produzione."
            )
        if app.config.get("SESSION_COOKIE_SAMESITE") not in {"Lax", "Strict"}:
            raise RuntimeError(
                "SESSION_COOKIE_SAMESITE deve essere Lax o Strict in produzione."
            )

    # --- Proxy fidati ----------------------------------------------------
    # Cloudflare Tunnel / Heroku aggiungono un solo hop. X-Forwarded-Host non
    # viene mai usato per ricostruire l'host: l'host resta quello della
    # richiesta e viene validato da TRUSTED_HOSTS.
    proxy_count = int(app.config.get("TRUSTED_PROXY_COUNT") or 0)
    if proxy_count > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxy_count,
            x_proto=proxy_count,
            x_host=0,
            x_port=0,
            x_prefix=0,
        )

    # --- Estensioni ------------------------------------------------------
    db.init_app(app)
    limiter.init_app(app)

    if Compress is not None:
        Compress(app)

    configure_logging(app)

    # --- Blueprint -------------------------------------------------------
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    # Schema temporaneo: gated da AUTO_CREATE_DB. In produzione il default è
    # False; il bootstrap iniziale può usare ``flask --app app init-db``.
    if app.config.get("AUTO_CREATE_DB"):
        with app.app_context():
            db.create_all()

    @app.cli.command("init-db")
    def init_db_command():
        """Crea lo schema iniziale (baseline temporanea, in attesa di Alembic)."""
        db.create_all()
        print("Schema iniziale creato.")

    # --- Contesto template ----------------------------------------------
    @app.context_processor
    def inject_security_context():
        def csp_nonce():
            return getattr(g, "csp_nonce", "")

        return dict(
            csrf_token=get_csrf_token,
            csp_nonce=csp_nonce,
            GOOGLE_SITE_VERIFICATION=os.environ.get("GOOGLE_SITE_VERIFICATION"),
            BING_SITE_VERIFICATION=os.environ.get("BING_SITE_VERIFICATION"),
        )

    @app.context_processor
    def utility_processor():
        def static_file(filename: str) -> str:
            try:
                file_path = os.path.join(app.static_folder, filename)
                version = int(os.path.getmtime(file_path))
            except Exception:
                version = int(datetime.now(timezone.utc).timestamp())
            return url_for("static", filename=filename, v=version)

        return dict(static_file=static_file)

    # --- Hook di richiesta ----------------------------------------------
    @app.before_request
    def assign_request_context():
        g.request_id = _request_id()
        g.csp_nonce = secrets.token_urlsafe(16)
        g.request_started = time.monotonic()

    @app.before_request
    def enforce_csrf():
        return csrf_protect()

    @app.before_request
    def enforce_same_origin():
        return origin_protect()

    @app.before_request
    def enforce_https():
        """Redirect HTTPS costruito sulla base canonica, non sull'Host."""
        if app.testing or app.debug:
            return None
        if request.path == "/healthz":
            return None
        if request.is_secure:
            return None
        if app.config.get("PREFERRED_URL_SCHEME") != "https":
            return None

        if _is_api_request():
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "HTTPS richiesto per le API.",
                    }
                ),
                400,
            )

        base = current_base_url()
        if not base.startswith("https://"):
            return None
        target = f"{base}{request.full_path.rstrip('?')}"
        if target == request.url:
            return None
        return redirect(target, code=301)

    @app.after_request
    def security_headers(response):
        nonce = getattr(g, "csp_nonce", "")
        script_sources = "'self' https://www.googletagmanager.com"
        if nonce:
            script_sources = (
                f"'self' 'nonce-{nonce}' https://www.googletagmanager.com"
            )
        csp_directives = [
            "default-src 'self'",
            f"script-src {script_sources}",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://www.google-analytics.com "
            "https://*.google-analytics.com https://www.googletagmanager.com",
            "manifest-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",
        ]
        if app.config.get("PREFERRED_URL_SCHEME") == "https":
            csp_directives.append("upgrade-insecure-requests")

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        if request.is_secure or app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response

    @app.after_request
    def cache_headers(response):
        """Cache esplicita: statics versionati, HTML mai in cache."""
        path = request.path
        if path.startswith("/static/"):
            filename = path.rsplit("/", 1)[-1]
            expires_one_year = format_datetime(
                datetime.now(timezone.utc) + timedelta(days=365), usegmt=True
            )
            if filename.endswith((".css", ".js")):
                response.headers["Cache-Control"] = "public, max-age=31536000"
                response.headers["Expires"] = expires_one_year
            elif filename.endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".avif", ".ico", ".svg")
            ):
                response.headers["Cache-Control"] = (
                    "public, max-age=31536000, immutable"
                )
                response.headers["Expires"] = expires_one_year
            elif filename.endswith((".woff", ".woff2", ".ttf", ".otf")):
                response.headers["Cache-Control"] = (
                    "public, max-age=31536000, immutable"
                )
            elif filename.endswith((".xml", ".txt", ".json", ".webmanifest")):
                response.headers["Cache-Control"] = "public, max-age=3600"
            else:
                response.headers["Cache-Control"] = "public, max-age=86400"
        elif response.content_type and "text/html" in response.content_type:
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        elif _is_api_request():
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.after_request
    def request_logging(response):
        if request.path.startswith("/static/"):
            return response
        started = getattr(g, "request_started", None)
        duration_ms = (
            (time.monotonic() - started) * 1000 if started is not None else 0
        )
        app.logger.info(
            "request_completed method=%s path=%s status=%s duration_ms=%.1f "
            "request_id=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            getattr(g, "request_id", "-"),
        )
        return response

    # --- Error handling --------------------------------------------------
    @app.errorhandler(NotFound)
    def handle_not_found(error):
        if _is_api_request():
            return (
                jsonify({"error": True, "message": "Risorsa non trovata"}),
                404,
            )
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def handle_request_too_large(error):
        if _is_api_request():
            return (
                jsonify(
                    {
                        "error": True,
                        "error_type": "payload_too_large",
                        "message": "Richiesta troppo grande.",
                    }
                ),
                413,
            )
        return "Richiesta troppo grande.", 413

    @app.errorhandler(429)
    def handle_rate_limited(error):
        retry_after = getattr(error, "retry_after", None)
        response = (
            jsonify(
                {
                    "error": True,
                    "error_type": "rate_limited",
                    "message": "Troppe richieste. Riprova più tardi.",
                }
            )
            if _is_api_request()
            else ("Troppe richieste. Riprova più tardi.", 429)
        )
        if isinstance(response, tuple):
            body, status = response
            result = app.make_response((body, status))
        else:
            result = app.make_response(response)
            result.status_code = 429
        if retry_after:
            result.headers["Retry-After"] = str(retry_after)
        return result

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if _is_api_request():
            return (
                jsonify(
                    {
                        "error": True,
                        "message": error.description or "Errore HTTP",
                    }
                ),
                error.code or 500,
            )
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        try:
            db.session.rollback()
        except Exception:
            pass
        app.logger.exception(
            "unhandled_exception request_id=%s path=%s",
            getattr(g, "request_id", "-"),
            request.path,
        )
        if _is_api_request():
            return (
                jsonify(
                    {
                        "error": True,
                        "message": "Errore interno del server.",
                    }
                ),
                500,
            )
        return render_template("500.html"), 500

    # --- Sitemap, PWA e file speciali -----------------------------------
    def _sitemap_response(xml: str, max_age: int):
        response = make_response(xml)
        response.headers["Content-Type"] = "application/xml; charset=utf-8"
        response.headers["Cache-Control"] = f"public, max-age={max_age}"
        return response

    @app.route("/sitemap.xml")
    def sitemap_index():
        today = datetime.now(timezone.utc).date().isoformat()
        base = current_base_url()
        xml = "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                "  <sitemap>",
                f"    <loc>{xml_escape(base + url_for('sitemap_static'))}</loc>",
                f"    <lastmod>{today}</lastmod>",
                "  </sitemap>",
                "  <sitemap>",
                f"    <loc>{xml_escape(base + url_for('sitemap_poesie'))}</loc>",
                f"    <lastmod>{today}</lastmod>",
                "  </sitemap>",
                "</sitemapindex>",
            ]
        )
        return _sitemap_response(xml, 3600)

    @app.route("/sitemap-static.xml")
    def sitemap_static():
        today = datetime.now(timezone.utc).date().isoformat()
        base = current_base_url()
        entries = [
            (url_for("web.index"), "weekly", "1.0"),
            (url_for("web.analyzer"), "weekly", "0.8"),
            (url_for("web.bacheca"), "daily", "0.8"),
            (url_for("web.wiki"), "weekly", "0.7"),
        ]
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for path, changefreq, priority in entries:
            parts.extend(
                [
                    "  <url>",
                    f"    <loc>{xml_escape(base + path)}</loc>",
                    f"    <lastmod>{today}</lastmod>",
                    f"    <changefreq>{changefreq}</changefreq>",
                    f"    <priority>{priority}</priority>",
                    "  </url>",
                ]
            )
        parts.append("</urlset>")
        return _sitemap_response("\n".join(parts), 3600)

    @app.route("/sitemap-poesie.xml")
    def sitemap_poesie():
        from models.poem import Poem

        base = current_base_url()
        try:
            poems = (
                Poem.query.order_by(Poem.created_at.desc()).limit(5000).all()
            )
        except Exception:
            app.logger.exception("sitemap_poems_query_failed")
            poems = []

        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for poem in poems:
            try:
                lastmod = (poem.created_at or datetime.now(timezone.utc)).date().isoformat()
            except Exception:
                lastmod = datetime.now(timezone.utc).date().isoformat()
            parts.extend(
                [
                    "  <url>",
                    f"    <loc>{xml_escape(base + url_for('web.dettaglio_poesia', poesia_id=poem.id))}</loc>",
                    f"    <lastmod>{lastmod}</lastmod>",
                    "    <changefreq>weekly</changefreq>",
                    "    <priority>0.6</priority>",
                    "  </url>",
                ]
            )
        parts.append("</urlset>")
        return _sitemap_response("\n".join(parts), 1800)

    @app.route("/sw.js")
    def service_worker():
        response = send_from_directory("static", "sw.js")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.mimetype = "application/javascript"
        return response

    @app.route("/robots.txt")
    def robots_txt():
        response = send_from_directory("static", "robots.txt")
        response.headers["Cache-Control"] = "public, max-age=300"
        response.mimetype = "text/plain"
        return response

    @app.route("/healthz")
    def healthz():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            app.logger.exception(
                "healthcheck_failed request_id=%s", getattr(g, "request_id", "-")
            )
            response = jsonify({"status": "error"})
            response.status_code = 503
            response.headers["Cache-Control"] = "no-store"
            return response
        response = jsonify({"status": "ok"})
        response.headers["Cache-Control"] = "no-store"
        return response

    # --- Route legacy ----------------------------------------------------
    @app.route("/analizza", methods=["POST"])
    def analizza_haiku():
        """Analisi specifica per haiku - route legacy."""
        text_input = request.form.get("text", "").strip()

        if not text_input:
            return render_template("index.html", haiku="", message="Inserisci del testo!")

        versi = [verso.strip() for verso in text_input.split("\n") if verso.strip()]

        if len(versi) != 3:
            return render_template(
                "index.html",
                haiku=text_input,
                message="Devi inserire esattamente 3 versi! >:(",
            )

        results = []
        for index, verso in enumerate(versi):
            results.append(
                {
                    "verse": index + 1,
                    "syllables": conta_sillabe(verso),
                    "target": [5, 7, 5][index],
                }
            )

        errors = [
            f"Il verso {result['verse']} dovrebbe avere {result['target']} sillabe, ne ha {result['syllables']}."
            for result in results
            if result["syllables"] != result["target"]
        ]

        message = (
            "Il tuo haiku è perfetto! :3"
            if not errors
            else "\n".join(errors)
        )
        return render_template("index.html", haiku=text_input, message=message)

    return app
