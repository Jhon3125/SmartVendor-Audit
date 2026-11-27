
from modules.risk_engine import generar_dictamen


def test_proveedor_aprobado():

    tributario = {
        "consulta_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "MANTENIMIENTO INDUSTRIAL"
    }

    ia = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "bajo",
        "recomendacion": "favorable",
        "justificacion": "Coherencia comercial.",
        "alertas": [],
        "puntaje_confianza": 90
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "APROBADO"


def test_proveedor_no_habido():

    tributario = {
        "consulta_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "NO HABIDO"
    }

    resultado = generar_dictamen(tributario, {})

    assert resultado["dictamen"] == "RECHAZADO"


def test_proveedor_baja_de_oficio():

    tributario = {
        "consulta_exitosa": True,
        "estado": "BAJA DE OFICIO",
        "condicion": "HABIDO"
    }

    resultado = generar_dictamen(tributario, {})

    assert resultado["dictamen"] == "RECHAZADO"


def test_proveedor_no_verificado():

    tributario = {
        "consulta_exitosa": False
    }

    resultado = generar_dictamen(tributario, {})

    assert resultado["dictamen"] == "PENDIENTE_VALIDACION"


def test_proveedor_con_riesgo_medio():

    tributario = {
        "consulta_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO"
    }

    ia = {
        "nivel_riesgo": "medio",
        "recomendacion": "revisar"
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"

def test_actividad_economica_no_verificada():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": False
    }

    resultado = generar_dictamen(tributario, {})

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "MEDIO"


def test_no_aprobar_si_gemini_detecta_alertas():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "MANTENIMIENTO INDUSTRIAL"
    }

    ia = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "bajo",
        "recomendacion": "favorable",
        "justificacion": "Existe coherencia comercial.",
        "alertas": ["Se requiere verificar experiencia del proveedor."],
        "puntaje_confianza": 90
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "MEDIO"


def test_no_aprobar_si_actividad_es_incoherente():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "VENTA DE PRODUCTOS ALIMENTICIOS"
    }

    ia = {
        "coherencia_comercial": "incoherente",
        "nivel_riesgo": "bajo",
        "recomendacion": "favorable",
        "justificacion": "No existe relación comercial.",
        "alertas": [],
        "puntaje_confianza": 90
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "ALTO"


def test_no_aprobar_si_riesgo_ia_es_alto():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "MANTENIMIENTO INDUSTRIAL"
    }

    ia = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "alto",
        "recomendacion": "favorable",
        "justificacion": "Se detectaron riesgos importantes.",
        "alertas": [],
        "puntaje_confianza": 85
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "ALTO"


def test_no_aprobar_si_recomendacion_es_desfavorable():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "MANTENIMIENTO INDUSTRIAL"
    }

    ia = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "bajo",
        "recomendacion": "desfavorable",
        "justificacion": "No se recomienda contratar.",
        "alertas": [],
        "puntaje_confianza": 90
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "ALTO"


def test_no_aprobar_si_coherencia_es_insuficiente():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "ACTIVIDAD NO DETERMINADA"
    }

    ia = {
        "coherencia_comercial": "insuficiente",
        "nivel_riesgo": "medio",
        "recomendacion": "revisar",
        "justificacion": "No hay información suficiente.",
        "alertas": [],
        "puntaje_confianza": 50
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "MEDIO"


def test_no_aprobar_si_falta_coherencia_en_respuesta_ia():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "MANTENIMIENTO INDUSTRIAL"
    }

    ia = {
        "nivel_riesgo": "bajo",
        "recomendacion": "favorable",
        "alertas": [],
        "puntaje_confianza": 90
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "OBSERVADO"
    assert resultado["nivel_riesgo"] == "MEDIO"


def test_aprobacion_requiere_coherencia_bajo_favorable_y_sin_alertas():

    tributario = {
        "consulta_tributaria_exitosa": True,
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "actividad_economica_verificada": True,
        "actividad_economica": "INTERMEDIACION FINANCIERA"
    }

    ia = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "bajo",
        "recomendacion": "favorable",
        "justificacion": "La actividad es coherente con el servicio.",
        "alertas": [],
        "puntaje_confianza": 95
    }

    resultado = generar_dictamen(tributario, ia)

    assert resultado["dictamen"] == "APROBADO"
    assert resultado["nivel_riesgo"] == "BAJO"
    assert resultado["puntaje_confianza"] == 95
