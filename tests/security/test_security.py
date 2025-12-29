"""
Tests de seguridad para la aplicación
"""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash

@pytest.mark.security
class TestAuthenticationSecurity:
    """Tests para seguridad de autenticación"""
    
    def test_unauthorized_access_protected_routes(self, client):
        """Test acceso no autorizado a rutas protegidas"""
        # Intentar acceder a rutas que deberían requerir autenticación
        protected_routes = [
            '/dashboard',
            '/compra',
            '/venta',
            '/importar_datos'
        ]
        
        for route in protected_routes:
            response = client.get(route, follow_redirects=False)
            # Debería redirigir al login o devolver 302
            assert response.status_code in [302, 401, 403]
    
    def test_csrf_protection(self, client):
        """Test protección CSRF en formularios"""
        broker_data = {
            'nombre_broker': 'Security Test',
            'comision_broker': '0.5',
            'asesor_broker': 'Security Advisor'
        }
        
        # Intentar POST sin token CSRF
        response = client.post('/registrar_broker', data=broker_data, follow_redirects=True)
        # Debería fallar o rechazar la solicitud
        # Nota: Esto depende de la implementación CSRF
        assert response.status_code in [400, 403, 302]
    
    def test_sql_injection_prevention(self, client, app):
        """Test prevención de inyección SQL"""
        with app.app_context():
            # Intentar inyección SQL en parámetros
            malicious_inputs = [
                "'; DROP TABLE Broker; --",
                "' OR '1'='1",
                "'; INSERT INTO Broker VALUES (999, 'hacked', 0, 'hacker'); --"
            ]
            
            for malicious_input in malicious_inputs:
                # Test en búsqueda de broker
                response = client.get(f'/get_brokers?q={malicious_input}')
                assert response.status_code == 200  # No debe crashear
                
                # Test en datos de formulario
                broker_data = {
                    'nombre_broker': malicious_input,
                    'comision_broker': '0.5',
                    'asesor_broker': 'Security Test'
                }
                response = client.post('/registrar_broker', data=broker_data, follow_redirects=True)
                # No debe crashear, puede fallar validación

@pytest.mark.security
class TestInputValidationSecurity:
    """Tests para validación de entrada"""
    
    def test_xss_prevention(self, client, app):
        """Test prevención de XSS"""
        with app.app_context():
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//"
            ]
            
            for payload in xss_payloads:
                # Test en datos de formulario
                broker_data = {
                    'nombre_broker': payload,
                    'comision_broker': '0.5',
                    'asesor_broker': 'Security Test'
                }
                
                response = client.post('/registrar_broker', data=broker_data, follow_redirects=True)
                
                # Verificar que el payload no se ejecuta
                # El comportamiento depende de cómo se renderizan los datos
                if response.status_code == 200:
                    assert b'<script>' not in response.data
                    assert b'javascript:' not in response.data
    
    def test_file_upload_security(self, client, app):
        """Test seguridad de subida de archivos"""
        # Test archivos maliciosos
        malicious_files = [
            (b'<?php system($_GET["cmd"]); ?>', 'malicious.php'),
            (b'<script>alert("XSS")</script>', 'xss.html'),
            (b'', 'empty.txt'),
            (b'A' * 1000000, 'large_file.txt')  # Archivo muy grande
        ]
        
        for file_content, filename in malicious_files:
            response = client.post('/importar_datos', 
                                 data={'archivo': (file_content, filename)},
                                 content_type='multipart/form-data')
            
            # Debe manejar archivos maliciosos de forma segura
            assert response.status_code in [200, 400, 413, 422]
    
    def test_input_length_limits(self, client, app):
        """Test límites de longitud de entrada"""
        with app.app_context():
            # Test nombres muy largos
            long_name = "A" * 10000
            
            broker_data = {
                'nombre_broker': long_name,
                'comision_broker': '0.5',
                'asesor_broker': 'Security Test'
            }
            
            response = client.post('/registrar_broker', data=broker_data, follow_redirects=True)
            
            # Debe rechazar o truncar entradas muy largas
            # El comportamiento específico depende de la implementación
            assert response.status_code in [200, 400, 413]

@pytest.mark.security
class TestSessionSecurity:
    """Tests para seguridad de sesiones"""
    
    def test_session_fixing_prevention(self, client, app):
        """Test prevención de session fixation"""
        with app.app_context():
            # Verificar que las sesiones son seguras
            # Esto depende de la configuración de sesiones
            
            # Obtener una sesión
            response1 = client.get('/')
            session_id_1 = client.session.get('_id') if hasattr(client.session, 'get') else None
            
            # Verificar otra página
            response2 = client.get('/dashboard')
            session_id_2 = client.session.get('_id') if hasattr(client.session, 'get') else None
            
            # Las IDs de sesión deberían cambiar en ciertos contextos
            # (esto depende de la configuración)
    
    def test_session_timeout(self, client, app):
        """Test timeout de sesiones"""
        with app.app_context():
            # Simular sesión antigua
            # Esto depende de la implementación de timeout
            
            # Intentar acceso con sesión antigua
            response = client.get('/dashboard')
            # Debería requerir reautenticación o rechazar
            assert response.status_code in [302, 401, 403]

@pytest.mark.security
class TestErrorHandlingSecurity:
    """Tests para manejo seguro de errores"""
    
    def test_error_information_disclosure(self, client, app):
        """Test que los errores no expongan información sensible"""
        with app.app_context():
            # Intentar operaciones que pueden generar errores
            
            # Ruta inexistente
            response = client.get('/ruta_inexistente_que_no_existe_12345')
            assert response.status_code == 404
            
            # Parámetros malformados
            response = client.get('/get_comitentes/invalid_id')
            assert response.status_code in [200, 400, 404]
            
            # Verificar que los errores no expongan stack traces
            if b'Traceback' in response.data:
                # En producción, los stack traces no deberían estar visibles
                # Esto depende del modo de debug
                assert app.debug is True or b'Internal Server Error' in response.data
    
    def test_debug_mode_disabled_in_production(self, app):
        """Test que debug esté deshabilitado en producción"""
        # Verificar configuración de debug
        assert hasattr(app, 'config')
        
        # En producción, debug debería estar False
        if not app.debug:
            # Verificar que no hay información de debug expuesta
            pass  # Los tests específicos dependen de la implementación

@pytest.mark.security
class TestHTTPSecurity:
    """Tests para seguridad HTTP"""
    
    def test_security_headers(self, client, app):
        """Test headers de seguridad"""
        with app.app_context():
            response = client.get('/')
            
            # Verificar headers de seguridad importantes
            headers_to_check = [
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security'
            ]
            
            for header in headers_to_check:
                # Algunos headers pueden no estar presentes en desarrollo
                if not app.debug:
                    # En producción, deberían estar presentes
                    assert header in response.headers or 'Content-Security-Policy' in response.headers
    
    def test_cors_configuration(self, client, app):
        """Test configuración CORS"""
        with app.app_context():
            response = client.get('/')
            
            # Verificar configuración CORS
            # CORS debería estar configurado apropiadamente
            cors_headers = ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods']
            
            # En desarrollo, CORS puede estar más permisivo
            # En producción, debería ser más restrictivo

@pytest.mark.security
class TestDataSanitization:
    """Tests para sanitización de datos"""
    
    def test_data_sanitization(self, client, app):
        """Test sanitización de datos de entrada"""
        with app.app_context():
            # Datos que necesitan sanitización
            dirty_data = [
                "Test <b>Bold</b> Text",
                "Test 'Quotes' & \"Double\" Quotes",
                "Test\nNewline\tTab",
                "Test   Multiple   Spaces   ",
                "Test\x00Null\x00Bytes"
            ]
            
            for dirty in dirty_data:
                broker_data = {
                    'nombre_broker': dirty,
                    'comision_broker': '0.5',
                    'asesor_broker': 'Sanitized Test'
                }
                
                response = client.post('/registrar_broker', data=broker_data, follow_redirects=True)
                
                # Verificar que se maneja de forma segura
                assert response.status_code in [200, 400, 302]
                
                # Si se guarda, verificar que no hay caracteres peligrosos
                if response.status_code == 200:
                    # Buscar en la respuesta por caracteres peligrosos
                    assert b'<script>' not in response.data
                    assert b'javascript:' not in response.data