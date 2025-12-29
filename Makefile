# Makefile para Cartera Financiera

.PHONY: help install test lint format clean run start stop logs shell git-init docker-build docker-run docker-dev docker-stop docker-logs docker-shell

help:
	@echo "🚀 COMANDOS DISPONIBLES:"
	@echo ""
	@echo "📋 DESARROLLO:"
	@echo "  make install      - Instalar dependencias"
	@echo "  make run          - Ejecutar aplicación Flask"
	@echo "  make start        - Iniciar aplicación (fondo)"
	@echo "  make stop         - Detener aplicación"
	@echo "  make logs         - Ver logs de la aplicación"
	@echo "  make shell        - Abrir shell en contenedor"
	@echo ""
	@echo "🧪 CALIDAD DE CÓDIGO:"
	@echo "  make test         - Ejecutar tests"
	@echo "  make lint         - Verificar código (flake8)"
	@echo "  make format       - Formatear código (black)"
	@echo "  make security     - Verificar seguridad (bandit)"
	@echo ""
	@echo "🗂️ GIT:"
	@echo "  make git-init     - Inicializar repositorio Git"
	@echo "  make git-status   - Ver estado de Git"
	@echo "  make git-commit   - Commit con hooks automáticos"
	@echo ""
	@echo "🐳 DOCKER:"
	@echo "  make docker-build - Construir imagen Docker"
	@echo "  make docker-run   - Ejecutar con Docker (producción)"
	@echo "  make docker-dev   - Ejecutar desarrollo con Docker"
	@echo "  make docker-stop  - Detener contenedores Docker"
	@echo "  make docker-logs  - Ver logs de contenedores"
	@echo "  make docker-shell - Abrir shell en contenedor"
	@echo ""
	@echo "🧹 MANTENIMIENTO:"
	@echo "  make clean        - Limpiar archivos temporales"
	@echo "  make backup       - Crear backup de BD"
	@echo "  make reset-db     - Resetear base de datos"
	@echo ""

# Instalación de dependencias
install:
	@echo "📦 Instalando dependencias..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

# Ejecutar aplicación
run:
	@echo "🚀 Iniciando aplicación Flask..."
	python app.py

# Iniciar en background
start:
	@echo "🚀 Iniciando aplicación en background..."
	nohup python app.py > app.log 2>&1 &
	@echo "✅ Aplicación iniciada (PID: $$(pgrep -f 'python app.py'))"

# Detener aplicación
stop:
	@echo "🛑 Deteniendo aplicación..."
	-pkill -f "python app.py"
	@echo "✅ Aplicación detenida"

# Ver logs
logs:
	@echo "📋 Mostrando logs de la aplicación:"
	@if [ -f app.log ]; then tail -f app.log; else echo "No hay logs disponibles"; fi

# Abrir shell
shell:
	@echo "🐚 Abriendo shell..."
	bash

# Ejecutar tests
test:
	@echo "🧪 Ejecutando tests..."
	pytest --cov=. --cov-report=html --cov-report=term -v

# Verificar código
lint:
	@echo "🔍 Verificando estilo de código..."
	flake8 . --max-line-length=88 --extend-ignore=E203,W503
	@echo "✅ Linting completado"

# Formatear código
format:
	@echo "📝 Formateando código..."
	black . --line-length=88
	isort .
	@echo "✅ Código formateado"

# Verificar seguridad
security:
	@echo "🔒 Verificando seguridad..."
	bandit -r . -f json -o security-report.json
	@echo "✅ Verificación de seguridad completada"

# Git inicialización
git-init:
	@echo "🔄 Inicializando Git..."
	git init
	git branch -m main
	@echo "✅ Git inicializado"

# Estado de Git
git-status:
	@echo "📋 Estado de Git:"
	git status

# Commit con hooks
git-commit:
	@echo "💾 Creando commit..."
	@if [ -z "$$(git status --porcelain)" ]; then \
		echo "⚠️ No hay cambios para commit"; \
	else \
		git add .; \
		read -p "📝 Mensaje de commit: " msg; \
		git commit -m "$$msg"; \
		echo "✅ Commit creado"; \
	fi

# Limpiar archivos temporales
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
	rm -f *.log security-report.json 2>/dev/null || true
	@echo "✅ Limpieza completada"

# Crear backup
backup:
	@echo "💾 Creando backup..."
	@if [ -f instance/cartera.db ]; then \
		cp instance/cartera.db "backup/cartera_$$(date +%Y%m%d_%H%M%S).db"; \
		echo "✅ Backup creado en backup/"; \
	else \
		echo "⚠️ Base de datos no encontrada"; \
	fi

# Resetear base de datos
reset-db:
	@echo "🔄 Reseteando base de datos..."
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	rm -f instance/cartera.db
	python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Base de datos reseteada')"
	@echo "✅ Base de datos reseteada"

# COMANDOS DOCKER

# Construir imagen Docker
docker-build:
	@echo "🐳 Construyendo imagen Docker..."
	docker build -t cartera-financiera .
	@echo "✅ Imagen Docker construida"

# Ejecutar en producción con Docker
docker-run:
	@echo "🐳 Ejecutando con Docker (producción)..."
	@if [ ! -f .env ]; then \
		echo "⚠️ Archivo .env no encontrado, copiando .env.template"; \
		cp .env.template .env; \
	fi
	docker-compose up -d
	@echo "✅ Aplicación ejecutándose en http://localhost"

# Setup completo automático
setup-docker:
	@echo "🚀 Configuración automática Docker..."
	./setup-docker.sh

# Ejecutar en desarrollo con Docker
docker-dev:
	@echo "🐳 Ejecutando desarrollo con Docker..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Desarrollo ejecutándose en http://localhost:5000"
	@echo "📊 phpMyAdmin disponible en http://localhost:8080"

# Ver estado de contenedores
docker-status:
	@echo "📊 Estado de contenedores:"
	docker-compose -f docker-compose.dev.yml ps

# Reiniciar solo la aplicación
docker-restart-app:
	@echo "🔄 Reiniciando aplicación..."
	docker-compose -f docker-compose.dev.yml restart app

# Detener contenedores Docker
docker-stop:
	@echo "🛑 Deteniendo contenedores Docker..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down
	@echo "✅ Contenedores detenidos"

# Ver logs de contenedores
docker-logs:
	@echo "📋 Mostrando logs de contenedores:"
	docker-compose logs -f

# Abrir shell en contenedor
docker-shell:
	@echo "🐚 Abriendo shell en contenedor..."
	docker-compose exec app bash

# Desarrollo completo
dev: clean install
	@echo "🚀 Configuración de desarrollo lista"
	@echo "Ejecuta 'make run' para iniciar la aplicación"