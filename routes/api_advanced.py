"""
Blueprint para APIs de métricas financieras avanzadas institucionales
Incluye VaR, Monte Carlo, Stress Testing y Métricas ESG
"""

from flask import Blueprint, jsonify, request
from metricas_avanzadas import (
    calcular_var_historico,
    calcular_var_parametrico,
    analisis_monte_carlo,
    stress_testing_automatizado,
    calcular_metricas_esg,
    portfolio_var_cartera
)
from utils.cache_config import cache_result
from datetime import datetime
import logging

api_advanced_bp = Blueprint('api_advanced', __name__)
logger = logging.getLogger(__name__)

@api_advanced_bp.route('/var/historico/<int:activo_id>', methods=['GET'])
@cache_result(timeout=300)  # Cache 5 minutos
def get_var_historico(activo_id):
    """
    Obtiene VaR histórico para un activo
    
    Query params:
        confidence_level (float): Nivel de confianza (default: 0.95)
        window_days (int): Ventana de días (default: 252)
    """
    try:
        confidence_level = float(request.args.get('confidence_level', 0.95))
        window_days = int(request.args.get('window_days', 252))
        
        result = calcular_var_historico(activo_id, confidence_level, window_days)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': result.get('timestamp', None)
        })
        
    except ValueError as e:
        logger.error(f"Error en parámetros de VaR histórico: {str(e)}")
        return jsonify({'error': 'Parámetros inválidos'}), 400
    except Exception as e:
        logger.error(f"Error en VaR histórico para activo {activo_id}: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/var/parametrico/<int:activo_id>', methods=['GET'])
@cache_result(timeout=300)  # Cache 5 minutos
def get_var_parametrico(activo_id):
    """
    Obtiene VaR paramétrico para un activo
    
    Query params:
        confidence_level (float): Nivel de confianza (default: 0.95)
    """
    try:
        confidence_level = float(request.args.get('confidence_level', 0.95))
        
        result = calcular_var_parametrico(activo_id, confidence_level)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': result.get('timestamp', None)
        })
        
    except ValueError as e:
        logger.error(f"Error en parámetros de VaR paramétrico: {str(e)}")
        return jsonify({'error': 'Parámetros inválidos'}), 400
    except Exception as e:
        logger.error(f"Error en VaR paramétrico para activo {activo_id}: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/monte-carlo/<int:activo_id>', methods=['GET'])
@cache_result(timeout=600)  # Cache 10 minutos
def get_monte_carlo(activo_id):
    """
    Obtiene análisis Monte Carlo para un activo
    
    Query params:
        num_simulaciones (int): Número de simulaciones (default: 10000)
        dias_horizonte (int): Días hacia adelante (default: 30)
    """
    try:
        num_simulaciones = int(request.args.get('num_simulaciones', 10000))
        dias_horizonte = int(request.args.get('dias_horizonte', 30))
        
        # Validar parámetros
        if num_simulaciones > 100000:
            return jsonify({'error': 'Máximo 100,000 simulaciones permitidas'}), 400
        if dias_horizonte > 365:
            return jsonify({'error': 'Máximo 365 días de horizonte'}), 400
        
        result = analisis_monte_carlo(activo_id, num_simulaciones, dias_horizonte)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': result.get('timestamp', None)
        })
        
    except ValueError as e:
        logger.error(f"Error en parámetros de Monte Carlo: {str(e)}")
        return jsonify({'error': 'Parámetros inválidos'}), 400
    except Exception as e:
        logger.error(f"Error en Monte Carlo para activo {activo_id}: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/stress-testing/<int:activo_id>', methods=['GET'])
@cache_result(timeout=1800)  # Cache 30 minutos
def get_stress_testing(activo_id):
    """
    Obtiene stress testing automatizado para un activo
    
    Query params:
        escenarios (str): JSON con escenarios personalizados (opcional)
    """
    try:
        escenarios_json = request.args.get('escenarios')
        escenarios = None
        
        if escenarios_json:
            import json
            try:
                escenarios = json.loads(escenarios_json)
            except json.JSONDecodeError:
                return jsonify({'error': 'Formato JSON inválido para escenarios'}), 400
        
        result = stress_testing_automatizado(activo_id, escenarios)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': result.get('timestamp', None)
        })
        
    except Exception as e:
        logger.error(f"Error en stress testing para activo {activo_id}: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/esg/<int:activo_id>', methods=['GET'])
@cache_result(timeout=3600)  # Cache 1 hora
def get_esg_metrics(activo_id):
    """
    Obtiene métricas ESG para un activo
    """
    try:
        result = calcular_metricas_esg(activo_id)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': result.get('timestamp', None)
        })
        
    except Exception as e:
        logger.error(f"Error en métricas ESG para activo {activo_id}: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/portfolio/var', methods=['GET'])
@cache_result(timeout=300)  # Cache 5 minutos
def get_portfolio_var():
    """
    Obtiene VaR de toda la cartera
    
    Query params:
        confidence_level (float): Nivel de confianza (default: 0.95)
        metodo (str): 'historico' o 'parametrico' (default: 'historico')
    """
    try:
        confidence_level = float(request.args.get('confidence_level', 0.95))
        metodo = request.args.get('metodo', 'historico')
        
        if metodo not in ['historico', 'parametrico']:
            return jsonify({'error': 'Método debe ser "historico" o "parametrico"'}), 400
        
        result = portfolio_var_cartera(confidence_level, metodo)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': result.get('timestamp', None)
        })
        
    except ValueError as e:
        logger.error(f"Error en parámetros de VaR de cartera: {str(e)}")
        return jsonify({'error': 'Parámetros inválidos'}), 400
    except Exception as e:
        logger.error(f"Error en VaR de cartera: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/risk-summary/<int:activo_id>', methods=['GET'])
@cache_result(timeout=300)  # Cache 5 minutos
def get_risk_summary(activo_id):
    """
    Obtiene resumen completo de riesgo para un activo
    Incluye VaR histórico, paramétrico, Monte Carlo y Stress Testing
    """
    try:
        # Obtener todas las métricas de riesgo
        var_historico = calcular_var_historico(activo_id)
        var_parametrico = calcular_var_parametrico(activo_id)
        monte_carlo = analisis_monte_carlo(activo_id)
        stress_testing = stress_testing_automatizado(activo_id)
        
        # Verificar si todas las métricas se calcularon correctamente
        metrics = {}
        if 'error' not in var_historico:
            metrics['var_historico'] = var_historico
        if 'error' not in var_parametrico:
            metrics['var_parametrico'] = var_parametrico
        if 'error' not in monte_carlo:
            metrics['monte_carlo'] = monte_carlo
        if 'error' not in stress_testing:
            metrics['stress_testing'] = stress_testing
        
        if not metrics:
            return jsonify({'error': 'No se pudieron calcular métricas de riesgo'}), 404
        
        # Crear resumen comparativo
        summary = {
            'activo_id': activo_id,
            'ticker': metrics.get('var_historico', {}).get('ticker', 'N/A'),
            'metricas_disponibles': list(metrics.keys()),
            'comparacion_var': {},
            'recomendaciones': [],
            'timestamp': var_historico.get('timestamp') if 'error' not in var_historico else None
        }
        
        # Comparar VaRs si están disponibles
        if 'var_historico' in metrics and 'var_parametrico' in metrics:
            var_hist = abs(metrics['var_historico']['var_historico']['var_porcentaje'])
            var_param = abs(metrics['var_parametrico']['var_parametrico']['var_porcentaje'])
            
            summary['comparacion_var'] = {
                'historico': var_hist,
                'parametrico': var_param,
                'diferencia': round(abs(var_hist - var_param), 3),
                'metodo_mas_conservador': 'historico' if var_hist > var_param else 'parametrico'
            }
        
        # Generar recomendaciones basadas en los resultados
        if 'var_historico' in metrics:
            var_hist = abs(metrics['var_historico']['var_historico']['var_porcentaje'])
            if var_hist > 5:
                summary['recomendaciones'].append('VaR alto - Considerar estrategias de cobertura')
            if var_hist > 10:
                summary['recomendaciones'].append('VaR muy alto - Evaluar reducción de posición')
        
        if 'stress_testing' in metrics:
            peor_escenario = metrics['stress_testing']['resumen_stress']['perdida_maxima']
            if peor_escenario > 40:
                summary['recomendaciones'].append('Alta vulnerabilidad a stress - Diversificar')
        
        summary['recomendaciones'].extend([
            'Monitorear métricas de riesgo regularmente',
            'Actualizar análisis ante cambios de mercado significativos'
        ])
        
        return jsonify({
            'success': True,
            'data': {
                'summary': summary,
                'detailed_metrics': metrics
            }
        })
        
    except Exception as e:
        logger.error(f"Error en resumen de riesgo para activo {activo_id}: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_advanced_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check para las APIs de métricas avanzadas
    """
    try:
        # Verificar que las funciones principales estén disponibles
        from metricas_avanzadas import (
            calcular_var_historico,
            calcular_var_parametrico,
            analisis_monte_carlo,
            stress_testing_automatizado,
            calcular_metricas_esg,
            portfolio_var_cartera
        )
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'var_historico': 'available',
                'var_parametrico': 'available',
                'monte_carlo': 'available',
                'stress_testing': 'available',
                'esg_metrics': 'available',
                'portfolio_var': 'available'
            }
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500