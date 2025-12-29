#!/bin/bash
# scripts/wait-for-db.sh

set -e

host="${DB_HOST:-db}"
port="${DB_PORT:-3306}"
user="${DB_USER:-root}"
password="${DB_PASSWORD}"

echo "🔍 Verificando conexión a MySQL en $host:$port..."

until mysqladmin ping -h"$host" -P"$port" -u"$user" -p"$password" --silent; do
  echo "❌ MySQL no disponible - esperando..."
  sleep 1
done

echo "✅ MySQL disponible!"