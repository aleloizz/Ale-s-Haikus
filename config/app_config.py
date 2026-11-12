import os
from datetime import timedelta


def env_value(name: str, default=None):
    """Legge un valore da ambiente o dal file indicato da ``<NAME>_FILE``.

    Il formato ``*_FILE`` permette di montare i segreti come file Docker
    (``/run/secrets/...``) senza esporli in ``docker inspect`` o nei log.
    """
    file_path = os.environ.get(f"{name}_FILE")
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                return handle.read().strip()
        except OSError as exc:
            raise RuntimeError(
                f"Impossibile leggere {name}_FILE: {file_path}"
            ) from exc
    value = os.environ.get(name)
    return default if value is None else value


def env_bool(name: str, default: bool = False) -> bool:
    """Legge un booleano da ambiente con valori espliciti e prevedibili."""
    value = env_value(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    """Legge un intero da ambiente, ignorando valori non validi."""
    value = env_value(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def env_list(name: str, default=None):
    """Legge una lista separata da virgole (utile per TRUSTED_HOSTS)."""
    value = env_value(name)
    if value is None:
        return list(default) if default is not None else None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _database_url():
    """Normalizza l'URL PostgreSQL fornito dai provider (es. Heroku).

    SQLAlchemy 2.1 può selezionare psycopg (v3) per ``postgresql://``; il
    progetto installa psycopg2, quindi il driver viene reso esplicito.
    """
    url = env_value("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    return url


class Config:
    """Configurazione base dell'applicazione."""

    # In produzione non deve esistere fallback: viene verificato in app factory.
    SECRET_KEY = env_value("SECRET_KEY")

    DATABASE_URL = _database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///poems.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookie di sessione: HttpOnly sempre, SameSite esplicito.
    SESSION_COOKIE_NAME = env_value("SESSION_COOKIE_NAME", "aleshaikus_session")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # CSRF applicativo (synchronizer token in sessione).
    CSRF_ENABLED = env_bool("CSRF_ENABLED", True)

    # Host e URL canonico: niente fiducia implicita nell'header Host.
    TRUSTED_HOSTS = None
    CANONICAL_BASE_URL = (
        env_value("CANONICAL_BASE_URL", "http://localhost:5000")
        or "http://localhost:5000"
    ).rstrip("/")
    TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0)

    # Limiti di richiesta: nessun upload previsto, 1 MiB è abbondante.
    MAX_CONTENT_LENGTH = 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 512 * 1024

    # Rate limiting configurabile (in produzione usare Redis per più worker).
    RATELIMIT_STORAGE_URI = env_value(
        "RATELIMIT_STORAGE_URI", "memory://"
    )
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_ENABLED = env_bool("RATELIMIT_ENABLED", True)

    # Schema: in produzione può essere disattivato dopo il baseline Alembic.
    AUTO_CREATE_DB = env_bool("AUTO_CREATE_DB", True)

    # Logging strutturato.
    LOG_LEVEL = env_value("LOG_LEVEL", "INFO")
    LOG_JSON = env_bool("LOG_JSON", False)


class DevelopmentConfig(Config):
    """Configurazione per ambiente di sviluppo locale."""

    DEBUG = True
    SECRET_KEY = env_value("SECRET_KEY") or "dev-secret-key-local-only"
    SQLALCHEMY_DATABASE_URI = _database_url() or "sqlite:///poems.db"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0)


class ProductionConfig(Config):
    """Configurazione per ambiente di produzione (PostgreSQL obbligatorio)."""

    DEBUG = False
    TESTING = False
    SECRET_KEY = env_value("SECRET_KEY")
    DATABASE_URL = _database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 2,
    }

    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
    TRUSTED_HOSTS = env_list(
        "TRUSTED_HOSTS",
        ["www.aleshaikus.me", "aleshaikus.me", "localhost", "127.0.0.1"],
    )
    CANONICAL_BASE_URL = (
        env_value("CANONICAL_BASE_URL", "https://www.aleshaikus.me")
        or "https://www.aleshaikus.me"
    ).rstrip("/")
    TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 1)
    PREFERRED_URL_SCHEME = "https"
    # In produzione lo schema si crea solo esplicitamente (bootstrap una tantum
    # con ``flask --app app init-db``) in attesa di Alembic.
    AUTO_CREATE_DB = env_bool("AUTO_CREATE_DB", False)
    LOG_JSON = env_bool("LOG_JSON", True)


class TestingConfig(Config):
    """Configurazione per test automatici."""

    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key-not-for-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False
    CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    TRUSTED_HOSTS = None
    TRUSTED_PROXY_COUNT = 0
    CANONICAL_BASE_URL = "http://localhost"
    AUTO_CREATE_DB = True
    LOG_JSON = False


# Dizionario delle configurazioni.
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    # Per sicurezza, il default punta alla produzione così da evitare
    # avvio accidentale con DEBUG attivo in ambienti non configurati.
    "default": ProductionConfig,
}
