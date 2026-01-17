"""
Extensiones Flask centralizadas
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

# Importaciones opcionales
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    FLASK_LIMITER_AVAILABLE = True
except ImportError:
    FLASK_LIMITER_AVAILABLE = False
    def get_remote_address():
        return 'unknown'
    class Limiter:
        def __init__(self, key_func=None, default_limits=None, storage_uri=None):
            self.key_func = key_func
            self.default_limits = default_limits or []
            self.storage_uri = storage_uri
        def init_app(self, app):
            pass
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

try:
    from flasgger import Swagger
    FLASGGER_AVAILABLE = True
except ImportError:
    FLASGGER_AVAILABLE = False
    # Mock Swagger class
    class Swagger:
        def __init__(self, app, config=None):
            self.app = app
            self.config = config or {}
        def __call__(self, *args, **kwargs):
            return self

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
cache = None  # Se inicializa en init_extensions

def init_extensions(app):
    """Inicializar todas las extensiones con la aplicación Flask"""
    
    # Configurar base de datos
    db.init_app(app)
    
    # Configurar migraciones
    migrate.init_app(app, db)
    
    # Configurar CSRF protection
    csrf.init_app(app)
    
    # Configurar rate limiting si está disponible
    if FLASK_LIMITER_AVAILABLE:
        limiter.init_app(app)
    else:
        print("⚠️ Flask-Limiter no disponible, rate limiting deshabilitado")
    
    # Configurar sistema de caching
    global cache
    cache = configure_cache(app)
    
    # Configurar Swagger para documentación API si está disponible
    global swagger
    if FLASGGER_AVAILABLE:
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
    else:
        # Crear instancia mock de Swagger
        swagger = type('MockSwagger', (), {
            'config': {
                'title': 'Cartera Financiera API (Mock)',
                'description': 'Documentación API no disponible',
                'version': '1.0.0'
            }
        })()
        print("⚠️ Flasgger no disponible, documentación API deshabilitada")
    
    return cache

def get_swagger():
    """Obtener instancia de Swagger"""
    return swagger