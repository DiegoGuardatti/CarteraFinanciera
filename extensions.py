"""
Extensiones Flask centralizadas
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
from utils.cache_config import configure_cache

# Instancias de extensiones
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour", "10 per minute"],
    storage_uri='memory://'
)
swagger = None  # Se inicializa en create_app

def init_extensions(app):
    """Inicializar todas las extensiones con la aplicación Flask"""
    
    # Configurar base de datos
    db.init_app(app)
    
    # Configurar migraciones
    migrate.init_app(app, db)
    
    # Configurar CSRF protection
    csrf.init_app(app)
    
    # Configurar rate limiting
    limiter.init_app(app)
    
    # Configurar sistema de caching
    cache = configure_cache(app)
    
    # Configurar Swagger para documentación API
    global swagger
    swagger = Swagger(app, config={
        'title': 'Cartera Financiera API',
        'description': 'API RESTful para gestión de cartera financiera con métricas avanzadas',
        'version': '1.0.0',
        'specs_route': '/apidocs/',
        'specs': [
            {
                'endpoint': 'v1_spec',
                'route': '/apidocs/v1.json',
                'title': 'Cartera Financiera API v1',
                'description': 'API RESTful para gestión de cartera financiera con métricas avanzadas',
                'version': '1.0.0'
            }
        ],
        'headers': [],
        'ui_params': {
            'tryItOutEnabled': True,
            'operationsSorter': 'alpha',
            'tagsSorter': 'alpha',
            'docExpansion': 'list'
        }
    })
    
    return cache

def get_swagger():
    """Obtener instancia de Swagger"""
    return swagger