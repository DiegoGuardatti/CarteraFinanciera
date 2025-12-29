# 📊 Sistema de Minería de Datos Financieros

Sistema automatizado para extraer, procesar y cargar datos financieros desde Excel y chat de transferencias MEP en la aplicación Cartera Financiera.

## 🎯 Funcionalidades

- **Extracción automática** de operaciones desde Excel (Acciones, CEDEARs, Bonos, ONs)
- **Parsing inteligente** de transferencias MEP desde historial de chat
- **Vinculación automática** entre operaciones y transferencias reales
- **Cálculo de métricas** financieras avanzadas
- **Generación de JSONs** para análisis y backup
- **Integración completa** con base de datos Flask/SQLAlchemy

## 📋 Requisitos

```bash
pip install pandas openpyxl
```

## 🚀 Uso Rápido

### 1. Preparar archivos de datos

- **Excel de operaciones**: Archivo con hojas `Acciones`, `CEDEARs`, `Bonos`, `ONs`
- **PDFs de reportes**: Archivos PDF de brokers con operaciones
- **Chat de transferencias** (opcional): Archivo de texto con historial MEP

### 2. Ejecutar extracción

```python
from sistema_mineria import MineriaDatosFinancieros

# Crear instancia
mineria = MineriaDatosFinancieros()

# Extraer del Excel
mineria.extraer_del_excel("datos_cartera.xlsx")

# Extraer de PDFs
mineria.extraer_de_pdfs(["reporte1.pdf", "reporte2.pdf"])

# Extraer transferencias del chat (opcional)
chat_text = open("historial_chat.txt").read()
mineria.extraer_transferencias_del_chat(chat_text)

# Vincular operaciones con transferencias
mineria.vincular_operaciones_con_transferencias()

# Generar JSONs
mineria.generar_json_completo()
```

### 3. Poblar base de datos Flask

```bash
# Solo Excel
python poblar_base_datos.py datos_cartera.xlsx

# Excel + PDFs
python poblar_base_datos.py datos.xlsx reporte1.pdf reporte2.pdf

# Con chat MEP
python poblar_base_datos.py datos.xlsx reporte.pdf --chat historial.txt
```

## 📊 Formatos Soportados

### Excel - Columnas requeridas

| Hoja     | Columnas principales                                                                                                                |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Acciones | Ticker, Fecha Compra, Precio Compra _, Cantidad, Pesos en compra _, Dólar MEP en la Compra, Fecha Venta, Precio Venta \*, Condición |
| CEDEARs  | (Mismas columnas)                                                                                                                   |
| Bonos    | (Mismas columnas)                                                                                                                   |
| ONs      | (Mismas columnas)                                                                                                                   |

### PDFs - Reportes de Brokers

**Formatos soportados:**

- Reportes de operaciones de brokers argentinos
- Confirmaciones de compra/venta
- Estados de cuenta

**Patrones reconocidos:**

```
Compra GGAL 100 acciones a $1500.50
Venta TSLA 50 CEDEARs a $250.75
15/12/2023 Compra AAPL 200 acciones $180.50
Acción MELI 150 acciones a $1200.00
```

**Librerías requeridas:**

```bash
pip install pdfplumber  # Recomendado
# o
pip install PyPDF2      # Alternativo
```

### Chat - Patrones de transferencias

```
15/12/2023 PUSA $500.000 425,50 USD
16/12/2023 PAGA $300.000 430,25 USD
20/12/2023 TRANSFERENCIA VIA MEP $200.000 TC MEP 435,00
```

## 📈 Archivos Generados

### `transferencias_mep.json`

```json
{
  "metadata": {
    "total_transferencias": 25,
    "fecha_generacion": "2025-12-28T16:15:00",
    "descripcion": "Transferencias MEP extraídas automáticamente"
  },
  "transferencias": [
    {
      "id": 1,
      "tipo": "ENTRADA",
      "fecha": "2023-12-15",
      "monto_pesos": 500000,
      "monto_usd": 1176.47,
      "tc_mep": 425.5,
      "descripcion": "15/12/2023 PUSA $500.000 425,50 USD",
      "procesada": true
    }
  ]
}
```

### `operaciones_completas.json`

```json
{
  "metadata": {
    "total_operaciones": 150,
    "operaciones_activas": 45,
    "operaciones_operadas": 105
  },
  "operaciones": [
    {
      "id_operacion": 1,
      "tipo_activo": "ACCION",
      "ticker": "GGAL",
      "fecha_compra": "2023-12-15",
      "precio_compra_ars": 1500.5,
      "cantidad": 100,
      "total_pesos_compra": 150050,
      "dolar_mep_compra": 425.5,
      "total_usd_compra": 352.94,
      "id_transferencia_compra": 1,
      "tc_mep_compra_real": 425.5,
      "condicion": "Activa"
    }
  ]
}
```

### `dashboard_financiero.json`

```json
{
  "metadata": {
    "fecha_generacion": "2025-12-28T16:15:00",
    "total_operaciones": 150,
    "total_transferencias": 25,
    "total_tickers": 45
  },
  "resumen_general": {
    "total_operaciones": 150,
    "operaciones_activas": 45,
    "total_invertido_usd": 50000,
    "ganancia_perdida_total_usd": 8750.5
  },
  "por_ticker": {
    "GGAL": {
      "operaciones": 5,
      "total_invertido_usd": 12000,
      "rentabilidad_usd": 2100,
      "rentabilidad_pct": 17.5
    }
  },
  "evolucion_mensual": {
    "2023-12": {
      "compras_usd": 35000,
      "ventas_usd": 15000,
      "balance_usd": -5000
    }
  }
}
```

## 🔧 API de Integración

### Métodos principales

```python
class MineriaDatosFinancieros:
    def extraer_del_excel(self, excel_path):
        """Extrae operaciones de todas las hojas del Excel"""

    def extraer_transferencias_del_chat(self, chat_text):
        """Parsea transferencias MEP del texto del chat"""

    def vincular_operaciones_con_transferencias(self):
        """Vincula operaciones con TCs MEP reales"""

    def generar_json_completo(self):
        """Genera todos los archivos JSON"""

    def calcular_resumen(self):
        """Calcula métricas generales"""

    def agrupar_por_ticker(self):
        """Agrupa métricas por ticker"""

    def calcular_evolucion_mensual(self):
        """Calcula evolución temporal"""
```

## 🎯 Integración con Flask

El script `poblar_base_datos.py` integra automáticamente los datos extraídos con la aplicación Flask:

1. **Inicializa** la aplicación y contexto de BD
2. **Extrae** datos del Excel y chat
3. **Crea** entidades básicas (Broker, Comitente, Instrumentos)
4. **Puebla** tabla de Tickers
5. **Carga** operaciones como Activos en BD
6. **Calcula** métricas automáticamente

## 📊 Resultado Final

Después de ejecutar el sistema:

- ✅ **Base de datos poblada** con datos reales
- ✅ **Dashboard funcional** con métricas calculadas
- ✅ **APIs operativas** con datos financieros reales
- ✅ **Reportes exportables** (CSV, Excel, PDF)
- ✅ **Backup completo** en archivos JSON

## 🚀 Próximos Pasos

1. **Instalar dependencias PDF** (opcional):

   ```bash
   pip install pdfplumber  # o PyPDF2
   ```

2. **Ejecutar** `python ejemplo_uso_mineria.py` para ver funcionamiento

3. **Preparar archivos**:

   - Excel con operaciones (hojas: Acciones, CEDEARs, Bonos, ONs)
   - PDFs de reportes de brokers
   - Archivo de chat con transferencias MEP

4. **Ejecutar población**:

   ```bash
   # Solo Excel
   python poblar_base_datos.py datos.xlsx

   # Excel + PDFs
   python poblar_base_datos.py datos.xlsx reporte1.pdf reporte2.pdf

   # Todo junto
   python poblar_base_datos.py datos.xlsx reporte.pdf --chat historial.txt
   ```

5. **Iniciar** aplicación Flask y disfrutar del dashboard con datos reales!

---

**💡 Tips**:

- El sistema procesa automáticamente Excel, PDFs y chat MEP
- Los PDFs se analizan con IA para extraer operaciones financieras
- Las transferencias MEP se vinculan automáticamente con operaciones
- Todo se integra perfectamente con la aplicación Flask existente
