#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de minería de datos financieros
"""

from sistema_mineria import MineriaDatosFinancieros

def ejemplo_basico():
    """Ejemplo básico de uso"""
    print("🚀 Ejemplo de uso del Sistema de Minería de Datos Financieros")
    print("=" * 60)

    # Crear instancia del sistema
    mineria = MineriaDatosFinancieros()

    # Simular datos de Excel (en la práctica vendrían de un archivo real)
    print("📊 Simulando extracción de datos del Excel...")
    # mineria.extraer_del_excel("tu_archivo.xlsx")

    # Simular extracción de PDFs
    print("📄 Simulando extracción de datos de PDFs...")
    # mineria.extraer_de_pdfs(["reporte_broker1.pdf", "reporte_broker2.pdf"])

    # Simular texto de chat con transferencias MEP
    chat_text = """
    15/12/2023 PUSA $500.000 425,50 USD - Transferencia entrada
    16/12/2023 PAGA $300.000 430,25 USD - Transferencia salida
    20/12/2023 TRANSFERENCIA VIA MEP $200.000 TC MEP 435,00
    """

    print("💬 Extrayendo transferencias MEP del chat...")
    mineria.extraer_transferencias_del_chat(chat_text)

    print(f"✅ Transferencias extraídas: {len(mineria.transferencias_mep)}")

    # Mostrar transferencias encontradas
    for trans in mineria.transferencias_mep:
        print(f"   • {trans['tipo']}: ${trans['monto_pesos']:,.0f} ARS = ${trans['monto_usd']:,.2f} USD (TC: {trans['tc_mep']})")

    # Generar JSONs
    print("💾 Generando archivos JSON...")
    mineria.generar_json_completo()

    print("✅ Archivos generados:")
    print("   • transferencias_mep.json")
    print("   • operaciones_completas.json")
    print("   • dashboard_financiero.json")

def ejemplo_integracion_flask():
    """Ejemplo de integración con la aplicación Flask"""
    print("\n🔗 Para integrar con la aplicación Flask:")
    print("1. Ejecutar: python poblar_base_datos.py datos.xlsx reporte.pdf [chat.txt]")
    print("2. Iniciar la app: python app.py")
    print("3. Acceder a: http://localhost:5000/dashboard_avanzado")
    print("4. Las métricas se calcularán con datos reales!")
    print("\n📊 Fuentes de datos soportadas:")
    print("   • Excel: Hojas de Acciones, CEDEARs, Bonos, ONs")
    print("   • PDFs: Reportes de brokers con operaciones")
    print("   • Chat: Transferencias MEP para TCs reales")

if __name__ == "__main__":
    ejemplo_basico()
    ejemplo_integracion_flask()