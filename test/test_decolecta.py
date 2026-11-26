
import pytest
from unittest.mock import MagicMock

from modules.rpa_sunat import DecolectaClient


@pytest.fixture
def respuesta_decolecta():
    return {
        "razon_social": "EMPRESA DE PRUEBA S.A.C.",
        "numero_documento": "20100047218",
        "estado": "ACTIVO",
        "condicion": "HABIDO",
        "direccion": "LIMA",
        "tipo": "SOCIEDAD ANONIMA CERRADA",
        "actividad_economica": "MANTENIMIENTO INDUSTRIAL",
        "numero_trabajadores": "20",
        "tipo_facturacion": "ELECTRONICA",
        "tipo_contabilidad": "COMPUTARIZADO",
        "comercio_exterior": "SIN ACTIVIDAD"
    }


def crear_cliente():
    cliente = DecolectaClient(api_key="token_ficticio")
    cliente.session = MagicMock()
    return cliente


def test_consulta_exitosa(respuesta_decolecta):

    cliente = crear_cliente()

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = respuesta_decolecta

    cliente.session.get.return_value = response

    resultado = cliente.consultar_ruc_completo(
        "20100047218"
    )

    assert resultado["consulta_exitosa"] is True
    assert resultado["actividad_economica"] == (
        "MANTENIMIENTO INDUSTRIAL"
    )
    assert resultado["fuente_actividad_economica"] == "Decolecta"


def test_ruc_invalido():

    cliente = crear_cliente()

    resultado = cliente.consultar_ruc_completo(
        "123456"
    )

    assert resultado["consulta_exitosa"] is False
    assert resultado["error"] == "RUC inválido"
    cliente.session.get.assert_not_called()


def test_token_no_configurado(monkeypatch):

    monkeypatch.delenv("DECOLECTA_API_KEY", raising=False)

    cliente = DecolectaClient(api_key="")

    resultado = cliente.consultar_ruc_completo(
        "20100047218"
    )

    assert resultado["consulta_exitosa"] is False
    assert "API_KEY" in resultado["error"]


def test_error_autenticacion():

    cliente = crear_cliente()

    response = MagicMock()
    response.status_code = 401

    cliente.session.get.return_value = response

    resultado = cliente.consultar_ruc_completo(
        "20100047218"
    )

    assert resultado["consulta_exitosa"] is False
    assert "Token inválido" in resultado["error"]


def test_cuota_agotada():

    cliente = crear_cliente()

    response = MagicMock()
    response.status_code = 429

    cliente.session.get.return_value = response

    resultado = cliente.consultar_ruc_completo(
        "20100047218"
    )

    assert resultado["consulta_exitosa"] is False
    assert "Cuota" in resultado["error"]


def test_actividad_economica_ausente():

    cliente = crear_cliente()

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "numero_documento": "20100047218",
        "razon_social": "EMPRESA DE PRUEBA S.A.C.",
        "estado": "ACTIVO",
        "condicion": "HABIDO"
    }

    cliente.session.get.return_value = response

    resultado = cliente.consultar_ruc_completo(
        "20100047218"
    )

    assert resultado["consulta_exitosa"] is True
    assert resultado["actividad_economica"] is None
    assert resultado["fuente_actividad_economica"] is None
