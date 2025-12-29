"""
Tests de integración para flujos de trabajo completos
"""

import pytest
import json
from modelo import Broker, Comitente, InstrumentoFinanciero, Ticker, Activo, db

@pytest.mark.integration
class TestBrokerWorkflow:
    """Test flujo completo de gestión de brokers"""
    
    def test_complete_broker_workflow(self, client, app):
        """Test flujo completo: crear broker → verificar → crear comitente"""
        with app.app_context():
            # 1. Crear un nuevo broker
            broker_data = {
                'nombre_broker': 'Workflow Broker',
                'comision_broker': '0.75',
                'asesor_broker': 'Workflow Advisor'
            }
            
            response = client.post('/registrar_broker', data=broker_data, follow_redirects=True)
            assert response.status_code in [200, 302]
            
            # 2. Verificar que se guardó en la base de datos
            broker = Broker.query.filter_by(Nombre='Workflow Broker').first()
            assert broker is not None
            assert broker.Comision == 0.75
            assert broker.Asesor == 'Workflow Advisor'
            
            # 3. Crear un comitente para este broker
            comitente_data = {
                'titular_comitente': 'Workflow Client',
                'numero_comitente': 'WORKFLOW001',
                'id_broker': str(broker.Id_Broker)
            }
            
            response = client.post('/registrar_comitente', data=comitente_data, follow_redirects=True)
            assert response.status_code in [200, 302]
            
            # 4. Verificar la relación
            comitente = Comitente.query.filter_by(Titular='Workflow Client').first()
            assert comitente is not None
            assert comitente.Id_Broker == broker.Id_Broker

@pytest.mark.integration
class TestTickerWorkflow:
    """Test flujo completo de gestión de tickers"""
    
    def test_complete_ticker_workflow(self, client, app):
        """Test flujo completo: crear instrumento → crear ticker → verificar relación"""
        with app.app_context():
            # 1. Crear un nuevo instrumento financiero
            instrumento_data = {
                'nombre_instrumento': 'Workflow Instrumento'
            }
            
            response = client.post('/registrar_InstrumentoFinanciero', 
                                  data=instrumento_data, 
                                  follow_redirects=True)
            assert response.status_code in [200, 302]
            
            # 2. Verificar que se guardó
            instrumento = InstrumentoFinanciero.query.filter_by(Nombre='Workflow Instrumento').first()
            assert instrumento is not None
            
            # 3. Crear un ticker para este instrumento
            ticker_data = {
                'nuevo_ticker': 'WFTICK',
                'descripcion_ticker': 'Ticker de workflow',
                'select_instrumento': str(instrumento.Id_InstrumentoFinanciero)
            }
            
            response = client.post('/registrar_ticker', 
                                  data=ticker_data, 
                                  follow_redirects=True)
            assert response.status_code in [200, 302]
            
            # 4. Verificar que se guardó y tiene la relación correcta
            ticker = Ticker.query.filter_by(Nombre_Ticker='WFTICK').first()
            assert ticker is not None
            assert ticker.Id_InstrumentoFinanciero == instrumento.Id_InstrumentoFinanciero

@pytest.mark.integration
class TestAjaxIntegration:
    """Test integración de endpoints AJAX"""
    
    def test_ajax_data_consistency(self, client, app, database):
        """Test consistencia de datos entre endpoints AJAX"""
        with app.app_context():
            # 1. Verificar que los datos de AJAX coinciden con la DB
            response = client.get('/get_instrumentos_financieros')
            assert response.status_code == 200
            
            ajax_data = json.loads(response.data)
            db_data = InstrumentoFinanciero.query.all()
            
            # Verificar que la cantidad coincide
            assert len(ajax_data) == len(db_data)
            
            # Verificar que los datos coinciden
            for i, ajax_item in enumerate(ajax_data):
                db_item = db_data[i]
                assert ajax_item['Id_InstrumentoFinanciero'] == db_item.Id_InstrumentoFinanciero
                assert ajax_item['Nombre'] == db_item.Nombre
    
    def test_ajax_relationships(self, client, app, database):
        """Test relaciones a través de AJAX"""
        with app.app_context():
            # Test get_comitentes con un broker válido
            broker_id = database['broker'].Id_Broker
            response = client.get(f'/get_comitentes/{broker_id}')
            assert response.status_code == 200
            
            ajax_data = json.loads(response.data)
            assert 'comitentes' in ajax_data
            
            # Verificar que los comitentes pertenecen al broker correcto
            for comitente in ajax_data['comitentes']:
                db_comitente = Comitente.query.get(comitente['Id_Comitente'])
                assert db_comitente.Id_Broker == broker_id
    
    def test_ajax_error_handling(self, client, app):
        """Test manejo de errores en AJAX"""
        with app.app_context():
            # Test con broker inexistente
            response = client.get('/get_comitentes/99999')
            assert response.status_code == 200  # No debe dar error 500
            
            ajax_data = json.loads(response.data)
            assert 'comitentes' in ajax_data
            assert len(ajax_data['comitentes']) == 0

@pytest.mark.integration
class TestFormValidationIntegration:
    """Test validación de formularios en contexto real"""
    
    def test_form_validation_errors(self, client, app):
        """Test validación de errores en formularios"""
        with app.app_context():
            # Test broker con datos vacíos
            response = client.post('/registrar_broker', data={}, follow_redirects=True)
            # Debería manejar el error graciosamente
            assert response.status_code in [200, 302]
    
    def test_duplicate_prevention(self, client, app, database):
        """Test prevención de duplicados"""
        with app.app_context():
            # Intentar crear un ticker con nombre duplicado
            ticker_data = {
                'nuevo_ticker': database['ticker'].Nombre_Ticker,
                'descripcion_ticker': 'Duplicado',
                'select_instrumento': str(database['instrumento'].Id_InstrumentoFinanciero)
            }
            
            response = client.post('/registrar_ticker', 
                                  data=ticker_data, 
                                  follow_redirects=True)
            
            # Debería manejar el duplicado graciosamente
            assert response.status_code in [200, 302]
            
            # Verificar que no se creó un duplicado
            count_before = Ticker.query.filter_by(Nombre_Ticker=database['ticker'].Nombre_Ticker).count()
            assert count_before == 1

@pytest.mark.integration
class TestDataConsistency:
    """Test consistencia de datos a través de la aplicación"""
    
    def test_broker_comitente_consistency(self, client, app, database):
        """Test consistencia entre brokers y comitentes"""
        with app.app_context():
            # Verificar que todos los comitentes tienen un broker válido
            comitentes = Comitente.query.all()
            for comitente in comitentes:
                broker = Broker.query.get(comitente.Id_Broker)
                assert broker is not None, f"Comitente {comitente.Id_Comitente} tiene broker inválido"
    
    def test_ticker_instrumento_consistency(self, client, app, database):
        """Test consistencia entre tickers e instrumentos"""
        with app.app_context():
            # Verificar que todos los tickers tienen un instrumento válido
            tickers = Ticker.query.all()
            for ticker in tickers:
                instrumento = InstrumentoFinanciero.query.get(ticker.Id_InstrumentoFinanciero)
                assert instrumento is not None, f"Ticker {ticker.Id_Ticker} tiene instrumento inválido"
    
    def test_activo_relationships_consistency(self, client, app, active_assets):
        """Test consistencia de relaciones de activos"""
        with app.app_context():
            for activo in active_assets:
                # Verificar relaciones
                assert activo.broker is not None
                assert activo.comitente is not None
                assert activo.ticker is not None
                
                # Verificar que las relaciones son consistentes
                assert activo.comitente.Id_Broker == activo.broker.Id_Broker

@pytest.mark.integration
class TestPerformanceIntegration:
    """Test de rendimiento en integración"""
    
    def test_multiple_ajax_calls(self, client, app, database):
        """Test múltiples llamadas AJAX concurrentes"""
        with app.app_context():
            broker_id = database['broker'].Id_Broker
            
            # Simular múltiples llamadas
            for i in range(5):
                response = client.get(f'/get_comitentes/{broker_id}')
                assert response.status_code == 200
                
                data = json.loads(response.data)
                assert 'comitentes' in data
    
    def test_large_dataset_handling(self, client, app):
        """Test manejo de datasets grandes"""
        with app.app_context():
            # Crear múltiples registros para test
            instruments = []
            for i in range(100):
                inst = InstrumentoFinanciero(Nombre=f'Instrumento {i}')
                instruments.append(inst)
                db.session.add(inst)
            
            db.session.commit()
            
            # Verificar que se pueden obtener todos
            response = client.get('/get_instrumentos_financieros')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert len(data) >= 100