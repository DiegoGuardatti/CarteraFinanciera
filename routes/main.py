"""
Rutas principales de la aplicación
"""

from flask import Blueprint, render_template
from modelo import Broker, InstrumentoFinanciero
from extensions import db

# Crear blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@main_bp.route('/compra')
def compra():
    """Página de registro de compras"""
    brokers = db.session.query(Broker).all()
    instrumentos = db.session.query(InstrumentoFinanciero).all()
    return render_template('compra.html', 
                         brokers=brokers, 
                         instrumentos=instrumentos)

@main_bp.route('/venta')
def venta():
    """Página de registro de ventas"""
    brokers = db.session.query(Broker).all()
    instrumentos = db.session.query(InstrumentoFinanciero).all()
    return render_template('venta.html', 
                         brokers=brokers, 
                         instrumentos=instrumentos)

@main_bp.route('/informe')
def informe():
    """Página de informes"""
    brokers = db.session.query(Broker).all()
    instrumentos = db.session.query(InstrumentoFinanciero).all()
    return render_template('informe.html', 
                         brokers=brokers, 
                         instrumentos=instrumentos)

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard ejecutivo con métricas financieras"""
    return render_template('dashboard.html')

@main_bp.route('/dashboard_avanzado')
def dashboard_avanzado():
    """Dashboard avanzado con análisis financiero profesional"""
    return render_template('dashboard_avanzado.html')

@main_bp.route('/formulario_venta')
def formulario_venta():
    """Formulario de venta"""
    brokers = db.session.query(Broker).all()
    instrumentos = db.session.query(InstrumentoFinanciero).all()
    return render_template('formulario_venta.html', 
                         brokers=brokers, 
                         instrumentos=instrumentos)

@main_bp.route('/descarga_reportes')
def descarga_reportes():
    """Página de descarga de reportes"""
    from modelo import Broker, Comitente, Ticker
    
    try:
        brokers = db.session.query(Broker).all()
        comitentes = db.session.query(Comitente).all()
        tickers = db.session.query(Ticker).all()
        
        return render_template('descarga_reportes.html', 
                             brokers=brokers, 
                             comitentes=comitentes, 
                             tickers=tickers)
        
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error cargando página de reportes: {str(e)}")
        from flask import jsonify
        return jsonify({'error': str(e)}), 500

