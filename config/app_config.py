import os
from datetime import timedelta


def env_bool(name: str, default: bool = False) -> bool:
    """Legge un booleano da ambiente con valori espliciti e prevedibili."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    """Legge un intero da ambiente, ignorando valori non validi."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def env_list(name: str, default=None):
    """Legge una lista separata da virgole (utile per TRUSTED_HOSTS)."""
    value = os.environ.get(name)
    if value is None:
        return list(default) if default is not None else None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _database_url():
    """Normalizza l'URL PostgreSQL fornito dai provider (es. Heroku)."""
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Configurazione base dell'applicazione."""

    # In produzione non deve esistere fallback: viene verificato in app factory.
    SECRET_KEY = os.environ.get("SECRET_KEY")

    DATABASE_URL = _database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///poems.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookie di sessione: HttpOnly sempre, SameSite esplicito.
    SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "aleshaikus_session")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # CSRF applicativo (synchronizer token in sessione).
    CSRF_ENABLED = env_bool("CSRF_ENABLED", True)

    # Host e URL canonico: niente fiducia implicita nell'header Host.
    TRUSTED_HOSTS = None
    CANONICAL_BASE_URL = os.environ.get(
        "CANONICAL_BASE_URL", "http://localhost:5000"
    ).rstrip("/")
    TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0)

    # Limiti di richiesta: nessun upload previsto, 1 MiB è abbondante.
    MAX_CONTENT_LENGTH = 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 512 * 1024

    # Rate limiting configurabile (in produzione usare Redis per più worker).
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_ENABLED = env_bool("RATELIMIT_ENABLED", True)

    # Schema: in produzione può essere disattivato dopo il baseline Alembic.
    AUTO_CREATE_DB = env_bool("AUTO_CREATE_DB", True)

    # Logging strutturato.
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_JSON = env_bool("LOG_JSON", False)


class DevelopmentConfig(Config):
    """Configurazione per ambiente di sviluppo locale."""

    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-local-only"
    SQLALCHEMY_DATABASE_URI = _database_url() or "sqlite:///poems.db"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0)


class ProductionConfig(Config):
    """Configurazione per ambiente di produzione (PostgreSQL obbligatorio)."""

    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
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
    CANONICAL_BASE_URL = os.environ.get(
        "CANONICAL_BASE_URL", "https://www.aleshaikus.me"
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
