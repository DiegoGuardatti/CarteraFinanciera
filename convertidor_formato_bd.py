"""
Convertidor de Transacciones Procesadas a Formato Base de Datos
Convierte las transacciones extraídas al formato requerido para la carga en la BBDD
"""

import csv
import re
from datetime import datetime

def convertir_a_formato_bd(transacciones_file, output_file):
    """
    Convierte transacciones procesadas al formato de base de datos
    """
    transacciones_formato_bd = []
    
    print(f"🔄 Convirtiendo {transacciones_file} a formato de base de datos...")
    
    # Configuración del comitente (extraer de los archivos originales)
    nombre_comitente = "38563 Guardatti Fernández"
    broker_nombre = "Banco Guardianes"  # Nombre genérico ya que no está claro en el archivo
    
    with open(transacciones_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Convertir fecha de DD/MM/YYYY a YYYY-MM-DD
            fecha_original = row['fecha']
            fecha_parts = fecha_original.split('/')
            fecha_db = f"{fecha_parts[2]}-{fecha_parts[1]}-{fecha_parts[0]}"
            
            # Datos básicos de la transacción
            ticker = row['ticker'].upper()
            cantidad = float(row['cantidad'])
            precio_unitario = float(row['precio_unitario'])
            
            # Calcular totales
            total_pesos_compra = float(row['importe_total'])
            precio_dolar_mep_compra = 100.0  # Valor aproximado, se puede ajustar
            total_dolares_compra = total_pesos_compra / precio_dolar_mep_compra
            
            # Para compras (no encontramos ventas en el primer análisis)
            transaccion_bd = {
                'Fecha_Compra': fecha_db,
                'Precio_Compra': precio_unitario,
                'Cantidad_Compra': cantidad,
                'Comision_Broker': 0.0,  # No está en los datos originales
                'Precio_Dolar_MEP_Compra': precio_dolar_mep_compra,
                'Fecha_Venta': '',  # Vacío porque no tenemos datos de venta
                'Precio_Venta': '',
                'Cantidad_Venta': '',
                'Total_Pesos_Venta': '',
                'Precio_Dolar_MEP_Venta': '',
                'Nombre_Broker': broker_nombre,
                'Nombre_Comitente': nombre_comitente,
                'Nombre_Ticker': ticker,
                'Descripcion_Ticker': f"{ticker} - Instrumento financiero",
                'Nombre_Instrumento': 'Acciones'
            }
            
            transacciones_formato_bd.append(transaccion_bd)
    
    # Guardar en el formato requerido
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Fecha_Compra', 'Precio_Compra', 'Cantidad_Compra', 'Comision_Broker',
            'Precio_Dolar_MEP_Compra', 'Fecha_Venta', 'Precio_Venta', 'Cantidad_Venta',
            'Total_Pesos_Venta', 'Precio_Dolar_MEP_Venta', 'Nombre_Broker', 
            'Nombre_Comitente', 'Nombre_Ticker', 'Descripcion_Ticker', 'Nombre_Instrumento'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transacciones_formato_bd)
    
    print(f"✅ Conversión completada. {len(transacciones_formato_bd)} transacciones guardadas en {output_file}")
    return len(transacciones_formato_bd)

def mejorar_parser_para_ventas():
    """
    Mejorar el parser original para detectar ventas VTAS correctamente
    """
    print("🔧 Mejorando parser para detectar ventas VTAS...")
    
    # Leer archivo original y buscar patrones VTAS
    try:
        with open("Consulta Cuenta Corriente Pesos y Dolares1.csv", 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        ventas_encontradas = []
        
        for i, line in enumerate(lines[5:], 6):  # Empezar desde línea 6
            if ',VTAS,' in line:
                parts = line.strip().split(',')
                if len(parts) >= 7:
                    fecha_str = parts[0].strip()
                    tipo_op = parts[1].strip()
                    numero_op = parts[2].strip()
                    importe_str = parts[3].strip()
                    descripcion = parts[6].strip()
                    
                    # Limpiar importe
                    if importe_str:
                        importe_limpio = importe_str.replace('"', '').replace(',', '').replace('-', '').strip()
                        if importe_limpio and importe_limpio != '':
                            try:
                                importe = float(importe_limpio)
                                
                                # Buscar ticker y cantidad en descripción
                                patron = r'(\d+\.?\d*)\s+([A-Z0-9]+)'
                                match = re.search(patron, descripcion)
                                
                                if match:
                                    cantidad = float(match.group(1))
                                    ticker = match.group(2).upper()
                                    precio_unitario = abs(importe) / cantidad if cantidad > 0 else 0
                                    
                                    # Convertir fecha
                                    fecha_parts = fecha_str.split('/')
                                    fecha_db = f"{fecha_parts[2]}-{fecha_parts[1]}-{fecha_parts[0]}"
                                    
                                    venta = {
                                        'tipo': 'VENTA',
                                        'fecha': fecha_db,
                                        'ticker': ticker,
                                        'precio_unitario': precio_unitario,
                                        'cantidad': cantidad,
                                        'importe_total': abs(importe),
                                        'numero_op': numero_op
                                    }
                                    ventas_encontradas.append(venta)
                                    
                            except:
                                continue
        
        print(f"📊 Se encontraron {len(ventas_encontradas)} ventas adicionales:")
        for venta in ventas_encontradas[:5]:  # Mostrar primeras 5
            print(f"  {venta['fecha']} | {venta['ticker']} | {venta['cantidad']} x ${venta['precio_unitario']:.2f}")
        
        return ventas_encontradas
        
    except Exception as e:
        print(f"❌ Error mejorando parser: {str(e)}")
        return []

if __name__ == "__main__":
    print("🚀 Iniciando conversión a formato de base de datos...")
    
    # Mejorar parser para ventas
    ventas = mejorar_parser_para_ventas()
    
    # Convertir compras al formato BD
    total_transacciones = convertir_a_formato_bd(
        "transacciones_procesadas.csv", 
        "movimientos_cartera_final.csv"
    )
    
    print(f"\n🎯 RESUMEN FINAL:")
    print(f"💰 Total transacciones: {total_transacciones}")
    print(f"📈 Compras procesadas: {total_transacciones}")
    print(f"📉 Ventas detectadas: {len(ventas)}")
    print(f"💾 Archivo final: movimientos_cartera_final.csv")
    
    print(f"\n📋 PRÓXIMOS PASOS:")
    print(f"1. Revisar el archivo 'movimientos_cartera_final.csv'")
    print(f"2. Ejecutar app_simple.py para cargar en la base de datos")
    print(f"3. Verificar dashboard con los datos cargados")
