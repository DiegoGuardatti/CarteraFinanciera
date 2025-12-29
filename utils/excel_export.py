#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de exportación Excel para Cartera Financiera
Genera reportes profesionales con múltiples hojas y gráficos
"""

import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
from openpyxl.chart import PieChart, BarChart, Reference
from flask import make_response
from modelo import db, Activo, Ticker, Broker, Comitente, InstrumentoFinanciero
from calculos_metricas import resumen_ejecutivo

def crear_estilo_header():
    """Crea estilo para headers"""
    return {
        'font': Font(bold=True, color='FFFFFF'),
        'fill': PatternFill(start_color='366092', end_color='366092', fill_type='solid'),
        'alignment': Alignment(horizontal='center', vertical='center'),
        'border': Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    }

def crear_estilo_datos():
    """Crea estilo para datos"""
    return {
        'font': Font(size=10),
        'alignment': Alignment(horizontal='left', vertical='center'),
        'border': Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    }

def crear_estilo_resumen():
    """Crea estilo para resumen"""
    return {
        'font': Font(bold=True, size=11),
        'fill': PatternFill(start_color='E6F2FF', end_color='E6F2FF', fill_type='solid'),
        'alignment': Alignment(horizontal='center', vertical='center'),
        'border': Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    }

def aplicar_estilo(cell, estilo):
    """Aplica estilo a una celda"""
    if 'font' in estilo:
        cell.font = estilo['font']
    if 'fill' in estilo:
        cell.fill = estilo['fill']
    if 'alignment' in estilo:
        cell.alignment = estilo['alignment']
    if 'border' in estilo:
        cell.border = estilo['border']

def exportar_activos_excel(filtros=None):
    """
    Exporta activos a formato Excel profesional
    
    Args:
        filtros (dict): Filtros para aplicar en la consulta
        
    Returns:
        bytes: Datos del archivo Excel
    """
    try:
        # Crear workbook
        wb = Workbook()
        
        # Eliminar hoja por defecto
        wb.remove(wb.active)
        
        # Obtener resumen ejecutivo
        resumen = resumen_ejecutivo()
        
        # === HOJA 1: RESUMEN EJECUTIVO ===
        ws_resumen = wb.create_sheet('Resumen Ejecutivo')
        
        # Título
        ws_resumen['A1'] = 'REPORTE EJECUTIVO - CARTERA FINANCIERA'
        ws_resumen['A1'].font = Font(bold=True, size=16)
        ws_resumen['A1'].alignment = Alignment(horizontal='center')
        ws_resumen.merge_cells('A1:E1')
        
        # Fecha
        ws_resumen['A2'] = f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
        ws_resumen['A2'].font = Font(size=12)
        
        # Métricas principales
        row = 4
        ws_resumen[f'A{row}'] = 'MÉTRICAS PRINCIPALES'
        ws_resumen[f'A{row}'].font = Font(bold=True, size=14, color='366092')
        
        row += 2
        metricas = [
            ('Total de Activos', resumen.get('total_activos', 0)),
            ('ROI Promedio (%)', round(resumen.get('roi_promedio', 0), 2)),
            ('Valor Total Cartera', f'${resumen.get("valor_total_cartera", 0):,.2f}'),
            ('Activos Vendidos', resumen.get('activos_vendidos', 0)),
            ('Activos en Cartera', resumen.get('activos_en_cartera', 0))
        ]
        
        for metrica, valor in metricas:
            ws_resumen[f'A{row}'] = metrica
            ws_resumen[f'B{row}'] = valor
            ws_resumen[f'A{row}'].font = Font(bold=True)
            row += 1
        
        # === HOJA 2: DETALLE DE ACTIVOS ===
        ws_activos = wb.create_sheet('Detalle Activos')
        
        # Headers
        headers = [
            'ID_Activo', 'Broker', 'Comitente', 'Ticker', 'Instrumento',
            'Fecha_Compra', 'Precio_Compra', 'Cantidad_Compra', 'Total_Pesos_Compra',
            'Fecha_Venta', 'Precio_Venta', 'Total_Pesos_Venta', 'Estado',
            'Ganancia_Pesos', 'ROI (%)'
        ]
        
        # Escribir headers
        for col, header in enumerate(headers, 1):
            cell = ws_activos.cell(row=1, column=col, value=header)
            aplicar_estilo(cell, crear_estilo_header())
        
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
        )
        
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
        
        resultados = query.all()
        
        # Escribir datos
        for row_idx, (activo, ticker, broker, comitente, instrumento) in enumerate(resultados, 2):
            # Calcular métricas
            ganancia_pesos = 0
            roi = 0
            
            if activo.Precio_Venta and activo.Cantidad_Nominales_Venta:
                ganancia_pesos = (activo.Precio_Venta - activo.Precio_Compra) * activo.Cantidad_Nominales_Venta
                if activo.Precio_Compra > 0:
                    roi = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
            
            datos_fila = [
                activo.Id_Activo,
                broker.Nombre if broker else '',
                comitente.Titular if comitente else '',
                ticker.Nombre_Ticker if ticker else '',
                instrumento.Nombre if instrumento else '',
                activo.Fecha_Hora_Compra.strftime('%d/%m/%Y') if activo.Fecha_Hora_Compra else '',
                activo.Precio_Compra or 0,
                activo.Cantidad_Nominales_Compra or 0,
                activo.Total_Pesos_Compra or 0,
                activo.Fecha_Hora_Venta.strftime('%d/%m/%Y') if activo.Fecha_Hora_Venta else '',
                activo.Precio_Venta or 0,
                activo.Total_Pesos_Venta or 0,
                activo.Activo_Estado or '',
                ganancia_pesos,
                round(roi, 2)
            ]
            
            for col_idx, valor in enumerate(datos_fila, 1):
                cell = ws_activos.cell(row=row_idx, column=col_idx, value=valor)
                aplicar_estilo(cell, crear_estilo_datos())
        
        # Ajustar ancho de columnas
        for column in ws_activos.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws_activos.column_dimensions[column_letter].width = adjusted_width
        
        # === HOJA 3: ANÁLISIS POR TICKER ===
        ws_tickers = wb.create_sheet('Análisis por Ticker')
        
        # Headers para análisis por ticker
        headers_ticker = [
            'Ticker', 'Instrumento', 'Total_Activos', 'Inversion_Total',
            'Precio_Promedio', 'Activos_Activos', 'Activos_Vendidos', '% Cartera'
        ]
        
        for col, header in enumerate(headers_ticker, 1):
            cell = ws_tickers.cell(row=1, column=col, value=header)
            aplicar_estilo(cell, crear_estilo_header())
        
        # Consulta de resumen por ticker
        query_ticker = db.session.query(
            Ticker.Nombre_Ticker,
            InstrumentoFinanciero.Nombre.label('instrumento'),
            db.func.count(Activo.Id_Activo).label('total_activos'),
            db.func.sum(Activo.Total_Pesos_Compra).label('inversion_total'),
            db.func.avg(Activo.Precio_Compra).label('precio_promedio'),
            db.func.count(
                db.case(
                    (Activo.Activo_Estado == 'EN_CARTERA', 1),
                    else_=None
                )
            ).label('activos_activos'),
            db.func.count(
                db.case(
                    (Activo.Activo_Estado == 'VENDIDO', 1),
                    else_=None
                )
            ).label('activos_vendidos')
        ).join(
            Activo, Ticker.Id_Ticker == Activo.Id_Ticker
        ).join(
            InstrumentoFinanciero, Ticker.Id_InstrumentoFinanciero == InstrumentoFinanciero.Id_InstrumentoFinanciero
        ).group_by(
            Ticker.Id_Ticker, Ticker.Nombre_Ticker, InstrumentoFinanciero.Nombre
        ).order_by(
            db.func.sum(Activo.Total_Pesos_Compra).desc()
        )
        
        resultados_ticker = query_ticker.all()
        inversion_total = sum([r.inversion_total or 0 for r in resultados_ticker])
        
        for row_idx, resultado in enumerate(resultados_ticker, 2):
            porcentaje_cartera = 0
            if inversion_total > 0 and resultado.inversion_total:
                porcentaje_cartera = (resultado.inversion_total / inversion_total) * 100
            
            datos_fila = [
                resultado.Nombre_Ticker,
                resultado.instrumento,
                resultado.total_activos,
                resultado.inversion_total or 0,
                round(resultado.precio_promedio or 0, 2),
                resultado.activos_activos,
                resultado.activos_vendidos,
                round(porcentaje_cartera, 2)
            ]
            
            for col_idx, valor in enumerate(datos_fila, 1):
                cell = ws_tickers.cell(row=row_idx, column=col_idx, value=valor)
                aplicar_estilo(cell, crear_estilo_datos())
        
        # Ajustar ancho de columnas para ticker
        for column in ws_tickers.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws_tickers.column_dimensions[column_letter].width = adjusted_width
        
        # === HOJA 4: ANÁLISIS DE PERFORMANCE ===
        ws_performance = wb.create_sheet('Performance')
        
        # Headers para performance
        headers_perf = ['Ticker', 'ROI (%)', 'Ganancia_Pesos', 'Estado', 'Fecha_Ultima_Operacion']
        
        for col, header in enumerate(headers_perf, 1):
            cell = ws_performance.cell(row=1, column=col, value=header)
            aplicar_estilo(cell, crear_estilo_header())
        
        # Consulta de performance
        query_perf = db.session.query(
            Ticker.Nombre_Ticker,
            Activo.Precio_Compra,
            Activo.Precio_Venta,
            Activo.Cantidad_Nominales_Compra,
            Activo.Activo_Estado,
            Activo.Fecha_Hora_Venta
        ).join(
            Activo, Ticker.Id_Ticker == Activo.Id_Ticker
        ).order_by(Ticker.Nombre_Ticker)
        
        resultados_perf = query_perf.all()
        
        for row_idx, (ticker, precio_compra, precio_venta, cantidad, estado, fecha_venta) in enumerate(resultados_perf, 2):
            roi = 0
            ganancia = 0
            
            if precio_venta and precio_compra and cantidad:
                ganancia = (precio_venta - precio_compra) * cantidad
                if precio_compra > 0:
                    roi = ((precio_venta - precio_compra) / precio_compra) * 100
            
            datos_fila = [
                ticker,
                round(roi, 2),
                round(ganancia, 2),
                estado or '',
                fecha_venta.strftime('%d/%m/%Y') if fecha_venta else ''
            ]
            
            for col_idx, valor in enumerate(datos_fila, 1):
                cell = ws_performance.cell(row=row_idx, column=col_idx, value=valor)
                aplicar_estilo(cell, crear_estilo_datos())
        
        # Ajustar ancho de columnas para performance
        for column in ws_performance.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws_performance.column_dimensions[column_letter].width = adjusted_width
        
        # Convertir a bytes
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        
        return excel_bytes.getvalue()
        
    except Exception as e:
        raise Exception(f"Error exportando Excel: {str(e)}")

def crear_respuesta_excel(excel_content, nombre_archivo):
    """
    Crea una respuesta HTTP para descarga de Excel
    
    Args:
        excel_content (bytes): Contenido Excel
        nombre_archivo (str): Nombre del archivo para descarga
        
    Returns:
        Response: Respuesta Flask para descarga
    """
    try:
        response = make_response(excel_content)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response
    except Exception as e:
        raise Exception(f"Error creando respuesta Excel: {str(e)}")

def exportar_resumen_comparativo_excel():
    """
    Exporta resumen comparativo entre diferentes períodos
    
    Returns:
        bytes: Datos del archivo Excel
    """
    try:
        wb = Workbook()
        wb.remove(wb.active)
        
        ws = wb.create_sheet('Comparativo')
        
        # Título
        ws['A1'] = 'ANÁLISIS COMPARATIVO CARTERA'
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal='center')
        ws.merge_cells('A1:D1')
        
        # Headers
        headers = ['Período', 'ROI (%)', 'Valor_Total', 'Cantidad_Activos']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            aplicar_estilo(cell, crear_estilo_header())
        
        # Datos comparativos (ejemplo)
        datos_comparativos = [
            ('Último Mes', 15.2, 1250000, 25),
            ('Últimos 3 Meses', 12.8, 1180000, 23),
            ('Último Año', 18.5, 1100000, 20)
        ]
        
        for row_idx, (periodo, roi, valor, cantidad) in enumerate(datos_comparativos, 4):
            datos_fila = [periodo, roi, valor, cantidad]
            for col_idx, valor_celda in enumerate(datos_fila, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=valor_celda)
                aplicar_estilo(cell, crear_estilo_datos())
        
        # Ajustar columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        
        return excel_bytes.getvalue()
        
    except Exception as e:
        raise Exception(f"Error exportando comparativo Excel: {str(e)}")