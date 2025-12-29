# 📊 IMPLEMENTACIÓN DE MÉTRICAS FINANCIERAS AVANZADAS

## 🎯 ENFOQUE EN INFORMES Y ANÁLISIS

Este documento detalla la implementación específica de las métricas financieras más importantes para la toma de decisiones de inversión en la cartera financiera.

---

## 📈 **MÉTRICAS DE RENTABILIDAD**

### 1. ROI (Return on Investment)

```python
# calculos_financieros.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from modelo import Activo, db

def calcular_roi_activo(activo_id):
    """
    Calcula el ROI de un activo específico
    ROI = (Valor Actual - Inversión Inicial) / Inversión Inicial * 100
    """
    activo = Activo.query.get(activo_id)

    if not activo:
        return None

    # Precio actual (último precio de venta o precio de compra si no se vendió)
    precio_actual = activo.Precio_Venta if activo.Precio_Venta else activo.Precio_Compra
    precio_inicial = activo.Precio_Compra

    # Cantidad actual (considerando ventas parciales)
    cantidad_inicial = activo.Cantidad_Nominales_Compra
    cantidad_actual = activo.Cantidad_Nominales_Venta if activo.Cantidad_Nominales_Venta else cantidad_inicial

    # Inversión inicial total
    inversion_inicial = precio_inicial * cantidad_inicial

    # Valor actual de la posición
    valor_actual = precio_actual * cantidad_actual

    # ROI
    roi = ((valor_actual - inversion_inicial) / inversion_inicial) * 100

    return {
        'roi_porcentaje': round(roi, 2),
        'ganancia_absoluta': round(valor_actual - inversion_inicial, 2),
        'valor_actual': round(valor_actual, 2),
        'inversion_inicial': round(inversion_inicial, 2),
        'dias_invertidos': (datetime.now() - activo.Fecha_Hora_Compra).days
    }

def calcular_roi_cartera_completa():
    """
    Calcula el ROI de la cartera completa
    """
    activos = Activo.query.filter(Activo.Activo_Estado.in_(['EN_CARTERA', 'VENDIDO'])).all()

    inversion_total = 0
    valor_actual_total = 0
    ganancia_total = 0

    for activo in activos:
        precio_actual = activo.Precio_Venta if activo.Precio_Venta else activo.Precio_Compra
        cantidad_actual = activo.Cantidad_Nominales_Venta if activo.Cantidad_Nominales_Venta else activo.Cantidad_Nominales_Compra

        inversion_total += activo.Precio_Compra * activo.Cantidad_Nominales_Compra
        valor_actual_total += precio_actual * cantidad_actual

    ganancia_total = valor_actual_total - inversion_total
    roi_portfolio = (ganancia_total / inversion_total) * 100 if inversion_total > 0 else 0

    return {
        'roi_portfolio': round(roi_portfolio, 2),
        'ganancia_total': round(ganancia_total, 2),
        'valor_cartera': round(valor_actual_total, 2),
        'inversion_total': round(inversion_total, 2),
        'num_activos': len(activos)
    }
```

### 2. TIR (Tasa Interna de Retorno)

```python
def calcular_tir_activo(activo_id):
    """
    Calcula la TIR de un activo considerando flujos de caja
    """
    activo = Activo.query.get(activo_id)

    # Flujos de caja
    flujos = []

    # Flujo inicial (compra) - negativo
    flujo_inicial = - (activo.Precio_Compra * activo.Cantidad_Nominales_Compra + activo.Comision_Broker)
    flujos.append(flujo_inicial)

    # Si hay venta, agregar flujo positivo
    if activo.Precio_Venta and activo.Cantidad_Nominales_Venta:
        flujo_venta = (activo.Precio_Venta * activo.Cantidad_Nominales_Venta)
        flujos.append(flujo_venta)
    else:
        # Valorizar posición actual
        precio_actual = activo.Precio_Compra  # Simplificado
        flujo_actual = precio_actual * activo.Cantidad_Nominales_Compra
        flujos.append(flujo_actual)

    # Tiempos (en años)
    fecha_compra = activo.Fecha_Hora_Compra
    fecha_actual = datetime.now()

    if activo.Fecha_Hora_Venta:
        fecha_final = activo.Fecha_Hora_Venta
        periodos = [0, (fecha_final - fecha_compra).days / 365.25]
    else:
        periodos = [0, (fecha_actual - fecha_compra).days / 365.25]

    # Calcular TIR usando método de Newton-Raphson
    def tir_function(rate):
        npv = sum([flujo / ((1 + rate) ** periodo) for flujo, periodo in zip(flujos, periodos)])
        return npv

    def tir_derivative(rate):
        d_npv = sum([-periodo * flujo / ((1 + rate) ** (periodo + 1))
                     for flujo, periodo in zip(flujos, periodos)])
        return d_npv

    # Iteración de Newton-Raphson
    rate = 0.1  # Estimación inicial 10%
    for _ in range(100):  # Máximo 100 iteraciones
        new_rate = rate - tir_function(rate) / tir_derivative(rate)
        if abs(new_rate - rate) < 1e-6:
            break
        rate = new_rate

    return {
        'tir_anual': round(rate * 100, 2),
        'flujos_caja': flujos,
        'dias_totales': (fecha_actual - fecha_compra).days
    }
```

### 3. Sharpe Ratio

```python
def calcular_sharpe_ratio(activo_id, benchmark_return=0.08):
    """
    Calcula el Sharpe Ratio del activo
    Sharpe Ratio = (Return del Activo - Risk Free Rate) / Volatilidad del Activo
    """
    activo = Activo.query.get(activo_id)

    # Obtener histórico de precios (simulado - en producción vendría de API)
    precios_historicos = obtener_precios_historicos(activo.Id_Ticker)

    if len(precios_historicos) < 30:  # Mínimo 30 días
        return {'error': 'Datos históricos insuficientes'}

    # Calcular returns diarios
    returns = np.diff(precios_historicos) / precios_historicos[:-1]

    # Return promedio anualizado
    return_promedio = np.mean(returns) * 252  # 252 días de trading por año

    # Volatilidad anualizada
    volatilidad = np.std(returns) * np.sqrt(252)

    # Risk free rate (8% anual = 0.08)
    risk_free_rate = benchmark_return

    # Sharpe Ratio
    sharpe_ratio = (return_promedio - risk_free_rate) / volatilidad if volatilidad > 0 else 0

    return {
        'sharpe_ratio': round(sharpe_ratio, 3),
        'return_anual': round(return_promedio * 100, 2),
        'volatilidad_anual': round(volatilidad * 100, 2),
        'excess_return': round((return_promedio - risk_free_rate) * 100, 2),
        'risk_free_rate': round(risk_free_rate * 100, 2)
    }

def obtener_precios_historicos(ticker_id):
    """
    Simula obtención de precios históricos
    En producción, esto vendría de una API financiera
    """
    # Generar datos simulados para ejemplo
    np.random.seed(42)
    precios_base = 100
    returns = np.random.normal(0.001, 0.02, 30)  # 30 días de returns
    precios = [precios_base]

    for ret in returns:
        precios.append(precios[-1] * (1 + ret))

    return np.array(precios[1:])  # Excluir precio inicial
```

---

## ⚠️ **MÉTRICAS DE RIESGO**

### 1. VaR (Value at Risk)

```python
def calcular_var_cartera(confianza=0.95, horizonte=1):
    """
    Calcula el VaR de la cartera
    VaR = Pérdida máxima esperada con X% de confianza en Y días
    """
    activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()

    # Matriz de correlación y volatilidades
    num_activos = len(activos)
    matriz_correlacion = np.eye(num_activos)
    volatilidades = []
    valores_actuales = []

    for i, activo in enumerate(activos):
        # Calcular volatilidad del activo
        precios_historicos = obtener_precios_historicos(activo.Id_Ticker)
        returns = np.diff(precios_historicos) / precios_historicos[:-1]
        volatilidad = np.std(returns) * np.sqrt(252)  # Anualizada

        volatilidades.append(volatilidad)
        valores_actuales.append(activo.Precio_Compra * activo.Cantidad_Nominales_Compra)

        # Matriz de correlación simplificada (en producción sería más compleja)
        for j in range(i+1, num_activos):
            correlacion = np.random.uniform(0.1, 0.8)  # Simulado
            matriz_correlacion[i][j] = matriz_correlacion[j][i] = correlacion

    # Construir matriz de covarianza
    volatilidades = np.array(volatilidades)
    valores_actuales = np.array(valores_actuales)
    matriz_covarianza = np.outer(volatilidades, volatilidades) * matriz_correlacion

    # Portfolio value
    valor_portfolio = np.sum(valores_actuales)

    # Pesos de la cartera
    pesos = valores_actuales / valor_portfolio

    # VaR usando método paramétrico (normal)
    z_score = norm.ppf(1 - confianza)  # 1.645 para 95% confianza

    # VaR del portfolio
    var_portfolio = z_score * np.sqrt(np.dot(pesos.T, np.dot(matriz_covarianza, pesos))) * valor_portfolio

    return {
        'var_confianza': f"{int(confianza*100)}%",
        'var_horizonte_dias': horizonte,
        'var_perdida_maxima': round(var_portfolio, 2),
        'var_porcentaje': round((var_portfolio / valor_portfolio) * 100, 2),
        'valor_cartera': round(valor_portfolio, 2),
        'metodo': 'Paramétrico (Distribución Normal)'
    }
```

### 2. Maximum Drawdown

```python
def calcular_maximum_drawdown(activo_id):
    """
    Calcula el Maximum Drawdown de un activo
    """
    precios_historicos = obtener_precios_historicos(activo.Id_Ticker)

    # Calcular peak y drawdown
    peak = precios_historicos[0]
    max_drawdown = 0
    max_drawdown_period = None

    for i, precio in enumerate(precios_historicos):
        if precio > peak:
            peak = precio

        drawdown = (peak - precio) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_period = (peak, precio)

    return {
        'max_drawdown_porcentaje': round(max_drawdown * 100, 2),
        'precio_peak': round(max_drawdown_period[0], 2),
        'precio_trough': round(max_drawdown_period[1], 2),
        'dias_en_recuperacion': calcular_dias_recuperacion(precios_historicos),
        'volatilidad_historica': round(np.std(np.diff(precios_historicos)/precios_historicos[:-1]) * 100, 2)
    }

def calcular_dias_recuperacion(precios):
    """
    Calcula los días promedio de recuperación después de caídas
    """
    returns = np.diff(precios) / precios[:-1]

    # Identificar caídas > 5%
    drawdowns = []
    current_peak = precios[0]
    peak_idx = 0

    for i, precio in enumerate(precios):
        if precio > current_peak:
            if i - peak_idx > 1:  # Solo si hubo al menos 1 día de caída
                drawdowns.append(i - peak_idx)
            current_peak = precio
            peak_idx = i

    return round(np.mean(drawdowns), 1) if drawdowns else 0
```

---

## 📊 **DASHBOARD EJECUTIVO**

### Template del Dashboard

```html
<!-- templates/dashboard_ejecutivo.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Ejecutivo - Cartera Financiera</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body class="bg-light">
    <div class="container-fluid mt-4">
        <!-- Header con KPIs principales -->
        <div class="row mb-4">
            <div class="col-12">
                <h1 class="text-center mb-4">Dashboard Ejecutivo</h1>
                <div class="row">
                    <!-- ROI Total -->
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5>ROI Cartera</h5>
                                <h2 id="roi-cartera">{{ roi_cartera }}%</h2>
                                <small>Ganancia Total: ${{ ganancia_total }}</small>
                            </div>
                        </div>
                    </div>

                    <!-- Sharpe Ratio -->
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h5>Sharpe Ratio</h5>
                                <h2 id="sharpe-ratio">{{ sharpe_ratio }}</h2>
                                <small>Risk-Adjusted Return</small>
                            </div>
                        </div>
                    </div>

                    <!-- VaR -->
                    <div class="col-md-3">
                        <div class="card bg-warning text-dark">
                            <div class="card-body">
                                <h5>VaR (95%)</h5>
                                <h2 id="var-95">${{ var_95 }}</h2>
                                <small>Pérdida máxima esperada</small>
                            </div>
                        </div>
                    </div>

                    <!-- Máximo Drawdown -->
                    <div class="col-md-3">
                        <div class="card bg-danger text-white">
                            <div class="card-body">
                                <h5>Max Drawdown</h5>
                                <h2 id="max-drawdown">{{ max_drawdown }}%</h5>
                                <small>Mayor pérdida histórica</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gráficos principales -->
        <div class="row mb-4">
            <!-- Performance Chart -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Performance de la Cartera</h5>
                    </div>
                    <div class="card-body">
                        <div id="performance-chart"></div>
                    </div>
                </div>
            </div>

            <!-- Asset Allocation -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Distribución de Activos</h5>
                    </div>
                    <div class="card-body">
                        <div id="allocation-pie"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Análisis de riesgo y métricas avanzadas -->
        <div class="row mb-4">
            <!-- Risk-Return Scatter -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Riesgo vs Rendimiento</h5>
                    </div>
                    <div class="card-body">
                        <div id="risk-return-scatter"></div>
                    </div>
                </div>
            </div>

            <!-- Correlation Matrix -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Matriz de Correlación</h5>
                    </div>
                    <div class="card-body">
                        <div id="correlation-heatmap"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabla de performance por activo -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Performance por Activo</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped" id="performance-table">
                                <thead>
                                    <tr>
                                        <th>Ticker</th>
                                        <th>ROI %</th>
                                        <th>Sharpe Ratio</th>
                                        <th>VaR %</th>
                                        <th>Max DD %</th>
                                        <th>Valor</th>
                                        <th>Peso %</th>
                                    </tr>
                                </thead>
                                <tbody id="performance-tbody">
                                    <!-- Se llena dinámicamente -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Cargar datos del dashboard
        async function cargarDashboard() {
            try {
                // KPIs principales
                const kpis = await fetch('/api/dashboard/kpis').then(r => r.json());
                document.getElementById('roi-cartera').textContent = kpis.roi_cartera + '%';
                document.getElementById('sharpe-ratio').textContent = kpis.sharpe_ratio;
                document.getElementById('var-95').textContent = '$' + kpis.var_95;
                document.getElementById('max-drawdown').textContent = kpis.max_drawdown + '%';

                // Gráfico de performance
                const performance = await fetch('/api/dashboard/performance').then(r => r.json());
                Plotly.newPlot('performance-chart', [{
                    x: performance.fechas,
                    y: performance.valores,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Cartera'
                }], {
                    title: 'Evolución del Valor de la Cartera',
                    xaxis: { title: 'Fecha' },
                    yaxis: { title: 'Valor ($)' }
                });

                // Gráfico de allocation
                const allocation = await fetch('/api/dashboard/allocation').then(r => r.json());
                Plotly.newPlot('allocation-pie', [{
                    labels: allocation.labels,
                    values: allocation.values,
                    type: 'pie'
                }]);

                // Risk-Return scatter
                const riskReturn = await fetch('/api/dashboard/risk-return').then(r => r.json());
                Plotly.newPlot('risk-return-scatter', [{
                    x: riskReturn.risk,
                    y: riskReturn.return,
                    mode: 'markers',
                    type: 'scatter',
                    text: riskReturn.tickers,
                    marker: { size: 10 }
                }], {
                    title: 'Riesgo vs Rendimiento por Activo',
                    xaxis: { title: 'Riesgo (Volatilidad %)' },
                    yaxis: { title: 'Rendimiento (%)' }
                });

                // Correlation heatmap
                const correlation = await fetch('/api/dashboard/correlation').then(r => r.json());
                Plotly.newPlot('correlation-heatmap', [{
                    z: correlation.matrix,
                    x: correlation.labels,
                    y: correlation.labels,
                    type: 'heatmap',
                    colorscale: 'RdBu'
                }]);

                // Tabla de performance
                const tableData = await fetch('/api/dashboard/performance-table').then(r => r.json());
                const tbody = document.getElementById('performance-tbody');
                tbody.innerHTML = tableData.map(activo => `
                    <tr>
                        <td>${activo.ticker}</td>
                        <td class="${activo.roi >= 0 ? 'text-success' : 'text-danger'}">${activo.roi}%</td>
                        <td>${activo.sharpe_ratio}</td>
                        <td>${activo.var}%</td>
                        <td>${activo.max_drawdown}%</td>
                        <td>$${activo.valor}</td>
                        <td>${activo.peso}%</td>
                    </tr>
                `).join('');

            } catch (error) {
                console.error('Error cargando dashboard:', error);
            }
        }

        // Cargar dashboard al cargar la página
        document.addEventListener('DOMContentLoaded', cargarDashboard);

        // Actualizar cada 5 minutos
        setInterval(cargarDashboard, 300000);
    </script>
</body>
</html>
```

---

## 📋 **APIs PARA EL DASHBOARD**

```python
# app.py - Nuevas rutas para el dashboard

@app.route('/api/dashboard/kpis')
def dashboard_kpis():
    """API para KPIs principales del dashboard"""
    try:
        # Calcular métricas de la cartera
        roi_data = calcular_roi_cartera_completa()
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()

        # Calcular Sharpe promedio
        sharpe_ratios = []
        for activo in activos:
            sharpe = calcular_sharpe_ratio(activo.Id_Activo)
            if 'sharpe_ratio' in sharpe:
                sharpe_ratios.append(sharpe['sharpe_ratio'])

        sharpe_promedio = np.mean(sharpe_ratios) if sharpe_ratios else 0

        # Calcular VaR
        var_data = calcular_var_cartera()

        # Calcular Max Drawdown promedio
        max_dds = []
        for activo in activos:
            dd_data = calcular_maximum_drawdown(activo.Id_Activo)
            max_dds.append(dd_data['max_drawdown_porcentaje'])

        max_dd_promedio = np.mean(max_dds) if max_dds else 0

        return jsonify({
            'roi_cartera': roi_data['roi_portfolio'],
            'ganancia_total': roi_data['ganancia_total'],
            'sharpe_ratio': round(sharpe_promedio, 3),
            'var_95': var_data['var_perdida_maxima'],
            'max_drawdown': round(max_dd_promedio, 2),
            'valor_cartera': roi_data['valor_cartera'],
            'num_activos': len(activos),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/performance')
def dashboard_performance():
    """API para gráfico de performance de la cartera"""
    try:
        # Generar datos de performance históricos
        # En producción, esto vendría de datos reales
        activos = Activo.query.all()

        # Simular serie temporal de performance
        fechas = pd.date_range(start='2024-01-01', end=datetime.now().date(), freq='D')
        valores = []
        valor_base = 100000  # $100,000 inicial

        for i, fecha in enumerate(fechas):
            # Simular variación diaria
            variacion = np.random.normal(0.001, 0.02)  # 0.1% promedio, 2% volatilidad
            if i == 0:
                valores.append(valor_base)
            else:
                valor_anterior = valores[-1]
                nuevo_valor = valor_anterior * (1 + variacion)
                valores.append(nuevo_valor)

        return jsonify({
            'fechas': [fecha.strftime('%Y-%m-%d') for fecha in fechas],
            'valores': [round(v, 2) for v in valores],
            'valor_inicial': valor_base,
            'valor_actual': valores[-1],
            'performance_total': round(((valores[-1] - valor_base) / valor_base) * 100, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/allocation')
def dashboard_allocation():
    """API para distribución de activos"""
    try:
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()

        allocation_data = {}
        valor_total = 0

        for activo in activos:
            ticker = activo.ticker.Nombre_Ticker
            valor = activo.Precio_Compra * activo.Cantidad_Nominales_Compra
            valor_total += valor

            if ticker in allocation_data:
                allocation_data[ticker] += valor
            else:
                allocation_data[ticker] = valor

        # Convertir a porcentajes
        labels = list(allocation_data.keys())
        values = [round((v / valor_total) * 100, 1) for v in allocation_data.values()]
        valores_absolutos = [round(v, 2) for v in allocation_data.values()]

        return jsonify({
            'labels': labels,
            'values': values,
            'valores_absolutos': valores_absolutos,
            'valor_total': round(valor_total, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/risk-return')
def dashboard_risk_return():
    """API para gráfico riesgo vs rendimiento"""
    try:
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()

        tickers = []
        risks = []
        returns = []

        for activo in activos:
            ticker = activo.ticker.Nombre_Ticker
            tickers.append(ticker)

            # Calcular métricas
            roi_data = calcular_roi_activo(activo.Id_Activo)
            sharpe_data = calcular_sharpe_ratio(activo.Id_Activo)

            risk = sharpe_data.get('volatilidad_anual', 0)
            return_pct = roi_data.get('roi_porcentaje', 0)

            risks.append(risk)
            returns.append(return_pct)

        return jsonify({
            'tickers': tickers,
            'risk': risks,
            'return': returns
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/correlation')
def dashboard_correlation():
    """API para matriz de correlación"""
    try:
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').limit(10).all()  # Max 10 para demo

        tickers = [activo.ticker.Nombre_Ticker for activo in activos]

        # Generar matriz de correlación simulada
        n = len(tickers)
        correlation_matrix = np.eye(n)

        for i in range(n):
            for j in range(i+1, n):
                corr = np.random.uniform(0.1, 0.9)  # Correlación simulada
                correlation_matrix[i][j] = correlation_matrix[j][i] = corr

        return jsonify({
            'labels': tickers,
            'matrix': correlation_matrix.tolist()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/performance-table')
def dashboard_performance_table():
    """API para tabla de performance por activo"""
    try:
        activos = Activo.query.filter(Activo.Activo_Estado == 'EN_CARTERA').all()

        table_data = []
        valor_total = sum([a.Precio_Compra * a.Cantidad_Nominales_Compra for a in activos])

        for activo in activos:
            roi_data = calcular_roi_activo(activo.Id_Activo)
            sharpe_data = calcular_sharpe_ratio(activo.Id_Activo)
            dd_data = calcular_maximum_drawdown(activo.Id_Activo)
            var_data = calcular_var_activo(activo.Id_Activo)

            valor = activo.Precio_Compra * activo.Cantidad_Nominales_Compra
            peso = round((valor / valor_total) * 100, 1)

            table_data.append({
                'ticker': activo.ticker.Nombre_Ticker,
                'roi': roi_data.get('roi_porcentaje', 0),
                'sharpe_ratio': sharpe_data.get('sharpe_ratio', 0),
                'var': var_data.get('var_porcentaje', 0),
                'max_drawdown': dd_data.get('max_drawdown_porcentaje', 0),
                'valor': round(valor, 2),
                'peso': peso
            })

        return jsonify(table_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 🎯 **PRÓXIMOS PASOS DE IMPLEMENTACIÓN**

### Esta Semana (Fase 1)

1. **Configurar infraestructura base**
2. **Crear calculos_financieros.py**
3. **Implementar APIs básicas de métricas**

### Próxima Semana (Fase 2)

1. **Dashboard HTML con gráficos**
2. **APIs completas para dashboard**
3. **Integración con frontend**

### Próximo Mes (Fase 3-4)

1. **Métricas avanzadas (TIR, VaR completo)**
2. **Sistema de reportes PDF**
3. **Optimización de performance**

¿Te gustaría que empecemos con la Fase 1, implementando primero las métricas básicas de ROI y la configuración del sistema?
