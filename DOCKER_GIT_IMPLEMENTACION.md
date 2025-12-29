# 🐳 DOCKERIZACIÓN Y GIT - PLAN DE IMPLEMENTACIÓN

## 🎯 OBJETIVO

Implementar Docker para containerización completa del proyecto y configurar Git con hooks, CI/CD y mejores prácticas de desarrollo.

## 📋 DOCKERIZACIÓN COMPLETA

### 1. 🏗️ Estructura de Docker

```
CarteraFinanciera/
├── Dockerfile                    # Imagen principal de la aplicación
├── docker-compose.yml           # Orquestación completa
├── docker-compose.dev.yml       # Desarrollo
├── docker-compose.prod.yml      # Producción
├── .dockerignore               # Archivos excluidos
├── nginx/                      # Configuración Nginx
│   ├── nginx.conf
│   └── default.conf
└── scripts/                    # Scripts de Docker
    ├── entrypoint.sh
    └── wait-for-db.sh
```

### 2. 📄 Dockerfile Principal

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app
USER app

# Copiar requirements y instalar dependencias Python
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copiar código de la aplicación
COPY --chown=app:app . .

# Crear directorios necesarios
RUN mkdir -p instance logs uploads
RUN chmod 755 instance logs uploads

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/dashboard/summary || exit 1

# Script de entrada
COPY --chown=app:app scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### 3. 🐳 Docker Compose Completo

```yaml
# docker-compose.yml
version: "3.8"

services:
  # Aplicación principal
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=mysql+pymysql://root:${DB_PASSWORD}@db:3306/CarteraFinanciera
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./instance:/app/instance
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/dashboard/summary"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Base de datos MySQL
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: CarteraFinanciera
      MYSQL_USER: ${DB_USER:-cartera_user}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  # Cache Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Proxy reverso Nginx
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      app:
        condition: service_healthy
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:

networks:
  default:
    name: cartera_network
```

### 4. 🚀 Docker Compose para Desarrollo

```yaml
# docker-compose.dev.yml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - DATABASE_URL=sqlite:///instance/cartera_dev.db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - /app/__pycache__
    command: ["flask", "run", "--host=0.0.0.0", "--port=5000"]
    depends_on:
      redis:
        condition: service_started

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # phpMyAdmin para desarrollo
  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    ports:
      - "8080:80"
    environment:
      PMA_HOST: db
      PMA_USER: root
      PMA_PASSWORD: ${DB_PASSWORD}
    depends_on:
      - db
```

### 5. 🔧 Scripts de Docker

```bash
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
```

```bash
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
```

### 6. ⚙️ Configuración Nginx

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:5000;
    }

    include /etc/nginx/conf.d/*.conf;
}
```

```nginx
# nginx/default.conf
server {
    listen 80;
    server_name localhost;

    client_max_body_size 10M;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # APIs
    location /api/ {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Archivos estáticos
    location /static/ {
        proxy_pass http://app;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://app;
        access_log off;
    }
}
```

### 7. 📄 .dockerignore

```
.git
.gitignore
README.md
*.md
.env
.env.local
.pytest_cache
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.env
.venv
pip-log.txt
.DS_Store
.vscode
.idea
*.swp
*.swo
node_modules
npm-debug.log
docker-compose*.yml
Dockerfile
.dockerignore
coverage
.coverage
htmlcov
.tox
.cache
nosetests.xml
translations
*.log
instance/cartera.db
instance/cartera_dev.db
```

---

## 🔄 CONFIGURACIÓN GIT AVANZADA

### 1. 📋 .gitignore Completo

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Database
instance/
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log
*.log.*

# Cache
.cache/
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Docker
.dockerignore
docker-compose*.yml

# SSL certificates
ssl/
*.pem
*.key
*.crt

# Backups
backup/
*.backup
*.bak

# Uploads
uploads/*
!uploads/.gitkeep
```

### 2. 🔧 Git Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Ejecutando pre-commit hooks..."

# Formatear código Python con black
if command -v black &> /dev/null; then
    echo "📝 Formateando código con black..."
    black --line-length 88 --target-version py39 .
fi

# Verificar estilo con flake8
if command -v flake8 &> /dev/null; then
    echo "🔍 Verificando estilo con flake8..."
    flake8 . --max-line-length=88 --extend-ignore=E203,W503
fi

# Ejecutar tests
if command -v pytest &> /dev/null; then
    echo "🧪 Ejecutando tests..."
    pytest --maxfail=1 --disable-warnings
fi

# Verificar seguridad con bandit
if command -v bandit &> /dev/null; then
    echo "🔒 Verificando seguridad con bandit..."
    bandit -r . -f json -o bandit-report.json
fi

echo "✅ Pre-commit hooks completados"
```

```bash
#!/bin/bash
# .git/hooks/pre-push

echo "🚀 Ejecutando pre-push hooks..."

# Ejecutar todos los tests
echo "🧪 Ejecutando suite completa de tests..."
pytest --cov=. --cov-report=xml --cov-report=html

# Verificar cobertura mínima (80%)
coverage_threshold=80
current_coverage=$(coverage report | tail -1 | awk '{print $4}' | sed 's/%//')
echo "📊 Cobertura actual: $current_coverage%"

if (( $(echo "$current_coverage < $coverage_threshold" | bc -l) )); then
    echo "❌ Cobertura insuficiente: $current_coverage% (mínimo: $coverage_threshold%)"
    exit 1
fi

echo "✅ Pre-push hooks completados"
```

### 3. 📝 GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test_password
          MYSQL_DATABASE: test_cartera
        ports:
          - 3306/tcp
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3

      redis:
        image: redis:7-alpine
        ports:
          - 6379/tcp
        options: --health-cmd="redis-cli ping" --health-interval=10s --health-timeout=5s --health-retries=3

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Install development dependencies
        run: |
          pip install pytest pytest-cov black flake8 bandit factory-boy

      - name: Lint with flake8
        run: |
          flake8 . --max-line-length=88 --extend-ignore=E203,W503

      - name: Format check with black
        run: |
          black --check --diff .

      - name: Security check with bandit
        run: |
          bandit -r . -f json -o bandit-report.json

      - name: Run tests
        env:
          DATABASE_URL: mysql+pymysql://root:test_password@localhost:3306/test_cartera
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html --cov-report=term

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            cartera-financiera:latest
            cartera-financiera:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: [test, build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: |
          echo "🚀 Deploying to production..."
          # Aquí irían los comandos de deploy
          # kubectl apply -f k8s/
          # o comandos de deploy específicos
```

### 4. 📋 requirements-dev.txt

```txt
# Testing
pytest==7.4.0
pytest-flask==1.2.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==19.12.0

# Code quality
black==23.9.1
flake8==6.1.0
flake8-docstrings==1.7.0
flake8-import-order==0.18.2
isort==5.12.0

# Security
bandit==1.7.5
safety==2.3.4

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==1.3.0
```

### 5. 📊 Makefile para Desarrollo

```makefile
# Makefile

.PHONY: help install test lint format clean docker-build docker-run

help:
	@echo "🚀 Comandos disponibles:"
	@echo "  install     - Instalar dependencias"
	@echo "  test        - Ejecutar tests"
	@echo "  lint        - Verificar código"
	@echo "  format      - Formatear código"
	@echo "  clean       - Limpiar archivos temporales"
	@echo "  docker-build - Construir imagen Docker"
	@echo "  docker-run  - Ejecutar con Docker"
	@echo "  docker-dev  - Ejecutar desarrollo con Docker"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest --cov=. --cov-report=html --cov-report=term

lint:
	flake8 . --max-line-length=88
	black --check .
	bandit -r .

format:
	black . --line-length=88
	isort .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docker-build:
	docker build -t cartera-financiera .

docker-run:
	docker-compose up -d

docker-dev:
	docker-compose -f docker-compose.dev.yml up -d

docker-stop:
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

docker-logs:
	docker-compose logs -f app

docker-shell:
	docker-compose exec app bash
```

---

## 🚀 COMANDOS DE IMPLEMENTACIÓN

### 1. 📦 Configuración Inicial

```bash
# 1. Configurar Git
git init
git add .
git commit -m "Initial commit"

# 2. Crear .gitignore y hooks
cp .gitignore.example .gitignore
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push

# 3. Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# 4. Configurar pre-commit
pip install pre-commit
pre-commit install
```

### 2. 🐳 Docker

```bash
# Construir imagen
docker build -t cartera-financiera .

# Ejecutar en desarrollo
docker-compose -f docker-compose.dev.yml up -d

# Ejecutar en producción
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Acceder al contenedor
docker-compose exec app bash
```

### 3. 🧪 Testing

```bash
# Ejecutar todos los tests
make test

# Tests con coverage
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/unit/test_models.py -v
```

### 4. 📋 CI/CD

```bash
# Configurar GitHub Actions
# El archivo .github/workflows/ci.yml se ejecuta automáticamente

# Verificar workflow localmente (opcional)
pip install act
act push
```

---

## 🎯 BENEFICIOS ESPERADOS

### Docker

- ✅ **Portabilidad**: Funciona igual en cualquier entorno
- ✅ **Consistencia**: Mismo comportamiento dev/prod
- ✅ **Escalabilidad**: Fácil escalado horizontal
- ✅ **Aislamiento**: Entornos aislados
- ✅ **Deploy**: Despliegue simplificado

### Git + CI/CD

- ✅ **Calidad**: Código siempre validado
- ✅ **Automatización**: Tests y deploy automáticos
- ✅ **Seguridad**: Verificaciones de seguridad automáticas
- ✅ **Documentación**: Historial completo
- ✅ **Colaboración**: Flujo de trabajo estructurado

---

**La implementación de Docker y Git completará la infraestructura profesional del proyecto, permitiendo desarrollo, testing y deployment automatizados.**
