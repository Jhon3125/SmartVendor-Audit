
import json
from pathlib import Path

from modules.rpa_sunat import OpenRUCClient, DecolectaClient


class ProviderService:
    """
    Consolida información tributaria y empresarial
    de OpenRUC y Decolecta.
    """

    def __init__(
        self,
        openruc=None,
        decolecta=None,
        cache_file="data/cache_proveedores.json"
    ):
        self.openruc = openruc or OpenRUCClient()
        self.decolecta = decolecta or DecolectaClient()

        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.cache = self._cargar_cache()

    def _cargar_cache(self):
        if not self.cache_file.exists():
            return {}

        try:
            datos = json.loads(
                self.cache_file.read_text(encoding="utf-8")
            )
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

    def consultar_proveedor(self, ruc, forzar_consulta=False):
        ruc = str(ruc).strip()

        if not forzar_consulta and ruc in self.cache:
            return {
                **self.cache[ruc],
                "desde_cache": True
            }

        # Consulta ambas fuentes.
        datos_openruc = self.openruc.consultar_ruc(ruc)

        datos_decolecta = (
            self.decolecta.consultar_ruc_completo(ruc)
        )

        openruc_ok = datos_openruc.get(
            "consulta_exitosa", False
        )

        decolecta_ok = datos_decolecta.get(
            "consulta_exitosa", False
        )

        # Decolecta tiene prioridad para los campos
        # que proporciona en su respuesta extendida.
        datos = {
            "ruc": ruc,
            "razon_social": (
                datos_decolecta.get("razon_social")
                or datos_openruc.get("razon_social")
            ),
            "estado": (
                datos_decolecta.get("estado")
                or datos_openruc.get("estado")
            ),
            "condicion": (
                datos_decolecta.get("condicion")
                or datos_openruc.get("condicion")
            ),
            "direccion": (
                datos_decolecta.get("direccion")
                or datos_openruc.get("direccion")
            ),
            "tipo_contribuyente": datos_decolecta.get(
                "tipo_contribuyente"
            ),
            "actividad_economica": datos_decolecta.get(
                "actividad_economica"
            ),
            "numero_trabajadores": datos_decolecta.get(
                "numero_trabajadores"
            ),
            "tipo_facturacion": datos_decolecta.get(
                "tipo_facturacion"
            ),
            "tipo_contabilidad": datos_decolecta.get(
                "tipo_contabilidad"
            ),
            "comercio_exterior": datos_decolecta.get(
                "comercio_exterior"
            ),
            "consulta_tributaria_exitosa": (
                openruc_ok or decolecta_ok
            ),
            "actividad_economica_verificada": bool(
                decolecta_ok
                and datos_decolecta.get("actividad_economica")
            ),
            "fuentes": {
                "openruc": openruc_ok,
                "decolecta": decolecta_ok
            },
            "fuente_actividad_economica": (
                "Decolecta"
                if decolecta_ok
                and datos_decolecta.get("actividad_economica")
                else None
            ),
            "errores_fuentes": {
                "openruc": datos_openruc.get("error"),
                "decolecta": datos_decolecta.get("error")
            },
            "desde_cache": False
        }

        # No almacenar un resultado donde ambas fuentes fallaron.
        if openruc_ok or decolecta_ok:
            self.cache[ruc] = datos
            self._guardar_cache()

        return datos
