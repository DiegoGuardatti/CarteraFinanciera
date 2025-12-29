-- Script de Optimización MySQL para Cartera Financiera
-- Ejecutar en phpMyAdmin > Pestaña SQL
-- Este script optimiza la base de datos existente para reportes rápidos
-- ==========================================
-- 1. ÍNDICES PARA CONSULTAS RÁPIDAS
-- ==========================================
-- Índice para consultas de reportes frecuentes (estado + fecha)
CREATE INDEX idx_activo_estado_fecha ON activo(Activo_Estado, Fecha_Hora_Compra);
-- Índice para análisis de tickers por estado
CREATE INDEX idx_activo_ticker_estado ON activo(Id_Ticker, Activo_Estado);
-- Índice para cálculo de ROI rápido
CREATE INDEX idx_activo_broker_comitente ON activo(Id_Broker, Id_Comitente);
-- Índice para join rápido entre tablas relacionadas
CREATE INDEX idx_ticker_instrumento ON ticker(Id_InstrumentoFinanciero);
CREATE INDEX idx_comitente_broker ON comitente(Id_Broker);
-- ==========================================
-- 2. VISTAS PRE-CALCULADAS PARA REPORTES
-- ==========================================
-- Vista para resumen rápido de cartera con ROI calculado
CREATE VIEW vista_resumen_cartera AS
SELECT a.Id_Activo,
    a.Id_Broker,
    a.Id_Comitente,
    a.Id_Ticker,
    b.Nombre as Nombre_Broker,
    c.Titular as Nombre_Comitente,
    t.Nombre_Ticker,
    t.Descripcion as Descripcion_Ticker,
    i.Nombre as Nombre_Instrumento,
    a.Fecha_Hora_Compra,
    a.Precio_Compra,
    a.Cantidad_Nominales_Compra,
    a.Total_Pesos_Compra,
    a.Total_Dolares_Compra,
    a.Fecha_Hora_Venta,
    a.Precio_Venta,
    a.Cantidad_Nominales_Venta,
    a.Total_Pesos_Venta,
    a.Total_Dolares_Venta,
    a.Activo_Estado,
    -- Cálculo de ROI en la vista
    CASE
        WHEN a.Precio_Venta IS NOT NULL
        AND a.Cantidad_Nominales_Venta IS NOT NULL THEN ROUND(
            (
                (
                    a.Precio_Venta * a.Cantidad_Nominales_Venta - a.Precio_Compra * a.Cantidad_Nominales_Compra
                ) / (a.Precio_Compra * a.Cantidad_Nominales_Compra)
            ) * 100,
            2
        )
        ELSE NULL
    END as ROI_Porcentaje,
    -- Valor actual del activo
    CASE
        WHEN a.Activo_Estado = 'EN_CARTERA' THEN a.Precio_Compra * a.Cantidad_Nominales_Compra
        WHEN a.Activo_Estado = 'VENDIDO'
        AND a.Precio_Venta IS NOT NULL THEN a.Precio_Venta * COALESCE(
            a.Cantidad_Nominales_Venta,
            a.Cantidad_Nominales_Compra
        )
        ELSE 0
    END as Valor_Actual
FROM activo a
    JOIN broker b ON a.Id_Broker = b.Id_Broker
    JOIN comitente c ON a.Id_Comitente = c.Id_Comitente
    JOIN ticker t ON a.Id_Ticker = t.Id_Ticker
    JOIN instrumento_financiero i ON t.Id_InstrumentoFinanciero = i.Id_InstrumentoFinanciero;
-- Vista para performance agregada por ticker
CREATE VIEW vista_performance_ticker AS
SELECT t.Id_Ticker,
    t.Nombre_Ticker,
    t.Descripcion,
    i.Nombre as Instrumento,
    COUNT(a.Id_Activo) as Total_Operaciones,
    SUM(a.Total_Pesos_Compra) as Inversion_Total,
    SUM(
        CASE
            WHEN a.Activo_Estado = 'EN_CARTERA' THEN a.Precio_Compra * a.Cantidad_Nominales_Compra
            WHEN a.Activo_Estado = 'VENDIDO'
            AND a.Precio_Venta IS NOT NULL THEN a.Precio_Venta * COALESCE(
                a.Cantidad_Nominales_Venta,
                a.Cantidad_Nominales_Compra
            )
            ELSE 0
        END
    ) as Valor_Actual_Total,
    ROUND(
        AVG(
            CASE
                WHEN a.Precio_Venta IS NOT NULL
                AND a.Cantidad_Nominales_Venta IS NOT NULL THEN (
                    (
                        a.Precio_Venta * a.Cantidad_Nominales_Venta - a.Precio_Compra * a.Cantidad_Nominales_Compra
                    ) / (a.Precio_Compra * a.Cantidad_Nominales_Compra)
                ) * 100
                ELSE NULL
            END
        ),
        2
    ) as ROI_Promedio
FROM ticker t
    JOIN instrumento_financiero i ON t.Id_InstrumentoFinanciero = i.Id_InstrumentoFinanciero
    LEFT JOIN activo a ON t.Id_Ticker = a.Id_Ticker
GROUP BY t.Id_Ticker,
    t.Nombre_Ticker,
    t.Descripcion,
    i.Nombre;
-- ==========================================
-- 3. STORED PROCEDURES PARA CÁLCULOS
-- ==========================================
DELIMITER // -- Stored Procedure para cálculo de ROI por activo
CREATE PROCEDURE CalcularROIActivo(IN activo_id INT) BEGIN
SELECT a.Id_Activo,
    t.Nombre_Ticker,
    a.Precio_Compra * a.Cantidad_Nominales_Compra as Inversion_Inicial,
    CASE
        WHEN a.Precio_Venta IS NOT NULL
        AND a.Cantidad_Nominales_Venta IS NOT NULL THEN a.Precio_Venta * a.Cantidad_Nominales_Venta
        ELSE a.Precio_Compra * a.Cantidad_Nominales_Compra
    END as Valor_Actual,
    CASE
        WHEN a.Precio_Venta IS NOT NULL
        AND a.Cantidad_Nominales_Venta IS NOT NULL THEN ROUND(
            (
                (
                    a.Precio_Venta * a.Cantidad_Nominales_Venta - a.Precio_Compra * a.Cantidad_Nominales_Compra
                ) / (a.Precio_Compra * a.Cantidad_Nominales_Compra)
            ) * 100,
            2
        )
        ELSE 0
    END as ROI_Porcentaje,
    DATEDIFF(NOW(), a.Fecha_Hora_Compra) as Dias_Posicion
FROM activo a
    JOIN ticker t ON a.Id_Ticker = t.Id_Ticker
WHERE a.Id_Activo = activo_id;
END // -- Stored Procedure para resumen de cartera
CREATE PROCEDURE ResumenCartera() BEGIN
SELECT COUNT(*) as Total_Activos,
    SUM(Total_Pesos_Compra) as Inversion_Total,
    SUM(
        CASE
            WHEN Activo_Estado = 'EN_CARTERA' THEN Precio_Compra * Cantidad_Nominales_Compra
            WHEN Activo_Estado = 'VENDIDO'
            AND Precio_Venta IS NOT NULL THEN Precio_Venta * COALESCE(
                Cantidad_Nominales_Venta,
                Cantidad_Nominales_Compra
            )
            ELSE 0
        END
    ) as Valor_Actual_Total,
    ROUND(
        AVG(
            CASE
                WHEN Precio_Venta IS NOT NULL
                AND Cantidad_Nominales_Venta IS NOT NULL THEN (
                    (
                        Precio_Venta * Cantidad_Nominales_Venta - Precio_Compra * Cantidad_Nominales_Compra
                    ) / (Precio_Compra * Cantidad_Nominales_Compra)
                ) * 100
                ELSE NULL
            END
        ),
        2
    ) as ROI_Promedio,
    COUNT(
        CASE
            WHEN Activo_Estado = 'EN_CARTERA' THEN 1
        END
    ) as Activos_Activos,
    COUNT(
        CASE
            WHEN Activo_Estado = 'VENDIDO' THEN 1
        END
    ) as Activos_Vendidos
FROM activo;
END // DELIMITER;
-- ==========================================
-- 4. CONSULTAS DE VERIFICACIÓN
-- ==========================================
-- Verificar que los índices se crearon correctamente
SHOW INDEX
FROM activo;
SHOW INDEX
FROM ticker;
-- Verificar que las vistas funcionan
SELECT *
FROM vista_resumen_cartera
LIMIT 5;
SELECT *
FROM vista_performance_ticker
LIMIT 5;
-- Probar los stored procedures
-- CALL CalcularROIActivo(1);
-- CALL ResumenCartera();
-- ==========================================
-- 5. TABLA DE BACKUP (OPCIONAL)
-- ==========================================
-- Crear tabla para backups automáticos
CREATE TABLE IF NOT EXISTS backup_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tabla VARCHAR(50) NOT NULL,
    fecha_backup TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    registros_backup INT,
    tamaño_mb DECIMAL(10, 2),
    usuario VARCHAR(50),
    INDEX idx_tabla_fecha (tabla, fecha_backup)
);
-- ==========================================
-- MENSAJE FINAL
-- ==========================================
SELECT 'Optimización MySQL completada exitosamente!' as Status,
    'Índices, vistas y stored procedures creados' as Detalles,
    NOW() as Fecha_Optimizacion;