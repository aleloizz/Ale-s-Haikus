import os

class Config:
    """Configurazione base dell'applicazione"""

    # In produzione non deve esistere fallback: viene verificato in app factory
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Configurazione database PostgreSQL per Heroku
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///poems.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurazioni per JSON
    JSON_AS_ASCII = False  # Supporto caratteri Unicode
    JSONIFY_PRETTYPRINT_REGULAR = True

    # Configurazioni per upload file (se necessario in futuro)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

class DevelopmentConfig(Config):
    """Configurazione per ambiente di sviluppo"""
    DEBUG = True
    # In dev consentiamo un fallback per convenienza local
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///poems.db'

class ProductionConfig(Config):
    """Configurazione per ambiente di produzione"""
    DEBUG = False
    # Nessun fallback: deve essere impostata la variabile d'ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Verificata nella app factory

class TestingConfig(Config):
    """Configurazione per testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Dizionario delle configurazioni
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    # Per sicurezza, il default punta alla produzione così da evitare
    # avvio accidentale con DEBUG attivo in ambienti non configurati.
    'default': ProductionConfig
}
