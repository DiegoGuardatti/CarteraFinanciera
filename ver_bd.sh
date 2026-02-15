#!/bin/bash
echo "=== CARTERA FINANCIERA - BASE DE DATOS ==="
echo ""

echo "📊 TABLAS EXISTENTES:"
mysql -h 127.0.0.1 -P 3306 -u cartera_user -pRootDevPass123! -e "USE CarteraFinanciera; SHOW TABLES;" 2>/dev/null

echo ""
echo "👥 USUARIOS:"
mysql -h 127.0.0.1 -P 3306 -u cartera_user -pRootDevPass123! -e "SELECT * FROM CarteraFinanciera.usuarios;" 2>/dev/null

echo ""
echo "💰 TRANSACCIONES (primeras 10):"
mysql -h 127.0.0.1 -P 3306 -u cartera_user -pRootDevPass123! -e "SELECT * FROM CarteraFinanciera.transacciones LIMIT 10;" 2>/dev/null

echo ""
echo "🏷️  CATEGORÍAS:"
mysql -h 127.0.0.1 -P 3306 -u cartera_user -pRootDevPass123! -e "SELECT * FROM CarteraFinanciera.categorias;" 2>/dev/null

echo ""
echo "📈 ESTADÍSTICAS:"
mysql -h 127.0.0.1 -P 3306 -u cartera_user -pRootDevPass123! -e "
USE CarteraFinanciera;
SELECT 
    (SELECT COUNT(*) FROM usuarios) as total_usuarios,
    (SELECT COUNT(*) FROM transacciones) as total_transacciones,
    (SELECT COUNT(*) FROM categorias) as total_categorias;
" 2>/dev/null
