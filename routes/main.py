"""
Rutas principales de la aplicación
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from modelo import Broker, InstrumentoFinanciero
from extensions import db, csrf

# Crear blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@main_bp.route('/compra')
def compra():
    """Página de registro de compras"""
    from modelo import Ticker
    brokers = db.session.query(Broker).all()
    instrumentos = db.session.query(InstrumentoFinanciero).all()
    tickers = db.session.query(Ticker).all()
    return render_template('compra.html', 
                         brokers=brokers, 
                         InstrumentoFinancieros=instrumentos,
                         tickers=tickers)

@main_bp.route('/venta')
def venta():
    """Página de registro de ventas"""
    from modelo import Ticker
    brokers = db.session.query(Broker).all()
    instrumentos = db.session.query(InstrumentoFinanciero).all()
    tickers = db.session.query(Ticker).all()
    return render_template('venta.html', 
                         brokers=brokers, 
                         InstrumentoFinancieros=instrumentos,
                         tickers=tickers)

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

@main_bp.route('/registrar_broker', methods=['POST'])
def registrar_broker():
    """Registrar un nuevo broker"""
    try:
        # Obtener datos del formulario
        nombre = request.form.get('Nombre_broker', '').strip()
        comision = request.form.get('Comision_broker', 0)
        asesor = request.form.get('Asesor_broker', '').strip()
        
        # Validar datos
        if not nombre:
            flash('El nombre del broker es obligatorio', 'error')
            return redirect(url_for('main.index'))
        
        try:
            comision = float(comision)
        except ValueError:
            flash('La comisión debe ser un número válido', 'error')
            return redirect(url_for('main.index'))
        
        # Verificar si el broker ya existe
        broker_existente = Broker.query.filter_by(Nombre=nombre).first()
        if broker_existente:
            flash(f'El broker "{nombre}" ya existe', 'error')
            return redirect(url_for('main.index'))
        
        # Crear nuevo broker
        nuevo_broker = Broker(
            Nombre=nombre,
            Comision=comision,
            Asesor=asesor
        )
        
        db.session.add(nuevo_broker)
        db.session.commit()
        
        flash(f'Broker "{nombre}" registrado exitosamente', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar broker: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/registrar_comitente', methods=['POST'])
def registrar_comitente():
    """Registrar un nuevo comitente"""
    try:
        from modelo import Comitente
        # Obtener datos del formulario
        id_broker = request.form.get('Id_Broker')
        titular = request.form.get('Titular', '').strip()
        numero = request.form.get('Numero', '').strip()
        
        # Validar datos
        if not id_broker:
            flash('Debe seleccionar un broker', 'error')
            return redirect(url_for('main.index'))
        
        if not titular:
            flash('El titular del comitente es obligatorio', 'error')
            return redirect(url_for('main.index'))
        
        if not numero:
            flash('El número de comitente es obligatorio', 'error')
            return redirect(url_for('main.index'))
        
        try:
            id_broker = int(id_broker)
        except ValueError:
            flash('El ID del broker debe ser un número válido', 'error')
            return redirect(url_for('main.index'))
        
        # Verificar si el broker existe
        broker = Broker.query.get(id_broker)
        if not broker:
            flash('El broker seleccionado no existe', 'error')
            return redirect(url_for('main.index'))
        
        # Verificar si el comitente ya existe
        comitente_existente = Comitente.query.filter_by(Numero=numero).first()
        if comitente_existente:
            flash(f'El comitente con número "{numero}" ya existe', 'error')
            return redirect(url_for('main.index'))
        
        # Crear nuevo comitente
        nuevo_comitente = Comitente(
            Titular=titular,
            Numero=numero,
            Id_Broker=id_broker
        )
        
        db.session.add(nuevo_comitente)
        db.session.commit()
        
        flash(f'Comitente "{titular}" registrado exitosamente', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar comitente: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/registrar_InstrumentoFinanciero', methods=['POST'])
def registrar_instrumento_financiero():
    """Registrar un nuevo instrumento financiero"""
    try:
        # Obtener datos del formulario
        nombre = request.form.get('Nombre_InstrumentoFinanciero', '').strip()
        
        # Validar datos
        if not nombre:
            flash('El nombre del instrumento financiero es obligatorio', 'error')
            return redirect(url_for('main.index'))
        
        # Verificar si el instrumento ya existe
        instrumento_existente = InstrumentoFinanciero.query.filter_by(Nombre=nombre).first()
        if instrumento_existente:
            flash(f'El instrumento financiero "{nombre}" ya existe', 'error')
            return redirect(url_for('main.index'))
        
        # Crear nuevo instrumento financiero
        nuevo_instrumento = InstrumentoFinanciero(
            Nombre=nombre
        )
        
        db.session.add(nuevo_instrumento)
        db.session.commit()
        
        flash(f'Instrumento financiero "{nombre}" registrado exitosamente', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar instrumento financiero: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/validar_ticker', methods=['POST'])
def validar_ticker():
    """Validar si un ticker existe"""
    try:
        from modelo import Ticker
        ticker = request.form.get('nuevoTicker', '').strip().upper()
        
        if not ticker:
            return jsonify({'existe': False, 'mensaje': ''})
        
        # Verificar si el ticker existe
        ticker_existente = Ticker.query.filter_by(Nombre_Ticker=ticker).first()
        
        if ticker_existente:
            return jsonify({'existe': True, 'mensaje': f'El ticker "{ticker}" ya existe'})
        
        return jsonify({'existe': False, 'mensaje': ''})
        
    except Exception as e:
        return jsonify({'existe': False, 'mensaje': str(e)})

@main_bp.route('/registrar_ticker', methods=['POST'])
def registrar_ticker():
    """Registrar un nuevo ticker"""
    try:
        from modelo import Ticker
        # Obtener datos del formulario
        ticker = request.form.get('nuevoTicker', '').strip().upper()
        descripcion = request.form.get('Descripcion', '').strip()
        id_instrumento = request.form.get('selectInstrumento')
        
        # Validar datos
        if not ticker:
            return jsonify({'existe': False, 'mensaje': 'El ticker es obligatorio'})
        
        if not descripcion:
            return jsonify({'existe': False, 'mensaje': 'La descripción es obligatoria'})
        
        if not id_instrumento:
            return jsonify({'existe': False, 'mensaje': 'Debe seleccionar un instrumento financiero'})
        
        try:
            id_instrumento = int(id_instrumento)
        except ValueError:
            return jsonify({'existe': False, 'mensaje': 'El ID del instrumento debe ser un número válido'})
        
        # Verificar si el instrumento existe
        instrumento = InstrumentoFinanciero.query.get(id_instrumento)
        if not instrumento:
            return jsonify({'existe': False, 'mensaje': 'El instrumento seleccionado no existe'})
        
        # Verificar si el ticker ya existe
        ticker_existente = Ticker.query.filter_by(Nombre_Ticker=ticker).first()
        if ticker_existente:
            return jsonify({'existe': False, 'mensaje': f'El ticker "{ticker}" ya existe'})
        
        # Crear nuevo ticker
        nuevo_ticker = Ticker(
            Nombre_Ticker=ticker,
            Descripcion=descripcion,
            Id_InstrumentoFinanciero=id_instrumento
        )
        
        db.session.add(nuevo_ticker)
        db.session.commit()
        
        return jsonify({'existe': False, 'mensaje': f'Ticker "{ticker}" registrado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'existe': False, 'mensaje': f'Error al registrar ticker: {str(e)}'})

@main_bp.route('/get_comitentes/<int:broker_id>')
def get_comitentes(broker_id):
    """Obtener comitentes por broker"""
    try:
        from modelo import Comitente
        comitentes = Comitente.query.filter_by(Id_Broker=broker_id).all()
        comitentes_data = [{'Id_Comitente': c.Id_Comitente, 'Titular': c.Titular} for c in comitentes]
        return {'comitentes': comitentes_data}
    except Exception as e:
        return {'comitentes': []}

@main_bp.route('/get_tickers/<int:instrumento_id>')
def get_tickers(instrumento_id):
    """Obtener tickers por instrumento financiero"""
    try:
        from modelo import Ticker
        tickers = Ticker.query.filter_by(Id_InstrumentoFinanciero=instrumento_id).all()
        tickers_data = [{'Id_Ticker': t.Id_Ticker, 'Nombre_Ticker': t.Nombre_Ticker, 'Descripcion': t.Descripcion} for t in tickers]
        return {'tickers': tickers_data}
    except Exception as e:
        return {'tickers': []}

@main_bp.route('/get_comision_broker/<int:broker_id>')
def get_comision_broker(broker_id):
    """Obtener comisión del broker"""
    try:
        broker = Broker.query.get(broker_id)
        if broker:
            return {'comision': broker.Comision}
        return {'comision': 0}
    except Exception as e:
        return {'comision': 0}

@main_bp.route('/get_compras/<int:ticker_id>')
def get_compras(ticker_id):
    """Obtener compras disponibles para venta de un ticker"""
    try:
        from modelo import Activo
        # Solo devolver activos que no estén vendidos
        compras = Activo.query.filter_by(Id_Ticker=ticker_id, Activo_Estado='EN_CARTERA').all()
        compras_data = [{
            'Id_Activo': c.Id_Activo,
            'Fecha_Hora_Compra': c.Fecha_Hora_Compra.isoformat() if c.Fecha_Hora_Compra else None,
            'Precio_Compra': c.Precio_Compra,
            'Cantidad_Nominales_Compra': c.Cantidad_Nominales_Compra,
            'Total_Pesos_Compra': c.Total_Pesos_Compra,
            'Total_Dolares_Compra': c.Total_Dolares_Compra
        } for c in compras]
        return jsonify(compras_data)
    except Exception as e:
        return jsonify([])

@main_bp.route('/registrar_compra', methods=['POST'])
def registrar_compra():
    """Registrar una compra"""
    try:
        # Obtener datos del formulario
        id_broker = request.form.get('Id_Broker')
        id_comitente = request.form.get('Id_Comitente')
        id_ticker = request.form.get('Id_Ticker')
        precio_dolar_mep = request.form.get('precioDolarMEPCompra')
        fecha_compra = request.form.get('fechaHoraCompra')
        precio_compra = request.form.get('precioCompra')
        cantidad = request.form.get('cantidadCompra')
        comision_broker = request.form.get('comisionBroker')
        total_pesos = request.form.get('totalPesosCompra')
        total_dolares = request.form.get('totalDolaresCompra')
        
        # Validar datos
        if not id_broker:
            return {'message': 'ID del broker es obligatorio', 'success': False}
        
        if not id_comitente:
            return {'message': 'ID del comitente es obligatorio', 'success': False}
        
        if not id_ticker:
            return {'message': 'ID del ticker es obligatorio', 'success': False}
        
        if not precio_dolar_mep:
            return {'message': 'Precio del dólar MEP es obligatorio', 'success': False}
        
        if not fecha_compra:
            return {'message': 'Fecha de compra es obligatoria', 'success': False}
        
        if not precio_compra:
            return {'message': 'Precio de compra es obligatorio', 'success': False}
        
        if not cantidad:
            return {'message': 'Cantidad es obligatoria', 'success': False}
        
        try:
            id_broker = int(id_broker)
            id_comitente = int(id_comitente)
            id_ticker = int(id_ticker)
            precio_dolar_mep = float(precio_dolar_mep.replace(',', '.'))
            precio_compra = float(precio_compra.replace(',', '.'))
            cantidad = float(cantidad.replace(',', '.'))
            if comision_broker:
                comision_broker = float(comision_broker.replace(',', '.'))
            else:
                comision_broker = 0
            if total_pesos:
                # Manejar formato español (1.234,56) y inglés (1234.56)
                total_pesos_str = total_pesos.replace('.', '').replace(',', '.')
                total_pesos = float(total_pesos_str)
            if total_dolares:
                # Manejar formato español (1.234,56) y inglés (1234.56)
                total_dolares_str = total_dolares.replace('.', '').replace(',', '.')
                total_dolares = float(total_dolares_str)
        except ValueError as e:
            return {'message': f'Datos numéricos inválidos: {str(e)}', 'success': False}
        
        from datetime import datetime
        try:
            fecha_compra_dt = datetime.strptime(fecha_compra, '%Y-%m-%dT%H:%M')
        except ValueError:
            return {'message': 'Formato de fecha inválido', 'success': False}
        
        # Crear nuevo activo
        from modelo import Activo
        nuevo_activo = Activo(
            Id_Broker=id_broker,
            Id_Comitente=id_comitente,
            Id_Ticker=id_ticker,
            Precio_Dolar_MEP_Compra=precio_dolar_mep,
            Fecha_Hora_Compra=fecha_compra_dt,
            Precio_Compra=precio_compra,
            Cantidad_Nominales_Compra=cantidad,
            Comision_Broker=comision_broker,
            Total_Pesos_Compra=total_pesos if total_pesos else precio_compra * cantidad,
            Total_Dolares_Compra=total_dolares if total_dolares else (precio_compra * cantidad) / precio_dolar_mep,
            Activo_Estado='EN_CARTERA'
        )
        
        db.session.add(nuevo_activo)
        db.session.commit()
        
        return {'message': 'Compra registrada exitosamente', 'success': True, 'id_activo': nuevo_activo.Id_Activo}
        
    except Exception as e:
        db.session.rollback()
        return {'message': f'Error al registrar compra: {str(e)}', 'success': False}

@main_bp.route('/registrar_venta', methods=['POST'])
@csrf.exempt
def registrar_venta():
    """Registrar una venta de un activo existente"""
    try:
        # Obtener datos del formulario JSON
        id_activo = request.json.get('Id_Activo')
        fecha_venta = request.json.get('Fecha_Hora_Venta')
        precio_venta = request.json.get('PrecioVenta')
        precio_dolar_mep = request.json.get('PrecioDolarMEPVenta')
        cantidad = request.json.get('CantidadVenta')
        total_pesos = request.json.get('Total_Pesos_Venta')
        total_dolares = request.json.get('Total_Dolares_Venta')
        
        # Validar datos obligatorios
        if not id_activo:
            return {'message': 'ID del activo es obligatorio', 'success': False}
        
        if not fecha_venta:
            return {'message': 'Fecha de venta es obligatoria', 'success': False}
        
        if not precio_venta:
            return {'message': 'Precio de venta es obligatorio', 'success': False}
        
        if not precio_dolar_mep:
            return {'message': 'Precio del dólar MEP es obligatorio', 'success': False}
        
        if not cantidad:
            return {'message': 'Cantidad es obligatoria', 'success': False}
        
        try:
            id_activo = int(id_activo)
            # Manejar formato español (1.234,56) y inglés (1234.56)
            precio_venta = float(str(precio_venta).replace(',', '.'))
            precio_dolar_mep = float(str(precio_dolar_mep).replace(',', '.'))
            cantidad = float(str(cantidad).replace(',', '.'))
            if total_pesos:
                total_pesos_str = str(total_pesos).replace('.', '').replace(',', '.')
                total_pesos = float(total_pesos_str)
            if total_dolares:
                total_dolares_str = str(total_dolares).replace('.', '').replace(',', '.')
                total_dolares = float(total_dolares_str)
        except ValueError as e:
            return {'message': f'Datos numéricos inválidos: {str(e)}', 'success': False}
        
        # Verificar si el activo existe
        from modelo import Activo
        activo = Activo.query.get(id_activo)
        if not activo:
            return {'message': 'Activo no encontrado', 'success': False}
        
        # Verificar que el activo no esté ya vendido
        if activo.Activo_Estado == 'VENDIDO':
            return {'message': 'El activo ya ha sido vendido', 'success': False}
        
        # Actualizar datos de venta
        from datetime import datetime
        activo.Fecha_Hora_Venta = datetime.strptime(fecha_venta, '%Y-%m-%dT%H:%M')
        activo.Precio_Venta = precio_venta
        activo.Precio_Dolar_MEP_Venta = precio_dolar_mep
        activo.Cantidad_Nominales_Venta = cantidad
        activo.Total_Pesos_Venta = total_pesos if total_pesos else precio_venta * cantidad
        activo.Total_Dolares_Venta = total_dolares if total_dolares else (precio_venta * cantidad) / precio_dolar_mep
        activo.Activo_Estado = 'VENDIDO'
        
        db.session.commit()
        
        return {'message': 'Venta registrada exitosamente', 'success': True}
        
    except Exception as e:
        db.session.rollback()
        return {'message': f'Error al registrar venta: {str(e)}', 'success': False}

@main_bp.route('/informe_activos', methods=['POST'])
@csrf.exempt
def informe_activos():
    """API para obtener activos filtrados para el informe"""
    try:
        from modelo import Activo, Comitente, Ticker
        
        # Obtener parámetros de filtro
        id_broker = request.form.get('broker', '')
        id_comitente = request.form.get('comitente', '')
        tipo_instrumento = request.form.get('tipo_instrumento', '')
        ticker = request.form.get('ticker', '')
        estado = request.form.get('estado', '')
        
        # Construir query
        query = db.session.query(Activo).join(Ticker)
        
        if id_broker:
            query = query.filter(Activo.Id_Broker == int(id_broker))
        if id_comitente:
            query = query.filter(Activo.Id_Comitente == int(id_comitente))
        if ticker:
            query = query.filter(Activo.Id_Ticker == int(ticker))
        if estado:
            query = query.filter(Activo.Activo_Estado == estado)
        if tipo_instrumento:
            query = query.filter(Ticker.Id_InstrumentoFinanciero == int(tipo_instrumento))
        
        activos = query.all()
        
        # Formatear resultados
        results = []
        total_ganancia = 0
        
        for a in activos:
            ganancia = 0
            porcentaje_pesos = 0
            porcentaje_dolares = 0
            
            if a.Total_Pesos_Venta and a.Total_Pesos_Compra:
                ganancia = a.Total_Pesos_Venta - a.Total_Pesos_Compra
                porcentaje_pesos = (ganancia / a.Total_Pesos_Compra) * 100 if a.Total_Pesos_Compra else 0
            
            if a.Total_Dolares_Venta and a.Total_Dolares_Compra:
                porcentaje_dolares = ((a.Total_Dolares_Venta - a.Total_Dolares_Compra) / a.Total_Dolares_Compra) * 100 if a.Total_Dolares_Compra else 0
            
            total_ganancia += ganancia
            
            ticker_info = db.session.query(Ticker).get(a.Id_Ticker)
            
            results.append({
                'Id_Activo': a.Id_Activo,
                'Fecha_Compra': a.Fecha_Hora_Compra.isoformat() if a.Fecha_Hora_Compra else None,
                'Precio_Compra': a.Precio_Compra,
                'Cantidad_Nominales_Compra': a.Cantidad_Nominales_Compra,
                'Total_Pesos_Compra': a.Total_Pesos_Compra,
                'Fecha_Venta': a.Fecha_Hora_Venta.isoformat() if a.Fecha_Hora_Venta else None,
                'Precio_Venta': a.Precio_Venta,
                'Total_Pesos_Venta': a.Total_Pesos_Venta,
                'Ganancia': ganancia,
                'Porcentaje_Pesos': porcentaje_pesos,
                'Dolar_MEP_Compra': a.Precio_Dolar_MEP_Compra,
                'Dolar_MEP_Venta': a.Precio_Dolar_MEP_Venta,
                'Porcentaje_Dolares': porcentaje_dolares,
                'Ticker': ticker_info.Nombre_Ticker if ticker_info else 'N/A',
                'Estado': a.Activo_Estado
            })
        
        return jsonify({
            'data': results,
            'total_ganancia_pesos': total_ganancia,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'data': []}), 500

@main_bp.route('/obtener_estados_activos', methods=['GET'])
def obtener_estados_activos():
    """API para obtener los estados posibles de los activos"""
    try:
        from modelo import Activo
        # Obtener estados únicos de la base de datos
        estados = db.session.query(Activo.Activo_Estado).distinct().all()
        estados_list = [e[0] for e in estados if e[0]]
        
        # Si no hay estados en la BD, devolver valores por defecto
        if not estados_list:
            estados_list = ['EN_CARTERA', 'VENDIDO', 'PENDIENTE']
        
        return jsonify(estados_list)
    except Exception as e:
        # En caso de error, devolver valores por defecto
        return jsonify(['EN_CARTERA', 'VENDIDO', 'PENDIENTE'])

