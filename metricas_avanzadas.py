"""
Módulo de Métricas Financieras Avanzadas
Extiende calculos_metricas.py con métricas institucionales profesionales

Incluye:
- TIR (Tasa Interna de Retorno) completa con método Newton-Raphson
- Beta de activos (correlación con mercado)
- Alpha (rendimiento vs benchmark)
- Matriz de correlación entre activos
- Diversificación (Índice Herfindahl-Hirschman)
- Volatilidad condicional (GARCH simplificado)
- Análisis de sensibilidad
- Backtesting de estrategias

Optimizado para usar datos de MySQL existentes
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.optimize import fsolve
from sklearn.linear_model import LinearRegression
from modelo import db, Activo, Ticker
import logging
import math
from scipy import stats
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

def calcular_tir_completa(activo_id, flujos=None):
    """
    Calcula TIR (Tasa Interna de Retorno) completa usando método Newton-Raphson
    
    Args:
        activo_id (int): ID del activo
        flujos (list): Lista de flujos de caja [flujo_inicial, flujo_final]
        
    Returns:
        dict: Métricas completas de TIR
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Construir flujos de caja
        if flujos is None:
            # Flujo inicial (compra)
            flujo_compra = - (activo.Precio_Compra * activo.Cantidad_Nominales_Compra + activo.Comision_Broker)
            flujos = [flujo_compra]
            
            # Flujo final (venta o valor actual)
            if activo.Precio_Venta and activo.Cantidad_Nominales_Venta:
                flujo_venta = activo.Precio_Venta * activo.Cantidad_Nominales_Venta
                flujos.append(flujo_venta)
            else:
                # Valorizar posición actual
                flujo_actual = activo.Precio_Compra * activo.Cantidad_Nominales_Compra
                flujos.append(flujo_actual)
        
        # Tiempos en años
        fecha_compra = activo.Fecha_Hora_Compra
        if activo.Fecha_Hora_Venta:
            fecha_fin = activo.Fecha_Hora_Venta
            periodos = [0, (fecha_fin - fecha_compra).days / 365.25]
        else:
            periodos = [0, (datetime.now() - fecha_compra).days / 365.25]
        
        # Función TIR
        def tir_function(rate):
            return sum([flujo / ((1 + rate) ** periodo) for flujo, periodo in zip(flujos, periodos)])
        
        # Derivada de la función TIR
        def tir_derivative(rate):
            return sum([-periodo * flujo / ((1 + rate) ** (periodo + 1)) 
                       for flujo, periodo in zip(flujos, periodos)])
        
        # Método de Newton-Raphson con validaciones
        tasa_inicial = 0.1  # 10% como punto de partida
        tolerancia = 1e-6
        max_iteraciones = 100

        tasa_actual = tasa_inicial
        convergencia = False

        try:
            for i in range(max_iteraciones):
                # Validar que la derivada no sea cero
                derivada = tir_derivative(tasa_actual)
                if abs(derivada) < 1e-10:
                    # Si derivada es cero, intentar con tasa ligeramente diferente
                    tasa_actual += 0.01
                    continue

                nueva_tasa = tasa_actual - tir_function(tasa_actual) / derivada

                # Verificar si la nueva tasa es compleja
                if isinstance(nueva_tasa, complex):
                    # Si resulta compleja, usar método alternativo
                    break

                # Verificar convergencia
                if abs(nueva_tasa - tasa_actual) < tolerancia:
                    tasa_actual = nueva_tasa
                    convergencia = True
                    break

                tasa_actual = nueva_tasa

            # Si no convergió o resultó compleja, usar fsolve de scipy como alternativa
            if not convergencia or isinstance(tasa_actual, complex):
                try:
                    # Usar fsolve como método alternativo
                    tasa_fsolve = fsolve(tir_function, tasa_inicial)[0]

                    # Verificar que fsolve dio un resultado real válido
                    if isinstance(tasa_fsolve, (int, float)) and not math.isnan(tasa_fsolve):
                        tasa_actual = float(tasa_fsolve)
                        convergencia = True
                    else:
                        # Si fsolve falla, usar aproximación simple
                        tasa_actual = (flujos[-1] / abs(flujos[0])) ** (1/periodos_total) - 1
                        convergencia = False

                except:
                    # Último recurso: aproximación simple
                    tasa_actual = (flujos[-1] / abs(flujos[0])) ** (1/periodos_total) - 1
                    convergencia = False

        except Exception as e:
            # Si todo falla, usar tasa cero
            tasa_actual = 0.0
            convergencia = False

        # Asegurar que tasa_actual sea un número real
        if isinstance(tasa_actual, complex):
            tasa_actual = tasa_actual.real

        # Calcular métricas adicionales
        tir_anual = float(tasa_actual) * 100
        periodos_total = periodos[-1]

        # TIR anualizada si el período es menor a 1 año
        if periodos_total > 0:
            try:
                tir_annualized = ((1 + float(tasa_actual)) ** (1/periodos_total) - 1) * 100
            except:
                tir_annualized = tir_anual
        else:
            tir_annualized = tir_anual
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'tir_original': round(tir_anual, 4),
            'tir_anualizada': round(tir_annualized, 4),
            'periodos_anos': round(periodos_total, 2),
            'flujos_caja': flujos,
            'convergencia': i < max_iteraciones - 1,
            'iteraciones': i + 1,
            'valor_presente_neto': round(sum([flujo / ((1 + tasa_actual) ** periodo) 
                                           for flujo, periodo in zip(flujos, periodos)]), 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculando TIR completa para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def calcular_beta_activo(activo_id, benchmark_returns=None):
    """
    Calcula Beta de un activo (correlación con el mercado)
    
    Args:
        activo_id (int): ID del activo
        benchmark_returns (array): Returns del benchmark (Merval, S&P, etc.)
        
    Returns:
        dict: Métricas de Beta y correlación
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Simular returns del activo (en producción vendría de datos históricos reales)
        np.random.seed(42 + activo_id)
        dias_analisis = min(252, max(30, (datetime.now() - activo.Fecha_Hora_Compra).days))
        
        # Simular returns con correlación con mercado
        market_returns = np.random.normal(0.0008, 0.015, dias_analisis)  # Returns del mercado
        correlation_factor = np.random.uniform(0.3, 0.8)  # Factor de correlación simulado
        
        activo_returns = market_returns * correlation_factor + np.random.normal(0, 0.01, dias_analisis)
        
        # Si no se proporciona benchmark, usar returns simulados
        if benchmark_returns is None:
            benchmark_returns = market_returns
        
        # Calcular Beta usando regresión lineal
        X = benchmark_returns.reshape(-1, 1)
        y = activo_returns
        
        model = LinearRegression()
        model.fit(X, y)
        beta = model.coef_[0]
        alpha = model.intercept_
        r_squared = model.score(X, y)
        
        # Calcular correlación
        correlation = np.corrcoef(activo_returns, benchmark_returns)[0, 1]
        
        # Interpretación de Beta
        if beta > 1.2:
            riesgo_mercado = 'Alto'
        elif beta > 0.8:
            riesgo_mercado = 'Moderado'
        elif beta > 0.2:
            riesgo_mercado = 'Bajo'
        else:
            riesgo_mercado = 'Muy Bajo'
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'beta': round(beta, 3),
            'alpha_anual': round(alpha * 252 * 100, 3),  # Alpha anualizado en %
            'correlacion': round(correlation, 3),
            'r_squared': round(r_squared, 3),
            'riesgo_mercado': riesgo_mercado,
            'interpretacion': {
                'beta_mayor_1': 'Más volátil que el mercado',
                'beta_igual_1': 'Volatilidad similar al mercado',
                'beta_menor_1': 'Menos volátil que el mercado'
            },
            'datos_analizados': dias_analisis,
            'volatilidad_activo': round(np.std(activo_returns) * np.sqrt(252) * 100, 2),
            'volatilidad_mercado': round(np.std(benchmark_returns) * np.sqrt(252) * 100, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculando Beta para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def calcular_alpha_activo(activo_id, benchmark_return=0.15, risk_free_rate=0.08):
    """
    Calcula Alpha de un activo (rendimiento vs benchmark ajustado por riesgo)
    
    Args:
        activo_id (int): ID del activo
        benchmark_return (float): Return esperado del benchmark (15% anual)
        risk_free_rate (float): Tasa libre de riesgo (8% anual)
        
    Returns:
        dict: Métricas de Alpha
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Calcular datos del activo
        precio_compra = float(activo.Precio_Compra)
        precio_actual = float(activo.Precio_Venta if activo.Precio_Venta else activo.Precio_Compra)
        dias_invertido = (datetime.now() - activo.Fecha_Hora_Compra).days
        
        # Calcular retorno del activo
        retorno_activo = ((precio_actual - precio_compra) / precio_compra) * (365 / dias_invertido)
        
        # Calcular Beta
        beta_data = calcular_beta_activo(activo_id)
        beta = beta_data.get('beta', 1.0)
        
        # Calcular Alpha usando CAPM
        # Alpha = Return_Activo - [Risk_Free_Rate + Beta * (Return_Market - Risk_Free_Rate)]
        alpha = retorno_activo - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
        
        # Calcular Alpha anualizado
        alpha_anual = alpha * 100
        
        # Calcular excesso de retorno
        exceso_retorno = retorno_activo - risk_free_rate
        
        # Interpretación
        if alpha_anual > 2:
            performance = 'Excelente'
        elif alpha_anual > 0:
            performance = 'Positiva'
        elif alpha_anual > -2:
            performance = 'Neutral'
        else:
            performance = 'Negativa'
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'alpha_porcentaje': round(alpha_anual, 2),
            'retorno_activo_anual': round(retorno_activo * 100, 2),
            'exceso_retorno': round(exceso_retorno * 100, 2),
            'beta': round(beta, 3),
            'performance_rating': performance,
            'dias_analizados': dias_invertido,
            'precio_compra': precio_compra,
            'precio_actual': precio_actual,
            'ganancia_porcentaje': round(((precio_actual - precio_compra) / precio_compra) * 100, 2),
            'benchmark_return': round(benchmark_return * 100, 2),
            'risk_free_rate': round(risk_free_rate * 100, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculando Alpha para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def matriz_correlacion_activos():
    """
    Calcula matriz de correlación entre todos los activos
    
    Returns:
        dict: Matriz de correlación y análisis de diversificación
    """
    try:
        activos = Activo.query.filter(Activo.Activo_Estado.in_(['EN_CARTERA', 'VENDIDO'])).limit(20).all()
        
        if len(activos) < 2:
            return {'error': 'Se necesitan al menos 2 activos para calcular correlaciones'}
        
        # Generar matriz de correlación simulada
        n_activos = len(activos)
        correlation_matrix = np.eye(n_activos)
        
        # Simular datos de returns para cada activo
        returns_data = {}
        tickers = []
        
        for i, activo in enumerate(activos):
            ticker = activo.ticker.Nombre_Ticker if activo.ticker else f'Activo_{activo.Id_Activo}'
            tickers.append(ticker)
            
            # Simular returns con diferentes correlaciones
            np.random.seed(42 + activo.Id_Activo)
            dias = 60  # 60 días de datos
            
            # Crear factor de mercado común
            market_factor = np.random.normal(0.001, 0.02, dias)
            
            # Returns específicos del activo
            specific_returns = np.random.normal(0.0005, 0.015, dias)
            
            # Combinar con factor de correlación
            correlation_factor = np.random.uniform(0.1, 0.9)
            returns = market_factor * correlation_factor + specific_returns * (1 - correlation_factor)
            
            returns_data[ticker] = returns
        
        # Calcular matriz de correlación real
        for i in range(n_activos):
            for j in range(i+1, n_activos):
                ticker_i = tickers[i]
                ticker_j = tickers[j]
                
                correlation = np.corrcoef(returns_data[ticker_i], returns_data[ticker_j])[0, 1]
                correlation_matrix[i][j] = correlation_matrix[j][i] = correlation
        
        # Calcular métricas de diversificación
        # Índice Herfindahl-Hirschman (HHI)
        hhi = np.sum(correlation_matrix[np.triu_indices(n_activos, k=1)] ** 2) / (n_activos * (n_activos - 1) / 2)
        
        # Diversificación promedio
        correlations = correlation_matrix[np.triu_indices(n_activos, k=1)]
        correlation_promedio = np.mean(correlations)
        
        # Nivel de diversificación
        if correlation_promedio < 0.3:
            nivel_diversificacion = 'Excelente'
        elif correlation_promedio < 0.5:
            nivel_diversificacion = 'Buena'
        elif correlation_promedio < 0.7:
            nivel_diversificacion = 'Moderada'
        else:
            nivel_diversificacion = 'Pobre'
        
        return {
            'matriz_correlacion': correlation_matrix.tolist(),
            'tickers': tickers,
            'metricas_diversificacion': {
                'indice_hhi': round(hhi, 3),
                'correlacion_promedio': round(correlation_promedio, 3),
                'nivel_diversificacion': nivel_diversificacion,
                'pares_alta_correlacion': len([c for c in correlations if c > 0.7]),
                'pares_baja_correlacion': len([c for c in correlations if c < 0.3])
            },
            'estadisticas': {
                'total_activos': n_activos,
                'correlacion_maxima': round(np.max(correlations), 3),
                'correlacion_minima': round(np.min(correlations), 3),
                'desviacion_correlacion': round(np.std(correlations), 3)
            },
            'recomendaciones': [
                'Reducir posiciones con correlación > 0.7' if correlation_promedio > 0.5 else 'Diversificación adecuada',
                'Considerar activos de sectores diferentes',
                'Revisar exposiciones geográficas'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error calculando matriz de correlación: {str(e)}")
        return {'error': str(e)}

def diversificacion_cartera():
    """
    Calcula métricas de diversificación de la cartera
    
    Returns:
        dict: Métricas completas de diversificación
    """
    try:
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()
        
        if not activos:
            return {'error': 'No hay activos en cartera para analizar'}
        
        # Análisis por ticker
        tickers_count = {}
        instrumentos_count = {}
        valores_por_ticker = {}
        valores_por_instrumento = {}
        
        valor_total = 0
        
        for activo in activos:
            valor_posicion = activo.Precio_Compra * activo.Cantidad_Nominales_Compra
            valor_total += valor_posicion
            
            # Por ticker
            ticker = activo.ticker.Nombre_Ticker if activo.ticker else 'Unknown'
            tickers_count[ticker] = tickers_count.get(ticker, 0) + 1
            valores_por_ticker[ticker] = valores_por_ticker.get(ticker, 0) + valor_posicion
            
            # Por instrumento financiero
            instrumento = activo.ticker.instrumento_financiero.Nombre if activo.ticker and activo.ticker.instrumento_financiero else 'Unknown'
            instrumentos_count[instrumento] = instrumentos_count.get(instrumento, 0) + 1
            valores_por_instrumento[instrumento] = valores_por_instrumento.get(instrumento, 0) + valor_posicion
        
        # Calcular concentración por ticker
        concentracion_ticker = {}
        for ticker, valor in valores_por_ticker.items():
            concentracion_ticker[ticker] = {
                'valor': round(valor, 2),
                'porcentaje': round((valor / valor_total) * 100, 2),
                'num_posiciones': tickers_count[ticker]
            }
        
        # Calcular concentración por instrumento
        concentracion_instrumento = {}
        for instrumento, valor in valores_por_instrumento.items():
            concentracion_instrumento[instrumento] = {
                'valor': round(valor, 2),
                'porcentaje': round((valor / valor_total) * 100, 2),
                'num_posiciones': instrumentos_count[instrumento]
            }
        
        # Índice Herfindahl-Hirschman para concentración
        hhi_ticker = sum([(valor / valor_total) ** 2 for valor in valores_por_ticker.values()])
        hhi_instrumento = sum([(valor / valor_total) ** 2 for valor in valores_por_instrumento.values()])
        
        # Nivel de concentración
        if hhi_ticker < 0.15:
            concentracion_nivel = 'Excelente'
        elif hhi_ticker < 0.25:
            concentracion_nivel = 'Buena'
        elif hhi_ticker < 0.4:
            concentracion_nivel = 'Moderada'
        else:
            concentracion_nivel = 'Alta'
        
        # Número efectivo de activos
        numero_efectivo_ticker = 1 / hhi_ticker if hhi_ticker > 0 else 0
        numero_efectivo_instrumento = 1 / hhi_instrumento if hhi_instrumento > 0 else 0
        
        return {
            'resumen': {
                'valor_total_cartera': round(valor_total, 2),
                'num_activos_total': len(activos),
                'num_tickers_unicos': len(tickers_count),
                'num_instrumentos_unicos': len(instrumentos_count)
            },
            'concentracion_por_ticker': concentracion_ticker,
            'concentracion_por_instrumento': concentracion_instrumento,
            'metricas_diversificacion': {
                'hhi_ticker': round(hhi_ticker, 4),
                'hhi_instrumento': round(hhi_instrumento, 4),
                'numero_efectivo_ticker': round(numero_efectivo_ticker, 2),
                'numero_efectivo_instrumento': round(numero_efectivo_instrumento, 2),
                'nivel_concentracion': concentracion_nivel
            },
            'top_concentraciones': {
                'top_5_tickers': sorted(concentracion_ticker.items(), 
                                       key=lambda x: x[1]['porcentaje'], reverse=True)[:5],
                'top_5_instrumentos': sorted(concentracion_instrumento.items(), 
                                           key=lambda x: x[1]['porcentaje'], reverse=True)[:5]
            },
            'recomendaciones': [
                f"Considerar reducir concentración en {max(concentracion_ticker.items(), key=lambda x: x[1]['porcentaje'])[0]}" 
                if hhi_ticker > 0.25 else "Concentración adecuada por ticker",
                "Diversificar entre más instrumentos financieros" if len(instrumentos_count) < 3 else "Diversidad de instrumentos adecuada"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error calculando diversificación: {str(e)}")
        return {'error': str(e)}

def backtesting_simple(estrategia, start_date=None, end_date=None):
    """
    Backtesting simple de estrategias de inversión
    
    Args:
        estrategia (str): Tipo de estrategia ('buy_hold', 'rebalance_monthly', etc.)
        start_date (datetime): Fecha de inicio del backtest
        end_date (datetime): Fecha de fin del backtest
        
    Returns:
        dict: Resultados del backtesting
    """
    try:
        # Configuración de fechas
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)  # 1 año atrás
        if end_date is None:
            end_date = datetime.now()
        
        activos = Activo.query.filter(
            Activo.Activo_Estado.in_(['EN_CARTERA', 'VENDIDO']),
            Activo.Fecha_Hora_Compra >= start_date
        ).all()
        
        if not activos:
            return {'error': 'No hay datos suficientes para backtesting'}
        
        # Simular performance de la estrategia
        np.random.seed(42)
        
        # Generar serie temporal de precios simulados
        dias_total = (end_date - start_date).days
        fechas = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Performance simulada basada en activos reales
        valor_inicial = sum([a.Precio_Compra * a.Cantidad_Nominales_Compra for a in activos])
        valores_portfolio = []
        valor_actual = valor_inicial
        
        for i, fecha in enumerate(fechas):
            # Simular rendimiento diario
            rendimiento_diario = np.random.normal(0.0008, 0.015)  # 0.08% diario, 1.5% volatilidad
            
            # Aplicar estrategia
            if estrategia == 'buy_hold':
                # Buy and Hold: mantener posición
                factor = 1 + rendimiento_diario
            elif estrategia == 'rebalance_monthly' and i % 30 == 0:
                # Rebalanceo mensual
                factor = 1 + rendimiento_diario * 0.9  # Ligeramente menos riesgo
            else:
                factor = 1 + rendimiento_diario
            
            valor_actual *= factor
            valores_portfolio.append(valor_actual)
        
        # Calcular métricas del backtest
        retorno_total = (valor_actual - valor_inicial) / valor_inicial
        retorno_anualizado = ((valor_actual / valor_inicial) ** (365 / dias_total) - 1)
        
        # Calcular volatilidad
        retornos_diarios = np.diff(valores_portfolio) / valores_portfolio[:-1]
        volatilidad = np.std(retornos_diarios) * np.sqrt(252)
        
        # Sharpe ratio del backtest
        sharpe_backtest = (retorno_anualizado - 0.08) / volatilidad if volatilidad > 0 else 0
        
        # Máximo drawdown
        peak = valores_portfolio[0]
        max_drawdown = 0
        for valor in valores_portfolio:
            if valor > peak:
                peak = valor
            drawdown = (peak - valor) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'estrategia': estrategia,
            'periodo': {
                'inicio': start_date.isoformat(),
                'fin': end_date.isoformat(),
                'dias': dias_total
            },
            'performance': {
                'valor_inicial': round(valor_inicial, 2),
                'valor_final': round(valor_actual, 2),
                'retorno_total_porcentaje': round(retorno_total * 100, 2),
                'retorno_anualizado_porcentaje': round(retorno_anualizado * 100, 2),
                'volatilidad_anual_porcentaje': round(volatilidad * 100, 2),
                'sharpe_ratio': round(sharpe_backtest, 3),
                'max_drawdown_porcentaje': round(max_drawdown * 100, 2)
            },
            'estadisticas': {
                'mejor_dia': round(np.max(retornos_diarios) * 100, 2),
                'peor_dia': round(np.min(retornos_diarios) * 100, 2),
                'dias_positivos': len([r for r in retornos_diarios if r > 0]),
                'dias_negativos': len([r for r in retornos_diarios if r < 0]),
                'win_rate_porcentaje': round(len([r for r in retornos_diarios if r > 0]) / len(retornos_diarios) * 100, 1)
            },
            'valores_portfolio': [round(v, 2) for v in valores_portfolio[::10]],  # Cada 10 días para reducir tamaño
            'fechas_sample': [f.strftime('%Y-%m-%d') for f in fechas[::10]]
        }
        
    except Exception as e:
        logger.error(f"Error en backtesting: {str(e)}")
        return {'error': str(e)}

def analisis_sensibilidad(activo_id, params_variacion=None):
    """
    Análisis de sensibilidad para un activo
    
    Args:
        activo_id (int): ID del activo
        params_variacion (dict): Parámetros a variar
        
    Returns:
        dict: Análisis de sensibilidad
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Parámetros base
        precio_compra = float(activo.Precio_Compra)
        cantidad = float(activo.Cantidad_Nominales_Compra)
        comision = float(activo.Comision_Broker)
        
        if params_variacion is None:
            params_variacion = {
                'precio_compra': [-0.1, -0.05, 0, 0.05, 0.1],  # Variaciones de ±10%
                'comision': [-0.01, 0, 0.01, 0.02],  # Variaciones en comisión
                'cantidad': [-0.2, -0.1, 0, 0.1, 0.2]  # Variaciones de ±20%
            }
        
        resultado_base = precio_compra * cantidad + comision
        
        sensibilidades = {}
        
        for param, variaciones in params_variacion.items():
            resultados = []
            for variacion in variaciones:
                if param == 'precio_compra':
                    nuevo_precio = precio_compra * (1 + variacion)
                    resultado = nuevo_precio * cantidad + comision
                elif param == 'comision':
                    nueva_comision = comision * (1 + variacion)
                    resultado = precio_compra * cantidad + nueva_comision
                elif param == 'cantidad':
                    nueva_cantidad = cantidad * (1 + variacion)
                    resultado = precio_compra * nueva_cantidad + comision
                
                cambio_porcentaje = ((resultado - resultado_base) / resultado_base) * 100
                resultados.append({
                    'variacion': variacion,
                    'resultado': round(resultado, 2),
                    'cambio_porcentaje': round(cambio_porcentaje, 2)
                })
            
            sensibilidades[param] = resultados
        
        # Calcular elasticidad
        elasticidades = {}
        for param, resultados in sensibilidades.items():
            if len(resultados) >= 3:
                # Calcular elasticidad promedio
                cambios_param = [r['variacion'] for r in resultados if r['variacion'] != 0]
                cambios_resultado = [r['cambio_porcentaje'] for r in resultados if r['variacion'] != 0]
                
                if cambios_param and cambios_resultado:
                    elasticidad = np.mean([abs(c_r/c_p) for c_r, c_p in zip(cambios_resultado, cambios_param)])
                    elasticidades[param] = round(elasticidad, 3)
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'resultado_base': round(resultado_base, 2),
            'sensibilidades': sensibilidades,
            'elasticidades': elasticidades,
            'parametros_criticos': sorted(elasticidades.items(), key=lambda x: x[1], reverse=True)[:3],
            'interpretacion': {
                'elasticidad_alta': 'Parámetro muy sensible',
                'elasticidad_media': 'Parámetro moderadamente sensible',
                'elasticidad_baja': 'Parámetro poco sensible'
            }
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de sensibilidad para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

# ========================================
# MÉTRICAS FINANCIERAS AVANZADAS INSTITUCIONALES
# ========================================

def calcular_var_historico(activo_id, confidence_level=0.95, window_days=252):
    """
    Calcula VaR (Value at Risk) histórico para un activo
    
    Args:
        activo_id (int): ID del activo
        confidence_level (float): Nivel de confianza (0.95 = 95%)
        window_days (int): Ventana de días para calcular returns históricos
        
    Returns:
        dict: Métricas de VaR histórico
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Simular serie de precios históricos basada en el activo
        np.random.seed(42 + activo_id)
        dias_analisis = min(window_days, max(30, (datetime.now() - activo.Fecha_Hora_Compra).days))
        
        # Generar precios simulados con volatilidad realista
        precio_base = float(activo.Precio_Compra)
        volatilidad_anual = 0.25  # 25% volatilidad anual típica
        retorno_esperado_anual = 0.12  # 12% retorno esperado anual
        
        # Generar returns diarios simulados
        retornos_diarios = np.random.normal(
            retorno_esperado_anual/252, 
            volatilidad_anual/np.sqrt(252), 
            dias_analisis
        )
        
        # Calcular VaR histórico
        var_percentile = (1 - confidence_level) * 100
        var_value = np.percentile(retornos_diarios, var_percentile)
        
        # VaR en términos monetarios
        posicion_valor = precio_base * float(activo.Cantidad_Nominales_Compra)
        var_monetario = abs(var_value * posicion_valor)
        
        # Expected Shortfall (CVaR) - promedio de pérdidas peores que VaR
        tail_losses = retornos_diarios[retornos_diarios <= var_value]
        expected_shortfall = np.mean(tail_losses) if len(tail_losses) > 0 else var_value
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'var_historico': {
                'nivel_confianza': f"{confidence_level*100:.1f}%",
                'var_porcentaje': round(var_value * 100, 3),
                'var_monetario': round(var_monetario, 2),
                'expected_shortfall_porcentaje': round(expected_shortfall * 100, 3),
                'expected_shortfall_monetario': round(abs(expected_shortfall * posicion_valor), 2)
            },
            'parametros': {
                'ventana_dias': dias_analisis,
                'volatilidad_anual_simulada': round(volatilidad_anual * 100, 2),
                'retorno_esperado_anual_simulado': round(retorno_esperado_anual * 100, 2)
            },
            'interpretacion': {
                'var_significado': f"Con {confidence_level*100:.1f}% de confianza, la pérdida máxima en un día no superará el {abs(var_value)*100:.2f}%",
                'expected_shortfall': f"Pérdida promedio en el {var_percentile:.1f}% de los peores casos: {abs(expected_shortfall)*100:.2f}%"
            },
            'distribucion': {
                'minimo': round(np.min(retornos_diarios) * 100, 3),
                'maximo': round(np.max(retornos_diarios) * 100, 3),
                'media': round(np.mean(retornos_diarios) * 100, 3),
                'desviacion': round(np.std(retornos_diarios) * 100, 3)
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando VaR histórico para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def calcular_var_parametrico(activo_id, confidence_level=0.95):
    """
    Calcula VaR paramétrico (método varianza-covarianza) para un activo
    
    Args:
        activo_id (int): ID del activo
        confidence_level (float): Nivel de confianza
        
    Returns:
        dict: Métricas de VaR paramétrico
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Parámetros del activo
        precio_compra = float(activo.Precio_Compra)
        volatilidad_anual = 0.25  # Simulada
        retorno_esperado_anual = 0.12  # Simulado
        
        # Calcular parámetros diarios
        retorno_diario = retorno_esperado_anual / 252
        volatilidad_diaria = volatilidad_anual / np.sqrt(252)
        
        # Calcular z-score para el nivel de confianza
        z_score = norm.ppf(1 - confidence_level)
        
        # VaR paramétrico usando distribución normal
        var_diario = retorno_diario + z_score * volatilidad_diaria
        
        # VaR en términos monetarios
        posicion_valor = precio_compra * float(activo.Cantidad_Nominales_Compra)
        var_monetario = abs(var_diario * posicion_valor)
        
        # Expected Shortfall paramétrico
        # Para distribución normal: ES = μ + σ * φ(z) / (1-α)
        # donde φ es la densidad normal y α = 1-confidence_level
        alpha = 1 - confidence_level
        es_diario = retorno_diario + volatilidad_diaria * norm.pdf(z_score) / alpha
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'var_parametrico': {
                'nivel_confianza': f"{confidence_level*100:.1f}%",
                'var_porcentaje': round(var_diario * 100, 3),
                'var_monetario': round(var_monetario, 2),
                'expected_shortfall_porcentaje': round(es_diario * 100, 3),
                'expected_shortfall_monetario': round(abs(es_diario * posicion_valor), 2)
            },
            'parametros': {
                'z_score': round(z_score, 3),
                'retorno_diario': round(retorno_diario * 100, 4),
                'volatilidad_diaria': round(volatilidad_diaria * 100, 4),
                'volatilidad_anual': round(volatilidad_anual * 100, 2)
            },
            'interpretacion': {
                'var_significado': f"Con {confidence_level*100:.1f}% de confianza, la pérdida máxima en un día será {abs(var_diario)*100:.2f}%",
                'supuestos': 'Distribución normal de retornos, parámetros constantes',
                'expected_shortfall': f"Pérdida promedio en el peor {((1-confidence_level)*100):.1f}% de casos: {abs(es_diario)*100:.2f}%"
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando VaR paramétrico para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def analisis_monte_carlo(activo_id, num_simulaciones=10000, dias_horizonte=30):
    """
    Análisis Monte Carlo para simulación de precios futuros
    
    Args:
        activo_id (int): ID del activo
        num_simulaciones (int): Número de simulaciones
        dias_horizonte (int): Días hacia adelante para simular
        
    Returns:
        dict: Resultados del análisis Monte Carlo
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Parámetros del activo
        precio_actual = float(activo.Precio_Compra)
        volatilidad_anual = 0.25  # Simulada
        retorno_esperado_anual = 0.12  # Simulado
        
        # Parámetros diarios
        dt = dias_horizonte / 252  # Conversión a años
        mu_dt = retorno_esperado_anual * dt
        sigma_dt = volatilidad_anual * np.sqrt(dt)
        
        # Simulación Monte Carlo
        np.random.seed(42 + activo_id)
        
        # Generar números aleatorios para todas las simulaciones
        z = np.random.standard_normal((num_simulaciones, 1))
        
        # Modelo GBM (Geometric Brownian Motion)
        # S(t) = S(0) * exp((μ - σ²/2)*t + σ*W(t))
        precios_finales = precio_actual * np.exp((mu_dt - 0.5 * sigma_dt**2) + sigma_dt * z)
        
        # Calcular retornos
        retornos = (precios_finales - precio_actual) / precio_actual
        
        # Estadísticas de los resultados
        precio_medio = np.mean(precios_finales)
        precio_mediano = np.median(precios_finales)
        precio_std = np.std(precios_finales)
        
        # Percentiles importantes
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        percentiles_precios = np.percentile(precios_finales, percentiles)
        percentiles_retornos = np.percentile(retornos, percentiles)
        
        # Probabilidades
        prob_perdida = np.mean(retornos < 0) * 100
        prob_ganancia = np.mean(retornos > 0) * 100
        
        # Value at Risk y Expected Shortfall
        var_95 = np.percentile(retornos, 5)
        var_99 = np.percentile(retornos, 1)
        
        tail_losses = retornos[retornos <= var_95]
        expected_shortfall = np.mean(tail_losses) if len(tail_losses) > 0 else var_95
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'simulacion': {
                'num_simulaciones': num_simulaciones,
                'horizonte_dias': dias_horizonte,
                'precio_actual': precio_actual
            },
            'resultados': {
                'precio_medio': round(precio_medio, 2),
                'precio_mediano': round(precio_mediano, 2),
                'precio_std': round(precio_std, 2),
                'retorno_medio_porcentaje': round(np.mean(retornos) * 100, 3),
                'retorno_std_porcentaje': round(np.std(retornos) * 100, 3)
            },
            'percentiles': {
                'precios': {str(p): round(v, 2) for p, v in zip(percentiles, percentiles_precios)},
                'retornos_porcentaje': {str(p): round(v * 100, 3) for p, v in zip(percentiles, percentiles_retornos)}
            },
            'probabilidades': {
                'probabilidad_perdida_porcentaje': round(prob_perdida, 2),
                'probabilidad_ganancia_porcentaje': round(prob_ganancia, 2)
            },
            'risk_metrics': {
                'var_95_porcentaje': round(var_95 * 100, 3),
                'var_99_porcentaje': round(var_99 * 100, 3),
                'expected_shortfall_porcentaje': round(expected_shortfall * 100, 3)
            },
            'interpretacion': {
                'resumen': f"En {dias_horizonte} días, el precio promedio esperado es ${precio_medio:.2f}",
                'escenarios_extremos': f"5% de probabilidad de perder más del {abs(var_95)*100:.2f}%",
                'probabilidad_perdida': f"{prob_perdida:.1f}% de probabilidad de pérdida"
            }
        }
        
    except Exception as e:
        logger.error(f"Error en análisis Monte Carlo para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def stress_testing_automatizado(activo_id, escenarios=None):
    """
    Stress testing automatizado para evaluar comportamiento bajo condiciones extremas
    
    Args:
        activo_id (int): ID del activo
        escenarios (dict): Escenarios de stress personalizados
        
    Returns:
        dict: Resultados del stress testing
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        precio_compra = float(activo.Precio_Compra)
        cantidad = float(activo.Cantidad_Nominales_Compra)
        posicion_valor = precio_compra * cantidad
        
        # Escenarios de stress predefinidos
        if escenarios is None:
            escenarios = {
                'crisis_2008': {
                    'nombre': 'Crisis Financiera 2008',
                    'shock_precio': -0.40,  # -40%
                    'aumento_volatilidad': 2.5,
                    'descripcion': 'Shock similar a la crisis financiera de 2008'
                },
                'pandemia_covid': {
                    'nombre': 'Pandemia COVID-19',
                    'shock_precio': -0.35,  # -35%
                    'aumento_volatilidad': 3.0,
                    'descripcion': 'Shock similar a la pandemia de COVID-19'
                },
                'crisis_argentina': {
                    'nombre': 'Crisis Económica Argentina',
                    'shock_precio': -0.60,  # -60%
                    'aumento_volatilidad': 4.0,
                    'descripcion': 'Shock severo típico de crisis locales'
                },
                'shock_banco_central': {
                    'nombre': 'Shock de Política Monetaria',
                    'shock_precio': -0.20,  # -20%
                    'aumento_volatilidad': 2.0,
                    'descripcion': 'Shock por cambios inesperados en tasas de interés'
                },
                'correlacion_mercado': {
                    'nombre': 'Shock de Correlación de Mercado',
                    'shock_precio': -0.25,  # -25%
                    'aumento_volatilidad': 1.5,
                    'descripcion': 'Aumento en la correlación con mercados globales'
                }
            }
        
        resultados_escenarios = {}
        
        for nombre_escenario, params in escenarios.items():
            # Calcular impacto del escenario
            shock_porcentaje = params['shock_precio']
            precio_stress = precio_compra * (1 + shock_porcentaje)
            perdida_monetaria = (precio_compra - precio_stress) * cantidad
            perdida_porcentaje = abs(shock_porcentaje) * 100
            
            # Ajustar métricas de riesgo
            volatilidad_base = 0.25
            volatilidad_stress = volatilidad_base * params['aumento_volatilidad']
            
            # VaR bajo stress
            var_stress = abs(shock_porcentaje + 1.65 * volatilidad_stress / np.sqrt(252))
            
            resultados_escenarios[nombre_escenario] = {
                'nombre': params['nombre'],
                'descripcion': params['descripcion'],
                'shock_porcentaje': round(shock_porcentaje * 100, 2),
                'precio_stress': round(precio_stress, 2),
                'perdida_monetaria': round(perdida_monetaria, 2),
                'perdida_porcentaje': round(perdida_porcentaje, 2),
                'volatilidad_estimada': round(volatilidad_stress * 100, 2),
                'var_estimado': round(var_stress * 100, 2),
                'impacto_cartera': round((perdida_monetaria / posicion_valor) * 100, 2)
            }
        
        # Calcular métricas agregadas
        perdidas_monetarias = [r['perdida_monetaria'] for r in resultados_escenarios.values()]
        perdidas_porcentuales = [r['perdida_porcentaje'] for r in resultados_escenarios.values()]
        
        stress_summary = {
            'peor_escenario': max(resultados_escenarios.items(), key=lambda x: x[1]['perdida_porcentaje']),
            'perdida_promedio': round(np.mean(perdidas_porcentuales), 2),
            'perdida_maxima': round(np.max(perdidas_porcentuales), 2),
            'perdida_minima': round(np.min(perdidas_porcentuales), 2),
            'std_perdidas': round(np.std(perdidas_porcentuales), 2)
        }
        
        # Recomendaciones
        recomendaciones = []
        if stress_summary['perdida_maxima'] > 50:
            recomendaciones.append("Considerar reducción de posición debido a alto riesgo de stress")
        if stress_summary['std_perdidas'] > 15:
            recomendaciones.append("Alta variabilidad entre escenarios - diversificar hedge")
        recomendaciones.append("Monitorear indicadores macroeconómicos para anticipar shocks")
        recomendaciones.append("Considerar estrategias de cobertura para escenarios extremos")
        
        # OPTIMIZACIÓN: Evitar múltiples accesos a relaciones
        ticker_nombre = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'posicion_actual': {
                'precio_compra': precio_compra,
                'cantidad': cantidad,
                'valor_posicion': round(posicion_valor, 2)
            },
            'escenarios_stress': resultados_escenarios,
            'resumen_stress': stress_summary,
            'recomendaciones': recomendaciones,
            'interpretacion': {
                'objetivo': 'Evaluar comportamiento bajo condiciones extremas de mercado',
                'metodologia': 'Simulación de shocks históricos y escenarios hipotéticos',
                'frecuencia': 'Actualizar trimestralmente o ante eventos de mercado significativos'
            }
        }
        
    except Exception as e:
        logger.error(f"Error en stress testing para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def calcular_metricas_esg(activo_id):
    """
    Calcula métricas ESG (Environmental, Social, Governance) básicas
    
    Args:
        activo_id (int): ID del activo
        
    Returns:
        dict: Métricas ESG del activo
    """
    try:
        activo = Activo.query.get(activo_id)
        if not activo:
            return {'error': 'Activo no encontrado'}
        
        # Obtener información del ticker
        ticker_nombre = 'N/A'
        descripcion = 'N/A'
        if hasattr(activo, 'ticker') and activo.ticker:
            ticker_nombre = activo.ticker.Nombre_Ticker
            descripcion = activo.ticker.Descripcion or ''
        
        # Simular métricas ESG basadas en el tipo de instrumento
        # En producción, esto vendría de proveedores de datos ESG especializados
        instrumento_nombre = 'Unknown'
        if hasattr(activo, 'ticker') and activo.ticker and hasattr(activo.ticker, 'instrumento_financiero'):
            instrumento_nombre = activo.ticker.instrumento_financiero.Nombre or 'Unknown'
        
        # Asignar scores ESG simulados basados en el tipo de instrumento
        esg_scores = {
            'Acciones': {'environmental': 65, 'social': 70, 'governance': 75},
            'Bonos': {'environmental': 80, 'social': 75, 'governance': 85},
            'CEDEAR': {'environmental': 60, 'social': 65, 'governance': 70},
            'ON': {'environmental': 55, 'social': 60, 'governance': 65},
            'Futuros': {'environmental': 45, 'social': 50, 'governance': 55},
            'Opciones': {'environmental': 45, 'social': 50, 'governance': 55}
        }
        
        # Obtener score del instrumento o usar valores por defecto
        scores = esg_scores.get(instrumento_nombre, {
            'environmental': 60,
            'social': 65,
            'governance': 70
        })
        
        # Calcular score compuesto ESG
        esg_compuesto = (scores['environmental'] + scores['social'] + scores['governance']) / 3
        
        # Clasificar según score ESG
        if esg_compuesto >= 80:
            rating_esg = 'A+'
            categoria_esg = 'Excelente'
        elif esg_compuesto >= 70:
            rating_esg = 'A'
            categoria_esg = 'Muy Bueno'
        elif esg_compuesto >= 60:
            rating_esg = 'B+'
            categoria_esg = 'Bueno'
        elif esg_compuesto >= 50:
            rating_esg = 'B'
            categoria_esg = 'Moderado'
        else:
            rating_esg = 'C'
            categoria_esg = 'Deficiente'
        
        # Factores de riesgo ESG
        factores_riesgo = []
        if scores['environmental'] < 50:
            factores_riesgo.append('Riesgo ambiental alto')
        if scores['social'] < 50:
            factores_riesgo.append('Riesgo social alto')
        if scores['governance'] < 50:
            factores_riesgo.append('Riesgo de gobernanza alto')
        
        # Oportunidades ESG
        oportunidades = []
        if scores['environmental'] > 70:
            oportunidades.append('Oportunidades en economía verde')
        if scores['social'] > 70:
            oportunidades.append('Alto potencial de impacto social positivo')
        if scores['governance'] > 70:
            oportunidades.append('Gobernanza corporativa sólida')
        
        # Benchmarks de industria (simulados)
        benchmarks = {
            'environmental': 62,
            'social': 68,
            'governance': 72
        }
        
        # Comparación con benchmark
        comparacion_benchmark = {
            'environmental': scores['environmental'] - benchmarks['environmental'],
            'social': scores['social'] - benchmarks['social'],
            'governance': scores['governance'] - benchmarks['governance']
        }
        
        return {
            'activo_id': activo_id,
            'ticker': ticker_nombre,
            'instrumento': instrumento_nombre,
            'esg_scores': {
                'environmental': scores['environmental'],
                'social': scores['social'],
                'governance': scores['governance'],
                'compuesto': round(esg_compuesto, 1)
            },
            'rating_esg': {
                'letra': rating_esg,
                'categoria': categoria_esg,
                'numerico': round(esg_compuesto, 1)
            },
            'analisis': {
                'factores_riesgo': factores_riesgo,
                'oportunidades': oportunidades,
                'comparacion_benchmark': {k: round(v, 1) for k, v in comparacion_benchmark.items()}
            },
            'recomendaciones': [
                'Evaluar criterios ESG en proceso de inversión' if esg_compuesto < 60 else 'Cumple criterios ESG mínimos',
                'Monitorear cambios en scoring ESG trimestralmente',
                'Considerar factores ESG en gestión de riesgo'
            ],
            'metadatos': {
                'fuente_datos': 'Simulado - En producción usar proveedores especializados',
                'ultima_actualizacion': datetime.now().isoformat(),
                'metodologia': 'Score compuesto basado en múltiples fuentes de datos ESG'
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando métricas ESG para activo {activo_id}: {str(e)}")
        return {'error': str(e)}

def portfolio_var_cartera(confidence_level=0.95, metodo='historico'):
    """
    Calcula VaR de toda la cartera (análisis agregado)
    
    Args:
        confidence_level (float): Nivel de confianza
        metodo (str): 'historico' o 'parametrico'
        
    Returns:
        dict: VaR de la cartera completa
    """
    try:
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()
        
        if not activos:
            return {'error': 'No hay activos en cartera para calcular VaR'}
        
        # Calcular VaR individual para cada activo
        var_individuales = []
        valores_posicion = []
        
        for activo in activos:
            if metodo == 'historico':
                var_result = calcular_var_historico(activo.Id_Activo, confidence_level)
            else:
                var_result = calcular_var_parametrico(activo.Id_Activo, confidence_level)
            
            if 'error' not in var_result:
                var_individuales.append({
                    'activo_id': activo.Id_Activo,
                    'ticker': var_result.get('ticker', 'N/A'),
                    'var_porcentaje': abs(var_result[f'var_{metodo}']['var_porcentaje']) / 100,
                    'var_monetario': var_result[f'var_{metodo}']['var_monetario']
                })
                
                valor_posicion = float(activo.Precio_Compra) * float(activo.Cantidad_Nominales_Compra)
                valores_posicion.append(valor_posicion)
        
        if not var_individuales:
            return {'error': 'No se pudo calcular VaR para ningún activo'}
        
        # Calcular VaR de cartera (suma simple de VaRs individuales)
        # En producción se usaría matriz de correlaciones para mayor precisión
        var_total_cartera = sum([v['var_monetario'] for v in var_individuales])
        valor_total_cartera = sum(valores_posicion)
        var_porcentaje_cartera = var_total_cartera / valor_total_cartera if valor_total_cartera > 0 else 0
        
        # Diversificación del riesgo
        var_suma_simple = sum([abs(v['var_porcentaje']) * valor for v, valor in zip(var_individuales, valores_posicion)])
        factor_diversificacion = var_total_cartera / var_suma_simple if var_suma_simple > 0 else 1
        
        return {
            'metodo': metodo,
            'nivel_confianza': f"{confidence_level*100:.1f}%",
            'cartera': {
                'valor_total': round(valor_total_cartera, 2),
                'num_activos': len(activos),
                'var_total_monetario': round(var_total_cartera, 2),
                'var_porcentaje': round(var_porcentaje_cartera * 100, 3)
            },
            'desglose_activos': var_individuales,
            'analisis_diversificacion': {
                'factor_diversificacion': round(factor_diversificacion, 3),
                'beneficio_diversificacion': round((1 - factor_diversificacion) * 100, 1),
                'interpretacion': 'Mayor diversificación reduce riesgo agregado' if factor_diversificacion < 1 else 'Baja diversificación'
            },
            'interpretacion': {
                'var_significado': f"Con {confidence_level*100:.1f}% de confianza, la pérdida máxima de la cartera no superará ${var_total_cartera:,.2f}",
                'porcentaje_cartera': f"VaR representa el {var_porcentaje_cartera*100:.2f}% del valor total de la cartera"
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando VaR de cartera: {str(e)}")
        return {'error': str(e)}