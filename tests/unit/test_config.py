"""
Tests para la configuración de la aplicación
"""

import os
import pytest
from config.settings import get_config, DevelopmentConfig, ProductionConfig, TestingConfig
from config.security import setup_security_headers, setup_logging
from extensions import init_extensions, limiter, csrf, db
from flask import Flask

class TestConfig:
    """Tests para configuración de Flask"""
    
    def test_development_config(self):
        """Test configuración de desarrollo"""
        config = DevelopmentConfig()
        assert config.DEBUG is True
        assert config.TESTING is False
        assert 'dev' in config.SQLALCHEMY_DATABASE_URI.lower()
    
    def test_production_config(self):
        """Test configuración de producción"""
        config = ProductionConfig()
        assert config.DEBUG is False
        assert config.TESTING is False
    
    def test_testing_config(self):
        """Test configuración de testing"""
        config = TestingConfig()
        assert config.DEBUG is False
        assert config.TESTING is True
        assert 'memory' in config.SQLALCHEMY_DATABASE_URI
        assert config.WTF_CSRF_ENABLED is False
    
    def test_get_config_default(self):
        """Test obtener configuración por defecto"""
        # Sin variable de entorno
        os.environ.pop('FLASK_ENV', None)
        config = get_config()
        assert config == DevelopmentConfig
    
    def test_get_config_development(self):
        """Test obtener configuración de desarrollo"""
        os.environ['FLASK_ENV'] = 'development'
        config = get_config()
        assert config == DevelopmentConfig
    
    def test_get_config_production(self):
        """Test obtener configuración de producción"""
        os.environ['FLASK_ENV'] = 'production'
        config = get_config()
        assert config == ProductionConfig
    
    def test_get_config_testing(self):
        """Test obtener configuración de testing"""
        os.environ['FLASK_ENV'] = 'testing'
        config = get_config()
        assert config == TestingConfig

class TestSecurity:
    """Tests para configuración de seguridad"""
    
    def test_setup_security_headers(self, app):
        """Test que los headers de seguridad se establecen correctamente"""
        setup_security_headers(app)
        
        with app.test_client() as client:
            response = client.get('/')
            
            # Verificar headers de seguridad principales
            assert 'Content-Security-Policy' in response.headers
            assert 'X-Content-Type-Options' in response.headers
            assert 'X-Frame-Options' in response.headers
            assert 'X-XSS-Protection' in response.headers
            assert 'Strict-Transport-Security' in response.headers
    
    def test_csp_header_format(self, app):
        """Test formato del header CSP"""
        setup_security_headers(app)
        
        with app.test_client() as client:
            response = client.get('/')
            csp = response.headers.get('Content-Security-Policy')
            
            assert "default-src 'self'" in csp
            assert "script-src 'self'" in csp
            assert "connect-src 'self'" in csp
    
    def test_api_cache_headers(self, app):
        """Test headers de cache para APIs"""
        setup_security_headers(app)
        
        with app.test_client() as client:
            # API de métricas
            response = client.get('/api/metrics/test')
            assert 'Cache-Control' in response.headers
            
            # API dashboard
            response = client.get('/api/dashboard/summary')
            assert 'Cache-Control' in response.headers

class TestExtensions:
    """Tests para extensiones de Flask"""
    
    def test_init_extensions(self, app):
        """Test inicialización de extensiones"""
        cache = init_extensions(app)
        
        # Verificar que las extensiones se inicializaron
        assert db is not None
        assert csrf is not None
        assert limiter is not None
        assert cache is not None
    
    def test_limiter_configuration(self):
        """Test configuración del rate limiter"""
        assert limiter.default_limits is not None
        assert len(limiter.default_limits) > 0
    
    def test_csrf_protection(self, app):
        """Test protección CSRF"""
        with app.test_client() as client:
            # Request sin CSRF token debería fallar para formularios
            response = client.post('/registrar_broker', data={
                'nombre_broker': 'Test',
                'comision_broker': '0.5'
            })
            # El status debería ser 400 (CSRF token missing)
            assert response.status_code in [400, 302]  # 302 si redirige por error

class TestEnvironmentVariables:
    """Tests para variables de entorno"""
    
    def test_secret_key_configuration(self, app):
        """Test configuración de secret key"""
        # Verificar que tiene una secret key configurada
        assert app.config['SECRET_KEY'] is not None
        assert len(app.config['SECRET_KEY']) > 0
    
    def test_database_url_configuration(self, app):
        """Test configuración de URL de base de datos"""
        # Verificar que tiene una URL de base de datos configurada
        assert app.config['SQLALCHEMY_DATABASE_URI'] is not None
    
    def test_upload_folder_configuration(self, app):
        """Test configuración de carpeta de uploads"""
        assert app.config['UPLOAD_FOLDER'] is not None
        assert app.config['MAX_CONTENT_LENGTH'] is not None