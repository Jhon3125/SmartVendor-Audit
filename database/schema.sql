-- ============================================================
-- SMARTVENDOR AUDIT
-- Esquema inicial de base de datos para MySQL 8.0.16+
-- ============================================================

CREATE DATABASE IF NOT EXISTS smartvendor_audit
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE smartvendor_audit;

-- ------------------------------------------------------------
-- 1. PROVEEDORES
-- Un registro único por RUC.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS proveedores (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ruc CHAR(11) NOT NULL,
    razon_social VARCHAR(255) NULL,
    estado VARCHAR(50) NULL,
    condicion VARCHAR(50) NULL,
    direccion VARCHAR(500) NULL,
    tipo_contribuyente VARCHAR(150) NULL,
    actividad_economica VARCHAR(500) NULL,
    numero_trabajadores VARCHAR(50) NULL,
    tipo_facturacion VARCHAR(100) NULL,
    tipo_contabilidad VARCHAR(100) NULL,
    comercio_exterior VARCHAR(150) NULL,
    actividad_verificada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_ultima_consulta DATETIME NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_proveedores_ruc (ruc),
    KEY idx_proveedores_razon_social (razon_social),
    CONSTRAINT chk_proveedores_ruc
        CHECK (ruc REGEXP '^[0-9]{11}$')
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 2. CONSULTAS_FUENTE
-- Historial de consultas a OpenRUC y Decolecta.
-- Permite controlar caché, errores y trazabilidad de fuentes.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS consultas_fuente (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    proveedor_id BIGINT UNSIGNED NOT NULL,
    fuente VARCHAR(30) NOT NULL,
    exitosa BOOLEAN NOT NULL DEFAULT FALSE,
    datos_respuesta JSON NULL,
    error TEXT NULL,
    consultado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_consultas_proveedor_fecha (proveedor_id, consultado_en),
    KEY idx_consultas_fuente_fecha (fuente, consultado_en),
    CONSTRAINT fk_consultas_proveedor
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_consultas_fuente
        CHECK (fuente IN ('OPENRUC', 'DECOLECTA'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 3. LOTES_AUDITORIA
-- Un lote representa un archivo Excel procesado.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lotes_auditoria (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre_archivo VARCHAR(255) NOT NULL,
    total_registros INT UNSIGNED NOT NULL DEFAULT 0,
    registros_validos INT UNSIGNED NOT NULL DEFAULT 0,
    registros_invalidos INT UNSIGNED NOT NULL DEFAULT 0,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizado_en DATETIME NULL,

    PRIMARY KEY (id),
    KEY idx_lotes_estado_fecha (estado, creado_en),
    CONSTRAINT chk_lotes_estado
        CHECK (estado IN ('PENDIENTE', 'PROCESANDO', 'COMPLETADO', 'COMPLETADO_CON_ERRORES', 'ERROR'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 4. COTIZACIONES
-- Cada fila válida del Excel o auditoría individual genera
-- una cotización asociada a un proveedor.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cotizaciones (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    proveedor_id BIGINT UNSIGNED NOT NULL,
    lote_id BIGINT UNSIGNED NULL,
    servicio_cotizado TEXT NOT NULL,
    monto DECIMAL(15,2) NOT NULL,
    moneda CHAR(3) NOT NULL DEFAULT 'PEN',
    creada_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_cotizaciones_proveedor_fecha (proveedor_id, creada_en),
    KEY idx_cotizaciones_lote (lote_id),
    CONSTRAINT fk_cotizaciones_proveedor
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_cotizaciones_lote
        FOREIGN KEY (lote_id) REFERENCES lotes_auditoria(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_cotizaciones_monto
        CHECK (monto > 0),
    CONSTRAINT chk_cotizaciones_moneda
        CHECK (moneda IN ('PEN', 'USD', 'EUR'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 5. REGISTROS_LOTE
-- Conserva todas las filas originales del Excel, incluso las
-- inválidas. cotizacion_id solo se completa para filas válidas.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS registros_lote (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    lote_id BIGINT UNSIGNED NOT NULL,
    fila_excel INT UNSIGNED NOT NULL,
    datos_originales JSON NOT NULL,
    estado_validacion VARCHAR(15) NOT NULL,
    errores_validacion JSON NULL,
    cotizacion_id BIGINT UNSIGNED NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_registro_lote_fila (lote_id, fila_excel),
    UNIQUE KEY uq_registro_cotizacion (cotizacion_id),
    KEY idx_registros_lote_estado (lote_id, estado_validacion),
    CONSTRAINT fk_registros_lote
        FOREIGN KEY (lote_id) REFERENCES lotes_auditoria(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_registros_cotizacion
        FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT chk_registros_estado_validacion
        CHECK (estado_validacion IN ('VALIDO', 'INVALIDO'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 6. AUDITORIAS
-- Una auditoría principal por cotización. Dictamen representa
-- el resultado vigente; el historial conserva cambios previos.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS auditorias (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    cotizacion_id BIGINT UNSIGNED NOT NULL,
    dictamen VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE_VALIDACION',
    nivel_riesgo VARCHAR(20) NULL,
    puntaje_confianza TINYINT UNSIGNED NOT NULL DEFAULT 0,
    motivo TEXT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    creada_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizada_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_auditorias_cotizacion (cotizacion_id),
    KEY idx_auditorias_dictamen_fecha (dictamen, actualizada_en),
    CONSTRAINT fk_auditorias_cotizacion
        FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_auditorias_dictamen
        CHECK (dictamen IN ('APROBADO', 'OBSERVADO', 'RECHAZADO', 'PENDIENTE_VALIDACION')),
    CONSTRAINT chk_auditorias_riesgo
        CHECK (nivel_riesgo IS NULL OR nivel_riesgo IN ('BAJO', 'MEDIO', 'ALTO', 'No determinado')),
    CONSTRAINT chk_auditorias_confianza
        CHECK (puntaje_confianza BETWEEN 0 AND 100),
    CONSTRAINT chk_auditorias_estado
        CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'COMPLETADA', 'ERROR'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 7. EVALUACIONES_IA
-- Cada evaluación de Gemini queda registrada. Una auditoría
-- puede tener varias evaluaciones por reprocesamientos.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evaluaciones_ia (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    auditoria_id BIGINT UNSIGNED NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    coherencia_comercial VARCHAR(40) NULL,
    nivel_riesgo VARCHAR(20) NULL,
    puntaje_confianza TINYINT UNSIGNED NULL,
    recomendacion VARCHAR(30) NULL,
    justificacion TEXT NULL,
    alertas JSON NULL,
    respuesta JSON NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    error TEXT NULL,
    creada_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_evaluaciones_auditoria_fecha (auditoria_id, creada_en),
    KEY idx_evaluaciones_estado (estado, creada_en),
    CONSTRAINT fk_evaluaciones_auditoria
        FOREIGN KEY (auditoria_id) REFERENCES auditorias(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_evaluaciones_coherencia
        CHECK (
            coherencia_comercial IS NULL OR
            coherencia_comercial IN (
                'coherente',
                'parcialmente_coherente',
                'incoherente',
                'insuficiente'
            )
        ),
    CONSTRAINT chk_evaluaciones_riesgo
        CHECK (nivel_riesgo IS NULL OR nivel_riesgo IN ('bajo', 'medio', 'alto')),
    CONSTRAINT chk_evaluaciones_recomendacion
        CHECK (
            recomendacion IS NULL OR
            recomendacion IN ('favorable', 'revisar', 'desfavorable')
        ),
    CONSTRAINT chk_evaluaciones_confianza
        CHECK (puntaje_confianza IS NULL OR puntaje_confianza BETWEEN 0 AND 100),
    CONSTRAINT chk_evaluaciones_estado
        CHECK (estado IN ('PENDIENTE', 'EXITOSA', 'ERROR'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 8. INTENTOS_GEMINI
-- Un registro por cada llamada, incluidos reintentos 503/429.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intentos_gemini (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    evaluacion_id BIGINT UNSIGNED NOT NULL,
    numero_intento TINYINT UNSIGNED NOT NULL,
    estado VARCHAR(20) NOT NULL,
    codigo_error INT NULL,
    detalle_error TEXT NULL,
    iniciado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizado_en DATETIME NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_intento_evaluacion_numero (evaluacion_id, numero_intento),
    KEY idx_intentos_estado_fecha (estado, iniciado_en),
    CONSTRAINT fk_intentos_evaluacion
        FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones_ia(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_intentos_estado
        CHECK (estado IN ('EN_PROCESO', 'EXITOSO', 'ERROR'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ------------------------------------------------------------
-- 9. HISTORIAL_AUDITORIAS
-- Registra creación, finalización y reprocesamientos.
-- No reemplaza el resultado vigente de auditorias.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS historial_auditorias (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    auditoria_id BIGINT UNSIGNED NOT NULL,
    dictamen_anterior VARCHAR(30) NULL,
    dictamen_nuevo VARCHAR(30) NOT NULL,
    accion VARCHAR(30) NOT NULL,
    observacion TEXT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_historial_auditoria_fecha (auditoria_id, creado_en),
    KEY idx_historial_dictamen_fecha (dictamen_nuevo, creado_en),
    CONSTRAINT fk_historial_auditoria
        FOREIGN KEY (auditoria_id) REFERENCES auditorias(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_historial_dictamen_anterior
        CHECK (
            dictamen_anterior IS NULL OR
            dictamen_anterior IN (
                'APROBADO',
                'OBSERVADO',
                'RECHAZADO',
                'PENDIENTE_VALIDACION'
            )
        ),
    CONSTRAINT chk_historial_dictamen_nuevo
        CHECK (
            dictamen_nuevo IN (
                'APROBADO',
                'OBSERVADO',
                'RECHAZADO',
                'PENDIENTE_VALIDACION'
            )
        ),
    CONSTRAINT chk_historial_accion
        CHECK (accion IN ('CREACION', 'EVALUACION', 'REPROCESAMIENTO', 'CAMBIO_DICTAMEN'))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================
-- FIN DEL ESQUEMA
-- ============================================================
