
def normalizar(valor):
    return str(valor or "").strip().upper()


def crear_resultado(
    dictamen,
    nivel_riesgo,
    motivo,
    alertas=None,
    puntaje_confianza=0
):
    return {
        "dictamen": dictamen,
        "nivel_riesgo": nivel_riesgo,
        "motivo": motivo,
        "alertas": alertas or [],
        "puntaje_confianza": puntaje_confianza
    }


def generar_dictamen(datos_tributarios, evaluacion_ia):

    if not isinstance(datos_tributarios, dict):
        datos_tributarios = {}

    # =================================================
    # 1. VALIDACIÓN DE CONSULTA TRIBUTARIA
    # =================================================

    consulta_exitosa = datos_tributarios.get(
        "consulta_tributaria_exitosa",
        datos_tributarios.get("consulta_exitosa", False)
    )

    if not consulta_exitosa:
        return crear_resultado(
            dictamen="PENDIENTE_VALIDACION",
            nivel_riesgo="NO DETERMINADO",
            motivo="No se pudo verificar la información tributaria.",
            alertas=["Consulta tributaria no disponible."]
        )

    estado = normalizar(datos_tributarios.get("estado"))
    condicion = normalizar(datos_tributarios.get("condicion"))

    # =================================================
    # 2. REGLAS TRIBUTARIAS DETERMINISTAS
    # =================================================

    if estado in ["BAJA DE OFICIO", "BAJA DEFINITIVA"]:
        return crear_resultado(
            dictamen="RECHAZADO",
            nivel_riesgo="ALTO",
            motivo=f"El proveedor presenta el estado tributario: {estado}.",
            alertas=[f"Estado tributario incompatible con la aprobación: {estado}."]
        )

    if condicion == "NO HABIDO":
        return crear_resultado(
            dictamen="RECHAZADO",
            nivel_riesgo="ALTO",
            motivo="El proveedor registra la condición tributaria NO HABIDO.",
            alertas=["Proveedor con domicilio fiscal NO HABIDO."]
        )

    if estado != "ACTIVO":
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="ALTO",
            motivo=f"Estado tributario pendiente de revisión: {estado or 'NO DISPONIBLE'}.",
            alertas=["El estado tributario no figura como ACTIVO."]
        )

    if condicion != "HABIDO":
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="ALTO",
            motivo=f"Condición tributaria pendiente de revisión: {condicion or 'NO DISPONIBLE'}.",
            alertas=["La condición tributaria no figura como HABIDO."]
        )

    # =================================================
    # 3. VALIDACIÓN DE ACTIVIDAD ECONÓMICA
    # =================================================

    actividad_verificada = datos_tributarios.get(
        "actividad_economica_verificada",
        False
    )

    actividad = datos_tributarios.get("actividad_economica")

    if not actividad_verificada or not actividad:
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="MEDIO",
            motivo=(
                "No se pudo verificar la actividad económica "
                "del proveedor. Se requiere revisión documental."
            ),
            alertas=["Actividad económica no verificada."]
        )

    # =================================================
    # 4. VALIDACIÓN DE RESPUESTA DE GEMINI
    # =================================================

    if not isinstance(evaluacion_ia, dict):
        evaluacion_ia = {}

    coherencia = normalizar(
        evaluacion_ia.get("coherencia_comercial")
    )

    riesgo_ia = normalizar(
        evaluacion_ia.get("nivel_riesgo")
    )

    recomendacion = normalizar(
        evaluacion_ia.get("recomendacion")
    )

    puntaje = evaluacion_ia.get("puntaje_confianza", 0)

    alertas_ia = evaluacion_ia.get("alertas", [])

    if not isinstance(alertas_ia, list):
        alertas_ia = ["La estructura de alertas de Gemini no es válida."]

    alertas = [
        str(alerta).strip()
        for alerta in alertas_ia
        if str(alerta).strip()
    ]

    # Validar campos obligatorios de la evaluación.

    coherencias_validas = [
        "COHERENTE",
        "PARCIALMENTE_COHERENTE",
        "INCOHERENTE",
        "INSUFICIENTE"
    ]

    riesgos_validos = ["BAJO", "MEDIO", "ALTO"]

    recomendaciones_validas = [
        "FAVORABLE",
        "REVISAR",
        "DESFAVORABLE"
    ]

    if (
        coherencia not in coherencias_validas
        or riesgo_ia not in riesgos_validos
        or recomendacion not in recomendaciones_validas
    ):
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="MEDIO",
            motivo="La evaluación de Gemini está incompleta o contiene valores no válidos.",
            alertas=alertas + [
                "Se requiere revisar manualmente la evaluación de inteligencia artificial."
            ],
            puntaje_confianza=0
        )

    # Validar puntaje de confianza.

    try:
        puntaje = int(puntaje)

        if not 0 <= puntaje <= 100:
            raise ValueError

    except (ValueError, TypeError):
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="MEDIO",
            motivo="El puntaje de confianza de Gemini no es válido.",
            alertas=alertas + [
                "Puntaje de confianza inválido."
            ]
        )

    motivo = evaluacion_ia.get(
        "justificacion",
        "Sin justificación proporcionada por Gemini."
    )

    # =================================================
    # 5. EVALUACIÓN DE RIESGO COMERCIAL
    # =================================================

    # Una incoherencia comercial impide la aprobación automática.

    if coherencia == "INCOHERENTE":
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="ALTO",
            motivo=motivo,
            alertas=alertas + [
                "La actividad económica presenta incompatibilidad con el servicio cotizado."
            ],
            puntaje_confianza=puntaje
        )

    # Información comercial insuficiente.

    if coherencia == "INSUFICIENTE":
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="MEDIO",
            motivo=motivo,
            alertas=alertas + [
                "No existe información suficiente para confirmar la coherencia comercial."
            ],
            puntaje_confianza=puntaje
        )

    # Riesgo alto detectado por Gemini.

    if riesgo_ia == "ALTO" or recomendacion == "DESFAVORABLE":
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="ALTO",
            motivo=motivo,
            alertas=alertas,
            puntaje_confianza=puntaje
        )

    # Cualquier alerta requiere revisión antes de aprobar.

    if alertas:
        nivel = "ALTO" if riesgo_ia == "ALTO" else "MEDIO"

        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo=nivel,
            motivo=motivo,
            alertas=alertas + [
                "La presencia de alertas impide la aprobación automática."
            ],
            puntaje_confianza=puntaje
        )

    # Coherencia parcial o recomendación de revisión.

    if (
        coherencia == "PARCIALMENTE_COHERENTE"
        or riesgo_ia == "MEDIO"
        or recomendacion == "REVISAR"
    ):
        return crear_resultado(
            dictamen="OBSERVADO",
            nivel_riesgo="MEDIO",
            motivo=motivo,
            alertas=[
                "El proveedor requiere revisión comercial adicional."
            ],
            puntaje_confianza=puntaje
        )

    # =================================================
    # 6. APROBACIÓN FINAL
    # =================================================

    if (
        coherencia == "COHERENTE"
        and riesgo_ia == "BAJO"
        and recomendacion == "FAVORABLE"
        and not alertas
    ):
        return crear_resultado(
            dictamen="APROBADO",
            nivel_riesgo="BAJO",
            motivo=motivo,
            alertas=[],
            puntaje_confianza=puntaje
        )

    # Protección adicional ante cualquier combinación inesperada.

    return crear_resultado(
        dictamen="OBSERVADO",
        nivel_riesgo="MEDIO",
        motivo=motivo,
        alertas=[
            "La evaluación no cumple todas las condiciones de aprobación automática."
        ],
        puntaje_confianza=puntaje
    )
