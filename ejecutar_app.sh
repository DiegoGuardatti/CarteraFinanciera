#!/bin/bash

# ==========================================
# SCRIPT DE INICIO - CARTERA FINANCIERA
# Configuración completa con optimizaciones
# ==========================================

echo "🚀 Cartera Financiera - Sistema Completo"
echo "========================================"

# Función para verificar comandos
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Python
if ! command_exists python3; then
    echo "❌ Error: Python3 no está instalado"
    exit 1
fi

# Crear y activar entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install -q -r requirements.txt

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p logs uploads

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado, copiando template..."
    cp .env.template .env
    echo "✅ Archivo .env creado. Revisa y configura las variables."
fi

# Ejecutar optimizaciones de MySQL (opcional)
read -p "¿Ejecutar optimizaciones MySQL? (recomendado) [Y/n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "🔧 Ejecutando optimizaciones de MySQL..."
    
    # Instalar PyMySQL si no está disponible
    python -c "import pymysql" 2>/dev/null || pip install pymysql
    
    # Ejecutar script de optimización en modo automático
    python ejecutar_optimizaciones_mysql.py --auto
    
    if [ $? -eq 0 ]; then
        echo "✅ Optimizaciones MySQL completadas"
    else
        echo "⚠️  Optimizaciones MySQL fallaron. Continuando sin optimizaciones..."
    fi
fi

# Ejecutar migraciones de base de datos
if [ -d "migrations" ]; then
    echo "🔄 Ejecutando migraciones de base de datos..."
    flask db upgrade
fi

# Verificar conexión a base de datos
echo "🔍 Verificando conexión a base de datos..."
python -c "
import sys
sys.path.append('.')
from modelo import db
from app import app
try:
    with app.app_context():
        db.create_all()
        print('✅ Base de datos verificada')
except Exception as e:
    print(f'❌ Error en base de datos: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Error en la verificación de base de datos"
    exit 1
fi

echo ""
echo "🌐 Iniciando servidor Flask..."
echo "📊 URLs disponibles:"
echo "   • http://localhost:5000/           - Página principal"
echo "   • http://localhost:5000/dashboard   - Dashboard básico"
echo "   • http://localhost:5000/dashboard_avanzado - Dashboard avanzado"
echo "   • http://localhost:5000/compra     - Registrar compra"
echo "   • http://localhost:5000/venta      - Registrar venta"
echo "   • http://localhost:5000/informe     - Informes"
echo ""
echo "📈 APIs disponibles:"
echo "   • GET /api/dashboard/summary        - Resumen ejecutivo"
echo "   • GET /api/metrics/portfolio       - ROI cartera"
echo "   • GET /api/metrics/tir/{id}        - TIR activo"
echo "   • GET /api/metrics/beta/{id}       - Beta activo"
echo "   • GET /api/metrics/alpha/{id}      - Alpha activo"
echo "   • GET /api/advanced/summary        - Métricas avanzadas"
echo ""
echo "🎯 Presiona Ctrl+C para detener el servidor"
echo "========================================"

# Iniciar Flask
python app.py
