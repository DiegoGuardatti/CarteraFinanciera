#!/usr/bin/env python3
"""
Script para importar datos de PDFs de Bull Market a la base de datos.
Extrae operaciones de cuenta corriente bursátil y las guarda en la BD.
"""

import os
import sys
import re
from datetime import datetime
from decimal import Decimal

# Configurar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports condicionales para PDF
try:
    import pdfplumber
    PDF_LIB = 'pdfplumber'
except ImportError:
    PDF_LIB = None
    print("⚠️ No se encontró pdfplumber. Instalar: pip install pdfplumber")

# Imports de Flask/SQLAlchemy (solo si se va a guardar en BD)
def get_db_models():
    """Lazy loading de modelos de BD"""
    from extensions import db
    from modelo import Broker, Comitente, Ticker, Activo, InstrumentoFinanciero
    return db, Broker, Comitente, Ticker, Activo, InstrumentoFinanciero


class ImportadorBullMarket:
    """Importador de datos desde PDFs de cuenta corriente de Bull Market"""
    
    # Tipos de comprobante que representan operaciones bursátiles
    OPERACIONES_COMPRA = {'CPRA', 'CPU$'}
    OPERACIONES_VENTA = {'VTAS', 'VTU$'}
    OPERACIONES_INGRESO = {'COBA', 'CDOA'}  # Créditos cuenta corriente
    OPERACIONES_EGRESO = {'PAGA', 'PU$A'}   # Transferencias MEP salida
    OPERACIONES_DIVIDENDO = {'DIV'}
    OPERACIONES_CAMBIO = {'DEC$', 'CCU$', 'DOLA'}  # Operaciones de cambio
    
    # Tickers conocidos por tipo
    CEDEARS = {'AAPL', 'TSLA', 'AMZN', 'GOOGL', 'MSFT', 'NVDA', 'META', 
               'NFLX', 'KO', 'DIS', 'DISN', 'BBD', 'HMY', 'PAAS', 'INTC', 
               'WMT', 'V', 'VALE', 'MIRG'}
    BONOS = {'AL30', 'AE38', 'AY24', 'GD30', 'AL29', 'AE29'}
    
    def __init__(self):
        self.operaciones = []
        self.transferencias = []
        self.errores = []
        self.stats = {
            'total_lineas': 0,
            'compras': 0,
            'ventas': 0,
            'transferencias_entrada': 0,
            'transferencias_salida': 0,
            'dividendos': 0,
            'ignoradas': 0
        }
    
    def extraer_de_pdf(self, pdf_path):
        """Extrae todas las operaciones de un archivo PDF"""
        if not PDF_LIB:
            print("❌ No hay librería disponible para procesar PDFs")
            return False
        
        if not os.path.exists(pdf_path):
            print(f"❌ Archivo no encontrado: {pdf_path}")
            return False
        
        print(f"📄 Procesando: {os.path.basename(pdf_path)}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for num_pagina, pagina in enumerate(pdf.pages, 1):
                    texto = pagina.extract_text()
                    if texto:
                        self._procesar_texto_pagina(texto, num_pagina, pdf_path)
            
            print(f"   ✅ Páginas procesadas: {len(pdf.pages)}")
            return True
            
        except Exception as e:
            print(f"❌ Error procesando PDF: {e}")
            self.errores.append(f"Error en {pdf_path}: {e}")
            return False
    
    def _procesar_texto_pagina(self, texto, num_pagina, pdf_path):
        """Procesa el texto de una página del PDF"""
        lineas = texto.split('\n')
        
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            
            self.stats['total_lineas'] += 1
            
            # Intentar parsear como operación
            operacion = self._parsear_linea_operacion(linea, pdf_path)
            
            if operacion:
                self.operaciones.append(operacion)
            elif self._es_transferencia(linea):
                transferencia = self._parsear_transferencia(linea, pdf_path)
                if transferencia:
                    self.transferencias.append(transferencia)
    
    def _parsear_linea_operacion(self, linea, pdf_path):
        """
        Parsea una línea del PDF y extrae la operación si es válida.
        
        Formato esperado:
        - Compra: "26/08/19 CPRA 338454 2,562.78 100.0000 AY24"
        - Venta:  "28/10/19 VTAS 503379 2,578.61- 100.0000- ALUA"
        """
        # Patrón para líneas de operación
        # Fecha(8) Tipo(4-5) Comprobante(6-7) Importe Cantidad Ticker
        patron = r'^(\d{2}/\d{2}/\d{2})\s+(\w+)\s+(\d+)\s+([\d.,]+-?)\s+([\d.,]+-?)\s+(\w+)$'
        
        match = re.match(patron, linea)
        if not match:
            return None
        
        fecha_str, tipo_op, comprobante, importe_str, cantidad_str, ticker = match.groups()
        
        # Filtrar tipos que no son operaciones bursátiles
        if tipo_op in self.OPERACIONES_INGRESO:
            self.stats['transferencias_entrada'] += 1
            return None
        if tipo_op in self.OPERACIONES_EGRESO:
            self.stats['transferencias_salida'] += 1
            return None
        if tipo_op in self.OPERACIONES_DIVIDENDO:
            self.stats['dividendos'] += 1
            return None
        if tipo_op in self.OPERACIONES_CAMBIO:
            self.stats['ignoradas'] += 1
            return None
        
        # Verificar si es compra o venta
        es_compra = tipo_op in self.OPERACIONES_COMPRA
        es_venta = tipo_op in self.OPERACIONES_VENTA
        
        if not es_compra and not es_venta:
            self.stats['ignoradas'] += 1
            return None
        
        # Parsear valores numéricos
        try:
            importe = self._parsear_numero(importe_str)
            cantidad = self._parsear_numero(cantidad_str)
            
            if importe <= 0 or cantidad <= 0:
                return None
            
            # Calcular precio unitario
            precio = importe / cantidad
            
            # Parsear fecha
            fecha = self._parsear_fecha(fecha_str)
            if not fecha:
                return None
            
            # Determinar tipo de activo
            tipo_activo = self._determinar_tipo_activo(ticker)
            
            # Crear registro de operación
            operacion = {
                'fecha': fecha,
                'tipo_operacion': 'COMPRA' if es_compra else 'VENTA',
                'ticker': ticker.upper(),
                'tipo_activo': tipo_activo,
                'cantidad': cantidad,
                'precio': round(precio, 4),
                'importe': round(importe, 2),
                'comprobante': comprobante,
                'fuente': os.path.basename(pdf_path)
            }
            
            if es_compra:
                self.stats['compras'] += 1
            else:
                self.stats['ventas'] += 1
            
            return operacion
            
        except Exception as e:
            self.errores.append(f"Error parseando línea: {linea} - {e}")
            return None
    
    def _es_transferencia(self, linea):
        """Verifica si la línea es una transferencia MEP"""
        return 'TRANSFERENCIA VIA MEP' in linea or 'MEP' in linea
    
    def _parsear_transferencia(self, linea, pdf_path):
        """Parsea una transferencia MEP"""
        # Buscar patrón de monto
        patron = r'([\d.,]+)\s+(?:TRANSFERENCIA|MEP)'
        match = re.search(patron, linea)
        if match:
            monto = self._parsear_numero(match.group(1))
            return {
                'tipo': 'TRANSFERENCIA_MEP',
                'monto': monto,
                'descripcion': linea,
                'fuente': os.path.basename(pdf_path)
            }
        return None
    
    def _parsear_numero(self, numero_str):
        """Convierte string numérico a float (formato argentino)"""
        # Remover el signo negativo al final si existe
        negativo = numero_str.endswith('-')
        numero_str = numero_str.rstrip('-')
        
        # Remover separador de miles y convertir coma decimal a punto
        numero_str = numero_str.replace('.', '').replace(',', '.')
        
        try:
            valor = float(numero_str)
            return -valor if negativo else valor
        except ValueError:
            return 0.0
    
    def _parsear_fecha(self, fecha_str):
        """Convierte string de fecha a objeto date"""
        try:
            # Formato DD/MM/YY
            return datetime.strptime(fecha_str, '%d/%m/%y').date()
        except ValueError:
            try:
                # Formato DD/MM/YYYY
                return datetime.strptime(fecha_str, '%d/%m/%Y').date()
            except ValueError:
                return None
    
    def _determinar_tipo_activo(self, ticker):
        """Determina el tipo de activo basado en el ticker"""
        ticker = ticker.upper()
        
        if ticker in self.CEDEARS:
            return 'CEDEAR'
        if ticker in self.BONOS or ticker.startswith(('AL', 'AE', 'GD', 'AY')):
            return 'BONO'
        if ticker.startswith('ON') or 'ON' in ticker:
            return 'OBLIGACION_NEGOCIABLE'
        
        # Por defecto, acción local
        return 'ACCION'
    
    def mostrar_resumen(self):
        """Muestra un resumen de las operaciones extraídas"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE EXTRACCIÓN")
        print("=" * 60)
        print(f"Total líneas procesadas: {self.stats['total_lineas']}")
        print(f"Operaciones de compra:   {self.stats['compras']}")
        print(f"Operaciones de venta:    {self.stats['ventas']}")
        print(f"Transferencias entrada:  {self.stats['transferencias_entrada']}")
        print(f"Transferencias salida:   {self.stats['transferencias_salida']}")
        print(f"Dividendos:              {self.stats['dividendos']}")
        print(f"Líneas ignoradas:        {self.stats['ignoradas']}")
        print(f"Total operaciones:       {len(self.operaciones)}")
        print(f"Total transferencias:    {len(self.transferencias)}")
        
        if self.errores:
            print(f"\n⚠️ Errores encontrados: {len(self.errores)}")
            for error in self.errores[:5]:
                print(f"   - {error}")
        
        # Mostrar tickers únicos
        tickers = set(op['ticker'] for op in self.operaciones)
        print(f"\n📈 Tickers únicos: {len(tickers)}")
        
        # Agrupar por ticker
        from collections import defaultdict
        por_ticker = defaultdict(lambda: {'compras': 0, 'ventas': 0, 'cantidad_comprada': 0, 'cantidad_vendida': 0})
        
        for op in self.operaciones:
            ticker = op['ticker']
            if op['tipo_operacion'] == 'COMPRA':
                por_ticker[ticker]['compras'] += 1
                por_ticker[ticker]['cantidad_comprada'] += op['cantidad']
            else:
                por_ticker[ticker]['ventas'] += 1
                por_ticker[ticker]['cantidad_vendida'] += op['cantidad']
        
        print("\n📋 Detalle por ticker:")
        print("-" * 60)
        for ticker, data in sorted(por_ticker.items()):
            saldo = data['cantidad_comprada'] - data['cantidad_vendida']
            estado = "EN CARTERA" if saldo > 0 else "CERRADO"
            print(f"  {ticker:8} | Compras: {data['compras']:3} | Ventas: {data['ventas']:3} | Saldo: {saldo:10.2f} | {estado}")
    
    def guardar_en_base_datos(self, id_broker, id_comitente, dolar_mep_default=1000):
        """
        Guarda las operaciones extraídas en la base de datos.
        
        Args:
            id_broker: ID del broker Bull Market en la BD
            id_comitente: ID del comitente en la BD
            dolar_mep_default: Valor del dólar MEP por defecto
        """
        if not self.operaciones:
            print("⚠️ No hay operaciones para guardar")
            return 0
        
        db, Broker, Comitente, Ticker, Activo, InstrumentoFinanciero = get_db_models()
        
        # Crear contexto de aplicación Flask
        from app import app
        guardados = 0
        
        with app.app_context():
            # Verificar que existen broker y comitente
            broker = db.session.get(Broker, id_broker)
            if not broker:
                print(f"❌ Broker con ID {id_broker} no encontrado")
                return 0
            
            comitente = db.session.get(Comitente, id_comitente)
            if not comitente:
                print(f"❌ Comitente con ID {id_comitente} no encontrado")
                return 0
            
            print(f"📝 Guardando operaciones para:")
            print(f"   Broker: {broker.Nombre}")
            print(f"   Comitente: {comitente.Titular}")
            
            # Agrupar operaciones por ticker para crear tickers primero
            tickers_a_crear = set(op['ticker'] for op in self.operaciones)
            
            # Crear tickers si no existen
            for ticker_nombre in tickers_a_crear:
                ticker_existente = Ticker.query.filter_by(Nombre_Ticker=ticker_nombre).first()
                if not ticker_existente:
                    # Buscar o crear instrumento financiero
                    op_ticker = next(op for op in self.operaciones if op['ticker'] == ticker_nombre)
                    tipo_activo = op_ticker['tipo_activo']
                    
                    # Buscar instrumento
                    instrumento = InstrumentoFinanciero.query.filter_by(Nombre=tipo_activo).first()
                    if not instrumento:
                        instrumento = InstrumentoFinanciero(Nombre=tipo_activo)
                        db.session.add(instrumento)
                        db.session.flush()
                    
                    # Crear ticker
                    nuevo_ticker = Ticker(
                        Nombre_Ticker=ticker_nombre,
                        Descripcion=f"{tipo_activo} - {ticker_nombre}",
                        Id_InstrumentoFinanciero=instrumento.Id_InstrumentoFinanciero
                    )
                    db.session.add(nuevo_ticker)
                    print(f"   ✅ Ticker creado: {ticker_nombre}")
            
            db.session.commit()
            
            # Procesar operaciones agrupadas por ticker
            # Primero procesar compras, luego ventas
            compras = [op for op in self.operaciones if op['tipo_operacion'] == 'COMPRA']
            ventas = [op for op in self.operaciones if op['tipo_operacion'] == 'VENTA']
            
            # Diccionario para rastrear posiciones abiertas (ticker -> lista de activos)
            posiciones_abiertas = {}
            
            # Procesar compras
            for op in sorted(compras, key=lambda x: x['fecha']):
                ticker = Ticker.query.filter_by(Nombre_Ticker=op['ticker']).first()
                if not ticker:
                    continue
                
                activo = Activo(
                    Id_Broker=id_broker,
                    Id_Comitente=id_comitente,
                    Id_Ticker=ticker.Id_Ticker,
                    Precio_Dolar_MEP_Compra=dolar_mep_default,
                    Fecha_Hora_Compra=datetime.combine(op['fecha'], datetime.min.time()),
                    Precio_Compra=op['precio'],
                    Cantidad_Nominales_Compra=op['cantidad'],
                    Comision_Broker=0,  # No tenemos este dato del PDF
                    Total_Pesos_Compra=op['importe'],
                    Total_Dolares_Compra=round(op['importe'] / dolar_mep_default, 2),
                    Activo_Estado='EN_CARTERA'
                )
                db.session.add(activo)
                db.session.flush()  # Para obtener el ID
                
                # Agregar a posiciones abiertas
                if op['ticker'] not in posiciones_abiertas:
                    posiciones_abiertas[op['ticker']] = []
                posiciones_abiertas[op['ticker']].append(activo)
                
                guardados += 1
            
            db.session.commit()
            
            # Procesar ventas (actualizar activos existentes)
            ventas_procesadas = 0
            for op in sorted(ventas, key=lambda x: x['fecha']):
                ticker_nombre = op['ticker']
                
                if ticker_nombre not in posiciones_abiertas or not posiciones_abiertas[ticker_nombre]:
                    print(f"   ⚠️ Venta sin compra previa: {ticker_nombre} - {op['fecha']}")
                    continue
                
                # Buscar posición abierta (FIFO)
                activo = posiciones_abiertas[ticker_nombre][0]
                
                # Actualizar con datos de venta
                activo.Fecha_Hora_Venta = datetime.combine(op['fecha'], datetime.min.time())
                activo.Precio_Venta = op['precio']
                activo.Cantidad_Nominales_Venta = op['cantidad']
                activo.Total_Pesos_Venta = op['importe']
                activo.Total_Dolares_Venta = round(op['importe'] / dolar_mep_default, 2)
                activo.Precio_Dolar_MEP_Venta = dolar_mep_default
                activo.Activo_Estado = 'VENDIDO'
                
                # Remover de posiciones abiertas si se vendió todo
                if op['cantidad'] >= activo.Cantidad_Nominales_Compra:
                    posiciones_abiertas[ticker_nombre].pop(0)
                
                ventas_procesadas += 1
                guardados += 1
            
            db.session.commit()
            
            print(f"\n✅ Operaciones guardadas: {guardados}")
            print(f"   Compras procesadas: {len(compras)}")
            print(f"   Ventas procesadas: {ventas_procesadas}")
        
        return guardados


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Importar datos de PDFs de Bull Market')
    parser.add_argument('--pdf', nargs='+', help='Archivos PDF a procesar')
    parser.add_argument('--guardar', action='store_true', help='Guardar en base de datos')
    parser.add_argument('--broker-id', type=int, default=1, help='ID del broker')
    parser.add_argument('--comitente-id', type=int, default=1, help='ID del comitente')
    parser.add_argument('--dolar-mep', type=float, default=1000, help='Dólar MEP por defecto')
    
    args = parser.parse_args()
    
    print("🚀 Importador de datos Bull Market")
    print("=" * 60)
    
    importador = ImportadorBullMarket()
    
    # Archivos PDF por defecto
    pdfs = args.pdf or [
        "Movimientos_bull_market_2019_2022.pdf",
        "Movimientos_bull_market_2023_2024.pdf"
    ]
    
    # Procesar PDFs
    for pdf in pdfs:
        if os.path.exists(pdf):
            importador.extraer_de_pdf(pdf)
        else:
            print(f"⚠️ Archivo no encontrado: {pdf}")
    
    # Mostrar resumen
    importador.mostrar_resumen()
    
    # Guardar en BD si se solicita
    if args.guardar:
        print("\n" + "=" * 60)
        print("💾 GUARDANDO EN BASE DE DATOS")
        print("=" * 60)
        importador.guardar_en_base_datos(
            id_broker=args.broker_id,
            id_comitente=args.comitente_id,
            dolar_mep_default=args.dolar_mep
        )
    else:
        print("\n💡 Para guardar en la base de datos, use: --guardar --broker-id X --comitente-id Y")


if __name__ == "__main__":
    main()
