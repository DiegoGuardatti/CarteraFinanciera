#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de exportación PDF para Cartera Financiera
Genera reportes profesionales en formato PDF con logos e información corporativa
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from flask import make_response
from modelo import db, Activo, Ticker, Broker, Comitente, InstrumentoFinanciero
from calculos_metricas import resumen_ejecutivo

def crear_estilo_personalizado():
    """Crea estilos personalizados para el PDF"""
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    styles.add(ParagraphStyle(
        name='TituloPersonalizado',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    ))
    
    # Estilo para subtítulos
    styles.add(ParagraphStyle(
        name='SubtituloPersonalizado',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.darkblue
    ))
    
    # Estilo para texto normal
    styles.add(ParagraphStyle(
        name='TextoNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6
    ))
    
    # Estilo para texto destacado
    styles.add(ParagraphStyle(
        name='TextoDestacado',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=6,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    ))
    
    return styles

class PDFPortada:
    """Clase para crear la portada del PDF"""
    
    def __init__(self, canvas_obj, doc):
        self.canvas = canvas_obj
        self.doc = doc
        
    def draw(self):
        """Dibuja la portada"""
        width, height = A4
        
        # Título principal
        self.canvas.setFont('Helvetica-Bold', 24)
        self.canvas.setFillColor(colors.darkblue)
        self.canvas.drawCentredText(width/2, height-150, 'CARTERA FINANCIERA')
        
        # Subtítulo
        self.canvas.setFont('Helvetica', 16)
        self.canvas.setFillColor(colors.grey)
        self.canvas.drawCentredText(width/2, height-180, 'Reporte Ejecutivo')
        
        # Información del reporte
        self.canvas.setFont('Helvetica', 12)
        self.canvas.setFillColor(colors.black)
        
        y_pos = height - 250
        self.canvas.drawString(50, y_pos, f'Fecha de Generación: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        self.canvas.drawString(50, y_pos - 20, f'Versión: 1.0')
        self.canvas.drawString(50, y_pos - 40, 'Sistema de Gestión de Cartera Financiera')
        
        # Línea decorativa
        self.canvas.setStrokeColor(colors.darkblue)
        self.canvas.setLineWidth(2)
        self.canvas.line(50, height - 300, width - 50, height - 300)
        
        # Pie de página
        self.canvas.setFont('Helvetica-Oblique', 10)
        self.canvas.setFillColor(colors.grey)
        self.canvas.drawCentredText(width/2, 50, 'Documento generado automáticamente por Cartera Financiera')

def generar_tabla_resumen_ejecutivo():
    """Genera tabla con resumen ejecutivo"""
    try:
        resumen = resumen_ejecutivo()
        
        # Datos de la tabla
        data = [
            ['MÉTRICA', 'VALOR'],
            ['Total de Activos', str(resumen.get('total_activos', 0))],
            ['ROI Promedio (%)', f"{round(resumen.get('roi_promedio', 0), 2)}"],
            ['Valor Total Cartera', f"${resumen.get('valor_total_cartera', 0):,.2f}"],
            ['Activos Vendidos', str(resumen.get('activos_vendidos', 0))],
            ['Activos en Cartera', str(resumen.get('activos_en_cartera', 0))]
        ]
        
        # Crear tabla
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Contenido
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        return table
        
    except Exception as e:
        return Paragraph(f"Error generando tabla resumen: {str(e)}", ParagraphStyle('Normal'))

def generar_tabla_top_performers():
    """Genera tabla con top performers"""
    try:
        from calculos_metricas import top_performers
        performers = top_performers(10)
        
        if not performers:
            return Paragraph("No hay datos de performance disponibles", ParagraphStyle('Normal'))
        
        # Headers
        data = [['TICKER', 'ROI (%)', 'GANANCIA', 'ESTADO']]
        
        # Datos
        for performer in performers:
            data.append([
                performer.get('ticker', 'N/A'),
                f"{round(performer.get('performance', 0), 2)}",
                f"${performer.get('ganancia', 0):,.2f}",
                performer.get('estado', 'N/A')
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Contenido
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Colores alternados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        return table
        
    except Exception as e:
        return Paragraph(f"Error generando tabla performance: {str(e)}", ParagraphStyle('Normal'))

def generar_tabla_analisis_tickers():
    """Genera tabla de análisis por ticker"""
    try:
        # Consulta para resumen por ticker
        query = db.session.query(
            Ticker.Nombre_Ticker,
            InstrumentoFinanciero.Nombre.label('instrumento'),
            db.func.count(Activo.Id_Activo).label('total_activos'),
            db.func.sum(Activo.Total_Pesos_Compra).label('inversion_total'),
            db.func.avg(Activo.Precio_Compra).label('precio_promedio')
        ).join(
            Activo, Ticker.Id_Ticker == Activo.Id_Ticker
        ).join(
            InstrumentoFinanciero, Ticker.Id_InstrumentoFinanciero == InstrumentoFinanciero.Id_InstrumentoFinanciero
        ).group_by(
            Ticker.Id_Ticker, Ticker.Nombre_Ticker, InstrumentoFinanciero.Nombre
        ).order_by(
            db.func.sum(Activo.Total_Pesos_Compra).desc()
        ).limit(10)
        
        resultados = query.all()
        
        if not resultados:
            return Paragraph("No hay datos de tickers disponibles", ParagraphStyle('Normal'))
        
        # Headers
        data = [['TICKER', 'INSTRUMENTO', 'ACTIVOS', 'INVERSIÓN TOTAL', 'PREC. PROMEDIO']]
        
        # Datos
        inversion_total = sum([r.inversion_total or 0 for r in resultados])
        
        for resultado in resultados:
            porcentaje_cartera = 0
            if inversion_total > 0 and resultado.inversion_total:
                porcentaje_cartera = (resultado.inversion_total / inversion_total) * 100
            
            data.append([
                resultado.Nombre_Ticker,
                resultado.instrumento,
                str(resultado.total_activos),
                f"${resultado.inversion_total or 0:,.2f}",
                f"{round(resultado.precio_promedio or 0, 2)}"
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[1*inch, 1.5*inch, 0.8*inch, 1.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Contenido
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Colores alternados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        return table
        
    except Exception as e:
        return Paragraph(f"Error generando tabla tickers: {str(e)}", ParagraphStyle('Normal'))

def exportar_reporte_ejecutivo_pdf():
    """
    Exporta reporte ejecutivo completo en PDF
    
    Returns:
        bytes: Datos del archivo PDF
    """
    try:
        # Crear documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Obtener estilos
        styles = crear_estilo_personalizado()
        
        # Contenido del PDF
        story = []
        
        # Portada (se maneja por separado)
        doc.build(story, onFirstPage=PDFPortada)
        
        # Página 2: Resumen Ejecutivo
        story.append(Spacer(1, 20))
        story.append(Paragraph("RESUMEN EJECUTIVO", styles['TituloPersonalizado']))
        
        story.append(Paragraph("El presente reporte presenta un análisis integral de la cartera financiera, incluyendo métricas principales, análisis de performance y recomendaciones estratégicas.", styles['TextoNormal']))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph("Métricas Principales", styles['SubtituloPersonalizado']))
        
        story.append(generar_tabla_resumen_ejecutivo())
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("Principales Observaciones", styles['SubtituloPersonalizado']))
        
        observaciones = [
            "• La cartera muestra un desempeño favorable con ROI promedio positivo",
            "• Diversificación adecuada entre diferentes instrumentos financieros",
            "• Activos en cartera representan mayor porcentaje que vendidos",
            "• Se recomienda monitoreo continuo de performance por ticker"
        ]
        
        for observacion in observaciones:
            story.append(Paragraph(observacion, styles['TextoNormal']))
        
        story.append(PageBreak())
        
        # Página 3: Análisis de Performance
        story.append(Paragraph("ANÁLISIS DE PERFORMANCE", styles['TituloPersonalizado']))
        
        story.append(Paragraph("Mejores Performers", styles['SubtituloPersonalizado']))
        story.append(Paragraph("Los siguientes activos han demostrado el mejor rendimiento en el período analizado:", styles['TextoNormal']))
        
        story.append(Spacer(1, 10))
        story.append(generar_tabla_top_performers())
        
        story.append(Spacer(1, 20))
        
        # Análisis por Ticker
        story.append(Paragraph("Análisis por Ticker", styles['SubtituloPersonalizado']))
        story.append(Paragraph("Distribución de la cartera por instrumento financiero:", styles['TextoNormal']))
        
        story.append(Spacer(1, 10))
        story.append(generar_tabla_analisis_tickers())
        
        story.append(PageBreak())
        
        # Página 4: Conclusiones y Recomendaciones
        story.append(Paragraph("CONCLUSIONES Y RECOMENDACIONES", styles['TituloPersonalizado']))
        
        story.append(Paragraph("Conclusiones", styles['SubtituloPersonalizado']))
        
        conclusiones = [
            "El análisis de la cartera financiera revela un desempeño general positivo con oportunidades de optimización.",
            "La diversificación actual proporciona un balance adecuado entre riesgo y retorno.",
            "Algunos activos muestran performance superior, sugiriendo estrategias de replicación.",
            "Se observa concentración en ciertos instrumentos que podría requerir rebalanceo."
        ]
        
        for conclusion in conclusiones:
            story.append(Paragraph(conclusion, styles['TextoNormal']))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph("Recomendaciones", styles['SubtituloPersonalizado']))
        
        recomendaciones = [
            "Implementar monitoreo diario de performance para activos con alta volatilidad",
            "Considerar rebalanceo trimestral para mantener distribución objetivo",
            "Evaluar oportunidades de inversión en activos con performance histórica favorable",
            "Establecer límites de concentración por instrumento financiero",
            "Revisar periódicamente la estrategia de diversificación según condiciones de mercado"
        ]
        
        for recomendacion in recomendaciones:
            story.append(Paragraph(recomendacion, styles['TextoDestacado']))
        
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}", styles['TextoNormal']))
        
        # Generar PDF
        doc.build(story)
        
        # Obtener contenido PDF
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        raise Exception(f"Error exportando PDF: {str(e)}")

def exportar_reporte_detallado_pdf(filtros=None):
    """
    Exporta reporte detallado de activos en PDF
    
    Args:
        filtros (dict): Filtros para aplicar
        
    Returns:
        bytes: Datos del archivo PDF
    """
    try:
        # Crear documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = crear_estilo_personalizado()
        story = []
        
        # Título
        story.append(Paragraph("DETALLE DE ACTIVOS", styles['TituloPersonalizado']))
        story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['TextoNormal']))
        
        # Filtros aplicados
        if filtros:
            story.append(Paragraph("Filtros Aplicados:", styles['SubtituloPersonalizado']))
            for key, value in filtros.items():
                story.append(Paragraph(f"• {key}: {value}", styles['TextoNormal']))
            story.append(Spacer(1, 20))
        
        # Consulta de datos
        query = db.session.query(
            Activo, Ticker, Broker, Comitente, InstrumentoFinanciero
        ).join(
            Ticker, Activo.Id_Ticker == Ticker.Id_Ticker
        ).join(
            Broker, Activo.Id_Broker == Broker.Id_Broker
        ).join(
            Comitente, Activo.Id_Comitente == Comitente.Id_Comitente
        ).join(
            InstrumentoFinanciero, Ticker.Id_InstrumentoFinanciero == InstrumentoFinanciero.Id_InstrumentoFinanciero
        ).order_by(Activo.Fecha_Hora_Compra.desc())
        
        # Aplicar filtros
        if filtros:
            if filtros.get('Id_Broker'):
                query = query.filter(Activo.Id_Broker == filtros['Id_Broker'])
            if filtros.get('Id_Comitente'):
                query = query.filter(Activo.Id_Comitente == filtros['Id_Comitente'])
            if filtros.get('Id_Ticker'):
                query = query.filter(Activo.Id_Ticker == filtros['Id_Ticker'])
            if filtros.get('Activo_Estado'):
                query = query.filter(Activo.Activo_Estado == filtros['Activo_Estado'])
        
        resultados = query.limit(100).all()  # Limitar para evitar PDFs muy largos
        
        # Tabla de activos
        story.append(Paragraph("Listado de Activos", styles['SubtituloPersonalizado']))
        
        # Headers de la tabla
        data = [['FECHA', 'TICKER', 'BROKER', 'PRECIO COMPRA', 'CANTIDAD', 'TOTAL', 'ESTADO', 'ROI (%)']]
        
        for activo, ticker, broker, comitente, instrumento in resultados:
            # Calcular ROI
            roi = 0
            if activo.Precio_Venta and activo.Precio_Compra:
                roi = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
            
            data.append([
                activo.Fecha_Hora_Compra.strftime('%d/%m/%Y') if activo.Fecha_Hora_Compra else '',
                ticker.Nombre_Ticker if ticker else '',
                broker.Nombre if broker else '',
                f"${activo.Precio_Compra:,.2f}" if activo.Precio_Compra else '',
                str(activo.Cantidad_Nominales_Compra) if activo.Cantidad_Nominales_Compra else '',
                f"${activo.Total_Pesos_Compra:,.2f}" if activo.Total_Pesos_Compra else '',
                activo.Activo_Estado or '',
                f"{roi:.2f}" if roi != 0 else ''
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[0.8*inch, 0.8*inch, 1*inch, 1*inch, 0.8*inch, 1*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            
            # Contenido
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            
            # Colores alternados
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        story.append(table)
        story.append(Paragraph(f"Total de registros: {len(resultados)}", styles['TextoNormal']))
        
        # Generar PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        raise Exception(f"Error exportando PDF detallado: {str(e)}")

def crear_respuesta_pdf(pdf_content, nombre_archivo):
    """
    Crea una respuesta HTTP para descarga de PDF
    
    Args:
        pdf_content (bytes): Contenido PDF
        nombre_archivo (str): Nombre del archivo para descarga
        
    Returns:
        Response: Respuesta Flask para descarga
    """
    try:
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response
    except Exception as e:
        raise Exception(f"Error creando respuesta PDF: {str(e)}")