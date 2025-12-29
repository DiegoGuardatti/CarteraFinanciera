#!/bin/bash
# setup-docker.sh - Script de configuración automática para Docker

set -e

echo "🚀 CONFIGURACIÓN AUTOMÁTICA DOCKER - CARTERA FINANCIERA"
echo "=================================================="

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️ Archivo .env no encontrado. Copiando desde .env.template..."
    cp .env.template .env
    echo "✅ Archivo .env creado. Puedes editarlo para ajustar la configuración."
fi

echo ""
echo "🔧 Paso 1: Construyendo imagen Docker..."
docker-compose -f docker-compose.dev.yml build

echo ""
echo "🗄️ Paso 2: Iniciando servicios (MySQL, Redis, App)..."
docker-compose -f docker-compose.dev.yml up -d

echo ""
echo "⏳ Paso 3: Esperando que MySQL esté listo..."
sleep 10

# Verificar que MySQL esté funcionando
echo "🔍 Verificando MySQL..."
until docker-compose -f docker-compose.dev.yml exec -T db mysqladmin ping -h"localhost" --silent; do
    echo "  ⏳ MySQL no está listo - esperando..."
    sleep 2
done
echo "✅ MySQL está funcionando!"

# Verificar que Redis esté funcionando
echo "🔍 Verificando Redis..."
until docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping | grep -q PONG; do
    echo "  ⏳ Redis no está listo - esperando..."
    sleep 2
done
echo "✅ Redis está funcionando!"

echo ""
echo "📊 Paso 4: Creando estructura de base de datos..."
docker-compose -f docker-compose.dev.yml exec -T app python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Base de datos inicializada')
"

echo ""
echo "🎯 CONFIGURACIÓN COMPLETADA!"
echo "=================================================="
echo "🌐 Aplicación: http://localhost:5000"
echo "📊 phpMyAdmin: http://localhost:8080"
echo "🗄️ MySQL: localhost:3307"
echo "💾 Redis: localhost:6379"
echo ""
echo "📋 COMANDOS ÚTILES:"
echo "  make docker-dev     - Iniciar desarrollo"
echo "  make docker-stop    - Detener servicios"
echo "  make docker-logs    - Ver logs"
echo "  make docker-shell   - Abrir shell en contenedor"
echo ""
echo "🔧 Para detener todo: docker-compose -f docker-compose.dev.yml down"
echo "🗑️ Para limpiar todo: docker-compose -f docker-compose.dev.yml down -v"
echo ""
echo "✅ ¡Proyecto listo para usar!"