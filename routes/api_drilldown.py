"""
API para Drill-Down y Análisis Detallado
Soporte para visualizaciones interactivas avanzadas
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import re

# Importaciones opcionales
try:
    from flask_login import login_required
    FLASK_LOGIN_AVAILABLE = True
except ImportError:
    FLASK_LOGIN_AVAILABLE = False
    def login_required(f):
        return f

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    # Mock numpy functions
    import random
    import math
    
    class MockNumpy:
        class random:
            @staticmethod
            def uniform(low, high):
                return random.uniform(low, high)
            
            @staticmethod
            def randint(low, high):
                return random.randint(low, high)
            
            @staticmethod
            def choice(seq, p=None):
                return random.choice(seq)
            
            @staticmethod
            def normal(mean, std, size):
                return [random.gauss(mean, std) for _ in range(size)]
        
        @staticmethod
        def mean(arr):
            return sum(arr) / len(arr) if arr else 0
        
        @staticmethod
        def std(arr):
            if len(arr) < 2:
                return 0
            mean = sum(arr) / len(arr)
            variance = sum((x - mean) ** 2 for x in arr) / (len(arr) - 1)
            return math.sqrt(variance)
    
    np = MockNumpy()

from extensions import db

# Función de validación de ticker simple
def validate_ticker(ticker):
    """Validar formato de ticker financiero"""
    return bool(re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', ticker))

api_drilldown_bp = Blueprint('api_drilldown', __name__, url_prefix='/api')

@api_drilldown_bp.route('/metrics/drill-down')
@login_required
def drill_down_analysis():
    """
    Endpoint para análisis drill-down por categoría
    Permite obtener detalles granulares de una categoría específica
    """
    try:
        category = request.args.get('category', '')
        
        if not category:
            return jsonify({'error': 'Categoría requerida'}), 400
        
        # Mapear categorías a tipos de análisis
        category_mapping = {
            'Q1': 'quarterly_q1',
            'Q2': 'quarterly_q2', 
            'Q3': 'quarterly_q3',
            'Q4': 'quarterly_q4',
            'Enero': 'monthly_01',
            'Febrero': 'monthly_02',
            'Marzo': 'monthly_03',
            'Abril': 'monthly_04',
            'Mayo': 'monthly_05',
            'Junio': 'monthly_06',
            'Julio': 'monthly_07',
            'Agosto': 'monthly_08',
            'Septiembre': 'monthly_09',
            'Octubre': 'monthly_10',
            'Noviembre': 'monthly_11',
            'Diciembre': 'monthly_12'
        }
        
        analysis_type = category_mapping.get(category, 'default')
        
        # Obtener datos detallados según el tipo de análisis
        detailed_data = get_detailed_analysis(analysis_type, category)
        
        return jsonify(detailed_data)
        
    except Exception as e:
        return jsonify({'error': f'Error en análisis drill-down: {str(e)}'}), 500

@api_drilldown_bp.route('/metrics/correlation-detailed')
@login_required
def correlation_detailed_analysis():
    """
    Análisis detallado de correlación entre dos activos
    """
    try:
        ticker1 = request.args.get('ticker1', '').upper()
        ticker2 = request.args.get('ticker2', '').upper()
        
        if not ticker1 or not ticker2:
            return jsonify({'error': 'Ambos tickers son requeridos'}), 400
        
        if ticker1 == ticker2:
            return jsonify({'error': 'Los tickers deben ser diferentes'}), 400
        
        # Validar tickers
        if not validate_ticker(ticker1) or not validate_ticker(ticker2):
            return jsonify({'error': 'Formato de ticker inválido'}), 400
        
        # Obtener análisis detallado de correlación
        detailed_analysis = get_correlation_details(ticker1, ticker2)
        
        return jsonify(detailed_analysis)
        
    except Exception as e:
        return jsonify({'error': f'Error en análisis de correlación: {str(e)}'}), 500

@api_drilldown_bp.route('/metrics/backtest-detailed/<int:period_id>')
@login_required
def backtest_detailed_analysis(period_id):
    """
    Análisis detallado de backtesting por período específico
    """
    try:
        # Obtener datos de backtesting para el período específico
        backtest_data = get_backtest_period_details(period_id)
        
        return jsonify(backtest_data)
        
    except Exception as e:
        return jsonify({'error': f'Error en análisis de backtesting: {str(e)}'}), 500

@api_drilldown_bp.route('/metrics/var-contribution-detailed/<ticker>')
@login_required
def var_contribution_detailed(ticker):
    """
    Contribución detallada al VaR por activo específico
    """
    try:
        ticker = ticker.upper()
        
        if not validate_ticker(ticker):
            return jsonify({'error': 'Formato de ticker inválido'}), 400
        
        # Obtener contribución detallada al VaR
        var_contribution = get_var_contribution_details(ticker)
        
        return jsonify(var_contribution)
        
    except Exception as e:
        return jsonify({'error': f'Error en análisis de VaR: {str(e)}'}), 500

@api_drilldown_bp.route('/metrics/risk-scenario-analysis/<ticker>')
@login_required
def risk_scenario_analysis(ticker):
    """
    Análisis de escenarios de riesgo para un activo específico
    """
    try:
        ticker = ticker.upper()
        
        if not validate_ticker(ticker):
            return jsonify({'error': 'Formato de ticker inválido'}), 400
        
        # Obtener análisis de escenarios de riesgo
        scenario_analysis = get_risk_scenario_analysis(ticker)
        
        return jsonify(scenario_analysis)
        
    except Exception as e:
        return jsonify({'error': f'Error en análisis de escenarios: {str(e)}'}), 500

def get_detailed_analysis(analysis_type, category):
    """
    Obtener análisis detallado según el tipo
    """
    # Simular datos detallados por categoría
    if 'quarterly' in analysis_type:
        return generate_quarterly_detailed_data(category)
    elif 'monthly' in analysis_type:
        return generate_monthly_detailed_data(category)
    else:
        return generate_default_detailed_data(category)

def generate_quarterly_detailed_data(quarter):
    """
    Generar datos detallados para análisis trimestral
    """
    # Simular distribución mensual dentro del trimestre
    monthly_data = []
    months_in_quarter = {
        'Q1': ['Enero', 'Febrero', 'Marzo'],
        'Q2': ['Abril', 'Mayo', 'Junio'],
        'Q3': ['Julio', 'Agosto', 'Septiembre'],
        'Q4': ['Octubre', 'Noviembre', 'Diciembre']
    }
    
    months = months_in_quarter.get(quarter, ['Enero', 'Febrero', 'Marzo'])
    
    for i, month in enumerate(months):
        monthly_data.append({
            'label': month,
            'value': np.random.randint(80000, 120000),
            'performance': np.random.uniform(-5, 15),
            'volatility': np.random.uniform(10, 30),
            'sharpe_ratio': np.random.uniform(0.5, 2.0)
        })
    
    return {
        'category': quarter,
        'analysis_type': 'quarterly_detailed',
        'labels': [item['label'] for item in monthly_data],
        'values': [item['value'] for item in monthly_data],
        'performance_data': [item['performance'] for item in monthly_data],
        'volatility_data': [item['volatility'] for item in monthly_data],
        'sharpe_data': [item['sharpe_ratio'] for item in monthly_data],
        'summary': {
            'total_value': sum(item['value'] for item in monthly_data),
            'avg_performance': np.mean([item['performance'] for item in monthly_data]),
            'avg_volatility': np.mean([item['volatility'] for item in monthly_data]),
            'avg_sharpe': np.mean([item['sharpe_ratio'] for item in monthly_data])
        }
    }

def generate_monthly_detailed_data(month):
    """
    Generar datos detallados para análisis mensual
    """
    # Simular distribución semanal dentro del mes
    weekly_data = []
    for week in range(1, 5):
        weekly_data.append({
            'label': f'Semana {week}',
            'value': np.random.randint(18000, 32000),
            'performance': np.random.uniform(-8, 12),
            'daily_returns': np.random.normal(0.02, 0.15, 5).tolist()
        })
    
    return {
        'category': month,
        'analysis_type': 'monthly_detailed',
        'labels': [item['label'] for item in weekly_data],
        'values': [item['value'] for item in weekly_data],
        'performance_data': [item['performance'] for item in weekly_data],
        'weekly_returns': [item['daily_returns'] for item in weekly_data],
        'summary': {
            'total_value': sum(item['value'] for item in weekly_data),
            'avg_performance': np.mean([item['performance'] for item in weekly_data]),
            'monthly_volatility': np.std([item['performance'] for item in weekly_data])
        }
    }

def generate_default_detailed_data(category):
    """
    Generar datos detallados por defecto
    """
    labels = ['Renta Variable', 'Renta Fija', 'Commodities', 'Alternativos']
    values = [np.random.randint(40000, 80000) for _ in labels]
    
    return {
        'category': category,
        'analysis_type': 'default_detailed',
        'labels': labels,
        'values': values,
        'summary': {
            'total_value': sum(values),
            'diversification_score': np.random.uniform(0.6, 0.9)
        }
    }

def get_correlation_details(ticker1, ticker2):
    """
    Obtener detalles de correlación entre dos activos
    """
    # Simular datos históricos de correlación
    correlation = np.random.uniform(-0.9, 0.9)
    
    # Calcular estadísticas de correlación
    correlation_stats = {
        'correlation_coefficient': correlation,
        'correlation_strength': get_correlation_strength(correlation),
        'statistical_significance': np.random.choice([True, False], p=[0.7, 0.3]),
        'p_value': np.random.uniform(0.01, 0.1),
        'confidence_interval': [
            correlation - np.random.uniform(0.1, 0.3),
            correlation + np.random.uniform(0.1, 0.3)
        ],
        'rolling_correlation_30d': np.random.uniform(-0.8, 0.8),
        'rolling_correlation_90d': np.random.uniform(-0.8, 0.8),
        'rolling_correlation_1y': np.random.uniform(-0.8, 0.8)
    }
    
    # Análisis de cointegración
    cointegration_analysis = {
        'is_cointegrated': np.random.choice([True, False], p=[0.3, 0.7]),
        'cointegration_p_value': np.random.uniform(0.01, 0.2),
        'hedge_ratio': np.random.uniform(0.5, 2.0)
    }
    
    # Recomendaciones basadas en correlación
    recommendations = get_correlation_recommendations(correlation)
    
    return {
        'ticker1': ticker1,
        'ticker2': ticker2,
        'correlation_analysis': correlation_stats,
        'cointegration_analysis': cointegration_analysis,
        'recommendations': recommendations,
        'risk_implications': get_risk_implications(correlation),
        'diversification_impact': get_diversification_impact(correlation)
    }

def get_correlation_strength(correlation):
    """
    Determinar la fuerza de la correlación
    """
    abs_corr = abs(correlation)
    if abs_corr >= 0.8:
        return 'Muy Alta'
    elif abs_corr >= 0.6:
        return 'Alta'
    elif abs_corr >= 0.4:
        return 'Moderada'
    elif abs_corr >= 0.2:
        return 'Baja'
    else:
        return 'Muy Baja'

def get_correlation_recommendations(correlation):
    """
    Generar recomendaciones basadas en correlación
    """
    if correlation > 0.8:
        return {
            'portfolio_action': 'Reducir exposición',
            'risk_level': 'Alto',
            'diversification_benefit': 'Bajo',
            'rebalancing_needed': True,
            'recommended_allocation_reduction': np.random.uniform(10, 30)
        }
    elif correlation < -0.5:
        return {
            'portfolio_action': 'Mantener o aumentar',
            'risk_level': 'Bajo',
            'diversification_benefit': 'Alto',
            'rebalancing_needed': False,
            'recommended_allocation_increase': np.random.uniform(5, 15)
        }
    else:
        return {
            'portfolio_action': 'Mantener',
            'risk_level': 'Moderado',
            'diversification_benefit': 'Moderado',
            'rebalancing_needed': False,
            'recommended_allocation_change': np.random.uniform(-5, 5)
        }

def get_risk_implications(correlation):
    """
    Implicaciones de riesgo basadas en correlación
    """
    return {
        'systematic_risk_increase': correlation > 0.6,
        'hedge_effectiveness': abs(correlation) < 0.3,
        'crisis_correlation_risk': correlation > 0.7,
        'market_stress_impact': get_market_stress_impact(correlation)
    }

def get_market_stress_impact(correlation):
    """
    Impacto en escenarios de estrés de mercado
    """
    stress_scenarios = {
        'crisis_2008': correlation * np.random.uniform(0.8, 1.2),
        'covid_2020': correlation * np.random.uniform(0.9, 1.1),
        'rate_hike': correlation * np.random.uniform(0.7, 1.3),
        'inflation_spike': correlation * np.random.uniform(0.6, 1.4)
    }
    return stress_scenarios

def get_diversification_impact(correlation):
    """
    Impacto en diversificación de cartera
    """
    return {
        'diversification_ratio': 1 - correlation**2,
        'effective_number_of_assets': 1 / (1 + correlation**2),
        'concentration_risk': correlation > 0.7,
        'optimal_weight_calculation': get_optimal_weights(correlation)
    }

def get_optimal_weights(correlation):
    """
    Calcular pesos óptimos considerando correlación
    """
    if abs(correlation) > 0.8:
        return {'ticker1': 0.6, 'ticker2': 0.4}  # Concentrar en el mejor
    elif correlation < -0.5:
        return {'ticker1': 0.5, 'ticker2': 0.5}  # Balancear equally
    else:
        return {'ticker1': 0.55, 'ticker2': 0.45}  # Ligero sesgo

def get_backtest_period_details(period_id):
    """
    Obtener detalles de backtesting por período
    """
    # Simular datos detallados de backtesting
    return {
        'period_id': period_id,
        'period_name': f'Período {period_id}',
        'performance_metrics': {
            'total_return': np.random.uniform(-20, 40),
            'annualized_return': np.random.uniform(-15, 25),
            'volatility': np.random.uniform(10, 35),
            'sharpe_ratio': np.random.uniform(0.2, 2.5),
            'max_drawdown': np.random.uniform(-25, -5),
            'win_rate': np.random.uniform(40, 70)
        },
        'risk_metrics': {
            'var_95': np.random.uniform(-15, -5),
            'expected_shortfall': np.random.uniform(-20, -8),
            'beta': np.random.uniform(0.5, 1.5),
            'alpha': np.random.uniform(-5, 10)
        },
        'transaction_details': {
            'total_trades': np.random.randint(50, 200),
            'winning_trades': np.random.randint(20, 120),
            'avg_trade_duration': np.random.uniform(5, 30),
            'profit_factor': np.random.uniform(0.8, 2.5)
        }
    }

def get_var_contribution_details(ticker):
    """
    Obtener contribución detallada al VaR por activo
    """
    return {
        'ticker': ticker,
        'individual_var': np.random.uniform(50000, 150000),
        'marginal_contribution': np.random.uniform(0.1, 0.4),
        'percentage_contribution': np.random.uniform(5, 25),
        'component_var': np.random.uniform(45000, 140000),
        'diversification_benefit': np.random.uniform(-10000, 20000),
        'risk_concentration': np.random.choice(['Low', 'Medium', 'High']),
        'optimization_suggestions': {
            'reduce_weight': np.random.uniform(0, 15),
            'hedge_recommendation': np.random.choice(['None', 'Mild', 'Strong']),
            'alternative_assets': ['Ticker1', 'Ticker2', 'Ticker3']
        }
    }

def get_risk_scenario_analysis(ticker):
    """
    Análisis de escenarios de riesgo para un activo
    """
    scenarios = {
        'market_crash': {
            'probability': np.random.uniform(5, 15),
            'expected_impact': np.random.uniform(-30, -60),
            'recovery_time': np.random.randint(12, 36)
        },
        'interest_rate_shock': {
            'probability': np.random.uniform(10, 25),
            'expected_impact': np.random.uniform(-10, -25),
            'recovery_time': np.random.randint(6, 18)
        },
        'sector_rotation': {
            'probability': np.random.uniform(15, 35),
            'expected_impact': np.random.uniform(-15, -35),
            'recovery_time': np.random.randint(3, 12)
        },
        'liquidity_crisis': {
            'probability': np.random.uniform(5, 20),
            'expected_impact': np.random.uniform(-20, -40),
            'recovery_time': np.random.randint(6, 24)
        }
    }
    
    return {
        'ticker': ticker,
        'scenario_analysis': scenarios,
        'overall_risk_score': np.random.uniform(30, 80),
        'risk_category': np.random.choice(['Low', 'Medium', 'High']),
        'recommended_hedging': {
            'options_strategy': np.random.choice(['Protective Put', 'Collar', 'None']),
            'futures_hedge': np.random.uniform(0, 0.5),
            'rebalancing_frequency': np.random.choice(['Monthly', 'Quarterly', 'As Needed'])
        }
    }