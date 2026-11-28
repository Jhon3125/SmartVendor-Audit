
from database.repositories.lote_repository import (
    crear_lote,
    actualizar_estado_lote,
    guardar_registro_lote,
    obtener_lote,
    listar_lotes,
    listar_registros_lote
)

try:
    print("Creando lote de prueba...")

    lote_id = crear_lote(
        nombre_archivo="prueba_proveedores.xlsx",
        total_registros=2,
        registros_validos=1,
        registros_invalidos=1
    )

    print("Lote creado:", lote_id)

    print("\nGuardando registro válido...")

    guardar_registro_lote(
        lote_id=lote_id,
        fila_excel=2,
        datos_originales={
            "ruc": "20100047218",
            "servicio_cotizado": "Intermediación financiera",
            "monto": 15000,
            "moneda": "PEN"
        },
        estado_validacion="VALIDO"
    )

    print("\nGuardando registro inválido...")

    guardar_registro_lote(
        lote_id=lote_id,
        fila_excel=3,
        datos_originales={
            "ruc": "123",
            "servicio_cotizado": "Consultoría",
            "monto": 2000
        },
        estado_validacion="INVALIDO",
        errores_validacion=["El RUC debe tener 11 dígitos."]
    )

    actualizar_estado_lote(lote_id, "COMPLETADO")

    print("\nConsultando lote...")

    lote = obtener_lote(lote_id)
    print("Archivo:", lote["nombre_archivo"])
    print("Estado:", lote["estado"])

    registros = listar_registros_lote(lote_id)

    print("\nRegistros guardados:", len(registros))

    for registro in registros:
        print(
            f"Fila {registro['fila_excel']}: "
            f"{registro['estado_validacion']}"
        )

    print("\nTotal de lotes:", len(listar_lotes()))

    print("\nPRUEBA COMPLETADA EXITOSAMENTE")

except Exception as error:
    print("ERROR:", error)
