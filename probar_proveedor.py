
import json

from modules.provider_service import ProviderService

service = ProviderService()

resultado = service.consultar_proveedor(
    "20100047218"
)

print("\nPERFIL EMPRESARIAL CONSOLIDADO\n")

print(
    json.dumps(
        resultado,
        indent=4,
        ensure_ascii=False
    )
)
