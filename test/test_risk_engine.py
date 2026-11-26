
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