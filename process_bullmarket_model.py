#!/usr/bin/env python3
"""
Script para procesar PDF de Bull Market y cargar datos según modelo Flask-SQLAlchemy
Autor: Sistema de Cartera Financiera
Fecha: 2024

Este script procesa PDFs de Bull Market y los carga en la base de datos
siguiendo el modelo de Flask-SQLAlchemy definido (Broker, Comitente, Ticker, Activo)
"""

import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

import pymysql
import pdfplumber
from pymysql.cursors import DictCursor


class BullMarketPDFProcessor:
    """Procesa PDFs de Bull Market y carga datos en base de datos MySQL"""
    
    # Mapeo de tipos de operación de Bull Market
    TIPOS_COMPRA = ['CPRA', 'CPU$', 'LIPA']
    TIPOS_VENTA = ['VTAS', 'VTU$']
    
    # Tipos de instrumentos financieros
    INSTRUMENTOS = {
        'ACCION': ['ALUA', 'GGAL', 'BMA', 'TECO2', 'TGSU2', 'TXAR', 'COME', 
                   'CELU', 'CEPU', 'GFVA', 'BHIP', 'CECO2', 'BOLT', 'GCDI',
                   'TRAN', 'CRES', 'IRSA', 'HARG', 'PAMP', 'CADO', 'SUPV', 'VALO'],
        'BONO': ['AY24', 'AL30', 'GN34O'],
        'CEDEAR': ['BBD', 'KO', 'INTC', 'WMT', 'DISN', 'V', 'HMY', 'PAAS', 'MIRG'],
        'FCI': ['CRCEO', 'MTCFO', 'IRC1O', 'IRCFO', 'YMCHO', 'PQCDO']
    }
    
    def __init__(self, db_config: Dict[str, str], broker_nombre: str = "Bull Market Brokers"):
        """
        Inicializa el procesador
        
        Args:
            db_config: Diccionario con configuración de base de datos
            broker_nombre: Nombre del broker (por defecto Bull Market)
        """
        self.db_config = db_config
        self.broker_nombre = broker_nombre
        self.connection = None
        
        # Cachés para evitar consultas repetidas
        self.broker_id = None
        self.comitente_cache = {}
        self.ticker_cache = {}
        self.instrumento_cache = {}
        
        # Tracking de operaciones para agrupar compra/venta
        self.operaciones_pendientes = {}  # ticker -> lista de operaciones de compra
        
    def connect_db(self):
        """Establece conexión con la base de datos"""
        try:
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            print("✓ Conexión a base de datos establecida")
        except Exception as e:
            print(f"✗ Error conectando a base de datos: {e}")
            raise
            
    def close_db(self):
        """Cierra la conexión con la base de datos"""
        if self.connection:
            self.connection.close()
            print("✓ Conexión cerrada")
            
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Convierte string de fecha DD/MM/YY a datetime"""
        try:
            return datetime.strptime(date_str, '%d/%m/%y')
        except ValueError:
            return None
            
    def parse_amount(self, amount_str: str) -> float:
        """Convierte string de monto a float"""
        try:
            clean_str = amount_str.replace('.', '').replace(',', '.')
            is_negative = clean_str.endswith('-')
            clean_str = clean_str.replace('-', '')
            value = float(clean_str)
            return -value if is_negative else value
        except (ValueError, InvalidOperation):
            return 0.0
            
    def extract_comitente_info(self, text: str) -> Optional[Tuple[str, str]]:
        """Extrae número y nombre de comitente del texto"""
        pattern = r'Comitente\s+(\d+)\s+([\w\s]+?)(?=\n|Desde)'
        match = re.search(pattern, text)
        
        if match:
            numero = match.group(1)
            nombre = match.group(2).strip()
            return (numero, nombre)
        return None
        
    def get_or_create_broker(self) -> int:
        """Obtiene o crea el broker Bull Market"""
        if self.broker_id:
            return self.broker_id
            
        cursor = self.connection.cursor()
        
        # Buscar broker existente
        cursor.execute("SELECT Id_Broker FROM broker WHERE Nombre = %s", (self.broker_nombre,))
        result = cursor.fetchone()
        
        if result:
            self.broker_id = result['Id_Broker']
        else:
            # Crear nuevo broker
            cursor.execute(
                "INSERT INTO broker (Nombre, Comision, Asesor) VALUES (%s, %s, %s)",
                (self.broker_nombre, 0.0, 'Sin Asesor')
            )
            self.connection.commit()
            self.broker_id = cursor.lastrowid
            
        return self.broker_id
        
    def get_or_create_comitente(self, numero: str, titular: str) -> int:
        """Obtiene o crea comitente"""
        key = f"{numero}_{self.broker_id}"
        if key in self.comitente_cache:
            return self.comitente_cache[key]
            
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO comitente (Titular, Numero, Id_Broker) VALUES (%s, %s, %s)",
                (titular, int(numero), self.broker_id)
            )
            self.connection.commit()
            comitente_id = cursor.lastrowid
        except pymysql.IntegrityError:
            cursor.execute(
                "SELECT Id_Comitente FROM comitente WHERE Numero = %s AND Id_Broker = %s",
                (int(numero), self.broker_id)
            )
            result = cursor.fetchone()
            comitente_id = result['Id_Comitente']
            
        self.comitente_cache[key] = comitente_id
        return comitente_id
        
    def get_tipo_instrumento(self, ticker: str) -> str:
        """Determina el tipo de instrumento financiero basado en el ticker"""
        ticker_upper = ticker.upper()
        
        for tipo, tickers in self.INSTRUMENTOS.items():
            if ticker_upper in tickers:
                return tipo
                
        return 'Otro'
        
    def get_or_create_instrumento(self, nombre: str) -> int:
        """Obtiene o crea instrumento financiero"""
        if nombre in self.instrumento_cache:
            return self.instrumento_cache[nombre]
            
        cursor = self.connection.cursor()
        
        cursor.execute(
            "SELECT Id_InstrumentoFinanciero FROM instrumento_financiero WHERE Nombre = %s",
            (nombre,)
        )
        result = cursor.fetchone()
        
        if result:
            instrumento_id = result['Id_InstrumentoFinanciero']
        else:
            cursor.execute(
                "INSERT INTO instrumento_financiero (Nombre) VALUES (%s)",
                (nombre,)
            )
            self.connection.commit()
            instrumento_id = cursor.lastrowid
            
        self.instrumento_cache[nombre] = instrumento_id
        return instrumento_id
        
    def get_or_create_ticker(self, ticker_nombre: str, descripcion: str = None) -> int:
        """Obtiene o crea ticker"""
        if ticker_nombre in self.ticker_cache:
            return self.ticker_cache[ticker_nombre]
            
        cursor = self.connection.cursor()
        
        # Buscar ticker existente
        cursor.execute(
            "SELECT Id_Ticker FROM ticker WHERE Nombre_Ticker = %s",
            (ticker_nombre,)
        )
        result = cursor.fetchone()
        
        if result:
            ticker_id = result['Id_Ticker']
        else:
            # Crear nuevo ticker
            tipo_instrumento = self.get_tipo_instrumento(ticker_nombre)
            instrumento_id = self.get_or_create_instrumento(tipo_instrumento)
            
            if not descripcion:
                descripcion = ticker_nombre
                
            cursor.execute(
                "INSERT INTO ticker (Nombre_Ticker, Descripcion, Id_InstrumentoFinanciero) VALUES (%s, %s, %s)",
                (ticker_nombre, descripcion, instrumento_id)
            )
            self.connection.commit()
            ticker_id = cursor.lastrowid
            
        self.ticker_cache[ticker_nombre] = ticker_id
        return ticker_id
        
    def parse_row(self, row: Dict) -> Optional[Dict]:
        """Parsea una fila de la tabla del PDF"""
        fecha = self.parse_date(row.get('F.Liquid', ''))
        if not fecha:
            return None
            
        tipo_op = row.get('Cpbt', '').strip()
        if not tipo_op:
            return None
            
        # Solo procesar compras y ventas
        if tipo_op not in self.TIPOS_COMPRA and tipo_op not in self.TIPOS_VENTA:
            return None
            
        # Parsear importes
        importe_pesos = abs(self.parse_amount(row.get('Importe', '0')))
        importe_dolares = abs(self.parse_amount(row.get('Dolares', '0')))
        
        # Extraer referencia
        referencia = row.get('Ref./Cantidad', '').strip()
        
        # Extraer ticker y cantidad
        ticker = None
        cantidad = None
        
        # Patrones: "100.0000 AY24", "73.9300- RIGAH"
        ref_pattern = r'([\d.]+)[\s-]*([\w\d]+)'
        ref_match = re.search(ref_pattern, referencia)
        
        if ref_match:
            cantidad_str = ref_match.group(1)
            ticker = ref_match.group(2)
            cantidad = abs(self.parse_amount(cantidad_str))
        
        # Si no hay ticker, no es una operación de activos
        if not ticker:
            return None
            
        return {
            'fecha': fecha,
            'tipo_operacion': tipo_op,
            'ticker': ticker,
            'cantidad': cantidad,
            'importe_pesos': importe_pesos,
            'importe_dolares': importe_dolares,
            'referencia': referencia
        }
        
    def calcular_precio_unitario(self, importe_pesos: float, cantidad: float) -> float:
        """Calcula el precio unitario"""
        if cantidad > 0:
            return importe_pesos / cantidad
        return 0.0
        
    def calcular_dolar_mep(self, importe_pesos: float, importe_dolares: float) -> float:
        """Calcula el tipo de cambio dólar MEP"""
        if importe_dolares > 0:
            return importe_pesos / importe_dolares
        return 0.0
        
    def insert_compra(self, comitente_id: int, operacion: Dict):
        """Inserta una operación de compra"""
        cursor = self.connection.cursor()
        
        ticker_id = self.get_or_create_ticker(operacion['ticker'])
        
        # Calcular valores
        precio_compra = self.calcular_precio_unitario(operacion['importe_pesos'], operacion['cantidad'])
        dolar_mep = self.calcular_dolar_mep(operacion['importe_pesos'], operacion['importe_dolares'])
        
        # Estimar comisión (ejemplo: 0.6% del total)
        comision = operacion['importe_pesos'] * 0.006
        
        try:
            cursor.execute("""
                INSERT INTO activo (
                    Id_Broker, Id_Comitente, Id_Ticker,
                    Fecha_Hora_Compra, Precio_Compra, Cantidad_Nominales_Compra,
                    Precio_Dolar_MEP_Compra, Comision_Broker,
                    Total_Pesos_Compra, Total_Dolares_Compra,
                    Activo_Estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.broker_id,
                comitente_id,
                ticker_id,
                operacion['fecha'],
                precio_compra,
                operacion['cantidad'],
                dolar_mep if dolar_mep > 0 else 1.0,
                comision,
                operacion['importe_pesos'],
                operacion['importe_dolares'],
                'EN_CARTERA'
            ))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error insertando compra: {e}")
            self.connection.rollback()
            return None
            
    def update_venta(self, activo_id: int, operacion: Dict):
        """Actualiza un activo existente con datos de venta"""
        cursor = self.connection.cursor()
        
        # Calcular valores de venta
        precio_venta = self.calcular_precio_unitario(operacion['importe_pesos'], operacion['cantidad'])
        dolar_mep_venta = self.calcular_dolar_mep(operacion['importe_pesos'], operacion['importe_dolares'])
        
        try:
            cursor.execute("""
                UPDATE activo SET
                    Fecha_Hora_Venta = %s,
                    Precio_Venta = %s,
                    Cantidad_Nominales_Venta = %s,
                    Precio_Dolar_MEP_Venta = %s,
                    Total_Pesos_Venta = %s,
                    Total_Dolares_Venta = %s,
                    Activo_Estado = 'VENDIDO'
                WHERE Id_Activo = %s
            """, (
                operacion['fecha'],
                precio_venta,
                operacion['cantidad'],
                dolar_mep_venta if dolar_mep_venta > 0 else 1.0,
                operacion['importe_pesos'],
                operacion['importe_dolares'],
                activo_id
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error actualizando venta: {e}")
            self.connection.rollback()
            return False
            
    def buscar_compra_pendiente(self, comitente_id: int, ticker: str, cantidad: float) -> Optional[int]:
        """Busca una compra pendiente para asociar con una venta"""
        cursor = self.connection.cursor()
        
        ticker_id = self.ticker_cache.get(ticker)
        if not ticker_id:
            return None
            
        # Buscar activo en cartera con mismo ticker y cantidad similar
        cursor.execute("""
            SELECT Id_Activo, Cantidad_Nominales_Compra
            FROM activo
            WHERE Id_Comitente = %s 
            AND Id_Ticker = %s
            AND Activo_Estado = 'EN_CARTERA'
            AND ABS(Cantidad_Nominales_Compra - %s) < 0.01
            ORDER BY Fecha_Hora_Compra
            LIMIT 1
        """, (comitente_id, ticker_id, cantidad))
        
        result = cursor.fetchone()
        return result['Id_Activo'] if result else None
        
    def process_operacion(self, comitente_id: int, operacion: Dict):
        """Procesa una operación (compra o venta)"""
        if operacion['tipo_operacion'] in self.TIPOS_COMPRA:
            # Es una compra
            activo_id = self.insert_compra(comitente_id, operacion)
            return activo_id is not None
            
        elif operacion['tipo_operacion'] in self.TIPOS_VENTA:
            # Es una venta - buscar compra correspondiente
            activo_id = self.buscar_compra_pendiente(
                comitente_id, 
                operacion['ticker'],
                operacion['cantidad']
            )
            
            if activo_id:
                return self.update_venta(activo_id, operacion)
            else:
                # No se encontró compra - insertar como nueva (puede ser una venta en corto o error)
                print(f"  ⚠ No se encontró compra para venta de {operacion['cantidad']} {operacion['ticker']}")
                return False
                
        return False
        
    def process_pdf(self, pdf_path: str) -> Tuple[int, int]:
        """Procesa un archivo PDF de Bull Market"""
        operaciones_procesadas = 0
        operaciones_insertadas = 0
        
        print(f"\n📄 Procesando PDF: {pdf_path}")
        
        # Obtener o crear broker
        self.get_or_create_broker()
        
        with pdfplumber.open(pdf_path) as pdf:
            # Extraer info de comitente
            first_page_text = pdf.pages[0].extract_text()
            comitente_info = self.extract_comitente_info(first_page_text)
            
            if not comitente_info:
                print("✗ No se pudo extraer información del comitente")
                return (0, 0)
                
            numero_comitente, nombre_comitente = comitente_info
            print(f"✓ Comitente: {numero_comitente} - {nombre_comitente}")
            
            comitente_id = self.get_or_create_comitente(numero_comitente, nombre_comitente)
            
            # Procesar cada página
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"  Procesando página {page_num}/{len(pdf.pages)}...", end='\r')
                
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                        
                    headers = table[0]
                    
                    for row_data in table[1:]:
                        if len(row_data) < len(headers):
                            continue
                            
                        row = dict(zip(headers, row_data))
                        operacion = self.parse_row(row)
                        
                        if operacion:
                            operaciones_procesadas += 1
                            
                            if self.process_operacion(comitente_id, operacion):
                                operaciones_insertadas += 1
                                
        print(f"\n✓ Procesamiento completo")
        print(f"  • Operaciones procesadas: {operaciones_procesadas}")
        print(f"  • Operaciones insertadas: {operaciones_insertadas}")
        
        return (operaciones_procesadas, operaciones_insertadas)


def main():
    """Función principal"""
    
    DB_CONFIG = {
        'host': 'db',
        'user': 'cartera_user',
        'password': 'RootDevPass123!',
        'database': 'CarteraFinanciera'
    }
    
    PDF_FILE = 'Movimientos_bull_market_2019_2022.pdf'
    
    print("=" * 60)
    print("PROCESADOR DE PDF BULL MARKET → MODELO FLASK")
    print("=" * 60)
    
    processor = BullMarketPDFProcessor(DB_CONFIG)
    
    try:
        processor.connect_db()
        total_procesados, total_insertados = processor.process_pdf(PDF_FILE)
        
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)
        print(f"Total procesados: {total_procesados}")
        print(f"Total insertados: {total_insertados}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        processor.close_db()


if __name__ == '__main__':
    main()
