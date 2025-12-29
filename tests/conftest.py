"""
Configuración global de pytest y fixtures compartidas
"""

import pytest
import tempfile
import os
from flask import Flask
from app import create_app
from extensions import db
from modelo import Ticker, Broker, Comitente, InstrumentoFinanciero, Activo
from datetime import datetime

@pytest.fixture(scope="session")
def app():
    """Crear aplicación Flask para tests"""
    # Configuración de testing
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'DEBUG': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Cliente de prueba para hacer requests HTTP"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner de comandos CLI para tests"""
    return app.test_cli_runner()

@pytest.fixture
def database(app):
    """Base de datos con datos de prueba"""
    with app.app_context():
        # Crear datos de prueba
        broker = Broker(Nombre="Broker Test", Comision=0.5, Asesor="Asesor Test")
        comitente = Comitente(Titular="Juan Test", Numero="123456", Id_Broker=1)
        instrumento = InstrumentoFinanciero(Nombre="Acción Test")
        ticker = Ticker(Nombre_Ticker="TEST", Descripcion="Ticker de prueba", Id_InstrumentoFinanciero=1)
        
        db.session.add_all([broker, comitente, instrumento, ticker])
        db.session.commit()
        
        yield {
            'broker': broker,
            'comitente': comitente, 
            'instrumento': instrumento,
            'ticker': ticker
        }
        
        # Limpiar datos
        db.session.rollback()

@pytest.fixture
def active_assets(database):
    """Activos de prueba en cartera"""
    activos = []
    with database['broker'].__class__.query.session.no_autoflush:
        for i in range(3):
            activo = Activo(
                Id_Broker=1,
                Id_Comitente=1,
                Id_Ticker=1,
                Precio_Compra=100.0 + i * 10,
                Cantidad_Nominales_Compra=10,
                Total_Pesos_Compra=(100.0 + i * 10) * 10,
                Total_Dolares_Compra=((100.0 + i * 10) * 10) / 1000,
                Fecha_Hora_Compra=datetime.now(),
                Precio_Dolar_MEP_Compra=1000,
                Activo_Estado="EN_CARTERA"
            )
            db.session.add(activo)
            activos.append(activo)
    
    db.session.commit()
    return activos

@pytest.fixture
def sold_assets(database):
    """Activos de prueba vendidos"""
    activos = []
    with database['broker'].__class__.query.session.no_autoflush:
        for i in range(2):
            activo = Activo(
                Id_Broker=1,
                Id_Comitente=1,
                Id_Ticker=1,
                Precio_Compra=100.0,
                Cantidad_Nominales_Compra=10,
                Total_Pesos_Compra=1000,
                Total_Dolares_Compra=1,
                Fecha_Hora_Compra=datetime.now(),
                Precio_Venta=120.0,
                Cantidad_Nominales_Venta=10,
                Total_Pesos_Venta=1200,
                Total_Dolares_Venta=1.2,
                Fecha_Hora_Venta=datetime.now(),
                Precio_Dolar_MEP_Compra=1000,
                Precio_Dolar_MEP_Venta=1000,
                Activo_Estado="VENDIDO"
            )
            db.session.add(activo)
            activos.append(activo)
    
    db.session.commit()
    return activos

@pytest.fixture
def sample_form_data():
    """Datos de formulario de ejemplo"""
    return {
        'broker_form': {
            'nombre_broker': 'Test Broker',
            'comision_broker': '0.5',
            'asesor_broker': 'Test Advisor'
        },
        'comitente_form': {
            'titular_comitente': 'Juan Pérez',
            'numero_comitente': '123456',
            'id_broker': '1'
        },
        'instrumento_form': {
            'nombre_instrumento': 'Acción'
        },
        'ticker_form': {
            'nuevo_ticker': 'TEST',
            'descripcion_ticker': 'Ticker de prueba',
            'select_instrumento': '1'
        }
    }

@pytest.fixture
def auth_headers():
    """Headers de autenticación para APIs"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

@pytest.fixture
def json_data():
    """Helper para datos JSON"""
    return {
        'broker': {
            'nombre': 'Test Broker',
            'comision': 0.5,
            'asesor': 'Test Advisor'
        },
        'comitente': {
            'titular': 'Juan Pérez',
            'numero': '123456',
            'id_broker': 1
        }
    }

# Fixtures para testing de seguridad
@pytest.fixture
def xss_payloads():
    """Payloads para testing XSS"""
    return [
        '<script>alert("xss")</script>',
        'javascript:alert("xss")',
        '<img src="x" onerror="alert(1)">',
        '"><script>alert("xss")</script>',
        "'; DROP TABLE users; --"
    ]

@pytest.fixture
def sql_injection_payloads():
    """Payloads para testing SQL injection"""
    return [
        "' OR '1'='1",
        "'; DROP TABLE brokers; --",
        "' UNION SELECT * FROM brokers --",
        "admin'--",
        "' OR 1=1#"
    ]

# Markers para categorizar tests
pytestmark = [
    pytest.mark.unit,
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.api,
    pytest.mark.database
]