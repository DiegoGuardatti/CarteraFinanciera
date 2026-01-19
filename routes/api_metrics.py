"""
API de Métricas Básicas
Endpoints para métricas de cartera y análisis financiero
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from extensions import db
from modelo import Activo, Broker

api_metrics_bp = Blueprint('api_metrics', __name__, url_prefix='/api/metrics')

@api_metrics_bp.route('/portfolio')
def get_portfolio_metrics():
    """
    Obtener métricas básicas del portfolio
    """
    try:
        # Obtener todos los activos
        activos = Activo.query.all()
        
        # Calcular métricas básicas
        total_inversion = sum(activo.Precio_Compra * activo.Cantidad_Nominales_Compra for activo in activos)
        valor_actual = sum(activo.Precio_Venta * activo.Cantidad_Nominales_Venta if activo.Precio_Venta else activo.Precio_Compra * activo.Cantidad_Nominales_Compra for activo in activos)
        
        # Calcular ganancia/perdida
        ganancia = valor_actual - total_inversion
        rendimiento = (ganancia / total_inversion) * 100 if total_inversion > 0 else 0
        
        # Obtener distribución por tipo de activo
        distribucion = {}
        for activo in activos:
            # Obtener tipo de activo desde ticker
            tipo = activo.ticker.instrumento_financiero.Nombre if activo.ticker and activo.ticker.instrumento_financiero else 'Desconocido'
            valor = activo.Precio_Venta * activo.Cantidad_Nominales_Venta if activo.Precio_Venta else activo.Precio_Compra * activo.Cantidad_Nominales_Compra
            distribucion[tipo] = distribucion.get(tipo, 0) + valor
        
        # Formatear distribución
        distribucion_percent = {k: round((v / valor_actual) * 100, 2) for k, v in distribucion.items()}
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'total_inversion': round(total_inversion, 2),
            'valor_actual': round(valor_actual, 2),
            'ganancia': round(ganancia, 2),
            'rendimiento_percent': round(rendimiento, 2),
            'distribucion': distribucion_percent
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@api_metrics_bp.route('/top-performers')
def get_top_performers():
    """
    Obtener los activos con mejor rendimiento
    """
    try:
        per_page = int(request.args.get('per_page', 5))
        
        # Obtener todos los activos
        activos = Activo.query.all()
        
        # Calcular rendimiento para cada activo
        activos_con_rendimiento = []
        for activo in activos:
            if activo.Precio_Venta:
                rendimiento = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
            else:
                rendimiento = 0  # Si no hay precio de venta, consideramos rendimiento 0
            activos_con_rendimiento.append({
                'id': activo.Id_Activo,
                'nombre': activo.ticker.Nombre_Ticker if activo.ticker else 'Desconocido',
                'tipo': activo.ticker.instrumento_financiero.Nombre if activo.ticker and activo.ticker.instrumento_financiero else 'Desconocido',
                'rendimiento': rendimiento,
                'precio_compra': activo.Precio_Compra,
                'precio_actual': activo.Precio_Venta if activo.Precio_Venta else activo.Precio_Compra,
                'cantidad': activo.Cantidad_Nominales_Compra
            })
        
        # Ordenar por rendimiento (descendente)
        activos_con_rendimiento.sort(key=lambda x: x['rendimiento'], reverse=True)
        
        # Tomar los top performers
        top_performers = activos_con_rendimiento[:per_page]
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'top_performers': top_performers
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@api_metrics_bp.route('/bottom-performers')
def get_bottom_performers():
    """
    Obtener los activos con peor rendimiento
    """
    try:
        limit = int(request.args.get('limit', 5))
        
        # Obtener todos los activos
        activos = Activo.query.all()
        
        # Calcular rendimiento para cada activo
        activos_con_rendimiento = []
        for activo in activos:
            if activo.Precio_Venta:
                rendimiento = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
            else:
                rendimiento = 0  # Si no hay precio de venta, consideramos rendimiento 0
            activos_con_rendimiento.append({
                'id': activo.Id_Activo,
                'nombre': activo.ticker.Nombre_Ticker if activo.ticker else 'Desconocido',
                'tipo': activo.ticker.instrumento_financiero.Nombre if activo.ticker and activo.ticker.instrumento_financiero else 'Desconocido',
                'rendimiento': rendimiento,
                'precio_compra': activo.Precio_Compra,
                'precio_actual': activo.Precio_Venta if activo.Precio_Venta else activo.Precio_Compra,
                'cantidad': activo.Cantidad_Nominales_Compra
            })
        
        # Ordenar por rendimiento (ascendente)
        activos_con_rendimiento.sort(key=lambda x: x['rendimiento'])
        
        # Tomar los bottom performers
        bottom_performers = activos_con_rendimiento[:limit]
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'bottom_performers': bottom_performers
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@api_metrics_bp.route('/performance-tickers')
def get_ticker_performance():
    """
    Obtener rendimiento por ticker
    """
    try:
        # Obtener todos los activos
        activos = Activo.query.all()
        
        # Calcular rendimiento por ticker
        ticker_performance = []
        for activo in activos:
            if activo.Precio_Venta:
                rendimiento = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
            else:
                rendimiento = 0  # Si no hay precio de venta, consideramos rendimiento 0
            ticker_performance.append({
                'ticker': activo.ticker.Nombre_Ticker if activo.ticker else 'Desconocido',
                'nombre': activo.ticker.Nombre_Ticker if activo.ticker else 'Desconocido',
                'rendimiento': rendimiento,
                'precio_compra': activo.Precio_Compra,
                'precio_actual': activo.Precio_Venta if activo.Precio_Venta else activo.Precio_Compra,
                'cantidad': activo.Cantidad_Nominales_Compra
            })
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'ticker_performance': ticker_performance
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@api_metrics_bp.route('/dashboard/summary')
def get_dashboard_summary():
    """
    Obtener resumen para el dashboard
    """
    try:
        # Obtener métricas básicas
        portfolio_data = get_portfolio_metrics()
        portfolio_json = portfolio_data.get_json()
        
        # Obtener top performers
        top_performers_data = get_top_performers()
        top_performers_json = top_performers_data.get_json()
        
        # Obtener bottom performers
        bottom_performers_data = get_bottom_performers()
        bottom_performers_json = bottom_performers_data.get_json()
        
        # Combinar datos
        summary = {
            'portfolio': portfolio_json,
            'top_performers': top_performers_json.get('top_performers', []),
            'bottom_performers': bottom_performers_json.get('bottom_performers', [])
        }
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500