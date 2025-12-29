import datetime  # AÑADIDO: Import faltante en la línea 1
import csv
import io
from flask import Flask, jsonify, render_template, redirect, request, url_for, make_response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm, CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from wtforms import StringField, FloatField, SelectField, HiddenField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename
import os
import requests
from flasgger import Swagger
from modelo import Ticker, db, Comitente, Broker, InstrumentoFinanciero, Activo
from utils.csv_export import exportar_activos_csv, exportar_resumen_cartera_csv, crear_respuesta_csv
from utils.excel_export import exportar_activos_excel, crear_respuesta_excel
from utils.pdf_export import exportar_reporte_ejecutivo_pdf, exportar_reporte_detallado_pdf, crear_respuesta_pdf
from utils.cache_config import configure_cache, cache_with_params, get_cache_config_for_api
from calculos_metricas import (
    calcular_roi_activo, 
    calcular_roi_cartera_completa,
    calcular_sharpe_ratio,
    calcular_maximum_drawdown,
    calcular_var_simple,
    top_performers,
    bottom_performers,
    performance_por_ticker,
    resumen_ejecutivo
)
from metricas_avanzadas import (
    calcular_tir_completa,
    calcular_beta_activo,
    calcular_alpha_activo,
    matriz_correlacion_activos,
    diversificacion_cartera,
    backtesting_simple,
    analisis_sensibilidad
)
from config import get_config, load_env_file
import logging
import html
import re
from markupsafe import escape, Markup

# ==========================================
# FUNCIONES DE SEGURIDAD - SANITIZACIÓN XSS
# ==========================================

def sanitize_input(input_text, max_length=255, allow_html=False):
    """
    Sanitiza inputs para prevenir ataques XSS
    """
    if not input_text:
        return ""
    
    # Convertir a string si no lo es
    input_text = str(input_text)
    
    # Limitar longitud
    if len(input_text) > max_length:
        input_text = input_text[:max_length]
    
    # Escapar HTML por defecto
    if not allow_html:
        input_text = escape(input_text)
        # Remover caracteres peligrosos adicionales
        input_text = re.sub(r'[<>"\']', '', input_text)
    else:
        # Si se permite HTML básico, solo escapar etiquetas peligrosas
        dangerous_tags = ['script', 'object', 'embed', 'link', 'style', 'iframe', 'frame', 'frameset', 'noframes', 'applet', 'base', 'meta', 'head', 'html', 'body']
        for tag in dangerous_tags:
            input_text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', input_text, flags=re.IGNORECASE | re.DOTALL)
            input_text = re.sub(f'<{tag}[^>]*/?>', '', input_text, flags=re.IGNORECASE)
    
    # Remover null bytes
    input_text = input_text.replace('\x00', '')
    
    return input_text.strip()

def validate_email(email):
    """
    Valida formato de email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_ticker(ticker):
    """
    Valida formato de ticker (solo letras, números y guiones)
    """
    pattern = r'^[A-Z0-9\-\.]{1,10}$'
    return re.match(pattern, ticker) is not None

def validate_numeric_input(value, min_value=None, max_value=None):
    """
    Valida input numérico
    """
    try:
        # Convertir a float
        numeric_value = float(value)
        
        # Validar rangos
        if min_value is not None and numeric_value < min_value:
            return False, None
        if max_value is not None and numeric_value > max_value:
            return False, None
            
        return True, numeric_value
    except (ValueError, TypeError):
        return False, None

def validate_date(date_string):
    """
    Valida formato de fecha
    """
    try:
        datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except (ValueError, TypeError):
        return False

# ==========================================
# CLASE DE VALIDACIÓN PERSONALIZADA
# ==========================================

from wtforms.validators import ValidationError

class XSSValidator:
    """Validador personalizado para prevenir XSS"""
    
    def __init__(self, message=None):
        self.message = message or 'El campo contiene contenido potencialmente peligroso'
    
    def __call__(self, form, field):
        if field.data:
            # Lista de patrones XSS comunes
            xss_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',  # onload, onclick, etc.
                r'vbscript:',
                r'data:text/html',
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>'
            ]
            
            field_text = str(field.data).lower()
            
            for pattern in xss_patterns:
                if re.search(pattern, field_text, re.IGNORECASE):
                    raise ValidationError(self.message)

def create_flask_app():
    app = Flask(__name__)
    
    # Cargar variables de entorno
    load_env_file('.env')
    
    # Aplicar configuración
    app.config.from_object(get_config())
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Configurar sistema de caching
    cache = configure_cache(app)
    
    # Configurar CSRF protection
    csrf = CSRFProtect(app)
    
    # ==========================================
    # CONFIGURACIÓN DE FLASK-LIMITER
    # ==========================================
    
    # Configurar limiter - usar memory:// siempre para evitar dependencia de Redis
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour", "10 per minute"],
        storage_uri='memory://'
    )
    
    # Inicializar Flasgger para documentación API
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
    
    # ==========================================
    # HEADERS DE SEGURIDAD
    # ==========================================
    
    @app.after_request
    def set_security_headers(response):
        """Establece headers de seguridad en todas las respuestas"""
        
        # Content Security Policy (CSP) - Previene XSS
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://code.jquery.com https://stackpath.bootstrapcdn.com https://ajax.googleapis.com https://cdn.plot.ly; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com https://cdn.plot.ly https://fonts.googleapis.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HTTP Strict Transport Security (HSTS) - Fuerza HTTPS
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # X-Content-Type-Options - Previene MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options - Previene clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection - Filtro XSS del navegador
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy - Controla la información de referrer
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy - Controla APIs del navegador
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'fullscreen=(self), '
            'sync-xhr=(self)'
        )
        
        # Cache-Control para APIs sensibles
        if request.path.startswith('/api/'):
            if 'metrics' in request.path or 'dashboard' in request.path:
                # APIs de métricas pueden ser cacheadas por 1 minuto
                response.headers['Cache-Control'] = 'public, max-age=60'
            else:
                # Otras APIs no deben ser cacheadas
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        
        return response
    
    # Rate limiting se aplica mediante decoradores en las rutas individuales
    
    # Configurar logging
    if not app.debug and not app.testing:
        os.makedirs('logs', exist_ok=True)
        file_handler = logging.FileHandler('logs/cartera.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 Cartera Financiera iniciada')
    
    return app, cache, csrf, limiter, swagger

app, cache, csrf, limiter, swagger = create_flask_app()
migrate = Migrate(app, db)

# ==========================================
# FORMULARIOS CON CSRF PROTECTION
# ==========================================

class BrokerForm(FlaskForm):
    """Formulario para registrar brokers"""
    nombre_broker = StringField('Nombre del Broker', validators=[DataRequired()])
    comision_broker = FloatField('Comisión', validators=[DataRequired(), NumberRange(min=0, max=100)])
    asesor_broker = StringField('Asesor')

class ComitenteForm(FlaskForm):
    """Formulario para registrar comitentes"""
    titular_comitente = StringField('Titular', validators=[DataRequired()])
    numero_comitente = StringField('Número', validators=[DataRequired()])
    id_broker = SelectField('Broker', coerce=int, validators=[DataRequired()])

class InstrumentoFinancieroForm(FlaskForm):
    """Formulario para registrar instrumentos financieros"""
    nombre_instrumento = StringField('Nombre', validators=[DataRequired()])

class TickerForm(FlaskForm):
    """Formulario para registrar tickers"""
    nuevo_ticker = StringField('Ticker', validators=[DataRequired()])
    descripcion_ticker = StringField('Descripción')
    select_instrumento = SelectField('Instrumento Financiero', coerce=int, validators=[DataRequired()])

class CompraForm(FlaskForm):
    """Formulario para registrar compras"""
    id_broker = SelectField('Broker', coerce=int, validators=[DataRequired()])
    id_comitente = SelectField('Comitente', coerce=int, validators=[DataRequired()])
    id_ticker = SelectField('Ticker', coerce=int, validators=[DataRequired()])
    precio_dolar_mep_compra = FloatField('Precio Dólar MEP Compra', validators=[DataRequired()])
    fecha_hora_compra = StringField('Fecha y Hora', validators=[DataRequired()])
    precio_compra = FloatField('Precio Compra', validators=[DataRequired()])
    cantidad_compra = FloatField('Cantidad', validators=[DataRequired()])
    comision_broker = FloatField('Comisión Broker', validators=[DataRequired()])
    total_pesos_compra = FloatField('Total Pesos', validators=[DataRequired()])
    total_dolares_compra = FloatField('Total Dólares', validators=[DataRequired()])

# ==========================================
# FORMULARIOS SEGUROS CON VALIDACIÓN XSS
# ==========================================

class SecureBrokerForm(FlaskForm):
    """Formulario seguro para registrar brokers con validación XSS"""
    nombre_broker = StringField('Nombre del Broker', validators=[
        DataRequired(message='El nombre del broker es obligatorio'),
        XSSValidator()
    ])
    comision_broker = FloatField('Comisión', validators=[
        DataRequired(message='La comisión es obligatoria'),
        NumberRange(min=0, max=100, message='La comisión debe estar entre 0 y 100')
    ])
    asesor_broker = StringField('Asesor', validators=[XSSValidator()])

class SecureComitenteForm(FlaskForm):
    """Formulario seguro para registrar comitentes con validación XSS"""
    titular_comitente = StringField('Titular', validators=[
        DataRequired(message='El titular es obligatorio'),
        XSSValidator()
    ])
    numero_comitente = StringField('Número', validators=[
        DataRequired(message='El número es obligatorio'),
        XSSValidator()
    ])
    id_broker = SelectField('Broker', coerce=int, validators=[DataRequired()])

class SecureInstrumentoFinancieroForm(FlaskForm):
    """Formulario seguro para registrar instrumentos financieros con validación XSS"""
    nombre_instrumento = StringField('Nombre', validators=[
        DataRequired(message='El nombre es obligatorio'),
        XSSValidator()
    ])

class SecureTickerForm(FlaskForm):
    """Formulario seguro para registrar tickers con validación XSS"""
    nuevo_ticker = StringField('Ticker', validators=[
        DataRequired(message='El ticker es obligatorio'),
        XSSValidator()
    ])
    descripcion_ticker = StringField('Descripción', validators=[XSSValidator()])
    select_instrumento = SelectField('Instrumento Financiero', coerce=int, validators=[DataRequired()])

# ==========================================
# RUTAS PRINCIPALES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compra')
def compra():
    brokers = db.session.query(Broker).all()
    InstrumentoFinancieros = db.session.query(InstrumentoFinanciero).all()
    return render_template('compra.html', brokers=brokers, InstrumentoFinancieros=InstrumentoFinancieros)

@app.route('/venta')
def venta():
    brokers = db.session.query(Broker).all()
    InstrumentoFinancieros = db.session.query(InstrumentoFinanciero).all()
    return render_template('venta.html', brokers=brokers, InstrumentoFinancieros=InstrumentoFinancieros)

@app.route('/informe')
def informe():
    brokers = db.session.query(Broker).all()
    InstrumentoFinancieros = db.session.query(InstrumentoFinanciero).all()
    return render_template('informe.html', brokers=brokers, InstrumentoFinancieros=InstrumentoFinancieros)

@app.route('/dashboard')
def dashboard():
    """Dashboard ejecutivo con métricas financieras"""
    return render_template('dashboard.html')

@app.route('/dashboard_avanzado')
def dashboard_avanzado():
    """Dashboard avanzado con análisis financiero profesional"""
    return render_template('dashboard_avanzado.html')

@app.route('/debug/database')
def debug_database():
    """Endpoint de debug para verificar el estado de la base de datos"""
    try:
        # Contar registros
        brokers_count = db.session.query(Broker).count()
        comitentes_count = db.session.query(Comitente).count()
        
        # Obtener algunos ejemplos
        brokers = db.session.query(Broker).all()
        comitentes = db.session.query(Comitente).all()
        
        # Obtener relaciones broker-comitente
        relaciones = []
        for broker in brokers:
            comits = db.session.query(Comitente).filter(Comitente.Id_Broker == broker.Id_Broker).all()
            relaciones.append({
                'broker_id': broker.Id_Broker,
                'broker_nombre': broker.Nombre,
                'comitentes_count': len(comits),
                'comitentes': [{'id': c.Id_Comitente, 'titular': c.Titular} for c in comits]
            })
        
        debug_info = {
            'status': 'ok',
            'brokers_count': brokers_count,
            'comitentes_count': comitentes_count,
            'brokers': [{'id': b.Id_Broker, 'nombre': b.Nombre} for b in brokers],
            'comitentes': [{'id': c.Id_Comitente, 'titular': c.Titular, 'broker_id': c.Id_Broker} for c in comitentes],
            'relaciones': relaciones
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/debug/test-comitentes/<int:broker_id>')
def debug_test_comitentes(broker_id):
    """Endpoint de test específico para probar la carga de comitentes"""
    try:
        print(f"[TEST] Probando comitentes para broker ID: {broker_id}")
        
        # Verificar que el broker existe
        broker = db.session.get(Broker, broker_id)
        if not broker:
            return jsonify({'error': f'Broker con ID {broker_id} no encontrado'}), 404
        
        # Obtener comitentes
        comitentes = db.session.query(Comitente).filter(Comitente.Id_Broker == broker_id).all()
        
        result = {
            'broker_id': broker_id,
            'broker_nombre': broker.Nombre,
            'comitentes_found': len(comitentes),
            'comitentes': [{'Id_Comitente': c.Id_Comitente, 'Titular': c.Titular} for c in comitentes]
        }
        
        print(f"[TEST] Resultado: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"[TEST ERROR] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/formulario_venta')
def formulario_venta():
    brokers = db.session.query(Broker).all()
    InstrumentoFinancieros = db.session.query(InstrumentoFinanciero).all()
    return render_template('formulario_venta.html', brokers=brokers, InstrumentoFinancieros=InstrumentoFinancieros)

@app.route('/registrar_broker', methods=['POST'])
def register_broker():
    form = SecureBrokerForm()
    
    if form.validate_on_submit():
        try:
            # Sanitizar datos antes de guardar
            nombre_sanitizado = sanitize_input(form.nombre_broker.data, max_length=100)
            asesor_sanitizado = sanitize_input(form.asesor_broker.data, max_length=100) if form.asesor_broker.data else ''
            
            new_broker = Broker(
                Nombre=nombre_sanitizado,
                Comision=form.comision_broker.data,
                Asesor=asesor_sanitizado
            )
            db.session.add(new_broker)
            db.session.commit()
            return redirect(url_for('compra'))
        except Exception as e:
            app.logger.error(f"Error registrando broker: {str(e)}")
            return redirect(url_for('compra', error=f'Error al registrar broker: {str(e)}'))
    else:
        # Log form validation errors for debugging
        app.logger.error(f"Errores en formulario broker: {form.errors}")
        return redirect(url_for('compra', error='Datos del formulario inválidos'))

@app.route('/registrar_comitente', methods=['POST'])
def register_comitente():
    form = SecureComitenteForm()
    
    if form.validate_on_submit():
        try:
            # Sanitizar datos antes de guardar
            titular_sanitizado = sanitize_input(form.titular_comitente.data, max_length=100)
            numero_sanitizado = sanitize_input(form.numero_comitente.data, max_length=50)
            
            new_comitente = Comitente(
                Titular=titular_sanitizado,
                Numero=numero_sanitizado,
                Id_Broker=form.id_broker.data
            )
            db.session.add(new_comitente)
            db.session.commit()
            return redirect(url_for('compra'))
        except Exception as e:
            app.logger.error(f"Error registrando comitente: {str(e)}")
            return redirect(url_for('compra', error=f'Error al registrar comitente: {str(e)}'))
    else:
        app.logger.error(f"Errores en formulario comitente: {form.errors}")
        return redirect(url_for('compra', error='Datos del formulario inválidos'))

@app.route('/registrar_InstrumentoFinanciero', methods=['POST'])
def register_InstrumentoFinanciero():
    form = SecureInstrumentoFinancieroForm()
    
    if form.validate_on_submit():
        try:
            # Sanitizar datos antes de guardar
            nombre_sanitizado = sanitize_input(form.nombre_instrumento.data, max_length=100)
            
            existing_instrumento = db.session.query(InstrumentoFinanciero).filter_by(Nombre=nombre_sanitizado).first()
            if existing_instrumento:
                return redirect(url_for('compra', error='El instrumento financiero ya existe'))

            new_InstrumentoFinanciero = InstrumentoFinanciero(Nombre=nombre_sanitizado)
            db.session.add(new_InstrumentoFinanciero)
            db.session.commit()
            return redirect(url_for('compra'))
        except Exception as e:
            app.logger.error(f"Error registrando instrumento financiero: {str(e)}")
            return redirect(url_for('compra', error=f'Error al registrar instrumento financiero: {str(e)}'))
    else:
        app.logger.error(f"Errores en formulario instrumento financiero: {form.errors}")
        return redirect(url_for('compra', error='Datos del formulario inválidos'))

@app.route('/registrar_ticker', methods=['POST'])
def registrar_ticker():
    form = SecureTickerForm()
    
    if form.validate_on_submit():
        try:
            # Sanitizar datos antes de guardar
            ticker_sanitizado = sanitize_input(form.nuevo_ticker.data, max_length=20).upper()
            descripcion_sanitizado = sanitize_input(form.descripcion_ticker.data, max_length=200) if form.descripcion_ticker.data else ''
            
            existing_ticker = db.session.query(Ticker).filter(Ticker.Nombre_Ticker==ticker_sanitizado).first()
            if existing_ticker:
                return redirect(url_for('compra', error='Este ticker ya existe'))

            nuevo_ticker_obj = Ticker(
                Nombre_Ticker=ticker_sanitizado,
                Descripcion=descripcion_sanitizado,
                Id_InstrumentoFinanciero=form.select_instrumento.data
            )
            db.session.add(nuevo_ticker_obj)
            db.session.commit()
            return redirect(url_for('compra'))
        except Exception as e:
            app.logger.error(f"Error registrando ticker: {str(e)}")
            return redirect(url_for('compra', error='Error al registrar el ticker.'))
    else:
        app.logger.error(f"Errores en formulario ticker: {form.errors}")
        return redirect(url_for('compra', error='Datos del formulario inválidos'))

# ==========================================
# RUTAS AJAX
# ==========================================

@app.route('/get_instrumentos_financieros', methods=['GET'])
def get_instrumentos_financieros():
    instrumentos = InstrumentoFinanciero.query.all()
    return jsonify([{'Id_InstrumentoFinanciero': instr.Id_InstrumentoFinanciero, 'Nombre': instr.Nombre} for instr in instrumentos])

@app.route('/get_comitentes/<int:Id_Broker>')
def get_comitentes(Id_Broker):
    print(f"[DEBUG] Solicitando comitentes para broker ID: {Id_Broker}")  # Debug log
    try:
        comitentes = db.session.query(Comitente).filter(Comitente.Id_Broker==Id_Broker).all()
        comitentes_list = [{'Id_Comitente': comitente.Id_Comitente, 'Titular': comitente.Titular} for comitente in comitentes]
        print(f"[DEBUG] Comitentes encontrados: {len(comitentes_list)}")  # Debug log
        return jsonify({'comitentes': comitentes_list})
    except Exception as e:
        print(f"[ERROR] Error en get_comitentes: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/validar_ticker', methods=['POST'])
def validar_ticker():
    try:
        nuevo_ticker = request.form.get('nuevoTicker').strip().upper()
        if not nuevo_ticker:
            return jsonify({'existe': False, 'mensaje': 'Ticker no proporcionado.'})

        existing_ticker = db.session.query(Ticker).filter(Ticker.Nombre_Ticker==nuevo_ticker).first()
        if existing_ticker:
            return jsonify({'existe': True, 'mensaje': 'Este ticker ya existe.'})
        else:
            return jsonify({'existe': False, 'mensaje': 'Ticker válido.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'existe': False, 'mensaje': 'Error al validar el ticker.'}), 500

@app.route('/get_tickers/<int:instrumento_id>', methods=['GET'])
def get_tickers(instrumento_id):
    tickers = db.session.query(Ticker).filter(Ticker.Id_InstrumentoFinanciero==instrumento_id).all()
    tickers_list = [{'Id_Ticker': ticker.Id_Ticker, 'Nombre_Ticker': ticker.Nombre_Ticker, 'Descripcion': ticker.Descripcion} for ticker in tickers]
    return jsonify({'tickers': tickers_list})

@app.route('/get_comision_broker/<int:broker_id>', methods=['GET'])
def get_comision_broker(broker_id):
    # Consulta la base de datos para obtener el broker por su ID
    broker = db.session.get(Broker, broker_id)
    
    if broker:
        # Devuelve la comisión del broker en formato JSON
        return jsonify({'comision': broker.Comision})
    else:
        # Si no se encuentra el broker, devuelve un error
        return jsonify({'error': 'Broker not found'}), 404

@app.route('/get_compras/<int:ticker_id>', methods=['GET'])
def get_compras(ticker_id):
    compras = Activo.query.filter(Activo.Id_Ticker==ticker_id, Activo.Activo_Estado=="EN_CARTERA").all()
    
    compras_data = [{
        'Id_Activo': compra.Id_Activo,
        'Fecha_Hora_Compra': compra.Fecha_Hora_Compra,
        'Precio_Compra': compra.Precio_Compra,
        'Cantidad_Nominales_Compra': compra.Cantidad_Nominales_Compra,
        'Total_Dolares_Compra': compra.Total_Dolares_Compra,
        'Total_Pesos_Compra': compra.Total_Pesos_Compra
    } for compra in compras]

    return jsonify(compras_data)

@app.route('/registrar_compra', methods=['POST'])
@limiter.limit("5 per minute")
def registrar_compra():
    try:
        Id_Broker = request.form.get('Id_Broker')
        Id_Comitente = request.form.get('Id_Comitente')
        Id_Ticker = request.form.get('Id_Ticker')
        Precio_Dolar_MEP_Compra = request.form.get('precioDolarMEPCompra')
        Fecha_Hora_Compra = request.form.get('fechaHoraCompra')
        Precio_Compra = request.form.get('precioCompra')
        Cantidad_Nominales_Compra = request.form.get('cantidadCompra')
        Comision_Broker = request.form.get('comisionBroker')
        Total_Pesos_Compra = request.form.get('totalPesosCompra')
        Total_Dolares_Compra = request.form.get('totalDolaresCompra')

        # Validar valores numéricos
        precio_float = float(Precio_Compra.replace(',', '.')) if Precio_Compra else 0
        cantidad_float = float(Cantidad_Nominales_Compra.replace(',', '.')) if Cantidad_Nominales_Compra else 0
        dolar_mep_float = float(Precio_Dolar_MEP_Compra.replace(',', '.')) if Precio_Dolar_MEP_Compra else 0
        
        # Calcular totales
        total_pesos = precio_float * cantidad_float
        total_dolares = total_pesos / dolar_mep_float if dolar_mep_float > 0 else 0
        
        # Crear nueva compra
        nueva_compra = Activo(
            Id_Broker=int(Id_Broker) if Id_Broker else None,
            Id_Comitente=int(Id_Comitente) if Id_Comitente else None,
            Id_Ticker=int(Id_Ticker) if Id_Ticker else None,
            Precio_Dolar_MEP_Compra=dolar_mep_float,
            Fecha_Hora_Compra=Fecha_Hora_Compra,
            Precio_Compra=precio_float,
            Cantidad_Nominales_Compra=cantidad_float,
            Comision_Broker=float(Comision_Broker.replace(',', '.')) if Comision_Broker else 0,
            Total_Pesos_Compra=total_pesos,
            Total_Dolares_Compra=total_dolares,
            Activo_Estado='EN_CARTERA'
        )
        
        db.session.add(nueva_compra)
        db.session.commit()

        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error registrando compra: {str(e)}")
        return redirect(url_for('index', error='Error al registrar la compra'))

# ==========================================
# IMPORTACIÓN DE COMPRAS DESDE ARCHIVO
# ==========================================

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/importar_compras', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def importar_compras():
    """
    Importar compras desde archivo CSV o Excel
    """
    if request.method == 'GET':
        brokers = db.session.query(Broker).all()
        comitentes = db.session.query(Comitente).all()
        instrumentos = db.session.query(InstrumentoFinanciero).all()
        tickers = db.session.query(Ticker).all()
        return render_template('importar_compras.html', 
                             brokers=brokers, 
                             comitentes=comitentes,
                             instrumentos=instrumentos,
                             tickers=tickers)
    
    if request.method == 'POST':
        try:
            # Verificar si se subió un archivo
            if 'archivo' not in request.files:
                return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
            
            archivo = request.files['archivo']
            
            if archivo.filename == '':
                return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
            
            if not allowed_file(archivo.filename):
                return jsonify({'success': False, 'error': 'Formato de archivo no permitido. Use CSV o Excel'}), 400
            
            # Obtener parámetros por defecto
            id_broker_default = request.form.get('id_broker_default')
            id_comitente_default = request.form.get('id_comitente_default')
            
            # Procesar archivo
            filename = secure_filename(archivo.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            
            compras_importadas = 0
            errores = []
            
            if extension == 'csv':
                # Procesar CSV
                stream = io.StringIO(archivo.stream.read().decode("UTF-8"), newline=None)
                reader = csv.DictReader(stream)
                
                for i, row in enumerate(reader, start=2):
                    try:
                        resultado = procesar_fila_compra(row, id_broker_default, id_comitente_default)
                        if resultado['success']:
                            compras_importadas += 1
                        else:
                            errores.append(f"Fila {i}: {resultado['error']}")
                    except Exception as e:
                        errores.append(f"Fila {i}: {str(e)}")
            
            elif extension in ['xlsx', 'xls']:
                # Procesar Excel
                try:
                    import pandas as pd
                    df = pd.read_excel(archivo)
                    
                    for i, row in df.iterrows():
                        try:
                            row_dict = row.to_dict()
                            resultado = procesar_fila_compra(row_dict, id_broker_default, id_comitente_default)
                            if resultado['success']:
                                compras_importadas += 1
                            else:
                                errores.append(f"Fila {i+2}: {resultado['error']}")
                        except Exception as e:
                            errores.append(f"Fila {i+2}: {str(e)}")
                except ImportError:
                    return jsonify({'success': False, 'error': 'pandas no está instalado para procesar Excel'}), 500
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'compras_importadas': compras_importadas,
                'errores': errores[:10],  # Limitar errores mostrados
                'total_errores': len(errores)
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error importando compras: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

def procesar_fila_compra(row, id_broker_default=None, id_comitente_default=None):
    """
    Procesa una fila de datos de compra y la guarda en la base de datos
    """
    try:
        # Mapear columnas (soportar diferentes nombres)
        ticker_nombre = row.get('Ticker') or row.get('ticker') or row.get('Nombre_Ticker') or row.get('TICKER')
        fecha = row.get('Fecha') or row.get('fecha') or row.get('Fecha_Compra') or row.get('FECHA')
        precio = row.get('Precio') or row.get('precio') or row.get('Precio_Compra') or row.get('PRECIO')
        cantidad = row.get('Cantidad') or row.get('cantidad') or row.get('Cantidad_Compra') or row.get('CANTIDAD')
        dolar_mep = row.get('Dolar_MEP') or row.get('dolar_mep') or row.get('Precio_Dolar_MEP') or row.get('DOLAR_MEP') or 1000
        comision = row.get('Comision') or row.get('comision') or row.get('Comision_Broker') or 0
        
        # Validar campos requeridos
        if not ticker_nombre:
            return {'success': False, 'error': 'Ticker no especificado'}
        if not precio:
            return {'success': False, 'error': 'Precio no especificado'}
        if not cantidad:
            return {'success': False, 'error': 'Cantidad no especificada'}
        
        # Buscar o crear ticker
        ticker = db.session.query(Ticker).filter(Ticker.Nombre_Ticker == str(ticker_nombre).upper().strip()).first()
        if not ticker:
            return {'success': False, 'error': f'Ticker {ticker_nombre} no encontrado'}
        
        # Obtener broker y comitente
        id_broker = row.get('Id_Broker') or id_broker_default
        id_comitente = row.get('Id_Comitente') or id_comitente_default
        
        if not id_broker or not id_comitente:
            return {'success': False, 'error': 'Broker o Comitente no especificado'}
        
        # Convertir valores numéricos
        try:
            precio_float = float(str(precio).replace(',', '.').strip())
            cantidad_float = float(str(cantidad).replace(',', '.').strip())
            dolar_mep_float = float(str(dolar_mep).replace(',', '.').strip()) if dolar_mep else 1000
            comision_float = float(str(comision).replace(',', '.').replace('%', '').strip()) if comision else 0
        except ValueError:
            return {'success': False, 'error': 'Error en formato numérico'}
        
        # Calcular totales
        total_pesos = precio_float * cantidad_float
        total_dolares = total_pesos / dolar_mep_float if dolar_mep_float > 0 else 0
        
        # Parsear fecha
        fecha_parsed = None
        if fecha:
            if isinstance(fecha, str):
                # Intentar varios formatos de fecha
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M']:
                    try:
                        fecha_parsed = datetime.datetime.strptime(fecha.strip(), fmt)
                        break
                    except ValueError:
                        continue
        if not fecha_parsed:
            fecha_parsed = datetime.datetime.now()
        
        # Crear activo
        nueva_compra = Activo(
            Id_Broker=int(id_broker),
            Id_Comitente=int(id_comitente),
            Id_Ticker=ticker.Id_Ticker,
            Precio_Dolar_MEP_Compra=dolar_mep_float,
            Fecha_Hora_Compra=fecha_parsed,
            Precio_Compra=precio_float,
            Cantidad_Nominales_Compra=cantidad_float,
            Comision_Broker=comision_float,
            Total_Pesos_Compra=total_pesos,
            Total_Dolares_Compra=total_dolares,
            Activo_Estado='EN_CARTERA'
        )
        
        db.session.add(nueva_compra)
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/plantilla_compras_csv')
def plantilla_compras_csv():
    """
    Descarga una plantilla CSV para importar compras
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'Ticker', 'Fecha', 'Precio', 'Cantidad', 'Dolar_MEP', 'Comision'
    ])
    
    # Fila de ejemplo
    writer.writerow([
        'GGAL', '2024-01-15', '1500.50', '100', '1050.00', '0.5'
    ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=plantilla_compras.csv'
    
    return response

# ==========================================
# IMPORTACIÓN DE VENTAS DESDE ARCHIVO
# ==========================================

@app.route('/importar_ventas', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def importar_ventas():
    """
    Importar ventas desde archivo CSV o Excel
    """
    if request.method == 'GET':
        brokers = db.session.query(Broker).all()
        instrumentos = db.session.query(InstrumentoFinanciero).all()
        return render_template('importar_ventas.html', 
                             brokers=brokers, 
                             instrumentos=instrumentos)
    
    if request.method == 'POST':
        try:
            if 'archivo' not in request.files:
                return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
            
            archivo = request.files['archivo']
            
            if archivo.filename == '':
                return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
            
            if not allowed_file(archivo.filename):
                return jsonify({'success': False, 'error': 'Formato de archivo no permitido. Use CSV o Excel'}), 400
            
            filename = secure_filename(archivo.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            
            ventas_importadas = 0
            errores = []
            
            if extension == 'csv':
                stream = io.StringIO(archivo.stream.read().decode("UTF-8"), newline=None)
                reader = csv.DictReader(stream)
                
                for i, row in enumerate(reader, start=2):
                    try:
                        resultado = procesar_fila_venta(row)
                        if resultado['success']:
                            ventas_importadas += 1
                        else:
                            errores.append(f"Fila {i}: {resultado['error']}")
                    except Exception as e:
                        errores.append(f"Fila {i}: {str(e)}")
            
            elif extension in ['xlsx', 'xls']:
                try:
                    import pandas as pd
                    df = pd.read_excel(archivo)
                    
                    for i, row in df.iterrows():
                        try:
                            row_dict = row.to_dict()
                            resultado = procesar_fila_venta(row_dict)
                            if resultado['success']:
                                ventas_importadas += 1
                            else:
                                errores.append(f"Fila {i+2}: {resultado['error']}")
                        except Exception as e:
                            errores.append(f"Fila {i+2}: {str(e)}")
                except ImportError:
                    return jsonify({'success': False, 'error': 'pandas no está instalado para procesar Excel'}), 500
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'ventas_importadas': ventas_importadas,
                'errores': errores[:10],
                'total_errores': len(errores)
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error importando ventas: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

def procesar_fila_venta(row):
    """
    Procesa una fila de datos de venta y actualiza el activo correspondiente
    """
    try:
        # Mapear columnas
        id_activo = row.get('Id_Activo') or row.get('id_activo') or row.get('ID_ACTIVO')
        ticker_nombre = row.get('Ticker') or row.get('ticker') or row.get('TICKER')
        fecha = row.get('Fecha') or row.get('fecha') or row.get('Fecha_Venta') or row.get('FECHA')
        precio = row.get('Precio') or row.get('precio') or row.get('Precio_Venta') or row.get('PRECIO')
        cantidad = row.get('Cantidad') or row.get('cantidad') or row.get('Cantidad_Venta') or row.get('CANTIDAD')
        dolar_mep = row.get('Dolar_MEP') or row.get('dolar_mep') or row.get('Precio_Dolar_MEP') or 1000
        
        # Buscar activo
        activo = None
        if id_activo:
            activo = Activo.query.get(int(id_activo))
        elif ticker_nombre:
            # Buscar el activo más antiguo en cartera con ese ticker
            ticker = db.session.query(Ticker).filter(Ticker.Nombre_Ticker == str(ticker_nombre).upper().strip()).first()
            if ticker:
                activo = Activo.query.filter(
                    Activo.Id_Ticker == ticker.Id_Ticker,
                    Activo.Activo_Estado == 'EN_CARTERA'
                ).order_by(Activo.Fecha_Hora_Compra.asc()).first()
        
        if not activo:
            return {'success': False, 'error': 'Activo no encontrado o ya vendido'}
        
        if activo.Activo_Estado == 'VENDIDO':
            return {'success': False, 'error': 'El activo ya fue vendido'}
        
        # Convertir valores
        try:
            precio_float = float(str(precio).replace(',', '.').strip())
            cantidad_float = float(str(cantidad).replace(',', '.').strip()) if cantidad else activo.Cantidad_Nominales_Compra
            dolar_mep_float = float(str(dolar_mep).replace(',', '.').strip()) if dolar_mep else 1000
        except ValueError:
            return {'success': False, 'error': 'Error en formato numérico'}
        
        # Calcular totales
        total_pesos = precio_float * cantidad_float
        total_dolares = total_pesos / dolar_mep_float if dolar_mep_float > 0 else 0
        
        # Parsear fecha
        fecha_parsed = None
        if fecha:
            if isinstance(fecha, str):
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M']:
                    try:
                        fecha_parsed = datetime.datetime.strptime(fecha.strip(), fmt)
                        break
                    except ValueError:
                        continue
        if not fecha_parsed:
            fecha_parsed = datetime.datetime.now()
        
        # Actualizar activo
        activo.Precio_Dolar_MEP_Venta = dolar_mep_float
        activo.Fecha_Hora_Venta = fecha_parsed
        activo.Precio_Venta = precio_float
        activo.Cantidad_Nominales_Venta = cantidad_float
        activo.Total_Pesos_Venta = total_pesos
        activo.Total_Dolares_Venta = total_dolares
        activo.Activo_Estado = 'VENDIDO'
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/plantilla_ventas_csv')
def plantilla_ventas_csv():
    """
    Descarga una plantilla CSV para importar ventas
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Ticker', 'Fecha', 'Precio', 'Cantidad', 'Dolar_MEP'
    ])
    
    writer.writerow([
        'GGAL', '2024-02-15', '1800.00', '100', '1100.00'
    ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=plantilla_ventas.csv'
    
    return response

@app.route('/registrar_venta', methods=['POST'])
@limiter.limit("3 per minute")
def registrar_venta():
    data = request.json  # Obtener datos JSON desde el request

    try:
        id_activo = data.get('Id_Activo')
        fecha_hora_venta = data.get('Fecha_Hora_Venta')
        precio_venta = float(data.get('PrecioVenta'))
        precio_dolar_mep_venta = float(data.get('PrecioDolarMEPVenta'))
        cantidad_venta = float(data.get('CantidadVenta'))
        total_pesos_venta = float(data.get('Total_Pesos_Venta'))

        # Calcular total en dólares en el backend
        if precio_dolar_mep_venta > 0:
            total_dolares_venta = precio_venta / precio_dolar_mep_venta
        else:
            total_dolares_venta = 0  # Evitar división por cero

        # Buscar el activo en la base de datos
        activo = Activo.query.filter_by(Id_Activo=id_activo).first()
        if not activo:
            return jsonify({'error': 'El Activo no se ha encontrado'}), 404

        # Actualizar datos del activo
        activo.Precio_Dolar_MEP_Venta = precio_dolar_mep_venta
        activo.Fecha_Hora_Venta = datetime.datetime.fromisoformat(fecha_hora_venta)  # Convertir a datetime
        activo.Precio_Venta = precio_venta
        activo.Cantidad_Nominales_Venta = cantidad_venta
        activo.Total_Pesos_Venta = total_pesos_venta
        activo.Total_Dolares_Venta = total_dolares_venta  # Se usa el cálculo del backend
        activo.Activo_Estado = 'VENDIDO'

        db.session.commit()

        return jsonify({'message': 'Venta registrada exitosamente', 'total_dolares_venta': total_dolares_venta}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registrando venta: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/obtener_estados_activos', methods=['GET'])
def obtener_estados_activos():
    # Obtener los estados únicos desde la base de datos, excluyendo nulos
    estados = Activo.query.with_entities(Activo.Activo_Estado.distinct())\
        .filter(Activo.Activo_Estado.isnot(None))\
        .order_by(Activo.Activo_Estado)\
        .all()
    # Extraer los valores de los resultados
    estados_unicos = [estado[0] for estado in estados if estado[0]]  # Excluir valores vacíos
    
    return jsonify(estados_unicos)

@app.route('/informe_activos', methods=['GET', 'POST'])
def informe_activos():
    print(f"[DEBUG] informe_activos llamado con método: {request.method}")  # Debug log
    
    if request.method == 'POST':
        try:
            # Obtener los parámetros
            Id_Broker = request.form.get('Id_Broker')
            Id_Comitente = request.form.get('Id_Comitente')
            Id_InstrumentoFinanciero = request.form.get('Id_InstrumentoFinanciero')
            Id_Ticker = request.form.get('Id_Ticker')
            activo_estado = request.form.get('Activo_Estado')
            
            # Parámetros de paginación
            try:
                page = int(request.form.get('page', 1))
            except (ValueError, TypeError):
                page = 1
                
            try:
                per_page = int(request.form.get('per_page', 20))
            except (ValueError, TypeError):
                per_page = 20
            
            print(f"[DEBUG] Parámetros recibidos: broker={Id_Broker}, comitente={Id_Comitente}, instrumento={Id_InstrumentoFinanciero}, ticker={Id_Ticker}, estado={activo_estado}")  # Debug log
            
            # Iniciar la consulta base
            query = Activo.query

            # Aplicar filtros solo si tienen valor
            if Id_Broker and Id_Broker != "":
                query = query.filter(Activo.Id_Broker == Id_Broker)
                
            if Id_Comitente and Id_Comitente != "":
                query = query.filter(Activo.Id_Comitente == Id_Comitente)
                
            if Id_Ticker and Id_Ticker != "":
                query = query.filter(Activo.Id_Ticker == Id_Ticker)
                
            if activo_estado and activo_estado != "":
                query = query.filter(Activo.Activo_Estado == activo_estado)

            # Aplicar paginación
            paginated_assets = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            activos = paginated_assets.items

            total_ganancia_pesos = 0
            resultados = []
            for activo in activos:
                if activo.Precio_Venta and activo.Cantidad_Nominales_Venta:
                    ganancia_pesos = (activo.Precio_Venta - activo.Precio_Compra) * activo.Cantidad_Nominales_Venta
                    total_ganancia_pesos += ganancia_pesos
                else:
                    ganancia_pesos = 'N/A'

                if activo.Precio_Venta and activo.Precio_Compra and activo.Precio_Compra > 0:
                    porcentaje_pesos = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
                else:
                    porcentaje_pesos = 'N/A'

                if activo.Total_Dolares_Venta is not None and activo.Total_Dolares_Compra is not None:
                    porcentaje_dolares = ((activo.Total_Dolares_Venta - activo.Total_Dolares_Compra) / activo.Total_Dolares_Compra) * 100
                else:
                    porcentaje_dolares = 'N/A'

                resultados.append({
                    'Id_Activo': activo.Id_Activo,
                    'Fecha_Compra': activo.Fecha_Hora_Compra,
                    'Precio_Compra': activo.Precio_Compra,
                    'Cantidad_Nominales_Compra': activo.Cantidad_Nominales_Compra,
                    'Cantidad_Nominales_Venta': activo.Cantidad_Nominales_Venta,
                    'Total_Pesos_Compra': activo.Total_Pesos_Compra,
                    'Fecha_Venta': activo.Fecha_Hora_Venta or 'N/A',
                    'Precio_Venta': activo.Precio_Venta or 'N/A',
                    'Total_Pesos_Venta': activo.Total_Pesos_Venta or 'N/A',
                    'Ganancia': ganancia_pesos,
                    'Porcentaje_Pesos': porcentaje_pesos,
                    'Dolar_MEP_Compra': activo.Total_Dolares_Compra,
                    'Dolar_MEP_Venta': activo.Total_Dolares_Venta,
                    'Porcentaje_Dolares': porcentaje_dolares,
                    'Ticker': activo.ticker.Nombre_Ticker if activo.ticker else 'N/A'
                })

            # Información de paginación
            pagination_info = {
                'page': page,
                'per_page': per_page,
                'total_items': paginated_assets.total,
                'total_pages': paginated_assets.pages,
                'has_next': paginated_assets.has_next,
                'has_prev': paginated_assets.has_prev,
                'next_page': page + 1 if paginated_assets.has_next else None,
                'prev_page': page - 1 if paginated_assets.has_prev else None
            }
            
            response = {
                'data': resultados,
                'pagination': pagination_info,
                'total_ganancia_pesos': total_ganancia_pesos
            }
            
            print(f"[DEBUG] Respuesta generada exitosamente con {len(resultados)} registros")  # Debug log
            return jsonify(response)
            
        except Exception as e:
            print(f"[ERROR] Error en informe_activos: {str(e)}")  # Debug log
            app.logger.error(f"Error en informe_activos: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # GET request - return empty response or render template
    print("[DEBUG] GET request received, returning empty response")  # Debug log
    return jsonify({'data': [], 'pagination': {}, 'total_ganancia_pesos': 0})

# ==========================================
# NUEVAS RUTAS PARA MÉTRICAS FINANCIERAS
# ==========================================

@app.route('/api/metrics/roi/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_roi_activo(activo_id):
    """API para ROI de un activo específico"""
    try:
        roi_data = calcular_roi_activo(activo_id)
        return jsonify(roi_data)
    except Exception as e:
        logging.error(f"Error en API ROI activo {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/portfolio')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_roi_portfolio():
    """API para ROI de la cartera completa"""
    try:
        portfolio_data = calcular_roi_cartera_completa()
        return jsonify(portfolio_data)
    except Exception as e:
        logging.error(f"Error en API ROI portfolio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/sharpe/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_sharpe_ratio(activo_id):
    """API para Sharpe Ratio"""
    try:
        sharpe_data = calcular_sharpe_ratio(activo_id)
        return jsonify(sharpe_data)
    except Exception as e:
        logging.error(f"Error en API Sharpe ratio {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/max-drawdown/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_max_drawdown(activo_id):
    """API para Maximum Drawdown"""
    try:
        dd_data = calcular_maximum_drawdown(activo_id)
        return jsonify(dd_data)
    except Exception as e:
        logging.error(f"Error en API Max Drawdown {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/var/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_var(activo_id):
    """API para Value at Risk"""
    try:
        confianza = request.args.get('confianza', 0.95, type=float)
        var_data = calcular_var_simple(activo_id, confianza)
        return jsonify(var_data)
    except Exception as e:
        logging.error(f"Error en API VaR {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/top-performers')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_top_performers():
    """API para mejores performers con paginación"""
    try:
        limit = request.args.get('limit', 5, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        performers = top_performers(limit=limit, page=page, per_page=per_page)
        return jsonify(performers)
    except Exception as e:
        logging.error(f"Error en API top performers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/bottom-performers')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_bottom_performers():
    """API para peores performers"""
    try:
        limit = request.args.get('limit', 5, type=int)
        performers = bottom_performers(limit)
        return jsonify(performers)
    except Exception as e:
        logging.error(f"Error en API bottom performers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/performance-tickers')
@cache.cached(timeout=get_cache_config_for_api('metricas_basicas')['timeout'])
def api_performance_tickers():
    """API para performance por ticker"""
    try:
        performance_data = performance_por_ticker()
        return jsonify(performance_data)
    except Exception as e:
        logging.error(f"Error en API performance tickers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/summary')
@cache.cached(timeout=get_cache_config_for_api('dashboard')['timeout'])
def api_dashboard_summary():
    """API para resumen ejecutivo del dashboard"""
    try:
        summary_data = resumen_ejecutivo()
        return jsonify(summary_data)
    except Exception as e:
        logging.error(f"Error en API dashboard summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# NUEVAS APIs PARA MÉTRICAS AVANZADAS
# ==========================================

@app.route('/api/metrics/tir/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_tir_completa(activo_id):
    """API para TIR completa con método Newton-Raphson"""
    try:
        tir_data = calcular_tir_completa(activo_id)
        return jsonify(tir_data)
    except Exception as e:
        logging.error(f"Error en API TIR {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/beta/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_beta(activo_id):
    """API para Beta de activo (correlación con mercado)"""
    try:
        beta_data = calcular_beta_activo(activo_id)
        return jsonify(beta_data)
    except Exception as e:
        logging.error(f"Error en API Beta {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/alpha/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_alpha(activo_id):
    """API para Alpha de activo"""
    try:
        alpha_data = calcular_alpha_activo(activo_id)
        return jsonify(alpha_data)
    except Exception as e:
        logging.error(f"Error en API Alpha {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/correlation-matrix')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_correlation_matrix():
    """API para matriz de correlación entre activos"""
    try:
        correlation_data = matriz_correlacion_activos()
        return jsonify(correlation_data)
    except Exception as e:
        logging.error(f"Error en API matriz correlación: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/diversification')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_diversificacion():
    """API para análisis de diversificación de cartera"""
    try:
        diversification_data = diversificacion_cartera()
        return jsonify(diversification_data)
    except Exception as e:
        logging.error(f"Error en API diversificación: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/backtesting')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_backtesting():
    """API para backtesting de estrategias"""
    try:
        estrategia = request.args.get('estrategia', 'buy_hold')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.datetime.fromisoformat(start_date_str)  # CORREGIDO: datetime.datetime
        if end_date_str:
            end_date = datetime.datetime.fromisoformat(end_date_str)  # CORREGIDO: datetime.datetime
        
        backtest_data = backtesting_simple(estrategia, start_date, end_date)
        return jsonify(backtest_data)
    except Exception as e:
        logging.error(f"Error en API backtesting: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/sensitivity/<int:activo_id>')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_sensibilidad(activo_id):
    """API para análisis de sensibilidad"""
    try:
        sensitivity_data = analisis_sensibilidad(activo_id)
        return jsonify(sensitivity_data)
    except Exception as e:
        logging.error(f"Error en API sensibilidad {activo_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/summary')
@cache.cached(timeout=get_cache_config_for_api('metricas_avanzadas')['timeout'])
def api_advanced_summary():
    """API para resumen de métricas avanzadas"""
    try:
        # Obtener algunos activos para análisis
        activos = Activo.query.limit(5).all()
        
        advanced_data = {
            'correlation_matrix': matriz_correlacion_activos(),
            'diversification': diversificacion_cartera(),
            'backtesting': backtesting_simple('buy_hold'),
            'sample_analyses': []
        }
        
        # Añadir análisis de muestra de algunos activos
        for activo in activos:
            try:
                analysis = {
                    'activo_id': activo.Id_Activo,
                    'ticker': activo.ticker.Nombre_Ticker if activo.ticker else 'N/A',
                    'tir': calcular_tir_completa(activo.Id_Activo),
                    'beta': calcular_beta_activo(activo.Id_Activo),
                    'alpha': calcular_alpha_activo(activo.Id_Activo)
                }
                advanced_data['sample_analyses'].append(analysis)
            except Exception as e:
                logging.warning(f"Error analizando activo {activo.Id_Activo}: {str(e)}")
        
        return jsonify(advanced_data)
    except Exception as e:
        logging.error(f"Error en API advanced summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# NUEVAS APIs PARA REPORTES AVANZADOS
# ==========================================

@app.route('/api/reports/activos-csv')
def api_report_activos_csv():
    """
    Exporta activos en formato CSV
    """
    try:
        # Obtener filtros de la query string
        filtros = {}
        if request.args.get('Id_Broker'):
            filtros['Id_Broker'] = int(request.args.get('Id_Broker'))
        if request.args.get('Id_Comitente'):
            filtros['Id_Comitente'] = int(request.args.get('Id_Comitente'))
        if request.args.get('Id_Ticker'):
            filtros['Id_Ticker'] = int(request.args.get('Id_Ticker'))
        if request.args.get('Activo_Estado'):
            filtros['Activo_Estado'] = request.args.get('Activo_Estado')
        
        # Generar CSV
        csv_content = exportar_activos_csv(filtros)
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # CORREGIDO: datetime.datetime
        filename = f'activos_cartera_{timestamp}.csv'
        
        # Crear respuesta
        response = crear_respuesta_csv(csv_content, filename)
        return response
        
    except Exception as e:
        logging.error(f"Error generando reporte CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/resumen-csv')
def api_report_resumen_csv():
    """
    Exporta resumen de cartera en formato CSV
    """
    try:
        # Generar CSV
        csv_content = exportar_resumen_cartera_csv()
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # CORREGIDO: datetime.datetime
        filename = f'resumen_cartera_{timestamp}.csv'
        
        # Crear respuesta
        response = crear_respuesta_csv(csv_content, filename)
        return response
        
    except Exception as e:
        logging.error(f"Error generando reporte resumen CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/activos-excel')
def api_report_activos_excel():
    """
    Exporta activos en formato Excel
    """
    try:
        # Obtener filtros de la query string
        filtros = {}
        if request.args.get('Id_Broker'):
            filtros['Id_Broker'] = int(request.args.get('Id_Broker'))
        if request.args.get('Id_Comitente'):
            filtros['Id_Comitente'] = int(request.args.get('Id_Comitente'))
        if request.args.get('Id_Ticker'):
            filtros['Id_Ticker'] = int(request.args.get('Id_Ticker'))
        if request.args.get('Activo_Estado'):
            filtros['Activo_Estado'] = request.args.get('Activo_Estado')
        
        # Generar Excel
        excel_content = exportar_activos_excel(filtros)
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # CORREGIDO: datetime.datetime
        filename = f'activos_cartera_{timestamp}.xlsx'
        
        # Crear respuesta
        response = crear_respuesta_excel(excel_content, filename)
        return response
        
    except Exception as e:
        logging.error(f"Error generando reporte Excel: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/ejecutivo-pdf')
def api_report_ejecutivo_pdf():
    """
    Exporta reporte ejecutivo en formato PDF
    """
    try:
        # Generar PDF
        pdf_content = exportar_reporte_ejecutivo_pdf()
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # CORREGIDO: datetime.datetime
        filename = f'reporte_ejecutivo_{timestamp}.pdf'
        
        # Crear respuesta
        response = crear_respuesta_pdf(pdf_content, filename)
        return response
        
    except Exception as e:
        logging.error(f"Error generando reporte ejecutivo PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/detalle-pdf')
def api_report_detalle_pdf():
    """
    Exporta reporte detallado en formato PDF
    """
    try:
        # Obtener filtros de la query string
        filtros = {}
        if request.args.get('Id_Broker'):
            filtros['Id_Broker'] = int(request.args.get('Id_Broker'))
        if request.args.get('Id_Comitente'):
            filtros['Id_Comitente'] = int(request.args.get('Id_Comitente'))
        if request.args.get('Id_Ticker'):
            filtros['Id_Ticker'] = int(request.args.get('Id_Ticker'))
        if request.args.get('Activo_Estado'):
            filtros['Activo_Estado'] = request.args.get('Activo_Estado')
        
        # Generar PDF
        pdf_content = exportar_reporte_detallado_pdf(filtros)
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # CORREGIDO: datetime.datetime
        filename = f'detalle_activos_{timestamp}.pdf'
        
        # Crear respuesta
        response = crear_respuesta_pdf(pdf_content, filename)
        return response
        
    except Exception as e:
        logging.error(f"Error generando reporte detallado PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/descarga_reportes')
def descarga_reportes():
    """
    Página de descarga de reportes
    """
    try:
        brokers = db.session.query(Broker).all()
        comitentes = db.session.query(Comitente).all()
        tickers = db.session.query(Ticker).all()
        
        return render_template('descarga_reportes.html', 
                             brokers=brokers, 
                             comitentes=comitentes, 
                             tickers=tickers)
        
    except Exception as e:
        logging.error(f"Error cargando página de reportes: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# PUNTO DE ENTRADA
# ==========================================

if __name__ == '__main__':
    # La aplicación ya está creada y configurada al inicio del archivo
    # Ejecutar en modo debug usando la configuración
    debug_mode = app.config.get('DEBUG', True)
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)