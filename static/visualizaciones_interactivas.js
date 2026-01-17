/**
 * Módulo de Visualizaciones Interactivas
 * Mejoras para drill-down charts, heatmaps dinámicos y exportación
 */

// ==================== CONFIGURACIÓN GLOBAL ====================
const VISUALIZATION_CONFIG = {
    theme: {
        primary: '#667eea',
        secondary: '#764ba2',
        success: '#28a745',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    },
    export: {
        formats: ['png', 'pdf', 'svg', 'html'],
        dpi: 300,
        width: 1200,
        height: 800
    },
    drilldown: {
        animationDuration: 500,
        easing: 'ease-in-out'
    }
};

// ==================== EXPORTACIÓN DE GRÁFICOS ====================
class ChartExporter {
    constructor() {
        this.initExportButtons();
    }

    initExportButtons() {
        // Buscar todos los contenedores de gráficos y agregar botones de exportación
        document.querySelectorAll('[id$="-chart"], #correlation-heatmap, #portfolio-var-chart').forEach(container => {
            this.addExportButtons(container);
        });
    }

    addExportButtons(container) {
        const chartId = container.id || 'chart-' + Math.random().toString(36).substr(2, 9);
        container.id = chartId;

        // Crear contenedor de botones
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'chart-export-buttons mb-2';
        buttonContainer.style.cssText = 'position: absolute; top: 10px; right: 10px; z-index: 1000;';

        // Agregar botones de exportación
        VISUALIZATION_CONFIG.export.formats.forEach(format => {
            const button = document.createElement('button');
            button.className = `btn btn-sm btn-outline-${this.getButtonColor(format)} me-1`;
            button.innerHTML = `<i class="fas fa-download"></i> ${format.toUpperCase()}`;
            button.onclick = () => this.exportChart(chartId, format);
            buttonContainer.appendChild(button);
        });

        // Insertar antes del contenedor
        container.parentNode.insertBefore(buttonContainer, container);
        
        // Ajustar posición del contenedor para los botones
        container.style.position = 'relative';
    }

    getButtonColor(format) {
        const colors = {
            'png': 'primary',
            'pdf': 'danger',
            'svg': 'success',
            'html': 'info'
        };
        return colors[format] || 'secondary';
    }

    async exportChart(chartId, format) {
        const chartContainer = document.getElementById(chartId);
        if (!chartContainer) {
            console.error('Contenedor de gráfico no encontrado:', chartId);
            return;
        }

        try {
            const filename = `chart_${chartId}_${new Date().toISOString().split('T')[0]}`;
            
            switch (format) {
                case 'png':
                    await this.exportToPNG(chartContainer, filename);
                    break;
                case 'pdf':
                    await this.exportToPDF(chartContainer, filename);
                    break;
                case 'svg':
                    await this.exportToSVG(chartContainer, filename);
                    break;
                case 'html':
                    await this.exportToHTML(chartContainer, filename);
                    break;
            }
        } catch (error) {
            console.error('Error exportando gráfico:', error);
            this.showExportError(error);
        }
    }

    async exportToPNG(container, filename) {
        // Usando Plotly.toImage para exportar a PNG
        if (typeof Plotly !== 'undefined') {
            const dataUrl = await Plotly.toImage(container, {
                format: 'png',
                width: VISUALIZATION_CONFIG.export.width,
                height: VISUALIZATION_CONFIG.export.height,
                dpi: VISUALIZATION_CONFIG.export.dpi
            });
            
            this.downloadDataUrl(dataUrl, `${filename}.png`);
        } else {
            throw new Error('Plotly no está disponible');
        }
    }

    async exportToPDF(container, filename) {
        // Crear PDF con jsPDF y html2canvas
        const { jsPDF } = window.jspdf;
        
        // Capturar como imagen primero
        const dataUrl = await Plotly.toImage(container, {
            format: 'png',
            width: VISUALIZATION_CONFIG.export.width,
            height: VISUALIZATION_CONFIG.export.height
        });

        // Crear PDF
        const pdf = new jsPDF({
            orientation: 'landscape',
            unit: 'mm',
            format: 'a4'
        });

        // Agregar imagen al PDF
        const imgProps = pdf.getImageProperties(dataUrl);
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
        
        pdf.addImage(dataUrl, 'PNG', 10, 10, pdfWidth - 20, pdfHeight - 20);
        pdf.save(`${filename}.pdf`);
    }

    async exportToSVG(container, filename) {
        if (typeof Plotly !== 'undefined') {
            const svgData = await Plotly.toImage(container, { format: 'svg' });
            this.downloadDataUrl(svgData, `${filename}.svg`);
        } else {
            throw new Error('Plotly no está disponible');
        }
    }

    async exportToHTML(container, filename) {
        // Crear archivo HTML autónomo con el gráfico
        const plotData = Plotly.data || [];
        const layout = Plotly.layout || {};
        
        const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <title>Gráfico Exportado - ${filename}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
        .header { text-align: center; margin-bottom: 20px; }
        .chart-container { width: 100%; height: 600px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Gráfico Financiero</h1>
        <p>Generado el ${new Date().toLocaleDateString('es-AR')}</p>
    </div>
    <div id="chart" class="chart-container"></div>
    <script>
        const data = ${JSON.stringify(plotData)};
        const layout = ${JSON.stringify(layout)};
        Plotly.newPlot('chart', data, layout, {responsive: true});
    </script>
</body>
</html>`;

        this.downloadFile(htmlContent, `${filename}.html`, 'text/html');
    }

    downloadDataUrl(dataUrl, filename) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    showExportError(error) {
        // Mostrar notificación de error
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            Error exportando gráfico: ${error.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alert);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => alert.remove(), 5000);
    }
}

// ==================== HEATMAPS DINÁMICOS ====================
class DynamicHeatmap {
    constructor(containerId, data) {
        this.containerId = containerId;
        this.data = data;
        this.selectedCell = null;
        this.tooltip = null;
        this.init();
    }

    init() {
        this.createHeatmap();
        this.addInteractivity();
        this.createTooltip();
    }

    createHeatmap() {
        const trace = {
            z: this.data.matriz_correlacion,
            x: this.data.tickers,
            y: this.data.tickers,
            type: 'heatmap',
            colorscale: [
                [0, '#d73027'],
                [0.1, '#fc8d59'],
                [0.2, '#fee08b'],
                [0.3, '#d9ef8b'],
                [0.4, '#91bfdb'],
                [0.5, '#4575b4'],
                [0.6, '#313695'],
                [0.7, '#4575b4'],
                [0.8, '#91bfdb'],
                [0.9, '#d9ef8b'],
                [1, '#fee08b']
            ],
            reversescale: false,
            zmid: 0,
            zmin: -1,
            zmax: 1,
            hovertemplate: 
                '<b>%{y} vs %{x}</b><br>' +
                'Correlación: %{z:.3f}<br>' +
                '<extra></extra>',
            colorbar: {
                title: 'Correlación',
                titleside: 'right',
                tickmode: 'linear',
                tick0: -1,
                dtick: 0.2
            }
        };

        const layout = {
            title: {
                text: `Matriz de Correlación Interactiva<br><sub>HHI: ${this.data.metricas_diversificacion.indice_hhi}</sub>`,
                font: { size: 16 }
            },
            xaxis: { 
                side: 'bottom',
                tickangle: -45
            },
            yaxis: { 
                side: 'left'
            },
            height: 450,
            margin: { t: 80, b: 100, l: 80, r: 50 },
            hovermode: 'closest'
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToAdd: [{
                name: 'Drill Down',
                icon: Plotly.Icons.search,
                click: (gd) => this.enableDrillDown()
            }]
        };

        Plotly.newPlot(this.containerId, [trace], layout, config);
    }

    addInteractivity() {
        // Evento de clic en celda
        this.containerId + '_on' && 
        document.getElementById(this.containerId).on('plotly_click', (data) => {
            this.handleCellClick(data);
        });

        // Evento de hover
        document.getElementById(this.containerId).on('plotly_hover', (data) => {
            this.showTooltip(data);
        });

        // Evento de salida del hover
        document.getElementById(this.containerId).on('plotly_unhover', () => {
            this.hideTooltip();
        });
    }

    handleCellClick(data) {
        if (data.points.length > 0) {
            const point = data.points[0];
            const x = point.x;
            const y = point.y;
            const correlation = point.z;

            this.selectedCell = { x, y, correlation };
            
            // Mostrar información detallada
            this.showDetailedInfo(x, y, correlation);
            
            // Destacar la celda seleccionada
            this.highlightCell(x, y);
        }
    }

    showDetailedInfo(ticker1, ticker2, correlation) {
        // Crear modal con información detallada
        const modalHtml = `
            <div class="modal fade" id="correlationDetailModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-search me-2"></i>
                                Análisis Detallado: ${ticker1} vs ${ticker2}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Información de Correlación</h6>
                                    <ul class="list-unstyled">
                                        <li><strong>Correlación:</strong> ${correlation.toFixed(3)}</li>
                                        <li><strong>Interpretación:</strong> ${this.interpretCorrelation(correlation)}</li>
                                        <li><strong>Significado:</strong> ${this.getCorrelationMeaning(correlation)}</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h6>Implicaciones para la Cartera</h6>
                                    <div class="alert alert-${correlation > 0.7 ? 'warning' : correlation < -0.3 ? 'info' : 'success'}">
                                        ${this.getPortfolioImplication(correlation)}
                                    </div>
                                </div>
                            </div>
                            <hr>
                            <h6>Análisis de Diversificación</h6>
                            <p class="small text-muted">
                                ${correlation > 0.8 ? 
                                    '⚠️ Alta correlación: Considerar reducir exposición a uno de estos activos.' :
                                    correlation < -0.5 ?
                                    '✅ Correlación negativa: Excelente para diversificación.' :
                                    '✅ Buena diversificación: Correlación moderada.'
                                }
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            <button type="button" class="btn btn-primary" onclick="window.open('/api/metrics/correlation-detailed?ticker1=${ticker1}&ticker2=${ticker2}', '_blank')">
                                <i class="fas fa-chart-line me-1"></i>Ver Análisis Completo
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior si existe
        const existingModal = document.getElementById('correlationDetailModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Agregar nuevo modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('correlationDetailModal'));
        modal.show();
    }

    highlightCell(ticker1, ticker2) {
        // Resaltar la celda seleccionada
        const update = {
            marker: {
                color: this.data.matriz_correlacion.map((row, i) => 
                    row.map((val, j) => 
                        (this.data.tickers[i] === ticker1 && this.data.tickers[j] === ticker2) ||
                        (this.data.tickers[i] === ticker2 && this.data.tickers[j] === ticker1)
                            ? '#ff6b6b' : val
                    )
                )
            }
        };

        Plotly.restyle(this.containerId, update);
    }

    interpretCorrelation(correlation) {
        if (correlation > 0.8) return 'Muy Alta Positiva';
        if (correlation > 0.6) return 'Alta Positiva';
        if (correlation > 0.3) return 'Moderada Positiva';
        if (correlation > -0.3) return 'Baja/Nula';
        if (correlation > -0.6) return 'Moderada Negativa';
        if (correlation > -0.8) return 'Alta Negativa';
        return 'Muy Alta Negativa';
    }

    getCorrelationMeaning(correlation) {
        if (correlation > 0.7) return 'Los activos tienden a moverse en la misma dirección';
        if (correlation < -0.5) return 'Los activos tienden a moverse en direcciones opuestas';
        return 'Los activos tienen movimientos independientes';
    }

    getPortfolioImplication(correlation) {
        if (correlation > 0.8) return 'Riesgo de concentración: Los activos no proporcionan diversificación efectiva.';
        if (correlation < -0.5) return 'Excelente diversificación: Estos activos se balancean mutuamente.';
        return 'Diversificación adecuada: Buena combinación de activos.';
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'chart-tooltip';
        this.tooltip.style.cssText = `
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
        `;
        document.body.appendChild(this.tooltip);
    }

    showTooltip(data) {
        if (data.points.length > 0) {
            const point = data.points[0];
            this.tooltip.innerHTML = `
                <strong>${point.y} vs ${point.x}</strong><br>
                Correlación: ${point.z.toFixed(3)}
            `;
            this.tooltip.style.display = 'block';
            this.tooltip.style.left = data.event.pageX + 10 + 'px';
            this.tooltip.style.top = data.event.pageY - 10 + 'px';
        }
    }

    hideTooltip() {
        this.tooltip.style.display = 'none';
    }

    enableDrillDown() {
        // Activar modo drill-down
        document.getElementById(this.containerId).style.cursor = 'crosshair';
        
        const notification = document.createElement('div');
        notification.className = 'alert alert-info position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        notification.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Modo Drill-Down activado. Haga clic en una celda para ver análisis detallado.
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 3000);
    }
}

// ==================== DRILL-DOWN CHARTS ====================
class DrillDownChart {
    constructor(containerId, baseData) {
        this.containerId = containerId;
        this.baseData = baseData;
        this.currentLevel = 0;
        this.history = [];
        this.init();
    }

    init() {
        this.createBaseChart();
        this.addDrillDownButtons();
    }

    createBaseChart() {
        // Gráfico base con datos agregados
        const trace = {
            labels: this.baseData.labels || [],
            values: this.baseData.values || [],
            type: 'pie',
            hole: 0.3,
            textinfo: 'label+percent',
            textposition: 'outside',
            marker: {
                colors: this.baseData.colors || this.generateColors(this.baseData.labels?.length || 0)
            },
            hovertemplate: '<b>%{label}</b><br>Valor: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        };

        const layout = {
            title: {
                text: this.baseData.title || 'Distribución de Cartera',
                font: { size: 18 }
            },
            height: 400,
            margin: { t: 60, b: 40, l: 40, r: 40 },
            showlegend: true,
            legend: {
                orientation: 'v',
                x: 1.05,
                y: 0.5
            }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToAdd: [{
                name: 'Drill Down',
                icon: Plotly.Icons.search,
                click: (gd) => this.startDrillDown()
            }]
        };

        Plotly.newPlot(this.containerId, [trace], layout, config);
        
        // Agregar evento de clic
        document.getElementById(this.containerId).on('plotly_click', (data) => {
            if (data.points.length > 0) {
                this.handleSliceClick(data.points[0]);
            }
        });
    }

    addDrillDownButtons() {
        const container = document.getElementById(this.containerId);
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'drill-down-controls mt-2';
        buttonContainer.innerHTML = `
            <button class="btn btn-sm btn-outline-primary me-2" onclick="window.drillDownChart.goBack()">
                <i class="fas fa-arrow-left"></i> Volver
            </button>
            <button class="btn btn-sm btn-outline-info" onclick="window.drillDownChart.reset()">
                <i class="fas fa-refresh"></i> Reiniciar
            </button>
        `;
        container.parentNode.insertBefore(buttonContainer, container.nextSibling);
    }

    startDrillDown() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-success position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        notification.innerHTML = `
            <i class="fas fa-search me-2"></i>
            Haga clic en una sección del gráfico para hacer drill-down.
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 3000);
    }

    handleSliceClick(point) {
        const label = point.label;
        const value = point.value;
        
        // Guardar estado actual
        this.history.push({
            containerId: this.containerId,
            data: this.baseData,
            level: this.currentLevel
        });

        // Obtener datos detallados para el siguiente nivel
        this.loadDetailedData(label, point);
    }

    async loadDetailedData(parentLabel, point) {
        try {
            // Simular llamada a API para obtener datos detallados
            const response = await fetch(`/api/metrics/drill-down?category=${encodeURIComponent(parentLabel)}`);
            const detailedData = await response.json();

            if (detailedData.error) {
                throw new Error(detailedData.error);
            }

            this.displayDetailedLevel(detailedData, parentLabel);
            this.currentLevel++;

        } catch (error) {
            console.error('Error cargando datos detallados:', error);
            this.showError('Error cargando datos detallados: ' + error.message);
        }
    }

    displayDetailedLevel(detailedData, parentLabel) {
        // Cambiar a gráfico de barras para mostrar detalles
        const trace = {
            x: detailedData.labels,
            y: detailedData.values,
            type: 'bar',
            marker: {
                color: this.generateColors(detailedData.labels.length),
                line: { color: '#333', width: 1 }
            },
            hovertemplate: '<b>%{x}</b><br>Valor: %{y}<extra></extra>'
        };

        const layout = {
            title: `Detalle: ${parentLabel}`,
            xaxis: { title: 'Elementos' },
            yaxis: { title: 'Valor' },
            height: 400,
            margin: { t: 60, b: 60, l: 60, r: 40 }
        };

        Plotly.react(this.containerId, [trace], layout);

        // Actualizar datos base
        this.baseData = detailedData;
    }

    goBack() {
        if (this.history.length > 0) {
            const previousState = this.history.pop();
            Plotly.react(previousState.containerId, 
                [previousState.data.trace], 
                previousState.data.layout
            );
            this.baseData = previousState.data;
            this.currentLevel--;
        }
    }

    reset() {
        if (this.history.length > 0) {
            const originalState = this.history[0];
            Plotly.react(this.containerId, 
                [originalState.data.trace], 
                originalState.data.layout
            );
            this.baseData = originalState.data;
            this.history = [];
            this.currentLevel = 0;
        }
    }

    generateColors(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 137.508) % 360; // Golden angle approximation
            colors.push(`hsl(${hue}, 70%, 60%)`);
        }
        return colors;
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger position-fixed';
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        alert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        `;
        document.body.appendChild(alert);

        setTimeout(() => alert.remove(), 5000);
    }
}

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar exportación de gráficos
    window.chartExporter = new ChartExporter();

    // Configurar heatmaps dinámicos cuando se carguen
    const correlationContainer = document.getElementById('correlation-heatmap');
    if (correlationContainer && window.correlationData) {
        window.dynamicHeatmap = new DynamicHeatmap('correlation-heatmap', window.correlationData);
    }

    // Configurar drill-down charts para backtesting
    const backtestContainer = document.getElementById('backtest-chart');
    if (backtestContainer && window.backtestData) {
        window.drillDownChart = new DrillDownChart('backtest-chart', {
            title: 'Performance por Período',
            labels: ['Q1', 'Q2', 'Q3', 'Q4'],
            values: [25, 35, 20, 20], // Datos de ejemplo
            trace: null,
            layout: null
        });
    }

    console.log('✅ Visualizaciones Interactivas inicializadas');
});

// ==================== EXPORTAR MÓDULOS ====================
window.VisualizationModules = {
    ChartExporter,
    DynamicHeatmap,
    DrillDownChart,
    VISUALIZATION_CONFIG
};