#!/bin/bash
# ==============================================================================
# SISTEMA DE BACKUP AUTOMATIZADO AVANZADO
# Cartera Financiera - Backup Completo con Monitoreo y Notificaciones
# ==============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ==================== CONFIGURACIÓN ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_DIR}/logs/backup_$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="${PROJECT_DIR}/backups"
DB_NAME="CarteraFinanciera"
DB_USER="${DB_USER:-root}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
RETENTION_DAYS=30
MAX_BACKUP_SIZE="1G"
COMPRESSION_LEVEL=6

# Configuración de notificaciones
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_NOTIFICATION="${EMAIL_NOTIFICATION:-}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-}"

# ==================== FUNCIONES DE UTILIDAD ====================

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

check_dependencies() {
    local deps=("mysqldump" "tar" "gzip" "du" "find" "bc")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            log_error "Dependencia requerida no encontrada: $dep"
            exit 1
        fi
    done
}

create_directories() {
    local dirs=("$BACKUP_DIR" "$(dirname "$LOG_FILE")")
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Directorio creado: $dir"
        fi
    done
}

# ==================== FUNCIONES DE BACKUP ====================

backup_database() {
    local backup_name="database_$(date +%Y%m%d_%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}.sql"
    local compressed_path="${backup_path}.gz"
    
    log_info "Iniciando backup de base de datos..."
    
    # Verificar conectividad a la base de datos
    if ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"${DB_PASSWORD:-}" --silent; then
        log_error "No se puede conectar a la base de datos"
        return 1
    fi
    
    # Crear backup con compresión
    if mysqldump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --user="$DB_USER" \
        --password="${DB_PASSWORD:-}" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --databases "$DB_NAME" | gzip -"$COMPRESSION_LEVEL" > "$compressed_path"; then
        
        local backup_size=$(du -h "$compressed_path" | cut -f1)
        log_success "Backup de base de datos completado: $compressed_path ($backup_size)"
        
        # Verificar integridad del backup
        if verify_backup_integrity "$compressed_path"; then
            echo "$compressed_path" >> "${BACKUP_DIR}/backup_manifest.txt"
            return 0
        else
            log_error "El backup de base de datos está corrupto"
            rm -f "$compressed_path"
            return 1
        fi
    else
        log_error "Error durante el backup de base de datos"
        return 1
    fi
}

backup_application_files() {
    local backup_name="app_files_$(date +%Y%m%d_%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}.tar.gz"
    
    log_info "Iniciando backup de archivos de aplicación..."
    
    # Archivos y directorios a incluir en el backup
    local include_paths=(
        "app.py"
        "config/"
        "routes/"
        "models/"
        "utils/"
        "templates/"
        "static/"
        "*.md"
        "*.txt"
        "*.yml"
        "*.yaml"
        "*.json"
        "*.sql"
        ".env*"
        "Dockerfile"
        "docker-compose.yml"
    )
    
    # Crear archivo tar con exclusión de directorios innecesarios
    local exclude_patterns=(
        --exclude="__pycache__"
        --exclude="*.pyc"
        --exclude=".git"
        --exclude="node_modules"
        --exclude="venv"
        --exclude="env"
        --exclude="*.log"
        --exclude="backups/*"
        --exclude="uploads/*"
        --exclude="*.tmp"
    )
    
    cd "$PROJECT_DIR"
    
    # Crear lista de archivos a incluir
    local temp_include_file=$(mktemp)
    for pattern in "${include_paths[@]}"; do
        find . -maxdepth 3 -name "$pattern" 2>/dev/null >> "$temp_include_file" || true
    done
    
    # Crear backup usando la lista de archivos
    if tar -czf "$backup_path" -T "$temp_include_file" "${exclude_patterns[@]}" 2>/dev/null; then
        local backup_size=$(du -h "$backup_path" | cut -f1)
        log_success "Backup de archivos completado: $backup_path ($backup_size)"
        
        # Verificar integridad del backup
        if verify_backup_integrity "$backup_path"; then
            echo "$backup_path" >> "${BACKUP_DIR}/backup_manifest.txt"
            rm -f "$temp_include_file"
            return 0
        else
            log_error "El backup de archivos está corrupto"
            rm -f "$backup_path" "$temp_include_file"
            return 1
        fi
    else
        log_error "Error durante el backup de archivos"
        rm -f "$temp_include_file"
        return 1
    fi
}

backup_uploaded_files() {
    local backup_name="uploads_$(date +%Y%m%d_%H%M%S)"
    local backup_path="${BACKUP_DIR}/${backup_name}.tar.gz"
    
    log_info "Iniciando backup de archivos subidos..."
    
    if [[ -d "${PROJECT_DIR}/uploads" ]] && [[ -n "$(ls -A "${PROJECT_DIR}/uploads" 2>/dev/null)" ]]; then
        cd "${PROJECT_DIR}/uploads"
        
        if tar -czf "$backup_path" . 2>/dev/null; then
            local backup_size=$(du -h "$backup_path" | cut -f1)
            log_success "Backup de archivos subidos completado: $backup_path ($backup_size)"
            
            if verify_backup_integrity "$backup_path"; then
                echo "$backup_path" >> "${BACKUP_DIR}/backup_manifest.txt"
                return 0
            else
                log_error "El backup de archivos subidos está corrupto"
                rm -f "$backup_path"
                return 1
            fi
        else
            log_error "Error durante el backup de archivos subidos"
            return 1
        fi
    else
        log_info "No hay archivos subidos para hacer backup"
        return 0
    fi
}

# ==================== FUNCIONES DE VERIFICACIÓN ====================

verify_backup_integrity() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        return 1
    fi
    
    # Verificar que el archivo no esté vacío
    if [[ ! -s "$backup_file" ]]; then
        return 1
    fi
    
    # Para archivos comprimidos, verificar que se pueden descomprimir
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file" 2>/dev/null; then
            return 1
        fi
    fi
    
    # Verificar tamaño máximo
    local backup_size_bytes=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo "0")
    local max_size_bytes=$(echo "$MAX_BACKUP_SIZE" | numfmt --from=iec 2>/dev/null || echo "1073741824") # Default 1GB
    
    if [[ $backup_size_bytes -gt $max_size_bytes ]]; then
        log_warn "Backup excede el tamaño máximo: $(numfmt --to=iec $backup_size_bytes) > $MAX_BACKUP_SIZE"
    fi
    
    return 0
}

verify_database_backup() {
    local backup_file="$1"
    
    log_info "Verificando integridad del backup de base de datos..."
    
    # Verificar que se puede leer el contenido del backup
    if ! zcat "$backup_file" | head -n 10 >/dev/null 2>&1; then
        log_error "No se puede leer el backup de base de datos"
        return 1
    fi
    
    # Verificar que contiene las tablas esperadas
    local expected_tables=("activos" "transacciones" "usuarios")
    for table in "${expected_tables[@]}"; do
        if ! zcat "$backup_file" | grep -q "CREATE TABLE.*$table"; then
            log_warn "Tabla $table no encontrada en el backup"
        fi
    done
    
    log_success "Verificación de backup de base de datos completada"
    return 0
}

# ==================== FUNCIONES DE LIMPIEZA ====================

cleanup_old_backups() {
    log_info "Limpiando backups antiguos (>$RETENTION_DAYS días)..."
    
    local deleted_count=0
    local total_size_freed=0
    
    while IFS= read -r -d '' backup_file; do
        if [[ -f "$backup_file" ]]; then
            local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo "0")
            total_size_freed=$((total_size_freed + file_size))
            rm -f "$backup_file"
            ((deleted_count++))
            log_info "Backup eliminado: $(basename "$backup_file")"
        fi
    done < <(find "$BACKUP_DIR" -name "*.gz" -o -name "*.tar.gz" -mtime +$RETENTION_DAYS -print0)
    
    if [[ $deleted_count -gt 0 ]]; then
        log_success "Limpieza completada: $deleted_count archivos eliminados, $(numfmt --to=iec $total_size_freed) liberados"
    else
        log_info "No hay backups antiguos para eliminar"
    fi
}

generate_backup_report() {
    local report_file="${BACKUP_DIR}/backup_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log_info "Generando reporte de backup..."
    
    {
        echo "========================================"
        echo "REPORTE DE BACKUP - $(date)"
        echo "========================================"
        echo ""
        echo "DIRECTORIO DE BACKUP: $BACKUP_DIR"
        echo "DIRECTORIO DEL PROYECTO: $PROJECT_DIR"
        echo ""
        echo "BACKUPS DISPONIBLES:"
        echo "-------------------"
        
        find "$BACKUP_DIR" -name "*.gz" -o -name "*.tar.gz" | sort | while IFS= read -r backup; do
            local file_size=$(du -h "$backup" | cut -f1)
            local file_date=$(stat -f%Sm "$backup" 2>/dev/null || stat -c%y "$backup" 2>/dev/null | cut -d' ' -f1)
            echo "$(basename "$backup") - $file_size - $file_date"
        done
        
        echo ""
        echo "ESTADÍSTICAS:"
        echo "-------------"
        echo "Total de backups: $(find "$BACKUP_DIR" -name "*.gz" -o -name "*.tar.gz" | wc -l)"
        echo "Espacio utilizado: $(du -sh "$BACKUP_DIR" | cut -f1)"
        echo "Espacio disponible: $(df -h "$BACKUP_DIR" | tail -1 | awk '{print $4}')"
        echo ""
        echo "========================================"
    } > "$report_file"
    
    log_success "Reporte generado: $report_file"
}

# ==================== FUNCIONES DE NOTIFICACIÓN ====================

send_slack_notification() {
    local message="$1"
    local color="${2:-good}"
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "Backup Cartera Financiera",
            "text": "$message",
            "ts": $(date +%s)
        }
    ]
}
EOF
)
        
        if curl -X POST -H 'Content-type: application/json' \
            --data "$payload" "$SLACK_WEBHOOK" >/dev/null 2>&1; then
            log_info "Notificación de Slack enviada"
        else
            log_warn "Error enviando notificación de Slack"
        fi
    fi
}

send_email_notification() {
    local subject="$1"
    local message="$2"
    
    if [[ -n "$EMAIL_NOTIFICATION" ]]; then
        {
            echo "Subject: $subject"
            echo "To: $EMAIL_NOTIFICATION"
            echo ""
            echo "$message"
            echo ""
            echo "Log completo disponible en: $LOG_FILE"
        } | sendmail "$EMAIL_NOTIFICATION" 2>/dev/null || {
            log_warn "Error enviando notificación por email"
        }
    fi
}

# ==================== FUNCIÓN PRINCIPAL ====================

perform_health_check() {
    if [[ -n "$HEALTH_CHECK_URL" ]]; then
        log_info "Realizando health check..."
        
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")
        
        if [[ "$response_code" == "200" ]]; then
            log_success "Health check exitoso"
            return 0
        else
            log_warn "Health check falló con código: $response_code"
            return 1
        fi
    else
        log_info "Health check no configurado"
        return 0
    fi
}

main() {
    log_info "=========================================="
    log_info "INICIANDO BACKUP AUTOMATIZADO AVANZADO"
    log_info "Fecha: $(date)"
    log_info "Directorio: $PROJECT_DIR"
    log_info "=========================================="
    
    # Verificar dependencias
    check_dependencies
    
    # Crear directorios necesarios
    create_directories
    
    # Realizar health check previo
    if ! perform_health_check; then
        log_warn "Health check previo falló, continuando con backup..."
    fi
    
    # Variables de estado
    local backup_success=true
    local total_backups=0
    local successful_backups=0
    
    # Ejecutar backups
    log_info "Iniciando proceso de backup..."
    
    # Backup de base de datos
    if backup_database; then
        ((successful_backups++))
    else
        backup_success=false
    fi
    ((total_backups++))
    
    # Backup de archivos de aplicación
    if backup_application_files; then
        ((successful_backups++))
    else
        backup_success=false
    fi
    ((total_backups++))
    
    # Backup de archivos subidos
    if backup_uploaded_files; then
        ((successful_backups++))
    fi
    ((total_backups++))
    
    # Limpiar backups antiguos
    cleanup_old_backups
    
    # Generar reporte
    generate_backup_report
    
    # Resultado final
    log_info "=========================================="
    if $backup_success; then
        log_success "BACKUP COMPLETADO EXITOSAMENTE"
        log_info "Backups realizados: $successful_backups/$total_backups"
        
        send_slack_notification "✅ Backup completado exitosamente ($successful_backups/$total_backups)" "good"
        send_email_notification "Backup Exitoso - Cartera Financiera" \
            "El backup se completó exitosamente.\n\nBackups realizados: $successful_backups/$total_backups\nLog: $LOG_FILE"
        
    else
        log_error "BACKUP COMPLETADO CON ERRORES"
        log_info "Backups exitosos: $successful_backups/$total_backups"
        
        send_slack_notification "⚠️ Backup completado con errores ($successful_backups/$total_backups)" "warning"
        send_email_notification "Backup con Errores - Cartera Financiera" \
            "El backup se completó con algunos errores.\n\nBackups exitosos: $successful_backups/$total_backups\nLog: $LOG_FILE"
    fi
    
    log_info "Log completo disponible en: $LOG_FILE"
    log_info "=========================================="
    
    # Realizar health check posterior
    perform_health_check
    
    # Exit code basado en el éxito
    if $backup_success && [[ $successful_backups -eq $total_backups ]]; then
        exit 0
    else
        exit 1
    fi
}

# ==================== EJECUCIÓN ====================
main "$@"