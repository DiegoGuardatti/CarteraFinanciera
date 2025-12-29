"""
Configuración para la aplicación de Cartera Financiera
Permite configuración flexible por entornos manteniendo compatibilidad con MySQL existente
"""

import os
from datetime import timedelta

class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Configuración de base de datos - usar variable de entorno o SQLite por defecto
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cartera.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/cartera.log'
    
    # Upload configurations
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
    # Logging más detallado en desarrollo
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # Logging en producción
    LOG_LEVEL = 'INFO'
    
    # Configuraciones de seguridad más estrictas
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = False
    TESTING = True
    
    # Base de datos en memoria para tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Logging mínimo en tests
    LOG_LEVEL = 'ERROR'

# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """
    Obtiene la configuración especificada o la por defecto
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])

# Función para cargar variables de entorno desde archivo .env
def load_env_file(env_file='.env'):
    """Carga variables de entorno desde archivo .env"""
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"✅ Variables de entorno cargadas desde {env_file}")
        except ImportError:
            print("⚠️  python-dotenv no está instalado. Instalar con: pip install python-dotenv")
        except Exception as e:
            print(f"⚠️  Error cargando {env_file}: {e}")

# Configuración de logging
def setup_logging(app):
    """Configura el sistema de logging"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not app.debug and not app.testing:
        # Crear directorio de logs si no existe
        os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
        
        # Configurar file handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'], 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 Cartera Financiera iniciada')

# Configuración de extensiones Flask
def init_extensions(app):
    """Inicializa extensiones Flask"""
    from flask_caching import Cache
    
    # Configurar cache
    app.cache = Cache(app)
    
    # Configurar logging
    setup_logging(app)

# Variables de entorno recomendadas para .env
ENV_TEMPLATE = """
# Configuración para Cartera Financiera
# Copiar a .env y ajustar valores

# Flask configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here-change-in-production

# Database configuration (MySQL existente)
DATABASE_URL=mysql+pymysql://root@localhost/CarteraFinanciera?unix_socket=/opt/lampp/var/mysql/mysql.sock

# Cache configuration
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/cartera.log

# File uploads
UPLOAD_FOLDER=uploads

# Email configuration (para reportes automáticos)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# External APIs (para cotizaciones en tiempo real)
ALPHA_VANTAGE_API_KEY=your-api-key
FINNHUB_API_KEY=your-api-key
"""