#!/bin/bash
set -e

echo "🚀 Iniciando Cartera Financiera..."

# Espera a la base de datos
if [ -f /usr/local/bin/wait-for-db.sh ]; then
    /usr/local/bin/wait-for-db.sh
fi

echo "🎯 Ejecutando: $@"
exec "$@"
