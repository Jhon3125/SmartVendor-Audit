
from database.repositories.proveedor_repository import obtener_por_ruc
from database.repositories.cotizacion_repository import guardar
from database.repositories.auditoria_repository import (
    crear_auditoria,
    obtener_auditoria,
    crear_evaluacion_ia,
    guardar_resultado_ia,
    registrar_intento_gemini,
    finalizar_intento_gemini,
    actualizar_dictamen,
    listar_evaluaciones,
    listar_intentos,
    listar_historial
)

try:
    print("1. Buscando proveedor...")

    proveedor = obtener_por_ruc("20100047218")

    if not proveedor:
        raise ValueError("No se encontró el proveedor.")

    print("Proveedor:", proveedor["razon_social"])

    print("\n2. Creando cotización...")

    cotizacion_id = guardar(
        proveedor_id=proveedor["id"],
        servicio_cotizado="Servicios de intermediación financiera",
        monto=15000,
        moneda="PEN"
    )

    print("Cotización:", cotizacion_id)

    print("\n3. Creando auditoría...")

    auditoria_id = crear_auditoria(cotizacion_id)

    print("Auditoría:", auditoria_id)

    print("\n4. Creando evaluación de Gemini...")

    evaluacion_id = crear_evaluacion_ia(
        auditoria_id,
        "gemini-4-hydrogen"
    )

    print("Evaluación:", evaluacion_id)

    print("\n5. Simulando intentos de Gemini...")

    for numero in range(1, 3):
        intento_id = registrar_intento_gemini(
            evaluacion_id,
            numero,
            "EN_PROCESO"
        )

        finalizar_intento_gemini(
            intento_id,
            "ERROR",
            codigo_error=503,
            detalle_error="Gemini temporalmente sobrecargado."
        )

    intento_id = registrar_intento_gemini(
        evaluacion_id,
        3,
        "EN_PROCESO"
    )

    finalizar_intento_gemini(
        intento_id,
        "EXITOSO"
    )

    print("Tres intentos registrados.")

    print("\n6. Guardando evaluación simulada...")

    resultado = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "bajo",
        "puntaje_confianza": 95,
        "justificacion": "Existe coherencia entre la actividad y el servicio.",
        "alertas": [],
        "recomendacion": "favorable"
    }

    guardar_resultado_ia(evaluacion_id, resultado)

    print("\n7. Actualizando dictamen...")

    actualizar_dictamen(
        auditoria_id=auditoria_id,
        dictamen="APROBADO",
        nivel_riesgo="BAJO",
        puntaje_confianza=95,
        motivo=resultado["justificacion"],
        observacion="Prueba del repositorio de auditorías.",
        accion="EVALUACION"
    )

    print("Dictamen actualizado.")

    print("\n8. Verificando información...")

    auditoria = obtener_auditoria(auditoria_id)

    print("RUC:", auditoria["ruc"])
    print("Dictamen:", auditoria["dictamen"])
    print("Riesgo:", auditoria["nivel_riesgo"])

    print("Evaluaciones:", len(listar_evaluaciones(auditoria_id)))
    print("Intentos:", len(listar_intentos(evaluacion_id)))
    print("Historial:", len(listar_historial(auditoria_id)))

    print("\nPRUEBA COMPLETADA EXITOSAMENTE")

except Exception as error:
    print("\nERROR EN LA PRUEBA:", error)
