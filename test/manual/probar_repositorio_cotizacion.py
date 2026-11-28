
from database.repositories.proveedor_repository import obtener_por_ruc
from database.repositories.cotizacion_repository import (
    guardar,
    obtener_por_id,
    listar_por_proveedor
)


try:
    print("Buscando proveedor...")

    proveedor = obtener_por_ruc("20100047218")

    if not proveedor:
        raise ValueError("No existe el proveedor de prueba en MySQL.")

    proveedor_id = proveedor["id"]

    print("Proveedor:", proveedor["razon_social"])

    print("\nRegistrando cotización...")

    cotizacion_id = guardar(
        proveedor_id=proveedor_id,
        servicio_cotizado="Servicios de intermediación financiera",
        monto=15000,
        moneda="PEN"
    )

    print("Cotización registrada. ID:", cotizacion_id)

    print("\nConsultando cotización...")

    cotizacion = obtener_por_id(cotizacion_id)

    print("RUC:", cotizacion["ruc"])
    print("Servicio:", cotizacion["servicio_cotizado"])
    print("Monto:", cotizacion["monto"])
    print("Moneda:", cotizacion["moneda"])

    print("\nListando cotizaciones del proveedor...")

    cotizaciones = listar_por_proveedor(proveedor_id)

    print("Total de cotizaciones:", len(cotizaciones))

    print("\nPRUEBA COMPLETADA EXITOSAMENTE")

except Exception as error:
    print("ERROR:", error)
