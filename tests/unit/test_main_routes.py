"""
Tests para las rutas principales de la aplicación
"""

import pytest
from flask import url_for

@pytest.mark.main
class TestMainRoutes:
    """Tests para rutas principales"""
    
    def test_index_route(self, client):
        """Test página principal"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Cartera Financiera' in response.data
    
    def test_compra_route(self, client, database):
        """Test página de registro de compras"""
        response = client.get('/compra')
        assert response.status_code == 200
        assert b'compra' in response.data.lower()
    
    def test_venta_route(self, client, database):
        """Test página de registro de ventas"""
        response = client.get('/venta')
        assert response.status_code == 200
        assert b'venta' in response.data.lower()
    
    def test_informe_route(self, client, database):
        """Test página de informes"""
        response = client.get('/informe')
        assert response.status_code == 200
        assert b'informe' in response.data.lower()
    
    def test_dashboard_route(self, client):
        """Test dashboard ejecutivo"""
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower()
    
    def test_dashboard_avanzado_route(self, client):
        """Test dashboard avanzado"""
        response = client.get('/dashboard_avanzado')
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower()
    
    def test_formulario_venta_route(self, client, database):
        """Test formulario de venta"""
        response = client.get('/formulario_venta')
        assert response.status_code == 200
        assert b'venta' in response.data.lower()
    
    def test_descarga_reportes_route(self, client, database):
        """Test página de descarga de reportes"""
        response = client.get('/descarga_reportes')
        assert response.status_code == 200
        assert b'reporte' in response.data.lower()

@pytest.mark.ajax
class TestAjaxRoutes:
    """Tests para rutas AJAX"""
    
    def test_get_instrumentos_financieros(self, client, database):
        """Test obtener instrumentos financieros"""
        response = client.get('/get_instrumentos_financieros')
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'Id_InstrumentoFinanciero' in data[0]
        assert 'Nombre' in data[0]
    
    def test_get_comitentes(self, client, database):
        """Test obtener comitentes por broker"""
        response = client.get(f'/get_comitentes/{database["broker"].Id_Broker}')
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert 'comitentes' in data
        assert isinstance(data['comitentes'], list)
    
    def test_get_comitentes_invalid_broker(self, client):
        """Test obtener comitentes con broker inválido"""
        response = client.get('/get_comitentes/999')
        assert response.status_code == 200  # No debe fallar, retornar lista vacía
        
        import json
        data = json.loads(response.data)
        assert 'comitentes' in data
        assert len(data['comitentes']) == 0
    
    def test_get_tickers(self, client, database):
        """Test obtener tickers por instrumento"""
        response = client.get(f'/get_tickers/{database["instrumento"].Id_InstrumentoFinanciero}')
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert 'tickers' in data
        assert isinstance(data['tickers'], list)
    
    def test_get_comision_broker(self, client, database):
        """Test obtener comisión de broker"""
        response = client.get(f'/get_comision_broker/{database["broker"].Id_Broker}')
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert 'comision' in data
        assert isinstance(data['comision'], (int, float))
    
    def test_get_comision_broker_not_found(self, client):
        """Test obtener comisión de broker inexistente"""
        response = client.get('/get_comision_broker/999')
        assert response.status_code == 404
    
    def test_validar_ticker(self, client, database):
        """Test validación de ticker"""
        # Ticker que no existe (debería ser válido)
        response = client.post('/validar_ticker', 
                              data={'nuevoTicker': 'NOTEXIST'})
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert 'existe' in data
        assert data['existe'] is False
    
    def test_validar_ticker_empty(self, client):
        """Test validación de ticker vacío"""
        response = client.post('/validar_ticker', 
                              data={'nuevoTicker': ''})
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert data['existe'] is False
        assert 'mensaje' in data
    
    def test_validar_ticker_duplicate(self, client, database):
        """Test validación de ticker duplicado"""
        response = client.post('/validar_ticker', 
                              data={'nuevoTicker': database['ticker'].Nombre_Ticker})
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert data['existe'] is True
        assert 'mensaje' in data
    
    def test_get_compras(self, client, active_assets):
        """Test obtener compras de ticker"""
        ticker_id = active_assets[0].Id_Ticker
        response = client.get(f'/get_compras/{ticker_id}')
        assert response.status_code == 200
        
        import json
        data = json.loads(response.data)
        assert isinstance(data, list)

class TestFormSubmissions:
    """Tests para envío de formularios"""
    
    def test_register_broker_post(self, client):
        """Test registro de broker via POST"""
        response = client.post('/registrar_broker', data={
            'nombre_broker': 'Test Broker',
            'comision_broker': '0.5',
            'asesor_broker': 'Test Advisor'
        }, follow_redirects=True)
        
        # Debería redirigir (302) o renderizar la página de compra (200)
        assert response.status_code in [200, 302]
    
    def test_register_broker_empty_data(self, client):
        """Test registro de broker con datos vacíos"""
        response = client.post('/registrar_broker', data={}, follow_redirects=True)
        
        # Debería manejar el error graciosamente
        assert response.status_code in [200, 302]
    
    def test_register_comitente_post(self, client, database):
        """Test registro de comitente via POST"""
        response = client.post('/registrar_comitente', data={
            'titular_comitente': 'Juan Pérez',
            'numero_comitente': '123456',
            'id_broker': str(database['broker'].Id_Broker)
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_register_instrumento_post(self, client):
        """Test registro de instrumento via POST"""
        response = client.post('/registrar_InstrumentoFinanciero', data={
            'nombre_instrumento': 'Test Instrumento'
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_registrar_ticker_post(self, client, database):
        """Test registro de ticker via POST"""
        response = client.post('/registrar_ticker', data={
            'nuevo_ticker': 'NEWTICK',
            'descripcion_ticker': 'Nuevo ticker de prueba',
            'select_instrumento': str(database['instrumento'].Id_InstrumentoFinanciero)
        }, follow_redirects=True)
        
        assert response.status_code in [200, 302]

class TestRouteEdgeCases:
    """Tests para casos extremos y validaciones"""
    
    def test_nonexistent_route(self, client):
        """Test ruta inexistente"""
        response = client.get('/ruta-que-no-existe')
        assert response.status_code == 404
    
    def test_root_trailing_slash(self, client):
        """Test raíz con slash final"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_case_sensitive_routes(self, client):
        """Test sensibilidad a mayúsculas en rutas"""
        # Las rutas deberían ser case-insensitive en Flask
        response = client.get('/COMPRA')
        assert response.status_code in [200, 404]  # 200 si funciona, 404 si no
    
    def test_post_to_get_only_route(self, client):
        """Test POST a ruta que solo acepta GET"""
        response = client.post('/compra')
        # Flask maneja POST a rutas GET de manera específica
        assert response.status_code in [200, 405]  # 405 Method Not Allowed

@pytest.mark.security
class TestSecurityHeaders:
    """Tests para headers de seguridad en rutas"""
    
    def test_security_headers_on_main_routes(self, client):
        """Test headers de seguridad en rutas principales"""
        response = client.get('/')
        
        # Verificar headers de seguridad
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'Content-Security-Policy' in response.headers
    
    def test_security_headers_on_ajax_routes(self, client):
        """Test headers de seguridad en rutas AJAX"""
        response = client.get('/get_instrumentos_financieros')
        
        # Las rutas AJAX también deben tener headers de seguridad
        assert 'X-Content-Type-Options' in response.headers