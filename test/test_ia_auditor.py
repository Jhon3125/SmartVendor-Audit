
import json
import pytest

from unittest.mock import MagicMock

from modules.ia_auditor import AuditorIA


@pytest.fixture
def proveedor():
    return {
        "ruc": "20100047218",
        "razon_social": "BANCO DE CREDITO DEL PERU",
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "servicio_cotizado": "Mantenimiento industrial",
        "monto": 15000
    }


@pytest.fixture
def respuesta_valida():
    return {
        "coherencia_comercial": "insuficiente",
        "nivel_riesgo": "medio",
        "puntaje_confianza": 85,
        "justificacion": (
            "Se necesita verificar la actividad económica."
        ),
        "alertas": [
            "Solicitar documentación adicional."
        ],
        "recomendacion": "revisar"
    }


def crear_auditor(respuesta_texto=None):

    cliente = MagicMock()

    cliente.models.generate_content.return_value.text = (
        respuesta_texto
    )

    auditor = AuditorIA(
        api_key="clave_ficticia_para_tests",
        client=cliente
    )

    return auditor, cliente


def test_evaluar_proveedor_respuesta_valida(
    proveedor,
    respuesta_valida
):

    auditor, cliente = crear_auditor(
        json.dumps(respuesta_valida)
    )

    resultado = auditor.evaluar_proveedor(proveedor)

    assert resultado == respuesta_valida

    cliente.models.generate_content.assert_called_once()


def test_gemini_devuelve_respuesta_vacia(proveedor):

    auditor, _ = crear_auditor(None)

    with pytest.raises(ValueError, match="respuesta vacía"):
        auditor.evaluar_proveedor(proveedor)


def test_gemini_devuelve_json_invalido(proveedor):

    auditor, _ = crear_auditor(
        "Esto no es un JSON válido"
    )

    with pytest.raises(ValueError, match="no cumple el esquema"):
        auditor.evaluar_proveedor(proveedor)


def test_gemini_devuelve_riesgo_invalido(proveedor):

    respuesta = {
        "coherencia_comercial": "coherente",
        "nivel_riesgo": "extremo",
        "puntaje_confianza": 90,
        "justificacion": "Evaluación de prueba.",
        "alertas": [],
        "recomendacion": "favorable"
    }

    auditor, _ = crear_auditor(
        json.dumps(respuesta)
    )

    with pytest.raises(ValueError, match="no cumple el esquema"):
        auditor.evaluar_proveedor(proveedor)


def test_api_key_no_configurada(monkeypatch):

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        AuditorIA()
