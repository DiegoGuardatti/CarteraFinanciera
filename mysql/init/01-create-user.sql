-- Crear usuario específico para la aplicación
CREATE USER IF NOT EXISTS 'cartera_user'@'%' IDENTIFIED BY 'RootDevPass123!';

-- Dar permisos a la base de datos específica
GRANT ALL PRIVILEGES ON CarteraFinanciera.* TO 'cartera_user'@'%';

-- Para desarrollo, también dar permisos de proceso
GRANT PROCESS ON *.* TO 'cartera_user'@'%';

-- Aplicar cambios
FLUSH PRIVILEGES;
