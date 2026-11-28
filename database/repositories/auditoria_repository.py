
import json

from database.connection import get_connection


DICTAMENES_VALIDOS = (
    "APROBADO",
    "OBSERVADO",
    "RECHAZADO",
    "PENDIENTE_VALIDACION"
)


def crear_auditoria(cotizacion_id):
    """Crea una auditoría inicial para una cotización."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO auditorias (
                cotizacion_id,
                dictamen,
                estado
            )
            VALUES (%s, 'PENDIENTE_VALIDACION', 'PENDIENTE')
            """,
            (cotizacion_id,)
        )

        auditoria_id = cursor.lastrowid
        connection.commit()

        return auditoria_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def obtener_auditoria(auditoria_id):
    """Obtiene una auditoría con los datos de su cotización y proveedor."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                a.*,
                c.servicio_cotizado,
                c.monto,
                c.moneda,
                p.ruc,
                p.razon_social
            FROM auditorias a
            INNER JOIN cotizaciones c
                ON c.id = a.cotizacion_id
            INNER JOIN proveedores p
                ON p.id = c.proveedor_id
            WHERE a.id = %s
            """,
            (auditoria_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def crear_evaluacion_ia(auditoria_id, modelo):
    """Registra una nueva evaluación de Gemini."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO evaluaciones_ia (
                auditoria_id,
                modelo,
                estado
            )
            VALUES (%s, %s, 'PENDIENTE')
            """,
            (auditoria_id, modelo)
        )

        evaluacion_id = cursor.lastrowid
        connection.commit()

        return evaluacion_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def guardar_resultado_ia(evaluacion_id, resultado):
    """Guarda la respuesta exitosa de Gemini."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE evaluaciones_ia
            SET
                coherencia_comercial = %s,
                nivel_riesgo = %s,
                puntaje_confianza = %s,
                recomendacion = %s,
                justificacion = %s,
                alertas = %s,
                respuesta = %s,
                estado = 'EXITOSA',
                error = NULL
            WHERE id = %s
            """,
            (
                resultado.get("coherencia_comercial"),
                resultado.get("nivel_riesgo"),
                resultado.get("puntaje_confianza"),
                resultado.get("recomendacion"),
                resultado.get("justificacion"),
                json.dumps(
                    resultado.get("alertas", []),
                    ensure_ascii=False
                ),
                json.dumps(
                    resultado,
                    ensure_ascii=False,
                    default=str
                ),
                evaluacion_id
            )
        )

        actualizado = cursor.rowcount > 0
        connection.commit()

        return actualizado

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def registrar_error_ia(evaluacion_id, error):
    """Registra el error de una evaluación fallida."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE evaluaciones_ia
            SET estado = 'ERROR',
                error = %s
            WHERE id = %s
            """,
            (str(error), evaluacion_id)
        )

        actualizado = cursor.rowcount > 0
        connection.commit()

        return actualizado

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def registrar_intento_gemini(
    evaluacion_id,
    numero_intento,
    estado,
    codigo_error=None,
    detalle_error=None
):
    """Registra un intento individual de comunicación con Gemini."""

    estados_validos = ("EN_PROCESO", "EXITOSO", "ERROR")

    if estado not in estados_validos:
        raise ValueError("Estado de intento no válido.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO intentos_gemini (
                evaluacion_id,
                numero_intento,
                estado,
                codigo_error,
                detalle_error,
                finalizado_en
            )
            VALUES (
                %s, %s, %s, %s, %s,
                CASE WHEN %s = 'EN_PROCESO'
                     THEN NULL ELSE NOW() END
            )
            """,
            (
                evaluacion_id,
                numero_intento,
                estado,
                codigo_error,
                detalle_error,
                estado
            )
        )

        intento_id = cursor.lastrowid
        connection.commit()

        return intento_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def finalizar_intento_gemini(
    intento_id,
    estado,
    codigo_error=None,
    detalle_error=None
):
    """Actualiza el resultado de un intento previamente iniciado."""

    if estado not in ("EXITOSO", "ERROR"):
        raise ValueError("El estado final debe ser EXITOSO o ERROR.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE intentos_gemini
            SET
                estado = %s,
                codigo_error = %s,
                detalle_error = %s,
                finalizado_en = NOW()
            WHERE id = %s
              AND estado = 'EN_PROCESO'
            """,
            (estado, codigo_error, detalle_error, intento_id)
        )

        actualizado = cursor.rowcount > 0
        connection.commit()

        return actualizado

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def actualizar_dictamen(
    auditoria_id,
    dictamen,
    nivel_riesgo=None,
    puntaje_confianza=0,
    motivo=None,
    observacion=None,
    accion="EVALUACION"
):
    """Actualiza el dictamen vigente y registra el cambio histórico."""

    if dictamen not in DICTAMENES_VALIDOS:
        raise ValueError("Dictamen no válido.")

    if accion not in (
        "CREACION",
        "EVALUACION",
        "REPROCESAMIENTO",
        "CAMBIO_DICTAMEN"
    ):
        raise ValueError("Acción histórica no válida.")

    if not 0 <= puntaje_confianza <= 100:
        raise ValueError("La confianza debe estar entre 0 y 100.")

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT dictamen
            FROM auditorias
            WHERE id = %s
            FOR UPDATE
            """,
            (auditoria_id,)
        )

        auditoria = cursor.fetchone()

        if not auditoria:
            raise ValueError("No existe la auditoría indicada.")

        dictamen_anterior = auditoria["dictamen"]

        cursor.execute(
            """
            UPDATE auditorias
            SET
                dictamen = %s,
                nivel_riesgo = %s,
                puntaje_confianza = %s,
                motivo = %s,
                estado = 'COMPLETADA'
            WHERE id = %s
            """,
            (
                dictamen,
                nivel_riesgo,
                puntaje_confianza,
                motivo,
                auditoria_id
            )
        )

        cursor.execute(
            """
            INSERT INTO historial_auditorias (
                auditoria_id,
                dictamen_anterior,
                dictamen_nuevo,
                accion,
                observacion
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                auditoria_id,
                dictamen_anterior,
                dictamen,
                accion,
                observacion
            )
        )

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def listar_evaluaciones(auditoria_id):
    """Lista las evaluaciones de IA de una auditoría."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM evaluaciones_ia
            WHERE auditoria_id = %s
            ORDER BY creada_en DESC, id DESC
            """,
            (auditoria_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def listar_intentos(evaluacion_id):
    """Lista los intentos de Gemini de una evaluación."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM intentos_gemini
            WHERE evaluacion_id = %s
            ORDER BY numero_intento ASC
            """,
            (evaluacion_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def listar_historial(auditoria_id):
    """Lista el historial de cambios de una auditoría."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM historial_auditorias
            WHERE auditoria_id = %s
            ORDER BY creado_en ASC, id ASC
            """,
            (auditoria_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def listar_auditorias():
    """Lista todas las auditorías con su proveedor, cotización y última evaluación IA."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                a.id AS auditoria_id,
                a.dictamen,
                a.nivel_riesgo,
                a.puntaje_confianza,
                a.motivo,
                a.estado,
                a.creada_en,
                a.actualizada_en,

                c.servicio_cotizado,
                c.monto,
                c.moneda,
                c.lote_id,

                p.ruc,
                p.razon_social,
                p.estado AS estado_tributario,
                p.condicion,
                p.actividad_economica,

                e.id AS evaluacion_id,
                e.coherencia_comercial,
                e.nivel_riesgo AS riesgo_ia,
                e.recomendacion,
                e.estado AS estado_gemini,
                e.error AS error_gemini

            FROM auditorias a

            INNER JOIN cotizaciones c
                ON c.id = a.cotizacion_id

            INNER JOIN proveedores p
                ON p.id = c.proveedor_id

            LEFT JOIN evaluaciones_ia e
                ON e.id = (
                    SELECT MAX(e2.id)
                    FROM evaluaciones_ia e2
                    WHERE e2.auditoria_id = a.id
                )

            ORDER BY a.id DESC
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()
