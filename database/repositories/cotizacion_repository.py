
from decimal import Decimal, InvalidOperation

from database.connection import get_connection


def guardar(proveedor_id, servicio_cotizado, monto, moneda="PEN", lote_id=None):
    """Registra una cotización asociada a un proveedor."""

    if not proveedor_id:
        raise ValueError("El proveedor_id es obligatorio.")

    if not servicio_cotizado or not servicio_cotizado.strip():
        raise ValueError("El servicio cotizado es obligatorio.")

    try:
        monto = Decimal(str(monto))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("El monto debe ser numérico.")

    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero.")

    moneda = str(moneda).strip().upper()

    if moneda not in ("PEN", "USD", "EUR"):
        raise ValueError("La moneda debe ser PEN, USD o EUR.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO cotizaciones (
                proveedor_id,
                lote_id,
                servicio_cotizado,
                monto,
                moneda
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                proveedor_id,
                lote_id,
                servicio_cotizado.strip(),
                monto,
                moneda
            )
        )

        cotizacion_id = cursor.lastrowid
        connection.commit()

        return cotizacion_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def obtener_por_id(cotizacion_id):
    """Obtiene una cotización por su identificador."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                c.*,
                p.ruc,
                p.razon_social
            FROM cotizaciones c
            INNER JOIN proveedores p
                ON p.id = c.proveedor_id
            WHERE c.id = %s
            """,
            (cotizacion_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def listar_por_proveedor(proveedor_id):
    """Lista las cotizaciones registradas para un proveedor."""

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                c.*,
                p.ruc,
                p.razon_social
            FROM cotizaciones c
            INNER JOIN proveedores p
                ON p.id = c.proveedor_id
            WHERE c.proveedor_id = %s
            ORDER BY c.creada_en DESC
            """,
            (proveedor_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()
