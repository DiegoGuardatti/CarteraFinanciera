"""
Procesador de Archivos de Cuenta Corriente
Convierte archivos CSV de movimientos de cuenta corriente al formato de la base de datos
"""

import csv
import re
from datetime import datetime

def procesar_archivo_cuenta_corriente(archivo_path):
    """
    Procesa un archivo de cuenta corriente y extrae transacciones de compra/venta
    """
    transacciones = []
    
    with open(archivo_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Encontrar la línea donde empiezan los datos
    data_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('F.Liquid,Cpbt,N.Cpbt'):
            data_start = i + 1
            break
    
    print(f"📊 Procesando archivo: {archivo_path}")
    print(f"📍 Datos empiezan en línea: {data_start + 1}")
    
    for line_num in range(data_start, len(lines)):
        line = lines[line_num].strip()
        
        # Saltar líneas vacías o de totales
        if not line or line.startswith(',Total') or line.startswith(',,'):
            continue
            
        # Separar por comas
        parts = line.split(',')
        
        if len(parts) < 7:
            continue
            
        fecha_str = parts[0].strip()
        tipo_op = parts[1].strip()
        numero_op = parts[2].strip()
        importe_str = parts[3].strip()
        dolares_str = parts[4].strip()
        moneda = parts[5].strip()
        descripcion = parts[6].strip()
        
        # Procesar solo compras y ventas
        if tipo_op not in ['CPRA', 'VTAS']:
            continue
            
        # Limpiar y convertir fecha (formato DD/MM/YY)
        try:
            fecha_parts = fecha_str.split('/')
            if len(fecha_parts) == 3:
                dia, mes, año = fecha_parts
                # Asumir año 20XX para años de 2 dígitos
                if len(año) == 2:
                    año = '20' + año
                fecha_convertida = f"{dia}/{mes}/{año}"
            else:
                continue
        except:
            continue
            
        # Limpiar importe (remover comas, guiones, etc.)
        if importe_str:
            importe_limpio = importe_str.replace('"', '').replace(',', '').replace('-', '').strip()
            if importe_limpio and importe_limpio != '':
                try:
                    importe = float(importe_limpio)
                except:
                    continue
            else:
                continue
        else:
            continue
            
        # Procesar descripción para extraer ticker y cantidad
        ticker = ''
        cantidad = 0
        descripcion_limpia = descripcion
        
        # Buscar patrón: "cantidad.0000 TICKER" o similar
        patron = r'(\d+\.?\d*)\s+([A-Z0-9]+)'
        match = re.search(patron, descripcion)
        
        if match:
            cantidad = float(match.group(1))
            ticker = match.group(2).upper()
            descripcion_limpia = descripcion.replace(match.group(0), '').strip()
        
        # Solo procesar si tenemos ticker y cantidad válidos
        if not ticker or cantidad <= 0:
            continue
            
        # Determinar tipo de transacción
        if tipo_op == 'CPRA':
            # COMPRA
            precio_unitario = importe / cantidad if cantidad > 0 else 0
            transaccion = {
                'tipo': 'COMPRA',
                'fecha': fecha_convertida,
                'ticker': ticker,
                'descripcion': descripcion_limpia,
                'precio_unitario': precio_unitario,
                'cantidad': cantidad,
                'importe_total': importe,
                'moneda': moneda if moneda else 'ARS',
                'numero_op': numero_op
            }
            transacciones.append(transaccion)
            
        elif tipo_op == 'VTAS':
            # VENTA
            precio_unitario = importe / cantidad if cantidad > 0 else 0
            transaccion = {
                'tipo': 'VENTA',
                'fecha': fecha_convertida,
                'ticker': ticker,
                'descripcion': descripcion_limpia,
                'precio_unitario': precio_unitario,
                'cantidad': cantidad,
                'importe_total': importe,
                'moneda': moneda if moneda else 'ARS',
                'numero_op': numero_op
            }
            transacciones.append(transaccion)
    
    return transacciones

def procesar_archivos_multiples(lista_archivos):
    """
    Procesa múltiples archivos y combina las transacciones
    """
    todas_transacciones = []
    
    for archivo in lista_archivos:
        try:
            transacciones = procesar_archivo_cuenta_corriente(archivo)
            todas_transacciones.extend(transacciones)
            print(f"✅ {archivo}: {len(transacciones)} transacciones procesadas")
        except Exception as e:
            print(f"❌ Error procesando {archivo}: {str(e)}")
    
    return todas_transacciones

def generar_reporte_transacciones(transacciones):
    """
    Genera un reporte de las transacciones procesadas
    """
    print("\n" + "="*80)
    print("📈 REPORTE DE TRANSACCIONES PROCESADAS")
    print("="*80)
    
    compras = [t for t in transacciones if t['tipo'] == 'COMPRA']
    ventas = [t for t in transacciones if t['tipo'] == 'VENTA']
    
    print(f"💰 COMPRAS: {len(compras)} transacciones")
    print(f"💸 VENTAS: {len(ventas)} transacciones")
    print(f"📊 TOTAL: {len(transacciones)} transacciones")
    
    # Top tickers por cantidad de operaciones
    tickers = {}
    for t in transacciones:
        ticker = t['ticker']
        if ticker not in tickers:
            tickers[ticker] = {'compras': 0, 'ventas': 0, 'total': 0}
        tickers[ticker][t['tipo'].lower() + 's'] += 1
        tickers[ticker]['total'] += 1
    
    print(f"\n📈 TOP 10 TICKERS POR ACTIVIDAD:")
    tickers_ordenados = sorted(tickers.items(), key=lambda x: x[1]['total'], reverse=True)
    
    for ticker, stats in tickers_ordenados[:10]:
        print(f"  {ticker:8} | C:{stats['compras']:3} V:{stats['ventas']:3} T:{stats['total']:3}")
    
    # Primeras transacciones como ejemplo
    print(f"\n📝 PRIMERAS 5 COMPRAS:")
    for t in compras[:5]:
        print(f"  {t['fecha']} | {t['ticker']:8} | {t['cantidad']:8.2f} x ${t['precio_unitario']:8.2f} = ${t['importe_total']:10.2f}")
    
    print(f"\n📝 PRIMERAS 5 VENTAS:")
    for t in ventas[:5]:
        print(f"  {t['fecha']} | {t['ticker']:8} | {t['cantidad']:8.2f} x ${t['precio_unitario']:8.2f} = ${t['importe_total']:10.2f}")

if __name__ == "__main__":
    # Procesar los archivos proporcionados
    archivos = [
        "Consulta Cuenta Corriente Pesos y Dolares1.csv",
        "Consulta Cuenta Corriente Pesos y Dolares.csv"
    ]
    
    print("🚀 Iniciando procesamiento de archivos de cuenta corriente...")
    
    transacciones = procesar_archivos_multiples(archivos)
    
    if transacciones:
        generar_reporte_transacciones(transacciones)
        
        # Guardar en formato CSV para revisión
        with open("transacciones_procesadas.csv", 'w', newline='', encoding='utf-8') as csvfile:
            if transacciones:
                fieldnames = transacciones[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(transacciones)
        print(f"\n💾 Transacciones guardadas en: transacciones_procesadas.csv")
        
    else:
        print("❌ No se encontraron transacciones válidas")
