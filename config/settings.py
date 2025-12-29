"""
Configuración de la aplicación Flask
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
def load_env_file(env_file='.env'):
    """Cargar archivo de variables de entorno"""
    if os.path.exists(env_file):
        load_dotenv(env_file)

def get_config():
    """Obtener configuración basada en el entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

class BaseConfig:
    """Configuración base"""
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/cartera.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Cache settings
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
    # Configuraciones específicas de desarrollo
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///instance/cartera_dev.db')
    
    # Cache más permisivo para desarrollo
    CACHE_TYPE = 'SimpleCache'
    
    # Rate limiting más permisivo para desarrollo
    RATELIMIT_STRATEGY = 'moving-window'

class TestingConfig(BaseConfig):
    """Configuración para testing"""
    DEBUG = False
    TESTING = True
    
    # Base de datos en memoria para tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Desactivar CSRF para tests
    WTF_CSRF_ENABLED = False
    
    # Cache nulo para tests
    CACHE_TYPE = 'NullCache'

class ProductionConfig(BaseConfig):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # Configuraciones específicas de producción
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Cache más robusto para producción
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate limiting más estricto para producción
    RATELIMIT_STRATEGY = 'moving-window'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Security headers más estrictos
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging más detallado
    LOG_LEVEL = 'WARNING'

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}