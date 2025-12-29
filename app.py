"""
Aplicación Flask principal - Arquitectura modular
Archivo principal minimalista que configura y ejecuta la aplicación
"""

from flask import Flask
from config.settings import load_env_file, get_config
from extensions import init_extensions, get_swagger
from config.security import configure_security
from routes.main import main_bp
from routes.ajax import ajax_bp
from routes.api_metrics import api_metrics_bp
from routes.api_advanced import api_advanced_bp
from routes.api_reports import api_reports_bp
from routes.imports import imports_bp
from routes.debug import debug_bp

def create_app():
    """Factory pattern para crear la aplicación Flask"""
    
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Cargar variables de entorno
    load_env_file('.env')
    
    # Aplicar configuración
    app.config.from_object(get_config())
    
    # Inicializar extensiones
    cache = init_extensions(app)
    
    # Configurar seguridad
    configure_security(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    return app, cache

def register_blueprints(app):
    """Registrar todos los blueprints de la aplicación"""
    
    # Rutas principales
    app.register_blueprint(main_bp)
    
    # Rutas AJAX
    app.register_blueprint(ajax_bp)
    
    # APIs de métricas básicas
    app.register_blueprint(api_metrics_bp)
    
    # APIs de métricas avanzadas
    app.register_blueprint(api_advanced_bp)
    
    # APIs de reportes
    app.register_blueprint(api_reports_bp)
    
    # Importación de archivos
    app.register_blueprint(imports_bp)
    
    # Rutas de debug
    app.register_blueprint(debug_bp)

# Crear instancia global de la aplicación
app, cache = create_app()
swagger = get_swagger()

# Punto de entrada
if __name__ == '__main__':
    # La aplicación ya está creada y configurada al inicio del archivo
    # Ejecutar en modo debug usando la configuración
    debug_mode = app.config.get('DEBUG', True)
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)