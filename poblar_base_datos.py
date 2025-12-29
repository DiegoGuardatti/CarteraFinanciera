#!/usr/bin/env python3
"""
Script para poblar la base de datos de Cartera Financiera
con datos extraídos del Excel y transferencias MEP
"""

import json
import os
import sys
from datetime import datetime
from sistema_mineria import MineriaDatosFinancieros

# Añadir el directorio actual al path para importar la aplicación Flask
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_flask_app
from modelo import db, Broker, Comitente, InstrumentoFinanciero, Ticker, Activo

class PobladorBaseDatos:
    def __init__(self):
        self.app = None
        self.mineria = MineriaDatosFinancieros()
        self.mapeo_ids = {}

    def inicializar_app(self):
        """Inicializa la aplicación Flask y contexto de BD"""
        app_tuple = create_flask_app()
        self.app = app_tuple[0]  # Extraer solo la app Flask de la tupla
        self.app.app_context().push()
        print("✅ Aplicación Flask inicializada")

    def poblar_datos_basicos(self):
        """Pobla datos básicos necesarios (brokers, comitentes, etc.)"""
        print("🏗️ Poblando datos básicos...")

        # Crear broker por defecto si no existe
        broker_default = Broker.query.filter_by(Nombre="Broker Principal").first()
        if not broker_default:
            broker_default = Broker(
                Nombre="Broker Principal",
                Comision=1.5,
                Asesor="Sistema Automático"
            )
            db.session.add(broker_default)
            db.session.commit()
            print("✅ Broker por defecto creado")

        # Crear comitente por defecto si no existe
        comitente_default = Comitente.query.filter_by(Numero="001").first()
        if not comitente_default:
            comitente_default = Comitente(
                Titular="Titular Principal",
                Numero="001",
                Id_Broker=broker_default.Id_Broker
            )
            db.session.add(comitente_default)
            db.session.commit()
            print("✅ Comitente por defecto creado")

        self.mapeo_ids['broker_default'] = broker_default.Id_Broker
        self.mapeo_ids['comitente_default'] = comitente_default.Id_Comitente

        # Crear instrumentos financieros básicos
        instrumentos = {
            'ACCION': 'Acciones',
            'CEDEAR': 'CEDEARs',
            'BONO': 'Bonos',
            'OBLIGACION_NEGOCIABLE': 'Obligaciones Negociables'
        }

        for tipo, nombre in instrumentos.items():
            instrumento = InstrumentoFinanciero.query.filter_by(Nombre=nombre).first()
            if not instrumento:
                instrumento = InstrumentoFinanciero(Nombre=nombre)
                db.session.add(instrumento)
                db.session.commit()
                print(f"✅ Instrumento {nombre} creado")

            self.mapeo_ids[f'instrumento_{tipo.lower()}'] = instrumento.Id_InstrumentoFinanciero

    def poblar_tickers(self):
        """Pobla la tabla de tickers desde los datos extraídos"""
        print("🏗️ Poblando tickers...")

        tickers_creados = 0
        for ticker_nombre, tipo_activo in self.mineria.tickers.items():
            # Verificar si ya existe
            ticker_existente = Ticker.query.filter_by(Nombre_Ticker=ticker_nombre).first()
            if ticker_existente:
                continue

            # Obtener ID del instrumento
            id_instrumento = self.mapeo_ids.get(f'instrumento_{tipo_activo.lower()}')
            if not id_instrumento:
                print(f"⚠️ Instrumento no encontrado para tipo {tipo_activo}")
                continue

            # Crear ticker
            ticker = Ticker(
                Nombre_Ticker=ticker_nombre,
                Descripcion=f"{tipo_activo} - {ticker_nombre}",
                Id_InstrumentoFinanciero=id_instrumento
            )
            db.session.add(ticker)
            tickers_creados += 1

        db.session.commit()
        print(f"✅ {tickers_creados} tickers creados")

    def poblar_activos(self):
        """Pobla la tabla de activos desde las operaciones extraídas"""
        print("🏗️ Poblando activos...")

        activos_creados = 0
        for operacion in self.mineria.operaciones:
            try:
                # Obtener IDs necesarios
                id_broker = self.mapeo_ids['broker_default']
                id_comitente = self.mapeo_ids['comitente_default']

                # Buscar ticker
                ticker = Ticker.query.filter_by(Nombre_Ticker=operacion['ticker']).first()
                if not ticker:
                    print(f"⚠️ Ticker {operacion['ticker']} no encontrado, omitiendo operación")
                    continue

                # Crear activo
                activo = Activo(
                    Id_Broker=id_broker,
                    Id_Comitente=id_comitente,
                    Id_Ticker=ticker.Id_Ticker,
                    Precio_Dolar_MEP_Compra=operacion.get('dolar_mep_compra', 1000),
                    Fecha_Hora_Compra=operacion['fecha_compra'],
                    Precio_Compra=operacion['precio_compra_ars'],
                    Cantidad_Nominales_Compra=operacion['cantidad'],
                    Comision_Broker=0.015,  # 1.5% por defecto
                    Total_Pesos_Compra=operacion['total_pesos_compra'],
                    Total_Dolares_Compra=operacion.get('total_usd_compra', 0),
                    # Campos de venta (si existen)
                    Precio_Dolar_MEP_Venta=operacion.get('tc_mep_venta_real'),
                    Fecha_Hora_Venta=operacion['fecha_venta'],
                    Precio_Venta=operacion['precio_venta_ars'],
                    Cantidad_Nominales_Venta=operacion['cantidad'] if operacion['fecha_venta'] else None,
                    Total_Pesos_Venta=operacion.get('total_pesos_venta', 0),
                    Total_Dolares_Venta=operacion.get('total_usd_mep_venta', 0),
                    Activo_Estado='VENDIDO' if operacion['fecha_venta'] else 'EN_CARTERA'
                )

                db.session.add(activo)
                activos_creados += 1

            except Exception as e:
                print(f"❌ Error creando activo para {operacion['ticker']}: {e}")
                continue

        db.session.commit()
        print(f"✅ {activos_creados} activos creados")

    def ejecutar_proceso_completo(self, excel_path=None, pdf_paths=None, chat_text=None):
        """Ejecuta el proceso completo de extracción y población"""
        print("🚀 Iniciando proceso de población de base de datos...")
        print("=" * 60)

        # Paso 1: Inicializar aplicación
        self.inicializar_app()

        total_operaciones_excel = 0
        total_operaciones_pdf = 0

        # Paso 2: Extraer datos del Excel (opcional)
        if excel_path:
            print("📊 Extrayendo datos del Excel...")
            operaciones_antes = len(self.mineria.operaciones)
            self.mineria.extraer_del_excel(excel_path)
            total_operaciones_excel = len(self.mineria.operaciones) - operaciones_antes

        # Paso 3: Extraer datos de PDFs (opcional)
        if pdf_paths:
            print("📄 Extrayendo datos de PDFs...")
            operaciones_antes = len(self.mineria.operaciones)
            self.mineria.extraer_de_pdfs(pdf_paths)
            total_operaciones_pdf = len(self.mineria.operaciones) - operaciones_antes

        # Paso 4: Extraer transferencias del chat (opcional)
        if chat_text:
            print("💬 Extrayendo transferencias MEP del chat...")
            self.mineria.extraer_transferencias_del_chat(chat_text)

            # Paso 5: Vincular operaciones con transferencias
            print("🔗 Vinculando operaciones con transferencias...")
            self.mineria.vincular_operaciones_con_transferencias()

        # Paso 6: Generar JSONs de respaldo
        print("💾 Generando archivos JSON...")
        self.mineria.generar_json_completo()

        # Paso 7: Poblar datos básicos
        self.poblar_datos_basicos()

        # Paso 8: Poblar tickers
        self.poblar_tickers()

        # Paso 9: Poblar activos
        self.poblar_activos()

        print("=" * 60)
        print("✅ Proceso completado exitosamente!")
        print(f"📈 Resumen:")
        print(f"   • Operaciones Excel: {total_operaciones_excel}")
        print(f"   • Operaciones PDFs: {total_operaciones_pdf}")
        print(f"   • Total operaciones: {len(self.mineria.operaciones)}")
        print(f"   • Transferencias MEP: {len(self.mineria.transferencias_mep)}")
        print(f"   • Tickers únicos: {len(self.mineria.tickers)}")
        print("\n🎯 La aplicación está lista para usar con datos reales!")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python poblar_base_datos.py <ruta_excel> [pdf1.pdf pdf2.pdf ...] [--chat archivo_chat.txt]")
        print("Ejemplos:")
        print("  python poblar_base_datos.py datos.xlsx")
        print("  python poblar_base_datos.py datos.xlsx reporte1.pdf reporte2.pdf")
        print("  python poblar_base_datos.py datos.xlsx --chat historial.txt")
        print("  python poblar_base_datos.py datos.xlsx reporte.pdf --chat chat.txt")
        sys.exit(1)

    excel_path = None
    pdf_paths = []
    chat_path = None

    # Parsear argumentos
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--chat':
            if i + 1 < len(sys.argv):
                chat_path = sys.argv[i + 1]
                i += 2
            else:
                print("❌ Error: --chat requiere un archivo")
                sys.exit(1)
        elif arg.endswith('.xlsx') or arg.endswith('.xls'):
            if excel_path is None:
                excel_path = arg
            else:
                print("❌ Error: Solo se permite un archivo Excel")
                sys.exit(1)
            i += 1
        elif arg.endswith('.pdf'):
            pdf_paths.append(arg)
            i += 1
        else:
            print(f"❌ Error: Argumento no reconocido: {arg}")
            sys.exit(1)

    # Validar que al menos hay un archivo de entrada
    if not excel_path and not pdf_paths:
        print("❌ Error: Debe proporcionar al menos un archivo Excel o PDF")
        print("Ejemplos:")
        print("  python poblar_base_datos.py datos.xlsx")
        print("  python poblar_base_datos.py reporte.pdf")
        print("  python poblar_base_datos.py datos.xlsx reporte1.pdf reporte2.pdf --chat chat.txt")
        sys.exit(1)

    # Verificar archivos
    if excel_path and not os.path.exists(excel_path):
        print(f"❌ Error: No se encuentra el archivo Excel: {excel_path}")
        sys.exit(1)

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"❌ Error: No se encuentra el archivo PDF: {pdf_path}")
            sys.exit(1)

    # Leer archivo de chat si se proporciona
    chat_text = None
    if chat_path and os.path.exists(chat_path):
        with open(chat_path, 'r', encoding='utf-8') as f:
            chat_text = f.read()
        print(f"✅ Archivo de chat cargado: {chat_path}")
    elif chat_path:
        print(f"⚠️ Archivo de chat no encontrado: {chat_path}")

    # Mostrar resumen de archivos
    print("📂 Archivos a procesar:")
    if excel_path:
        print(f"   • Excel: {excel_path}")
    if pdf_paths:
        print(f"   • PDFs: {len(pdf_paths)} archivos")
        for pdf in pdf_paths:
            print(f"     - {pdf}")
    if chat_text:
        print(f"   • Chat MEP: {len(chat_text.split())} palabras")

    # Ejecutar proceso
    poblador = PobladorBaseDatos()
    poblador.ejecutar_proceso_completo(excel_path, pdf_paths if pdf_paths else None, chat_text)

if __name__ == "__main__":
    main()