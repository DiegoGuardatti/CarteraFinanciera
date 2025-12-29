# sistema_mineria.py
import json
import pandas as pd
import re
from datetime import datetime
from collections import defaultdict
import os
try:
    import pdfplumber
    PDF_LIB = 'pdfplumber'
except ImportError:
    try:
        import PyPDF2
        PDF_LIB = 'PyPDF2'
    except ImportError:
        PDF_LIB = None
        print("⚠️ No se encontró librería para PDFs. Instalar: pip install pdfplumber")

class MineriaDatosFinancieros:
    def __init__(self):
        self.transferencias_mep = []
        self.operaciones = []
        self.tickers = {}
        self.id_counter = 1

    def extraer_del_excel(self, excel_path):
        """Extrae todas las operaciones del Excel"""
        try:
            # Primero intentar con el formato estándar (múltiples hojas)
            xl = pd.ExcelFile(excel_path)
            hojas_disponibles = xl.sheet_names
            print(f"Hojas encontradas: {hojas_disponibles}")

            # Mapeo de hojas a tipos de activos
            hojas_tipo = {
                'Acciones': 'ACCION',
                'CEDEARs': 'CEDEAR',
                'Bonos': 'BONO',
                'ONs': 'OBLIGACION_NEGOCIABLE'
            }

            operaciones_encontradas = False
            for hoja in hojas_disponibles:
                if hoja in hojas_tipo:
                    try:
                        df = pd.read_excel(excel_path, sheet_name=hoja)
                        print(f"Procesando hoja {hoja}...")

                        for _, row in df.iterrows():
                            if pd.notna(row.get('Ticker')):
                                operacion = self._crear_operacion_desde_row(row, hojas_tipo[hoja])
                                if operacion:
                                    self.operaciones.append(operacion)
                                    self.tickers[row['Ticker']] = hojas_tipo[hoja]
                                    operaciones_encontradas = True

                    except Exception as e:
                        print(f"Error procesando hoja {hoja}: {e}")
                        continue

            # Si no encontró operaciones en hojas estándar, intentar formato de cuenta corriente
            if not operaciones_encontradas and len(hojas_disponibles) == 1:
                print("Intentando formato de cuenta corriente...")
                operaciones_encontradas = self._procesar_cuenta_corriente(excel_path, hojas_disponibles[0])

        except Exception as e:
            print(f"Error general procesando Excel: {e}")

        print(f"Total operaciones extraídas: {len(self.operaciones)}")
        print(f"Total tickers únicos: {len(self.tickers)}")

    def _procesar_cuenta_corriente(self, excel_path, hoja):
        """Procesa formato de cuenta corriente bursátil argentina"""
        try:
            df = pd.read_excel(excel_path, sheet_name=hoja)
            print(f"Procesando cuenta corriente - {len(df)} filas")

            operaciones_procesadas = 0

            for _, row in df.iterrows():
                try:
                    # Verificar si es una operación bursátil (tiene especie y cantidad)
                    especie = str(row.get('Especie', '')).strip()
                    cantidad = row.get('Cantidad', 0)
                    comprobante = str(row.get('Comprobante', '')).strip()

                    if (pd.notna(especie) and especie and
                        pd.notna(cantidad) and cantidad != 0 and
                        comprobante not in ['RETENCION', 'DIVIDENDOS']):  # Excluir retenciones y dividendos

                        operacion = self._crear_operacion_cuenta_corriente(row)
                        if operacion:
                            self.operaciones.append(operacion)
                            self.tickers[especie] = self._determinar_tipo_por_especie(especie)
                            operaciones_procesadas += 1

                except Exception as e:
                    print(f"Error procesando fila: {e}")
                    continue

            print(f"Operaciones bursátiles procesadas: {operaciones_procesadas}")
            return operaciones_procesadas > 0

        except Exception as e:
            print(f"Error procesando cuenta corriente: {e}")
            return False

    def _crear_operacion_cuenta_corriente(self, row):
        """Crea operación desde fila de cuenta corriente"""
        try:
            especie = str(row['Especie']).strip()
            cantidad = float(row['Cantidad'])
            precio = float(row.get('Precio', 0))
            importe = float(row.get('Importe', 0))

            # Determinar tipo de operación por el signo del importe
            es_compra = importe < 0  # Importes negativos = compras (dinero sale)

            # Calcular precio si no está disponible
            if precio == 0 and abs(importe) > 0 and abs(cantidad) > 0:
                precio = abs(importe) / abs(cantidad)

            operacion = {
                'id_operacion': self.id_counter,
                'tipo_activo': self._determinar_tipo_por_especie(especie),
                'ticker': especie,
                'fecha_compra': row['Operado'].date() if pd.notna(row.get('Operado')) else datetime.now().date(),
                'precio_compra_ars': precio,
                'cantidad': abs(cantidad),  # Siempre positivo
                'total_pesos_compra': abs(importe),
                'dolar_mep_compra': 1000,  # Valor por defecto, se puede ajustar
                'condicion': 'Activa',
                'fuente': 'Cuenta_Corriente'
            }

            # Calcular total en USD
            operacion['total_usd_compra'] = operacion['total_pesos_compra'] / operacion['dolar_mep_compra']

            # Si es venta (importe positivo), agregar campos de venta
            if not es_compra:
                operacion.update({
                    'fecha_venta': operacion['fecha_compra'],
                    'precio_venta_ars': precio,
                    'total_pesos_venta': abs(importe),
                    'total_usd_venta': operacion['total_usd_compra'],
                    'condicion': 'Operada'
                })

            self.id_counter += 1
            return operacion

        except Exception as e:
            print(f"Error creando operación cuenta corriente: {e}")
            return None

    def _determinar_tipo_por_especie(self, especie):
        """Determina tipo de activo por código de especie"""
        especie_upper = especie.upper()

        # CEDEARs comunes (acciones extranjeras)
        if especie_upper in ['AAPL', 'TSLA', 'AMZN', 'GOOGL', 'MSFT', 'NVDA', 'META', 'NFLX', 'KO', 'DIS']:
            return 'CEDEAR'

        # Bonos (generalmente empiezan con letras específicas)
        if (len(especie) <= 6 and
            (especie_upper.startswith(('AL', 'GD', 'AE', 'AY', 'CO', 'DI', 'DU', 'PA', 'PE', 'PR')) or
             especie_upper.endswith(('D', 'V', 'C')))):
            return 'BONO'

        # Obligaciones negociables (ONs)
        if especie_upper.startswith(('ON', 'OC')) or 'ON' in especie_upper:
            return 'OBLIGACION_NEGOCIABLE'

        # Por defecto, acción local
        return 'ACCION'

    def extraer_de_pdfs(self, pdf_paths):
        """Extrae operaciones desde archivos PDF"""
        if not PDF_LIB:
            print("❌ No hay librería disponible para procesar PDFs")
            return

        if isinstance(pdf_paths, str):
            pdf_paths = [pdf_paths]

        print("📄 Procesando archivos PDF...")

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"⚠️ PDF no encontrado: {pdf_path}")
                continue

            try:
                texto_pdf = self._extraer_texto_pdf(pdf_path)
                operaciones_pdf = self._parsear_operaciones_pdf(texto_pdf, pdf_path)

                for op in operaciones_pdf:
                    if op:
                        self.operaciones.append(op)
                        self.tickers[op['ticker']] = op['tipo_activo']

                print(f"✅ Procesado: {pdf_path} - {len(operaciones_pdf)} operaciones")

            except Exception as e:
                print(f"❌ Error procesando PDF {pdf_path}: {e}")

        print(f"Total operaciones de PDFs: {len([op for op in self.operaciones if 'fuente' in op and op['fuente'] == 'PDF'])}")

    def _extraer_texto_pdf(self, pdf_path):
        """Extrae texto completo de un archivo PDF"""
        texto_completo = ""

        try:
            if PDF_LIB == 'pdfplumber':
                with pdfplumber.open(pdf_path) as pdf:
                    for pagina in pdf.pages:
                        texto_pagina = pagina.extract_text()
                        if texto_pagina:
                            texto_completo += texto_pagina + "\n"

            elif PDF_LIB == 'PyPDF2':
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for pagina in pdf_reader.pages:
                        texto_pagina = pagina.extract_text()
                        if texto_pagina:
                            texto_completo += texto_pagina + "\n"

        except Exception as e:
            print(f"Error extrayendo texto del PDF: {e}")

        return texto_completo

    def _parsear_operaciones_pdf(self, texto_pdf, fuente_pdf):
        """Parsea operaciones financieras desde texto de PDF"""
        operaciones = []

        # Patrones comunes en PDFs de brokers argentinos
        patrones_operaciones = [
            # Patrón para compras: "Compra GGAL 100 acciones a $1500.50"
            r'(?i)compra\s+(\w+)\s+(\d+(?:[.,]\d+)?)\s+(?:acciones?|nominales?)\s+a\s+\$?([\d.,]+)',

            # Patrón para ventas: "Venta TSLA 50 CEDEARs a $250.75"
            r'(?i)venta\s+(\w+)\s+(\d+(?:[.,]\d+)?)\s+(?:acciones?|nominales?|cedears?|bonos?|ons?)\s+a\s+\$?([\d.,]+)',

            # Patrón con fechas: "15/12/2023 Compra AAPL 200 acciones $180.50"
            r'(\d{1,2}/\d{1,2}/\d{4})\s+(?i)compra\s+(\w+)\s+(\d+(?:[.,]\d+)?)\s+(?:acciones?|nominales?)\s+\$?([\d.,]+)',

            # Patrón con tipo de activo específico
            r'(?i)(acción|bono|cedear|on)\s+(\w+)\s+(\d+(?:[.,]\d+)?)\s+(?:acciones?|nominales?)\s+a\s+\$?([\d.,]+)',
        ]

        # Patrones para fechas
        patrones_fechas = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # dd/mm/yyyy
            r'(\d{1,2}-\d{1,2}-\d{4})',  # dd-mm-yyyy
            r'fecha:?\s*(\d{1,2}/\d{1,2}/\d{4})',  # "fecha: 15/12/2023"
        ]

        # Buscar fechas en el documento
        fechas_encontradas = []
        for patron_fecha in patrones_fechas:
            matches = re.findall(patron_fecha, texto_pdf)
            fechas_encontradas.extend(matches)

        fecha_default = fechas_encontradas[0] if fechas_encontradas else None

        # Procesar cada patrón de operación
        for patron in patrones_operaciones:
            matches = re.findall(patron, texto_pdf)

            for match in matches:
                try:
                    operacion = self._procesar_match_pdf(match, fecha_default, fuente_pdf)
                    if operacion:
                        operaciones.append(operacion)

                except Exception as e:
                    print(f"Error procesando match PDF: {match} - {e}")

        return operaciones

    def _procesar_match_pdf(self, match, fecha_default, fuente_pdf):
        """Procesa un match de regex de PDF y crea operación"""
        try:
            # match puede ser tuple de diferentes longitudes según el patrón
            if len(match) == 3:
                # Patrón simple: ticker, cantidad, precio
                ticker, cantidad, precio = match
                fecha = fecha_default
                tipo_operacion = "COMPRA"  # Asumir compra por defecto
            elif len(match) == 4:
                # Patrón con fecha: fecha, ticker, cantidad, precio
                fecha, ticker, cantidad, precio = match
                tipo_operacion = "COMPRA"
            elif len(match) == 5:
                # Patrón con tipo: tipo_activo, ticker, cantidad, precio, ?
                tipo_activo, ticker, cantidad, precio, _ = match
                fecha = fecha_default
                tipo_operacion = "COMPRA"
            else:
                return None

            # Limpiar y convertir valores
            ticker = ticker.upper().strip()
            cantidad = self._limpiar_numero(cantidad)
            precio = self._limpiar_numero(precio)

            if cantidad <= 0 or precio <= 0:
                return None

            # Determinar tipo de activo basado en el ticker o contexto
            tipo_activo = self._determinar_tipo_activo_pdf(ticker, fuente_pdf)

            # Crear operación
            operacion = {
                'id_operacion': self.id_counter,
                'tipo_activo': tipo_activo,
                'ticker': ticker,
                'fecha_compra': self._parsear_fecha(fecha) if fecha else datetime.now().date(),
                'precio_compra_ars': precio,
                'cantidad': cantidad,
                'total_pesos_compra': precio * cantidad,
                'dolar_mep_compra': 1000,  # Valor por defecto, se puede ajustar
                'condicion': 'Activa',
                'fuente': 'PDF',
                'archivo_pdf': os.path.basename(fuente_pdf)
            }

            # Calcular total en USD
            operacion['total_usd_compra'] = operacion['total_pesos_compra'] / operacion['dolar_mep_compra']

            self.id_counter += 1
            return operacion

        except Exception as e:
            print(f"Error procesando operación PDF: {e}")
            return None

    def _determinar_tipo_activo_pdf(self, ticker, fuente_pdf):
        """Determina el tipo de activo basado en el ticker y fuente PDF"""
        # Lógica heurística para determinar tipo de activo
        nombre_pdf = os.path.basename(fuente_pdf).lower()

        # Si el nombre del PDF indica el tipo
        if 'bono' in nombre_pdf:
            return 'BONO'
        elif 'cedear' in nombre_pdf:
            return 'CEDEAR'
        elif 'on' in nombre_pdf or 'obligacion' in nombre_pdf:
            return 'OBLIGACION_NEGOCIABLE'

        # Heurísticas por ticker
        ticker_lower = ticker.lower()

        # Tickers que suenan como CEDEARs (generalmente empresas extranjeras)
        cedears_comunes = ['tsla', 'aapl', 'amzn', 'goog', 'msft', 'nvda', 'meta', 'NFLX']
        if ticker_lower in cedears_comunes:
            return 'CEDEAR'

        # Tickers que suenan como bonos
        if ticker_lower.startswith(('al', 'gd', 'ae')) and len(ticker) <= 6:
            return 'BONO'

        # Por defecto, asumir acción local
        return 'ACCION'

    def _crear_operacion_desde_row(self, row, tipo_activo):
        """Crea una operación estructurada desde una fila del Excel"""
        try:
            # Calcular totales si no están presentes
            precio_compra = row.get('Precio Compra *', 0)
            cantidad = row.get('Cantidad', 0)
            total_pesos_compra = row.get('Pesos en compra *', precio_compra * cantidad)

            operacion = {
                'id_operacion': self.id_counter,
                'tipo_activo': tipo_activo,
                'ticker': str(row['Ticker']).strip().upper(),
                'fecha_compra': self._parsear_fecha(row.get('Fecha Compra')),
                'precio_compra_ars': float(precio_compra) if pd.notna(precio_compra) else 0,
                'cantidad': float(cantidad) if pd.notna(cantidad) else 0,
                'total_pesos_compra': float(total_pesos_compra) if pd.notna(total_pesos_compra) else 0,
                'dolar_mep_compra': float(row.get('Dólar MEP en la Compra', 1000)) if pd.notna(row.get('Dólar MEP en la Compra')) else 1000,
                'fecha_venta': self._parsear_fecha(row.get('Fecha Venta')),
                'precio_venta_ars': float(row.get('Precio Venta *', 0)) if pd.notna(row.get('Precio Venta *')) else None,
                'dividendos': float(row.get('* Dividendos', 0)) if pd.notna(row.get('* Dividendos')) else 0,
                'condicion': str(row.get('Condición', 'Activa')).strip(),
                'total_pesos_venta': 0,
                'total_usd_compra': 0,
                'total_usd_venta': 0
            }

            # Calcular totales en USD
            if operacion['total_pesos_compra'] > 0 and operacion['dolar_mep_compra'] > 0:
                operacion['total_usd_compra'] = operacion['total_pesos_compra'] / operacion['dolar_mep_compra']

            if operacion['precio_venta_ars'] and operacion['cantidad'] > 0:
                operacion['total_pesos_venta'] = operacion['precio_venta_ars'] * operacion['cantidad']

            self.id_counter += 1
            return operacion

        except Exception as e:
            print(f"Error creando operación: {e}")
            return None

    def _parsear_fecha(self, fecha):
        """Parsea fechas en múltiples formatos"""
        if pd.isna(fecha):
            return None

        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
        for fmt in formatos:
            try:
                return datetime.strptime(str(fecha).strip(), fmt).date()
            except ValueError:
                continue
        return None

    def extraer_transferencias_del_chat(self, chat_text):
        """Extrae transferencias MEP del historial del chat"""
        # Patrones para identificar transferencias
        patrones = [
            r'(\d{2}/\d{2}/\d{4}).*?(PUSA|PAGA|CPUS).*?(\$\s*[\d.,]+).*?([\d.,]+)\s*USD',
            r'TC MEP.*?([\d.,]+)',
            r'TRANSFERENCIA VIA MEP'
        ]

        # Procesar el texto del chat línea por línea
        lines = chat_text.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['PUSA', 'PAGA', 'CPUS', 'VIA MEP']):
                transferencia = self._parsear_transferencia(line)
                if transferencia:
                    self.transferencias_mep.append(transferencia)

    def _parsear_transferencia(self, line):
        """Convierte una línea de texto en una transferencia estructurada"""
        try:
            # Patrones regex para diferentes formatos de transferencias MEP
            patrones = [
                # Formato: "15/12/2023 PUSA $500.000 425,50 USD"
                r'(\d{2}/\d{2}/\d{4})\s+(PUSA|PAGA|CPUS)\s+\$\s*([\d.,]+)\s+([\d.,]+)\s*USD',
                # Formato: "15/12/2023 TRANSFERENCIA VIA MEP $500.000 TC MEP 425,50"
                r'(\d{2}/\d{2}/\d{4})\s+TRANSFERENCIA\s+VIA\s+MEP\s+\$\s*([\d.,]+)\s+TC\s+MEP\s+([\d.,]+)',
                # Formato simple: "PUSA $100.000"
                r'(PUSA|PAGA|CPUS)\s+\$\s*([\d.,]+)'
            ]

            for patron in patrones:
                match = re.search(patron, line, re.IGNORECASE)
                if match:
                    return self._procesar_match_transferencia(match, line)

            return None

        except Exception as e:
            print(f"Error parseando línea: {line} - {e}")
            return None

    def _procesar_match_transferencia(self, match, linea_original):
        """Procesa un match de regex y crea la transferencia"""
        try:
            grupos = match.groups()

            # Determinar tipo basado en el contenido
            tipo = 'ENTRADA' if 'PUSA' in linea_original.upper() else 'SALIDA'

            # Extraer fecha (puede no estar presente en algunos formatos)
            fecha = None
            if len(grupos) >= 4 and grupos[0] and re.match(r'\d{2}/\d{2}/\d{4}', grupos[0]):
                fecha = datetime.strptime(grupos[0], '%d/%m/%Y').date()

            # Extraer monto en pesos
            monto_pesos = self._limpiar_numero(grupos[-2]) if len(grupos) >= 3 else 0

            # Extraer TC MEP
            tc_mep = self._limpiar_numero(grupos[-1]) if len(grupos) >= 2 else 0

            # Calcular monto en USD
            monto_usd = monto_pesos / tc_mep if tc_mep > 0 else 0

            transferencia = {
                'id': self.id_counter,
                'tipo': tipo,
                'fecha': fecha,
                'monto_pesos': monto_pesos,
                'monto_usd': monto_usd,
                'tc_mep': tc_mep,
                'descripcion': linea_original.strip(),
                'procesada': False
            }

            self.id_counter += 1
            return transferencia

        except Exception as e:
            print(f"Error procesando match: {e}")
            return None

    def _limpiar_numero(self, numero_str):
        """Limpia y convierte string numérico a float"""
        if not numero_str:
            return 0.0

        # Remover símbolos de moneda y espacios
        numero_str = re.sub(r'[$\s]', '', str(numero_str))

        # Manejar formato argentino (coma como separador decimal)
        if ',' in numero_str and '.' in numero_str:
            # Formato 123.456,78 -> 123456.78
            numero_str = numero_str.replace('.', '').replace(',', '.')
        elif ',' in numero_str:
            # Formato 123,45 -> 123.45
            numero_str = numero_str.replace(',', '.')

        try:
            return float(numero_str)
        except ValueError:
            return 0.0

    def buscar_transferencia(self, tipo, fecha_min=None, fecha_max=None, sentido='anterior'):
        """Busca la transferencia más cercana según criterios"""
        transferencias_filtradas = [t for t in self.transferencias_mep if t['tipo'] == tipo and t['fecha']]

        if not transferencias_filtradas:
            return None

        # Ordenar por fecha
        transferencias_filtradas.sort(key=lambda x: x['fecha'])

        if sentido == 'anterior' and fecha_max:
            # Buscar la última transferencia antes de fecha_max
            candidatas = [t for t in transferencias_filtradas if t['fecha'] <= fecha_max]
            return candidatas[-1] if candidatas else None

        elif sentido == 'posterior' and fecha_min:
            # Buscar la primera transferencia después de fecha_min
            candidatas = [t for t in transferencias_filtradas if t['fecha'] >= fecha_min]
            return candidatas[0] if candidatas else None

        return None

    def vincular_operaciones_con_transferencias(self):
        """Vincula cada operación con transferencias MEP reales"""
        print("Vinculando operaciones con transferencias MEP...")

        operaciones_vinculadas = 0

        for op in self.operaciones:
            vinculada = False

            # Para compras: buscar última ENTRADA MEP antes de fecha_compra
            if op['fecha_compra']:
                transferencia = self.buscar_transferencia(
                    tipo='ENTRADA',
                    fecha_max=op['fecha_compra'],
                    sentido='anterior'
                )
                if transferencia:
                    op['id_transferencia_compra'] = transferencia['id']
                    op['tc_mep_compra_real'] = transferencia['tc_mep']
                    op['total_usd_mep_compra'] = op['total_pesos_compra'] / transferencia['tc_mep'] if transferencia['tc_mep'] > 0 else 0
                    transferencia['procesada'] = True
                    vinculada = True

            # Para ventas: buscar próxima SALIDA MEP después de fecha_venta
            if op['fecha_venta']:
                transferencia = self.buscar_transferencia(
                    tipo='SALIDA',
                    fecha_min=op['fecha_venta'],
                    sentido='posterior'
                )
                if transferencia:
                    op['id_transferencia_venta'] = transferencia['id']
                    op['tc_mep_venta_real'] = transferencia['tc_mep']
                    op['total_usd_mep_venta'] = op['total_pesos_venta'] / transferencia['tc_mep'] if transferencia['tc_mep'] > 0 else 0
                    transferencia['procesada'] = True
                    vinculada = True

            if vinculada:
                operaciones_vinculadas += 1

        print(f"Operaciones vinculadas: {operaciones_vinculadas}/{len(self.operaciones)}")

    def generar_json_completo(self):
        """Genera todos los archivos JSON necesarios"""
        # 1. Transferencias MEP
        with open('transferencias_mep.json', 'w') as f:
            json.dump({
                'metadata': {
                    'total_transferencias': len(self.transferencias_mep),
                    'fecha_generacion': datetime.now().isoformat(),
                    'descripcion': 'Transferencias MEP extraídas automáticamente'
                },
                'transferencias': self.transferencias_mep
            }, f, indent=2, default=str)

        # 2. Operaciones
        with open('operaciones_completas.json', 'w') as f:
            json.dump({
                'metadata': {
                    'total_operaciones': len(self.operaciones),
                    'operaciones_activas': sum(1 for op in self.operaciones if op['condicion'] in ['Activa', 'Stock']),
                    'operaciones_operadas': sum(1 for op in self.operaciones if op['condicion'] == 'Operada')
                },
                'operaciones': self.operaciones
            }, f, indent=2, default=str)

        # 3. Dashboard resumen
        self.generar_dashboard()

    def calcular_resumen(self):
        """Calcula métricas generales de la cartera"""
        resumen = {
            'total_operaciones': len(self.operaciones),
            'operaciones_activas': sum(1 for op in self.operaciones if op['condicion'] in ['Activa', 'Stock']),
            'operaciones_vendidas': sum(1 for op in self.operaciones if op['condicion'] == 'Operada'),
            'total_invertido_usd': sum(op.get('total_usd_compra', 0) for op in self.operaciones),
            'total_vendido_usd': sum(op.get('total_usd_venta', 0) for op in self.operaciones if op.get('total_usd_venta')),
            'total_dividendos': sum(op.get('dividendos', 0) for op in self.operaciones),
            'transferencias_entrada': sum(1 for t in self.transferencias_mep if t['tipo'] == 'ENTRADA'),
            'transferencias_salida': sum(1 for t in self.transferencias_mep if t['tipo'] == 'SALIDA'),
            'total_mep_entradas_usd': sum(t['monto_usd'] for t in self.transferencias_mep if t['tipo'] == 'ENTRADA'),
            'total_mep_salidas_usd': sum(t['monto_usd'] for t in self.transferencias_mep if t['tipo'] == 'SALIDA')
        }

        # Calcular ganancia/pérdida total
        resumen['ganancia_perdida_total_usd'] = resumen['total_vendido_usd'] - resumen['total_invertido_usd'] + resumen['total_dividendos']

        return resumen

    def agrupar_por_ticker(self):
        """Agrupa métricas por ticker"""
        tickers_data = defaultdict(lambda: {
            'operaciones': 0,
            'total_invertido_usd': 0,
            'total_vendido_usd': 0,
            'dividendos': 0,
            'activas': 0,
            'vendidas': 0
        })

        for op in self.operaciones:
            ticker = op['ticker']
            tickers_data[ticker]['operaciones'] += 1
            tickers_data[ticker]['total_invertido_usd'] += op.get('total_usd_compra', 0)
            tickers_data[ticker]['total_vendido_usd'] += op.get('total_usd_venta', 0)
            tickers_data[ticker]['dividendos'] += op.get('dividendos', 0)

            if op['condicion'] in ['Activa', 'Stock']:
                tickers_data[ticker]['activas'] += 1
            elif op['condicion'] == 'Operada':
                tickers_data[ticker]['vendidas'] += 1

        # Calcular rentabilidad por ticker
        for ticker, data in tickers_data.items():
            vendido = data['total_vendido_usd']
            invertido = data['total_invertido_usd']
            data['rentabilidad_usd'] = vendido - invertido + data['dividendos']
            data['rentabilidad_pct'] = (data['rentabilidad_usd'] / invertido * 100) if invertido > 0 else 0

        return dict(tickers_data)

    def agrupar_por_tipo(self):
        """Agrupa métricas por tipo de activo"""
        tipos_data = defaultdict(lambda: {
            'operaciones': 0,
            'total_invertido_usd': 0,
            'total_vendido_usd': 0,
            'dividendos': 0,
            'tickers_unicos': set()
        })

        for op in self.operaciones:
            tipo = op['tipo_activo']
            tipos_data[tipo]['operaciones'] += 1
            tipos_data[tipo]['total_invertido_usd'] += op.get('total_usd_compra', 0)
            tipos_data[tipo]['total_vendido_usd'] += op.get('total_usd_venta', 0)
            tipos_data[tipo]['dividendos'] += op.get('dividendos', 0)
            tipos_data[tipo]['tickers_unicos'].add(op['ticker'])

        # Convertir sets a listas y calcular métricas
        for tipo, data in tipos_data.items():
            data['tickers_unicos'] = list(data['tickers_unicos'])
            data['num_tickers'] = len(data['tickers_unicos'])
            vendido = data['total_vendido_usd']
            invertido = data['total_invertido_usd']
            data['rentabilidad_usd'] = vendido - invertido + data['dividendos']
            data['rentabilidad_pct'] = (data['rentabilidad_usd'] / invertido * 100) if invertido > 0 else 0

        return dict(tipos_data)

    def calcular_evolucion_mensual(self):
        """Calcula evolución mensual de inversiones"""
        evolucion = defaultdict(lambda: {
            'compras_usd': 0,
            'ventas_usd': 0,
            'dividendos': 0,
            'transferencias_entrada_usd': 0,
            'transferencias_salida_usd': 0
        })

        # Procesar operaciones
        for op in self.operaciones:
            if op.get('fecha_compra'):
                mes_key = f"{op['fecha_compra'].year}-{op['fecha_compra'].month:02d}"
                evolucion[mes_key]['compras_usd'] += op.get('total_usd_compra', 0)

            if op.get('fecha_venta'):
                mes_key = f"{op['fecha_venta'].year}-{op['fecha_venta'].month:02d}"
                evolucion[mes_key]['ventas_usd'] += op.get('total_usd_venta', 0)

            if op.get('dividendos', 0) > 0:
                # Asumir dividendos en el mes de compra si no hay fecha específica
                if op['fecha_compra']:
                    mes_key = f"{op['fecha_compra'].year}-{op['fecha_compra'].month:02d}"
                    evolucion[mes_key]['dividendos'] += op['dividendos']

        # Procesar transferencias
        for trans in self.transferencias_mep:
            if trans['fecha']:
                mes_key = f"{trans['fecha'].year}-{trans['fecha'].month:02d}"
                if trans['tipo'] == 'ENTRADA':
                    evolucion[mes_key]['transferencias_entrada_usd'] += trans['monto_usd']
                else:
                    evolucion[mes_key]['transferencias_salida_usd'] += trans['monto_usd']

        # Calcular balance mensual
        for mes, data in evolucion.items():
            data['balance_usd'] = (data['ventas_usd'] + data['dividendos'] +
                                 data['transferencias_entrada_usd'] -
                                 data['compras_usd'] - data['transferencias_salida_usd'])

        return dict(evolucion)

    def generar_dashboard(self):
        """Genera dashboard con métricas clave"""
        print("Generando dashboard financiero...")

        dashboard = {
            'metadata': {
                'fecha_generacion': datetime.now().isoformat(),
                'total_operaciones': len(self.operaciones),
                'total_transferencias': len(self.transferencias_mep),
                'total_tickers': len(self.tickers)
            },
            'resumen_general': self.calcular_resumen(),
            'por_ticker': self.agrupar_por_ticker(),
            'por_tipo_activo': self.agrupar_por_tipo(),
            'evolucion_mensual': self.calcular_evolucion_mensual()
        }

        with open('dashboard_financiero.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, default=str, ensure_ascii=False)

        print("Dashboard generado: dashboard_financiero.json")