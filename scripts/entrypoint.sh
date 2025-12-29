#!/bin/bash
# scripts/entrypoint.sh

set -e

echo "🚀 Iniciando Cartera Financiera..."

# Esperar a que la base de datos esté lista
echo "⏳ Esperando base de datos..."
/usr/local/bin/wait-for-db.sh

# Ejecutar migraciones si es necesario
echo "🔄 Ejecutando migraciones..."
if [ "$FLASK_ENV" = "production" ]; then
    flask db upgrade || echo "⚠️ Migraciones no disponibles"
fi

# Inicializar datos si es necesario
if [ "$INIT_DATA" = "true" ]; then
    echo "📊 Inicializando datos de prueba..."
    python poblar_base_datos.py || echo "⚠️ Error poblando datos"
fi

echo "✅ Aplicación lista!"
exec "$@"