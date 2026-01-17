#!/bin/bash
# ==============================================================================
# SCRIPT DE CONFIGURACIÓN DE MONITOREO Y BACKUP
# Cartera Financiera - Setup Completo del Sistema
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ==================== COLORES PARA OUTPUT ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==================== FUNCIONES DE CONFIGURACIÓN ====================

check_dependencies() {
    log_info "Verificando dependencias..."
    
    local deps=("docker" "docker-compose" "curl" "jq")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Dependencias faltantes: ${missing[*]}"
        log_info "Por favor instale las dependencias faltantes e intente nuevamente."
        exit 1
    fi
    
    log_success "Todas las dependencias están disponibles"
}

create_directory_structure() {
    log_info "Creando estructura de directorios..."
    
    local dirs=(
        "$PROJECT_DIR/monitoring"
        "$PROJECT_DIR/monitoring/grafana/provisioning"
        "$PROJECT_DIR/monitoring/grafana/dashboards"
        "$PROJECT_DIR/monitoring/rules"
        "$PROJECT_DIR/monitoring/logs"
        "$PROJECT_DIR/backups"
        "$PROJECT_DIR/logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Directorio creado: $dir"
        fi
    done
    
    log_success "Estructura de directorios creada"
}

setup_environment_variables() {
    log_info "Configurando variables de entorno..."
    
    local env_file="$PROJECT_DIR/.env.monitoring"
    
    cat > "$env_file" << 'EOF'
# ==============================================================================
# VARIABLES DE ENTORNO PARA MONITOREO
# Cartera Financiera - Sistema de Monitoreo y Alertas
# ==============================================================================

# Configuración de Base de Datos
DB_HOST=localhost
DB_PORT=3306
DB_NAME=CarteraFinanciera
DB_USER=root
DB_PASSWORD=your_password_here

# Configuración de Grafana
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_ADMIN_EMAIL=admin@cartera.local

# Configuración de Alertas
DEFAULT_ALERT_EMAIL=admin@cartera.local
CRITICAL_ALERT_EMAIL=admin@cartera.local
DB_TEAM_EMAIL=database@cartera.local
SECURITY_TEAM_EMAIL=security@cartera.local
FINANCE_TEAM_EMAIL=finance@cartera.local
OPS_TEAM_EMAIL=ops@cartera.local

# Slack Integration (Opcional)
SLACK_WEBHOOK_URL=
SLACK_WEBHOOK_URL_CRITICAL=

# SMTP Configuration (Opcional)
SMTP_PASSWORD=
SMTP_SERVER=localhost
SMTP_PORT=587

# Webhook para Integraciones
WEBHOOK_URL=

# URLs de Health Check
HEALTH_CHECK_URL=http://localhost:5000/api/health
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
ALERTMANAGER_URL=http://localhost:9093

# Configuración de Backup
BACKUP_RETENTION_DAYS=30
BACKUP_MAX_SIZE=1G
NOTIFICATION_EMAIL=admin@cartera.local

# Configuración de Servicios Externos
JAEGER_URL=http://localhost:16686
TURBINE_URL=http://localhost:8080
EOF

    log_success "Archivo de variables de entorno creado: $env_file"
    log_warn "IMPORTANTE: Edite $env_file con sus valores reales antes de continuar"
}

create_docker_compose_override() {
    log_info "Creando configuración de Docker Compose..."
    
    local override_file="$PROJECT_DIR/docker-compose.override.yml"
    
    cat > "$override_file" << 'EOF'
version: '3.8'

services:
  # Aplicación principal con configuración de monitoreo
  app:
    environment:
      - FLASK_ENV=production
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir
    volumes:
      - ./monitoring/prometheus_multiproc:/tmp/prometheus_multiproc_dir
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=5000"
      - "prometheus.io/path=/metrics"

  # Base de datos MySQL con exporter
  mysql:
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}

  # Redis con exporter
  redis:
    ports:
      - "6379:6379"
EOF

    log_success "Archivo de override creado: $override_file"
}

setup_crontab() {
    log_info "Configurando cron jobs para backup automático..."
    
    local backup_script="$PROJECT_DIR/scripts/backup_advanced.sh"
    local cron_file="$PROJECT_DIR/crontab.bak"
    
    # Crear crontab backup
    cat > "$cron_file" << EOF
# ==============================================================================
# CRON JOBS PARA CARTERA FINANCIERA
# Sistema de Backup y Monitoreo Automático
# ==============================================================================

# Backup diario a las 2:00 AM
0 2 * * * $backup_script >> $PROJECT_DIR/logs/backup_cron.log 2>&1

# Limpieza de logs antiguos (semanal, domingos a las 3:00 AM)
0 3 * * 0 find $PROJECT_DIR/logs -name "*.log" -mtime +30 -delete

# Verificación de salud del sistema (cada 5 minutos)
*/5 * * * * curl -s http://localhost:5000/api/health > /dev/null

# Reinicio de Prometheus si es necesario (diaria a las 4:00 AM)
0 4 * * * docker restart cartera-prometheus 2>/dev/null || true

# Actualización de dashboards Grafana (semanal, domingos a las 5:00 AM)
0 5 * * 0 curl -X POST http://localhost:3000/api/admin/provisioning/dashboards/reload 2>/dev/null || true
EOF

    # Mostrar instrucciones
    log_success "Archivo de crontab creado: $cron_file"
    log_info "Para instalar los cron jobs, ejecute:"
    log_info "crontab $cron_file"
    log_info "O para ver el contenido:"
    log_info "cat $cron_file"
}

create_monitoring_scripts() {
    log_info "Creando scripts de monitoreo adicionales..."
    
    # Script de verificación de servicios
    cat > "$PROJECT_DIR/scripts/check_services.sh" << 'EOF'
#!/bin/bash
# Verificación rápida de servicios

services=("cartera-app" "cartera-mysql" "cartera-redis" "cartera-prometheus" "cartera-grafana")

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        echo "✅ $service está ejecutándose"
    else
        echo "❌ $service no está ejecutándose"
    fi
done
EOF

    # Script de inicio rápido
    cat > "$PROJECT_DIR/scripts/start_monitoring.sh" << 'EOF'
#!/bin/bash
# Inicio rápido del stack de monitoreo

cd "$(dirname "$0")/.."
docker-compose -f docker-compose.monitoring.yml up -d

echo "Monitoreo iniciado. URLs disponibles:"
echo "- Grafana: http://localhost:3000 (admin/admin123)"
echo "- Prometheus: http://localhost:9090"
echo "- Alertmanager: http://localhost:9093"
echo "- Health Check: http://localhost:5000/api/health"
EOF

    # Script de parada
    cat > "$PROJECT_DIR/scripts/stop_monitoring.sh" << 'EOF'
#!/bin/bash
# Parada del stack de monitoreo

cd "$(dirname "$0")/.."
docker-compose -f docker-compose.monitoring.yml down

echo "Monitoreo detenido."
EOF

    # Hacer scripts ejecutables
    chmod +x "$PROJECT_DIR/scripts/check_services.sh"
    chmod +x "$PROJECT_DIR/scripts/start_monitoring.sh"
    chmod +x "$PROJECT_DIR/scripts/stop_monitoring.sh"
    
    log_success "Scripts de monitoreo creados"
}

create_documentation() {
    log_info "Creando documentación del sistema..."
    
    cat > "$PROJECT_DIR/MONITORING_SETUP.md" << 'EOF'
# Sistema de Monitoreo y Backup - Cartera Financiera

## 🚀 Inicio Rápido

### 1. Configuración Inicial
```bash
# Hacer ejecutables los scripts
chmod +x scripts/*.sh

# Ejecutar setup completo
./scripts/setup_monitoring.sh
```

### 2. Variables de Entorno
Edite `.env.monitoring` con sus configuraciones:
- Credenciales de base de datos
- Emails de notificación
- URLs de servicios

### 3. Iniciar Monitoreo
```bash
# Iniciar stack completo
docker-compose -f docker-compose.monitoring.yml up -d

# O usar script de inicio rápido
./scripts/start_monitoring.sh
```

## 📊 Servicios Disponibles

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Grafana | http://localhost:3000 | admin/admin123 |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Health Check | http://localhost:5000/api/health | - |
| Node Exporter | http://localhost:9100 | - |
| MySQL Exporter | http://localhost:9104 | - |
| Redis Exporter | http://localhost:9121 | - |

## 🔧 Configuración de Alertas

### Email
Configure SMTP en `monitoring/alertmanager.yml`

### Slack
Configure webhook en variables de entorno

### Criterios de Alertas
- **Críticas**: Aplicación down, base de datos no disponible
- **Warning**: Alto uso de CPU/memoria, espacio en disco bajo
- **Info**: Backups completados, servicios reiniciados

## 💾 Backup Automático

### Configuración Manual
```bash
# Ejecutar backup manual
./scripts/backup_advanced.sh

# Ver logs de backup
tail -f logs/backup_$(date +%Y%m%d)*.log
```

### Backup Automático (Cron)
```bash
# Instalar cron jobs
crontab crontab.bak

# Verificar instalación
crontab -l
```

## 🔍 Health Checks

### Endpoints Disponibles
- `/api/health` - Health check básico
- `/api/health/detailed` - Health check detallado
- `/api/metrics` - Métricas para Prometheus
- `/api/status` - Status simple para load balancers

### Monitoreo Automático
- Prometheus monitorea endpoints cada 15s
- Alertmanager envía notificaciones
- Backup automático diario a las 2:00 AM

## 📈 Dashboards Grafana

### Dashboards Incluidos
- **System Overview**: CPU, Memoria, Disco
- **Application Metrics**: Requests, Response Times
- **Database Metrics**: Conexiones, Queries Lentas
- **Financial Application**: APIs específicas de cartera

## 🚨 Alertas Configuradas

### Infraestructura
- CPU > 80%
- Memoria > 85%
- Disco < 15%

### Aplicación
- Aplicación no disponible
- Tiempo de respuesta > 2s
- Tasa de errores HTTP > 5%

### Base de Datos
- MySQL no disponible
- Conexiones > 80% del máximo
- Queries lentas > 0.1/s

### Financiero
- APIs de métricas no disponibles
- Dashboard no accesible
- Errores en cálculos de cartera

## 🔧 Comandos Útiles

```bash
# Verificar servicios
./scripts/check_services.sh

# Reiniciar monitoreo
./scripts/stop_monitoring.sh
./scripts/start_monitoring.sh

# Ver logs de contenedor
docker logs cartera-prometheus
docker logs cartera-grafana

# Ejecutar backup manual
./scripts/backup_advanced.sh

# Verificar health check
curl http://localhost:5000/api/health
```

## 📝 Logs

- **Backup**: `logs/backup_YYYYMMDD_HHMMSS.log`
- **Aplicación**: Configurar en `config.py`
- **Docker**: `docker logs <container_name>`

## 🔒 Seguridad

### Recomendaciones
1. Cambiar credenciales por defecto
2. Configurar HTTPS para Grafana/Prometheus
3. Restringir acceso por IP
4. Configurar autenticación en Alertmanager

### Variables Sensibles
- DB_PASSWORD
- GRAFANA_ADMIN_PASSWORD
- SMTP_PASSWORD

## 🆘 Troubleshooting

### Problemas Comunes

#### Prometheus no recopila datos
```bash
# Verificar targets
curl http://localhost:9090/api/v1/targets

# Reiniciar Prometheus
docker restart cartera-prometheus
```

#### Grafana no carga dashboards
```bash
# Verificar datasource
curl http://localhost:3000/api/datasources

# Recargar provisioning
curl -X POST http://localhost:3000/api/admin/provisioning/dashboards/reload
```

#### Alertas no se envían
```bash
# Verificar configuración Alertmanager
curl http://localhost:9093/api/v1/status

# Ver alertas activas
curl http://localhost:9093/api/v1/alerts
```

## 📞 Soporte

Para problemas o consultas:
1. Revisar logs en `logs/`
2. Verificar health check endpoint
3. Consultar documentación de servicios individuales

---
*Última actualización: $(date)*
EOF

    log_success "Documentación creada: MONITORING_SETUP.md"
}

show_completion_summary() {
    log_success "=========================================="
    log_success "CONFIGURACIÓN COMPLETADA EXITOSAMENTE"
    log_success "=========================================="
    
    echo
    log_info "📁 Archivos creados:"
    echo "  - .env.monitoring (configurar con sus valores)"
    echo "  - docker-compose.override.yml"
    echo "  - crontab.bak (instalar con: crontab crontab.bak)"
    echo "  - MONITORING_SETUP.md (documentación completa)"
    echo
    log_info "🔧 Scripts disponibles:"
    echo "  - ./scripts/start_monitoring.sh"
    echo "  - ./scripts/stop_monitoring.sh"
    echo "  - ./scripts/check_services.sh"
    echo "  - ./scripts/backup_advanced.sh"
    echo
    log_info "⚙️ Próximos pasos:"
    echo "  1. Editar .env.monitoring con sus configuraciones"
    echo "  2. Instalar cron jobs: crontab crontab.bak"
    echo "  3. Iniciar monitoreo: ./scripts/start_monitoring.sh"
    echo "  4. Acceder a Grafana: http://localhost:3000 (admin/admin123)"
    echo
    log_warn "IMPORTANTE: Configure las variables de entorno antes de continuar!"
    echo
}

# ==================== FUNCIÓN PRINCIPAL ====================
main() {
    log_info "Iniciando configuración de sistema de monitoreo y backup..."
    
    check_dependencies
    create_directory_structure
    setup_environment_variables
    create_docker_compose_override
    setup_crontab
    create_monitoring_scripts
    create_documentation
    
    show_completion_summary
}

# ==================== EJECUCIÓN ====================
main "$@"