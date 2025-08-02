import os

class Config:
    """Configurazione base dell'applicazione"""
    
    # Chiave segreta per le sessioni (usa variabile d'ambiente in produzione)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configurazione database PostgreSQL per Heroku
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///instance/poems.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurazioni per JSON
    JSON_AS_ASCII = False  # Supporto caratteri Unicode
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Configurazioni per upload file (se necessario in futuro)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

class DevelopmentConfig(Config):
    """Configurazione per ambiente di sviluppo"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/poems.db'

class ProductionConfig(Config):
    """Configurazione per ambiente di produzione"""
    DEBUG = False
    
    # In produzione, assicurati che SECRET_KEY sia impostata
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable must be set for production")

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
    'default': DevelopmentConfig
}
