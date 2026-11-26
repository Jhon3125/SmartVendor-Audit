
import json
import re
from pathlib import Path

import requests


API_BASE_URL = "https://openruc.com/api/ruc"
CACHE_FILE = Path("data/cache_rucs.json")


def validar_ruc(ruc):
    """Valida estructura, prefijo y dígito verificador del RUC."""

    ruc = str(ruc).strip()

    if not re.fullmatch(r"\d{11}", ruc):
        return False

    if ruc[:2] not in {"10", "15", "16", "17", "20"}:
        return False

    factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    suma = sum(
        int(digito) * factor
        for digito, factor in zip(ruc[:10], factores)
    )

    resultado = 11 - (suma % 11)

    if resultado == 11:
        digito_verificador = 0
    elif resultado == 10:
        digito_verificador = 1
    else:
        digito_verificador = resultado

    return digito_verificador == int(ruc[-1])


class OpenRUCClient:

    def __init__(self, cache_file=CACHE_FILE, timeout=15):
        self.cache_file = Path(cache_file)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SmartVendor-Audit/1.0"
        })

        self.cache_file.parent.mkdir(
            parents=True, exist_ok=True
        )

        if not self.cache_file.exists():
            self.cache_file.write_text(
                "{}", encoding="utf-8"
            )

        self.cache = self._cargar_cache()

    def _cargar_cache(self):
        try:
            contenido = self.cache_file.read_text(
                encoding="utf-8"
            )
            datos = json.loads(contenido)
            return datos if isinstance(datos, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _guardar_cache(self):
        temporal = self.cache_file.with_suffix(".tmp")

        temporal.write_text(
            json.dumps(
                self.cache,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

        temporal.replace(self.cache_file)

    def consultar_ruc(self, ruc):
        ruc = str(ruc).strip()

        if not validar_ruc(ruc):
            return {
                "ruc": ruc,
                "consulta_exitosa": False,
                "error": "RUC inválido"
            }

        # Consultar primero la caché.
        if ruc in self.cache:
            return {
                **self.cache[ruc],
                "desde_cache": True
            }

        try:
            url = f"{API_BASE_URL}/{ruc}"

            response = self.session.get(
                url,
                timeout=self.timeout
            )

            if response.status_code == 404:
                return {
                    "ruc": ruc,
                    "consulta_exitosa": False,
                    "error": "RUC no encontrado"
                }

            response.raise_for_status()

            datos = response.json()

            if not isinstance(datos, dict):
                raise ValueError("Respuesta JSON inválida")

            # Compatibilidad con respuestas directas
            # y respuestas que contienen un objeto data.
            if isinstance(datos.get("data"), dict):
                datos = datos["data"]

            resultado = {
                "ruc": str(datos.get("ruc", ruc)),
                "razon_social": datos.get("razon_social"),
                "estado": datos.get("estado"),
                "condicion": datos.get("condicion"),
                "direccion": datos.get("direccion"),
                "consulta_exitosa": True,
                "desde_cache": False
            }

            campos_requeridos = [
                "razon_social",
                "estado",
                "condicion"
            ]

            if any(
                not resultado.get(campo)
                for campo in campos_requeridos
            ):
                return {
                    "ruc": ruc,
                    "consulta_exitosa": False,
                    "error": "Respuesta incompleta de OpenRUC"
                }

            self.cache[ruc] = resultado
            self._guardar_cache()

            return resultado

        except requests.Timeout:
            return {
                "ruc": ruc,
                "consulta_exitosa": False,
                "error": "Tiempo de espera agotado"
            }

        except requests.RequestException as error:
            return {
                "ruc": ruc,
                "consulta_exitosa": False,
                "error": f"Error de conexión: {error}"
            }

        except (ValueError, json.JSONDecodeError) as error:
            return {
                "ruc": ruc,
                "consulta_exitosa": False,
                "error": f"Error procesando respuesta: {error}"
            }

    def procesar_lote(self, proveedores):
        resultados = []

        for _, proveedor in proveedores.iterrows():
            resultado = self.consultar_ruc(
                proveedor["ruc"]
            )

            resultado["servicio_cotizado"] = (
                proveedor["servicio_cotizado"]
            )
            resultado["monto"] = proveedor["monto"]
            resultado["fila_excel"] = (
                proveedor["fila_excel"]
            )

            resultados.append(resultado)

        return resultados
