
import json

from database.connection import get_connection


def crear_lote(nombre_archivo, total_registros, registros_validos, registros_invalidos):
    """Crea un lote de auditoría masiva."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO lotes_auditoria (
                nombre_archivo,
                total_registros,
                registros_validos,
                registros_invalidos,
                estado
            )
            VALUES (%s, %s, %s, %s, 'PENDIENTE')
            """,
            (
                nombre_archivo,
                total_registros,
                registros_validos,
                registros_invalidos
            )
        )

        lote_id = cursor.lastrowid
        connection.commit()

        return lote_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def actualizar_estado_lote(lote_id, estado):
    """Actualiza el estado de un lote."""

    estados_validos = (
        "PENDIENTE",
        "PROCESANDO",
        "COMPLETADO",
        "COMPLETADO_CON_ERRORES",
        "ERROR"
    )

    if estado not in estados_validos:
        raise ValueError("Estado de lote no válido.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if estado in ("COMPLETADO", "COMPLETADO_CON_ERRORES", "ERROR"):
            cursor.execute(
                """
                UPDATE lotes_auditoria
                SET estado = %s, finalizado_en = NOW()
                WHERE id = %s
                """,
                (estado, lote_id)
            )
        else:
            cursor.execute(
                """
                UPDATE lotes_auditoria
                SET estado = %s, finalizado_en = NULL
                WHERE id = %s
                """,
                (estado, lote_id)
            )

        connection.commit()
        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def guardar_registro_lote(
    lote_id,
    fila_excel,
    datos_originales,
    estado_validacion,
    errores_validacion=None,
    cotizacion_id=None
):
    """Guarda una fila original del Excel, válida o inválida."""

    if estado_validacion not in ("VALIDO", "INVALIDO"):
        raise ValueError("El estado de validación debe ser VALIDO o INVALIDO.")

    if estado_validacion == "INVALIDO" and cotizacion_id is not None:
        raise ValueError("Un registro inválido no puede tener cotización.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO registros_lote (
                lote_id,
                fila_excel,
                datos_originales,
                estado_validacion,
                errores_validacion,
                cotizacion_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                lote_id,
                fila_excel,
                json.dumps(datos_originales, ensure_ascii=False, default=str),
                estado_validacion,
                json.dumps(errores_validacion, ensure_ascii=False, default=str)
                if errores_validacion else None,
                cotizacion_id
            )
        )

        registro_id = cursor.lastrowid
        connection.commit()

        return registro_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def obtener_lote(lote_id):
    """Obtiene los datos generales de un lote."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM lotes_auditoria
            WHERE id = %s
            """,
            (lote_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def listar_lotes():
    """Lista los lotes registrados, del más reciente al más antiguo."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM lotes_auditoria
            ORDER BY creado_en DESC
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def listar_registros_lote(lote_id):
    """Lista todas las filas originales de un lote."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM registros_lote
            WHERE lote_id = %s
            ORDER BY fila_excel ASC
            """,
            (lote_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()
