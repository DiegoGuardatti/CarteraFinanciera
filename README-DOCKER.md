# 🐳 GUÍA DE DOCKER - CARTERA FINANCIERA

## 🚀 INICIO RÁPIDO

### Desarrollo Local con Docker

```bash
# 1. Construir imagen
make docker-build

# 2. Ejecutar en desarrollo
make docker-dev

# 3. Acceder a la aplicación
# App: http://localhost:5000
# phpMyAdmin: http://localhost:8080
```

### Producción con Docker

```bash
# 1. Copiar configuración
cp .env.template .env
# Editar .env con tus credenciales

# 2. Ejecutar en producción
make docker-run

# 3. Acceder a la aplicación
# App: http://localhost
```

## 📋 COMANDOS DISPONIBLES

### Construcción y Ejecución

```bash
make docker-build    # Construir imagen Docker
make docker-run      # Ejecutar producción con Docker
make docker-dev      # Ejecutar desarrollo con Docker
make docker-stop     # Detener todos los contenedores
make docker-logs     # Ver logs en tiempo real
make docker-shell    # Abrir shell en contenedor
```

### Gestión Manual

```bash
# Construir imagen manualmente
docker build -t cartera-financiera .

# Ejecutar servicios
docker-compose up -d

# Desarrollo
docker-compose -f docker-compose.dev.yml up -d

# Ver logs
docker-compose logs -f app

# Acceder al contenedor
docker-compose exec app bash

# Detener servicios
docker-compose down
```

## 🏗️ ARQUITECTURA

### Servicios en Producción

- **app**: Aplicación Flask con Gunicorn
- **db**: Base de datos MySQL 8.0
- **redis**: Cache Redis
- **nginx**: Proxy reverso

### Servicios en Desarrollo

- **app**: Aplicación Flask en modo desarrollo
- **redis**: Cache Redis
- **phpmyadmin**: Interfaz web para MySQL

## 📁 ESTRUCTURA DE DIRECTORIOS

```
CarteraFinanciera/
├── Dockerfile                    # Imagen principal
├── docker-compose.yml           # Orquestación producción
├── docker-compose.dev.yml       # Orquestación desarrollo
├── .dockerignore               # Archivos excluidos
├── nginx/                      # Configuración Nginx
│   ├── nginx.conf
│   └── default.conf
├── scripts/                    # Scripts de Docker
│   ├── entrypoint.sh
│   └── wait-for-db.sh
├── logs/                       # Logs de aplicación
├── uploads/                    # Archivos subidos
├── ssl/                        # Certificados SSL
└── mysql/init/                 # Scripts de inicialización BD
```

## ⚙️ CONFIGURACIÓN

### Variables de Entorno (.env)

```bash
# Base de datos
DB_PASSWORD=tu_password_seguro
DB_USER=cartera_user

# Aplicación
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta

# Cache
REDIS_URL=redis://redis:6379/0
```

### Personalización

#### Modificar configuración de la aplicación

1. Editar `docker-compose.yml` o `docker-compose.dev.yml`
2. Ajustar variables de entorno
3. Reiniciar contenedores: `make docker-stop && make docker-run`

#### Agregar inicialización de BD

1. Crear scripts SQL en `mysql/init/`
2. Los scripts se ejecutan automáticamente al crear el contenedor

#### Configurar SSL

1. Colocar certificados en `ssl/`
2. Configurar Nginx para HTTPS
3. Actualizar `nginx/default.conf`

## 🔧 SOLUCIÓN DE PROBLEMAS

### Contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs app

# Verificar estado de contenedores
docker-compose ps

# Reiniciar contenedor específico
docker-compose restart app
```

### Base de datos no conecta

```bash
# Verificar estado de MySQL
docker-compose exec db mysqladmin ping

# Ver logs de MySQL
docker-compose logs db

# Verificar variables de entorno
docker-compose exec app env | grep DB
```

### Problemas de permisos

```bash
# Verificar permisos de directorios
ls -la logs/ uploads/

# Corregir permisos
sudo chown -R $USER:$USER logs/ uploads/
```

### Limpiar Docker

```bash
# Detener y eliminar contenedores
make docker-stop

# Eliminar imágenes (opcional)
docker system prune -a

# Eliminar volúmenes (CUIDADO: elimina datos)
docker-compose down -v
```

## 🚀 DEPLOYMENT

### Servidor de Producción

1. **Configurar servidor**: Ubuntu 20.04+ con Docker
2. **Subir código**: Git clone o rsync
3. **Configurar .env**: Credenciales de producción
4. **Ejecutar**: `make docker-run`
5. **Configurar Nginx**: Proxy reverso en puerto 80/443

### Docker Swarm (Escalado)

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml cartera

# Escalar servicios
docker service scale cartera_app=3
```

### Kubernetes

```bash
# Convertir docker-compose a Kubernetes
kompose convert

# Aplicar manifiestos
kubectl apply -f kubernetes/
```

## 📊 MONITOREO

### Health Checks

- **App**: `http://localhost:5000/api/dashboard/summary`
- **MySQL**: `mysqladmin ping`
- **Redis**: `redis-cli ping`

### Logs

```bash
# Logs de aplicación
make docker-logs

# Logs específicos
docker-compose logs -f app
docker-compose logs -f db
```

### Métricas

- CPU y memoria: `docker stats`
- Espacio en disco: `docker system df`
- Estado de servicios: `docker-compose ps`

## 🔒 SEGURIDAD

### Mejores Prácticas

1. **No usar root**: Usuario no-root en contenedor
2. **Variables de entorno**: Nunca hardcodear credenciales
3. **Puertos limitados**: Solo exponer 80/443 externamente
4. **SSL/TLS**: Usar certificados válidos en producción
5. **Firewall**: Configurar reglas de entrada

### Seguridad en Desarrollo

```bash
# Variables seguras para desarrollo
FLASK_ENV=development
SECRET_KEY=development_key_change_in_production
DEBUG=True
```

## 🆘 SOPORTE

### Problemas Comunes

1. **Puerto en uso**: Cambiar puerto en docker-compose.yml
2. **Memoria insuficiente**: Aumentar RAM del contenedor
3. **Permisos de archivos**: Verificar ownership de directorios

### Logs Útiles

- `docker-compose logs app`: Aplicación Flask
- `docker-compose logs db`: Base de datos MySQL
- `docker-compose logs nginx`: Proxy reverso

### Comandos de Diagnóstico

```bash
# Estado general
docker-compose ps

# Uso de recursos
docker stats

# Conectividad de red
docker network ls
docker network inspect cartera_network

# Espacio en disco
docker system df
```
