#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de exportación CSV para Cartera Financiera
Genera reportes en formato CSV con encoding UTF-8
"""

import csv
import io
import os
from datetime import datetime
from flask import make_response
from modelo import db, Activo, Ticker, Broker, Comitente, InstrumentoFinanciero

def exportar_activos_csv(filtros=None):
    """
    Exporta activos a formato CSV
    
    Args:
        filtros (dict): Filtros para aplicar en la consulta
        
    Returns:
        str: CSV en formato string
    """
    try:
        # Construir consulta base
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
        
        # Aplicar filtros si existen
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
        
        # Crear buffer de memoria para el CSV
        output = io.StringIO()
        
        # Configurar el writer CSV con encoding UTF-8
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Escribir headers
        headers = [
            'ID_Activo',
            'Broker',
            'Comitente',
            'Ticker',
            'Instrumento_Financiero',
            'Fecha_Compra',
            'Precio_Compra',
            'Cantidad_Compra',
            'Total_Pesos_Compra',
            'Total_Dolares_Compra',
            'Fecha_Venta',
            'Precio_Venta',
            'Cantidad_Venta',
            'Total_Pesos_Venta',
            'Total_Dolares_Venta',
            'Estado',
            'Ganancia_Pesos',
            'Porcentaje_Pesos',
            'ROI'
        ]
        writer.writerow(headers)
        
        # Escribir datos
        for activo, ticker, broker, comitente, instrumento in resultados:
            # Calcular métricas
            ganancia_pesos = 0
            porcentaje_pesos = 0
            roi = 0
            
            if activo.Precio_Venta and activo.Cantidad_Nominales_Venta:
                ganancia_pesos = (activo.Precio_Venta - activo.Precio_Compra) * activo.Cantidad_Nominales_Venta
                if activo.Precio_Compra > 0:
                    porcentaje_pesos = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
                    roi = ((activo.Precio_Venta - activo.Precio_Compra) / activo.Precio_Compra) * 100
            
            row = [
                activo.Id_Activo,
                broker.Nombre if broker else '',
                comitente.Titular if comitente else '',
                ticker.Nombre_Ticker if ticker else '',
                instrumento.Nombre if instrumento else '',
                activo.Fecha_Hora_Compra.strftime('%Y-%m-%d %H:%M:%S') if activo.Fecha_Hora_Compra else '',
                round(activo.Precio_Compra, 2) if activo.Precio_Compra else '',
                activo.Cantidad_Nominales_Compra,
                round(activo.Total_Pesos_Compra, 2) if activo.Total_Pesos_Compra else '',
                round(activo.Total_Dolares_Compra, 2) if activo.Total_Dolares_Compra else '',
                activo.Fecha_Hora_Venta.strftime('%Y-%m-%d %H:%M:%S') if activo.Fecha_Hora_Venta else '',
                round(activo.Precio_Venta, 2) if activo.Precio_Venta else '',
                activo.Cantidad_Nominales_Venta if activo.Cantidad_Nominales_Venta else '',
                round(activo.Total_Pesos_Venta, 2) if activo.Total_Pesos_Venta else '',
                round(activo.Total_Dolares_Venta, 2) if activo.Total_Dolares_Venta else '',
                activo.Activo_Estado if activo.Activo_Estado else '',
                round(ganancia_pesos, 2),
                round(porcentaje_pesos, 2),
                round(roi, 2)
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
        
    except Exception as e:
        raise Exception(f"Error exportando CSV: {str(e)}")

def exportar_resumen_cartera_csv():
    """
    Exporta resumen de la cartera completa
    
    Returns:
        str: CSV en formato string
    """
    try:
        # Consulta para resumen por ticker
        query = db.session.query(
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
        
        resultados = query.all()
        
        # Crear buffer de memoria
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Headers
        headers = [
            'Ticker',
            'Instrumento_Financiero',
            'Total_Activos',
            'Inversion_Total_Pesos',
            'Precio_Promedio_Compra',
            'Activos_Activos',
            'Activos_Vendidos',
            'Porcentaje_Cartera'
        ]
        writer.writerow(headers)
        
        # Calcular total de inversión para porcentajes
        inversion_total_cartera = sum([r.inversion_total or 0 for r in resultados])
        
        # Escribir datos
        for resultado in resultados:
            porcentaje_cartera = 0
            if inversion_total_cartera > 0 and resultado.inversion_total:
                porcentaje_cartera = (resultado.inversion_total / inversion_total_cartera) * 100
            
            row = [
                resultado.Nombre_Ticker,
                resultado.instrumento,
                resultado.total_activos,
                round(resultado.inversion_total or 0, 2),
                round(resultado.precio_promedio or 0, 2),
                resultado.activos_activos,
                resultado.activos_vendidos,
                round(porcentaje_cartera, 2)
            ]
            writer.writerow(row)
        
        # Fila de totales
        writer.writerow([
            'TOTALES',
            '',
            sum([r.total_activos for r in resultados]),
            round(inversion_total_cartera, 2),
            '',
            sum([r.activos_activos for r in resultados]),
            sum([r.activos_vendidos for r in resultados]),
            '100.00'
        ])
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
        
    except Exception as e:
        raise Exception(f"Error exportando resumen CSV: {str(e)}")

def crear_respuesta_csv(csv_content, nombre_archivo):
    """
    Crea una respuesta HTTP para descarga de CSV
    
    Args:
        csv_content (str): Contenido CSV
        nombre_archivo (str): Nombre del archivo para descarga
        
    Returns:
        Response: Respuesta Flask para descarga
    """
    try:
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response
    except Exception as e:
        raise Exception(f"Error creando respuesta CSV: {str(e)}")

def exportar_con_metadatos(csv_content, tipo_reporte, filtros=None):
    """
    Exporta CSV con metadatos adicionales
    
    Args:
        csv_content (str): Contenido CSV base
        tipo_reporte (str): Tipo de reporte (activos, resumen)
        filtros (dict): Filtros aplicados
        
    Returns:
        str: CSV con metadatos
    """
    try:
        # Crear buffer de memoria
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Escribir metadatos
        writer.writerow(['=== REPORTE CARTERA FINANCIERA ==='])
        writer.writerow(['Tipo', tipo_reporte])
        writer.writerow(['Fecha_Generacion', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        if filtros:
            writer.writerow(['Filtros_Aplicados'])
            for key, value in filtros.items():
                writer.writerow([f'{key}: {value}'])
        
        writer.writerow([''])  # Línea en blanco
        
        # Agregar contenido CSV original
        csv_lines = csv_content.strip().split('\n')
        for line in csv_lines:
            writer.writerow(line.split(','))
        
        resultado = output.getvalue()
        output.close()
        
        return resultado
        
    except Exception as e:
        raise Exception(f"Error exportando con metadatos: {str(e)}")