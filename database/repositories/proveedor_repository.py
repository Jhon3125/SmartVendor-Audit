
from database.connection import get_connection


def obtener_por_ruc(ruc):
    """Busca un proveedor por su RUC."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM proveedores
            WHERE ruc = %s
            """,
            (ruc,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def guardar(proveedor):
    """Inserta un proveedor nuevo."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO proveedores (
                ruc,
                razon_social,
                estado,
                condicion,
                direccion,
                tipo_contribuyente,
                actividad_economica,
                numero_trabajadores,
                tipo_facturacion,
                tipo_contabilidad,
                comercio_exterior,
                actividad_verificada,
                fecha_ultima_consulta
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, NOW()
            )
            """,
            (
                proveedor.get("ruc"),
                proveedor.get("razon_social"),
                proveedor.get("estado"),
                proveedor.get("condicion"),
                proveedor.get("direccion"),
                proveedor.get("tipo_contribuyente"),
                proveedor.get("actividad_economica"),
                proveedor.get("numero_trabajadores"),
                proveedor.get("tipo_facturacion"),
                proveedor.get("tipo_contabilidad"),
                proveedor.get("comercio_exterior"),
                proveedor.get("actividad_economica_verificada", False)
            )
        )

        connection.commit()
        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def actualizar(proveedor):
    """Actualiza los datos de un proveedor existente."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE proveedores
            SET
                razon_social = %s,
                estado = %s,
                condicion = %s,
                direccion = %s,
                tipo_contribuyente = %s,
                actividad_economica = %s,
                numero_trabajadores = %s,
                tipo_facturacion = %s,
                tipo_contabilidad = %s,
                comercio_exterior = %s,
                actividad_verificada = %s,
                fecha_ultima_consulta = NOW()
            WHERE ruc = %s
            """,
            (
                proveedor.get("razon_social"),
                proveedor.get("estado"),
                proveedor.get("condicion"),
                proveedor.get("direccion"),
                proveedor.get("tipo_contribuyente"),
                proveedor.get("actividad_economica"),
                proveedor.get("numero_trabajadores"),
                proveedor.get("tipo_facturacion"),
                proveedor.get("tipo_contabilidad"),
                proveedor.get("comercio_exterior"),
                proveedor.get("actividad_economica_verificada", False),
                proveedor.get("ruc")
            )
        )

        connection.commit()
        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def guardar_o_actualizar(proveedor):
    """Inserta el proveedor o actualiza sus datos si el RUC existe."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO proveedores (
                ruc,
                razon_social,
                estado,
                condicion,
                direccion,
                tipo_contribuyente,
                actividad_economica,
                numero_trabajadores,
                tipo_facturacion,
                tipo_contabilidad,
                comercio_exterior,
                actividad_verificada,
                fecha_ultima_consulta
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, NOW()
            )
            ON DUPLICATE KEY UPDATE
                razon_social = VALUES(razon_social),
                estado = VALUES(estado),
                condicion = VALUES(condicion),
                direccion = VALUES(direccion),
                tipo_contribuyente = VALUES(tipo_contribuyente),
                actividad_economica = VALUES(actividad_economica),
                numero_trabajadores = VALUES(numero_trabajadores),
                tipo_facturacion = VALUES(tipo_facturacion),
                tipo_contabilidad = VALUES(tipo_contabilidad),
                comercio_exterior = VALUES(comercio_exterior),
                actividad_verificada = VALUES(actividad_verificada),
                fecha_ultima_consulta = NOW()
            """,
            (
                proveedor.get("ruc"),
                proveedor.get("razon_social"),
                proveedor.get("estado"),
                proveedor.get("condicion"),
                proveedor.get("direccion"),
                proveedor.get("tipo_contribuyente"),
                proveedor.get("actividad_economica"),
                proveedor.get("numero_trabajadores"),
                proveedor.get("tipo_facturacion"),
                proveedor.get("tipo_contabilidad"),
                proveedor.get("comercio_exterior"),
                proveedor.get("actividad_economica_verificada", False)
            )
        )

        connection.commit()

        return obtener_por_ruc(proveedor.get("ruc"))

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
