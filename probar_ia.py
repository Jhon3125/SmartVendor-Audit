
from modules.ia_auditor import AuditorIA

auditor = AuditorIA()

proveedor = {
    "ruc": "20100047218",
    "razon_social": "BANCO DE CREDITO DEL PERU",
    "estado": "ACTIVO",
    "condicion": "HABIDO",
    "servicio_cotizado": "Mantenimiento de maquinaria industrial",
    "monto": 15000
}

print("\nConsultando Gemini...\n")

resultado = auditor.evaluar_proveedor(proveedor)

print("RESULTADO DE AUDITORÍA:")
print(resultado)
