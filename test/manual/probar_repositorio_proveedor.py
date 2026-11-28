
from database.repositories.proveedor_repository import (
    obtener_por_ruc,
    guardar_o_actualizar
)


proveedor_prueba = {
    "ruc": "20100047218",
    "razon_social": "BANCO DE CREDITO DEL PERU",
    "estado": "ACTIVO",
    "condicion": "HABIDO",
    "direccion": "JR. CENTENARIO NRO 156",
    "tipo_contribuyente": "SOCIEDAD ANONIMA",
    "actividad_economica": "OTROS TIPOS DE INTERMEDIACION MONETARIA",
    "numero_trabajadores": "21202",
    "tipo_facturacion": "MANUAL",
    "tipo_contabilidad": "COMPUTARIZADO",
    "comercio_exterior": "SIN ACTIVIDAD",
    "actividad_economica_verificada": True
}

try:
    print("Guardando proveedor...")

    proveedor = guardar_o_actualizar(proveedor_prueba)

    print("\nPROVEEDOR GUARDADO CORRECTAMENTE")
    print(proveedor)

    print("\nVerificando búsqueda por RUC...")

    resultado = obtener_por_ruc("20100047218")

    if resultado:
        print("PROVEEDOR ENCONTRADO")
        print("Razón social:", resultado["razon_social"])
        print("RUC:", resultado["ruc"])
    else:
        print("No se encontró el proveedor.")

except Exception as error:
    print("ERROR:", error)
