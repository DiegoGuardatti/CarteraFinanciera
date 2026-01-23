#!/bin/bash
cd ~/Repositorios/CarteraFinanciera

echo "🛑 Deteniendo contenedores anteriores..."
docker-compose down -v 2>/dev/null

echo "🗑️  Limpiando..."
docker system prune -f 2>/dev/null

echo "🐳 Iniciando base de datos..."
docker-compose up -d db

echo "⏳ Esperando a que MySQL esté listo..."
for i in {1..30}; do
    if docker-compose exec db mysqladmin ping -u root -pRootDevPass123! --silent; then
        echo "✅ MySQL listo!"
        break
    fi
    echo "⏰ Esperando... ($i/30)"
    sleep 2
done

echo "🚀 Iniciando aplicación y servicios..."
docker-compose up -d

echo "📊 Verificando..."
docker-compose ps

echo ""
echo "✅ ¡Listo! Accede a:"
echo "   🌐 Aplicación: http://localhost:5000"
echo "   🗄️  MySQL: localhost:3306"
echo "       - Root: root / RootDevPass123!"
echo "       - App: cartera_user / RootDevPass123!"
echo "   🔥 Redis: localhost:6379"
echo ""
echo "📝 Para ver logs: docker-compose logs -f app"
