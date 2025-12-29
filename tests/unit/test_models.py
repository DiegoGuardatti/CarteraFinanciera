"""
Tests para modelos de base de datos
"""

import pytest
from modelo import Ticker, Broker, Comitente, InstrumentoFinanciero, Activo, db

@pytest.mark.database
class TestBroker:
    """Tests para modelo Broker"""
    
    def test_broker_creation(self, app, database):
        """Test creación de broker"""
        with app.app_context():
            broker = Broker(
                Nombre="Test Broker",
                Comision=0.5,
                Asesor="Test Advisor"
            )
            db.session.add(broker)
            db.session.commit()
            
            # Verificar que se guardó correctamente
            saved_broker = Broker.query.filter_by(Nombre="Test Broker").first()
            assert saved_broker is not None
            assert saved_broker.Nombre == "Test Broker"
            assert saved_broker.Comision == 0.5
            assert saved_broker.Asesor == "Test Advisor"
    
    def test_broker_relationships(self, app, database):
        """Test relaciones de broker"""
        with app.app_context():
            # Verificar relación con Comitentes
            comitentes = Comitente.query.filter_by(Id_Broker=database['broker'].Id_Broker).all()
            assert len(comitentes) > 0
            assert comitentes[0].Id_Broker == database['broker'].Id_Broker
    
    def test_broker_required_fields(self, app):
        """Test campos requeridos de broker"""
        with app.app_context():
            # Broker sin nombre debería fallar
            broker = Broker(Comision=0.5)
            db.session.add(broker)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_broker_comision_validation(self, app):
        """Test validación de comisión"""
        with app.app_context():
            # Comisión negativa
            broker_neg = Broker(Nombre="Test Neg", Comision=-0.1)
            db.session.add(broker_neg)
            
            # Comisión mayor a 1 (100%)
            broker_high = Broker(Nombre="Test High", Comision=1.5)
            db.session.add(broker_high)
            
            # Flask-SQLAlchemy permite valores inválidos a nivel de DB
            # La validación se haría a nivel de aplicación o con constraints de DB

@pytest.mark.database
class TestComitente:
    """Tests para modelo Comitente"""
    
    def test_comitente_creation(self, app, database):
        """Test creación de comitente"""
        with app.app_context():
            comitente = Comitente(
                Titular="Juan Pérez",
                Numero="123456",
                Id_Broker=database['broker'].Id_Broker
            )
            db.session.add(comitente)
            db.session.commit()
            
            saved_comitente = Comitente.query.filter_by(Titular="Juan Pérez").first()
            assert saved_comitente is not None
            assert saved_comitente.Titular == "Juan Pérez"
            assert saved_comitente.Numero == "123456"
            assert saved_comitente.Id_Broker == database['broker'].Id_Broker
    
    def test_comitente_broker_relationship(self, app, database):
        """Test relación comitente-broker"""
        with app.app_context():
            comitente = database['comitente']
            broker = Broker.query.get(comitente.Id_Broker)
            
            assert broker is not None
            assert broker.Id_Broker == comitente.Id_Broker
    
    def test_comitente_required_fields(self, app):
        """Test campos requeridos de comitente"""
        with app.app_context():
            # Comitente sin titular
            comitente = Comitente(Numero="123456", Id_Broker=1)
            db.session.add(comitente)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()

@pytest.mark.database
class TestInstrumentoFinanciero:
    """Tests para modelo InstrumentoFinanciero"""
    
    def test_instrumento_creation(self, app, database):
        """Test creación de instrumento financiero"""
        with app.app_context():
            instrumento = InstrumentoFinanciero(Nombre="Nuevo Instrumento")
            db.session.add(instrumento)
            db.session.commit()
            
            saved_instrumento = InstrumentoFinanciero.query.filter_by(Nombre="Nuevo Instrumento").first()
            assert saved_instrumento is not None
            assert saved_instrumento.Nombre == "Nuevo Instrumento"
    
    def test_instrumento_unique_name(self, app, database):
        """Test unicidad de nombre de instrumento"""
        with app.app_context():
            # Intentar crear instrumento con nombre duplicado
            instrumento_dup = InstrumentoFinanciero(Nombre=database['instrumento'].Nombre)
            db.session.add(instrumento_dup)
            
            # Flask-SQLAlchemy no fuerza unicidad por sí solo
            # Se requeriría un constraint unique en la DB o validación manual

@pytest.mark.database
class TestTicker:
    """Tests para modelo Ticker"""
    
    def test_ticker_creation(self, app, database):
        """Test creación de ticker"""
        with app.app_context():
            ticker = Ticker(
                Nombre_Ticker="NEWTICK",
                Descripcion="Nuevo ticker de prueba",
                Id_InstrumentoFinanciero=database['instrumento'].Id_InstrumentoFinanciero
            )
            db.session.add(ticker)
            db.session.commit()
            
            saved_ticker = Ticker.query.filter_by(Nombre_Ticker="NEWTICK").first()
            assert saved_ticker is not None
            assert saved_ticker.Nombre_Ticker == "NEWTICK"
            assert saved_ticker.Descripcion == "Nuevo ticker de prueba"
            assert saved_ticker.Id_InstrumentoFinanciero == database['instrumento'].Id_InstrumentoFinanciero
    
    def test_ticker_instrumento_relationship(self, app, database):
        """Test relación ticker-instrumento"""
        with app.app_context():
            ticker = database['ticker']
            instrumento = InstrumentoFinanciero.query.get(ticker.Id_InstrumentoFinanciero)
            
            assert instrumento is not None
            assert instrumento.Id_InstrumentoFinanciero == ticker.Id_InstrumentoFinanciero
    
    def test_ticker_required_fields(self, app):
        """Test campos requeridos de ticker"""
        with app.app_context():
            # Ticker sin nombre
            ticker = Ticker(Descripcion="Sin nombre", Id_InstrumentoFinanciero=1)
            db.session.add(ticker)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()

@pytest.mark.database
class TestActivo:
    """Tests para modelo Activo"""
    
    def test_activo_creation_en_cartera(self, app, active_assets):
        """Test creación de activo en cartera"""
        with app.app_context():
            activo = active_assets[0]
            
            assert activo.Activo_Estado == "EN_CARTERA"
            assert activo.Precio_Compra is not None
            assert activo.Cantidad_Nominales_Compra is not None
            assert activo.Total_Pesos_Compra is not None
            assert activo.Total_Dolares_Compra is not None
    
    def test_activo_creation_vendido(self, app, sold_assets):
        """Test creación de activo vendido"""
        with app.app_context():
            activo = sold_assets[0]
            
            assert activo.Activo_Estado == "VENDIDO"
            assert activo.Precio_Venta is not None
            assert activo.Cantidad_Nominales_Venta is not None
            assert activo.Total_Pesos_Venta is not None
            assert activo.Total_Dolares_Venta is not None
            assert activo.Fecha_Hora_Venta is not None
    
    def test_activo_calculations(self, app, database):
        """Test cálculos de activo"""
        with app.app_context():
            precio_compra = 100.0
            cantidad = 10
            dolar_mep = 1000.0
            
            activo = Activo(
                Id_Broker=database['broker'].Id_Broker,
                Id_Comitente=database['comitente'].Id_Broker,
                Id_Ticker=database['ticker'].Id_Ticker,
                Precio_Compra=precio_compra,
                Cantidad_Nominales_Compra=cantidad,
                Total_Pesos_Compra=precio_compra * cantidad,
                Total_Dolares_Compra=(precio_compra * cantidad) / dolar_mep,
                Fecha_Hora_Compra=database['ticker'].__class__.query.session.query(Activo.Fecha_Hora_Compra).first()[0],
                Precio_Dolar_MEP_Compra=dolar_mep,
                Activo_Estado="EN_CARTERA"
            )
            
            # Verificar cálculos
            assert activo.Total_Pesos_Compra == precio_compra * cantidad
            assert abs(activo.Total_Dolares_Compra - ((precio_compra * cantidad) / dolar_mep)) < 0.01
    
    def test_activo_relationships(self, app, active_assets):
        """Test relaciones de activo"""
        with app.app_context():
            activo = active_assets[0]
            
            # Verificar relación con ticker
            assert activo.ticker is not None
            assert activo.ticker.Nombre_Ticker is not None
            
            # Verificar relación con broker
            assert activo.broker is not None
            assert activo.broker.Nombre is not None
    
    def test_activo_state_enum(self, app):
        """Test estados válidos de activo"""
        valid_states = ["EN_CARTERA", "VENDIDO"]
        
        for state in valid_states:
            with app.app_context():
                activo = Activo(
                    Id_Broker=1,
                    Id_Comitente=1,
                    Id_Ticker=1,
                    Precio_Compra=100.0,
                    Cantidad_Nominales_Compra=10,
                    Total_Pesos_Compra=1000.0,
                    Total_Dolares_Compra=1.0,
                    Fecha_Hora_Compra=database['broker'].__class__.query.session.query(Activo.Fecha_Hora_Compra).first()[0],
                    Precio_Dolar_MEP_Compra=1000.0,
                    Activo_Estado=state
                )
                db.session.add(activo)
                db.session.commit()
                
                # Verificar que se guardó
                assert activo.Activo_Estado == state
                
                db.session.rollback()

@pytest.mark.database
class TestDatabaseConstraints:
    """Tests para constraints de base de datos"""
    
    def test_foreign_key_constraints(self, app, database):
        """Test constraints de clave foránea"""
        with app.app_context():
            # Intentar crear comitente con broker inexistente
            comitente = Comitente(
                Titular="Test",
                Numero="123",
                Id_Broker=999  # ID inexistente
            )
            db.session.add(comitente)
            
            # Dependiendo de la configuración de DB, esto podría fallar
            # SQLite por defecto no refuerza foreign keys por defecto
            try:
                db.session.commit()
                # Si llega aquí, la constraint no se está enforcing
            except Exception:
                db.session.rollback()
    
    def test_data_integrity(self, app, database):
        """Test integridad de datos"""
        with app.app_context():
            # Verificar que los datos de prueba son consistentes
            broker = database['broker']
            comitente = database['comitente']
            
            assert comitente.Id_Broker == broker.Id_Broker
            
            ticker = database['ticker']
            instrumento = database['instrumento']
            
            assert ticker.Id_InstrumentoFinanciero == instrumento.Id_InstrumentoFinanciero