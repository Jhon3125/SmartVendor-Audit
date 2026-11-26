
from modules.rpa_sunat import validar_ruc


def test_ruc_valido():
    assert validar_ruc("20100047218") is True


def test_ruc_sunat_valido():
    assert validar_ruc("20131312955") is True


def test_ruc_con_menos_digitos():
    assert validar_ruc("2010004721") is False


def test_ruc_con_letras():
    assert validar_ruc("2010004721A") is False


def test_ruc_prefijo_invalido():
    assert validar_ruc("30100047218") is False


def test_ruc_digito_verificador_incorrecto():
    assert validar_ruc("20100047219") is False
