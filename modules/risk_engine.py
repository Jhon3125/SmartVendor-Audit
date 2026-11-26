
def normalizar(valor):
    return str(valor or "").strip().upper()


def generar_dictamen(datos_tributarios, evaluacion_ia):

    # Compatibilidad con el resultado antiguo y el nuevo.
    consulta_exitosa = datos_tributarios.get(
        "consulta_tributaria_exitosa",
        datos_tributarios.get("consulta_exitosa", False)
    )

    if not consulta_exitosa:
        return {
            "dictamen": "PENDIENTE_VALIDACION",
            "nivel_riesgo": "NO DETERMINADO",
            "motivo": "No se pudo verificar la información tributaria.",
            "alertas": ["Consulta tributaria no disponible."]
        }

    estado = normalizar(datos_tributarios.get("estado"))
    condicion = normalizar(datos_tributarios.get("condicion"))

    # 1. Reglas tributarias deterministas.

    if estado in ["BAJA DE OFICIO", "BAJA DEFINITIVA"]:
        return {
            "dictamen": "RECHAZADO",
            "nivel_riesgo": "ALTO",
            "motivo": f"Estado tributario: {estado}",
            "alertas": []
        }

    if condicion == "NO HABIDO":
        return {
            "dictamen": "RECHAZADO",
            "nivel_riesgo": "ALTO",
            "motivo": "Proveedor con domicilio NO HABIDO.",
            "alertas": []
        }

    if estado != "ACTIVO":
        return {
            "dictamen": "OBSERVADO",
            "nivel_riesgo": "ALTO",
            "motivo": f"Estado tributario pendiente de revisión: {estado}",
            "alertas": []
        }

    if condicion != "HABIDO":
        return {
            "dictamen": "OBSERVADO",
            "nivel_riesgo": "ALTO",
            "motivo": f"Condición tributaria pendiente: {condicion}",
            "alertas": []
        }

    # 2. Verificar actividad económica.

    actividad_verificada = datos_tributarios.get(
        "actividad_economica_verificada", False
    )

    if not actividad_verificada:
        return {
            "dictamen": "OBSERVADO",
            "nivel_riesgo": "MEDIO",
            "motivo": (
                "No se pudo verificar la actividad económica "
                "del proveedor. Se requiere revisión documental."
            ),
            "alertas": [
                "Actividad económica no verificada."
            ],
            "puntaje_confianza": 0
        }

    # 3. Validar resultado de Gemini.

    if not isinstance(evaluacion_ia, dict):
        evaluacion_ia = {}

    riesgo_ia = normalizar(
        evaluacion_ia.get("nivel_riesgo")
    )

    recomendacion = normalizar(
        evaluacion_ia.get("recomendacion")
    )

    if (
        riesgo_ia not in ["BAJO", "MEDIO", "ALTO"]
        or recomendacion not in [
            "FAVORABLE", "REVISAR", "DESFAVORABLE"
        ]
    ):
        return {
            "dictamen": "OBSERVADO",
            "nivel_riesgo": "MEDIO",
            "motivo": "Resultado de IA no válido.",
            "alertas": ["Se requiere revisión manual."]
        }

    # 4. Generar dictamen comercial.

    if riesgo_ia == "BAJO" and recomendacion == "FAVORABLE":
        dictamen = "APROBADO"
        nivel = "BAJO"

    elif riesgo_ia == "ALTO" or recomendacion == "DESFAVORABLE":
        dictamen = "OBSERVADO"
        nivel = "ALTO"

    else:
        dictamen = "OBSERVADO"
        nivel = "MEDIO"

    return {
        "dictamen": dictamen,
        "nivel_riesgo": nivel,
        "motivo": evaluacion_ia.get("justificacion", ""),
        "alertas": evaluacion_ia.get("alertas", []),
        "puntaje_confianza": evaluacion_ia.get(
            "puntaje_confianza", 0
        )
    }
