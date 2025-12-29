#!/bin/bash

# Script de Backup Automático para Cartera Financiera
# Crear backups automáticos de la base de datos MySQL/phpMyAdmin
# Configurar en cron para ejecución automática

# ==========================================
# CONFIGURACIÓN
# ==========================================

# Configuración de base de datos (ajustar según tu entorno)
DB_HOST="localhost"
DB_PORT="3306"
DB_USER="root"
DB_NAME="CarteraFinanciera"
DB_PASSWORD=""  # Si tienes password, agregar aquí o usar .my.cnf

# Configuración de backup
BACKUP_DIR="/media/diego/DiscoViejo1/home/diego/Documentos/Cartera Finaciera/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cartera_backup_${DATE}.sql"
RETENTION_DAYS=30  # Mantener backups por 30 días

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# ==========================================
# FUNCIONES
# ==========================================

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cleanup_old_backups() {
    log_message "Limpiando backups antiguos (>${RETENTION_DAYS} días)..."
    find "$BACKUP_DIR" -name "cartera_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    log_message "Limpieza completada"
}

create_backup() {
    log_message "Iniciando backup de la base de datos..."
    
    # Crear el backup con mysqldump
    mysqldump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --user="$DB_USER" \
        --password="$DB_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-database \
        --databases "$DB_NAME" > "$BACKUP_DIR/$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log_message "Backup creado exitosamente: $BACKUP_DIR/$BACKUP_FILE"
        
        # Comprimir el backup para ahorrar espacio
        gzip "$BACKUP_DIR/$BACKUP_FILE"
        COMPRESSED_FILE="${BACKUP_FILE}.gz"
        log_message "Backup comprimido: $COMPRESSED_FILE"
        
        # Mostrar tamaño del archivo
        SIZE=$(du -h "$BACKUP_DIR/$COMPRESSED_FILE" | cut -f1)
        log_message "Tamaño del backup: $SIZE"
        
        # Verificar integridad del backup comprimido
        if gunzip -t "$BACKUP_DIR/$COMPRESSED_FILE"; then
            log_message "Verificación de integridad: OK"
        else
            log_message "ERROR: Backup corrupto!"
            exit 1
        fi
        
    else
        log_message "ERROR: Fallo al crear backup"
        exit 1
    fi
}

test_backup() {
    log_message "Probando integridad del backup..."
    
    # Listar archivos de backup recientes
    log_message "Backups disponibles:"
    ls -la "$BACKUP_DIR"/cartera_backup_*.sql.gz 2>/dev/null | tail -5
    
    # Verificar estructura del backup más reciente
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/cartera_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        log_message "Verificando último backup: $(basename "$LATEST_BACKUP")"
        
        # Extraer primeras líneas para verificar estructura
        gunzip -c "$LATEST_BACKUP" | head -20 | grep -E "(CREATE TABLE|INSERT INTO|Database:|--)" | head -10
    fi
}

show_statistics() {
    log_message "Estadísticas del sistema de backup:"
    
    # Contar backups
    TOTAL_BACKUPS=$(ls "$BACKUP_DIR"/cartera_backup_*.sql.gz 2>/dev/null | wc -l)
    log_message "Total de backups: $TOTAL_BACKUPS"
    
    # Tamaño total
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    log_message "Espacio total usado: $TOTAL_SIZE"
    
    # Backup más reciente
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/cartera_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        LATEST_DATE=$(date -r "$LATEST_BACKUP" '+%Y-%m-%d %H:%M:%S')
        log_message "Último backup: $LATEST_DATE"
    fi
}

# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

case "${1:-backup}" in
    "backup")
        log_message "=== INICIANDO BACKUP CARTERA FINANCIERA ==="
        create_backup
        cleanup_old_backups
        test_backup
        log_message "=== BACKUP COMPLETADO EXITOSAMENTE ==="
        ;;
    
    "cleanup")
        log_message "=== LIMPIEZA DE BACKUPS ANTIGUOS ==="
        cleanup_old_backups
        show_statistics
        ;;
    
    "test")
        log_message "=== PRUEBA DE INTEGRIDAD ==="
        test_backup
        show_statistics
        ;;
    
    "stats")
        show_statistics
        ;;
    
    "help"|"-h"|"--help")
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos disponibles:"
        echo "  backup    - Crear backup completo (por defecto)"
        echo "  cleanup   - Limpiar backups antiguos"
        echo "  test      - Probar integridad de backups"
        echo "  stats     - Mostrar estadísticas"
        echo "  help      - Mostrar esta ayuda"
        echo ""
        echo "Configuración actual:"
        echo "  Base de datos: $DB_NAME"
        echo "  Directorio backup: $BACKUP_DIR"
        echo "  Retención: $RETENTION_DAYS días"
        echo ""
        echo "Para configurar backup automático, agregar a crontab:"
        echo "  0 2 * * * /path/to/backup_cartera.sh backup"
        echo "  0 3 * * 0 /path/to/backup_cartera.sh cleanup"
        ;;
    
    *)
        log_message "Comando desconocido: $1"
        log_message "Usa '$0 help' para ver comandos disponibles"
        exit 1
        ;;
esac