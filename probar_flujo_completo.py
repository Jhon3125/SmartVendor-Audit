
from modules.provider_service import ProviderService
from modules.ia_auditor import AuditorIA
from modules.risk_engine import generar_dictamen

import json


def ejecutar_auditoria():

    # 1. Datos de prueba del proveedor.
    proveedor = {
        "ruc": "20100047218",
        "servicio_cotizado": (
            "Servicios de intermediación financiera"
        ),
        "monto": 15000,
        "moneda": "PEN"
    }

    print("\n" + "=" * 55)
    print("SMARTVENDOR AUDIT - AUDITORÍA COMPLETA")
    print("=" * 55)

    # 2. Obtener información tributaria y empresarial.
    print("\n[1/3] Consultando fuentes empresariales...")

    servicio = ProviderService()

    perfil = servicio.consultar_proveedor(
        proveedor["ruc"]
    )

    if not perfil.get("consulta_tributaria_exitosa"):
        print("ERROR: No se pudo verificar al proveedor.")
        print(perfil.get("errores_fuentes"))
        return

    proveedor.update(perfil)

    print("Información empresarial obtenida correctamente.")
    print("Actividad:", proveedor.get("actividad_economica"))
    print("Desde caché:", proveedor.get("desde_cache"))

    # 3. Evaluación mediante Gemini.
    print("\n[2/3] Evaluando proveedor con Gemini...")

    auditor = AuditorIA()

    try:
        evaluacion = auditor.evaluar_proveedor(proveedor)

    except RuntimeError as error:
        print(f"\nNO SE PUDO COMPLETAR LA AUDITORÍA: {error}")
        return

    print("Evaluación de Gemini completada.")

    # 4. Aplicar motor de reglas.
    print("\n[3/3] Generando dictamen final...")

    dictamen = generar_dictamen(
        perfil,
        evaluacion
    )

    # 5. Mostrar resultados.
    print("\n" + "=" * 55)
    print("RESULTADO FINAL DE AUDITORÍA")
    print("=" * 55)

    print("\nPERFIL DEL PROVEEDOR:")
    print(json.dumps({
        "ruc": proveedor.get("ruc"),
        "razon_social": proveedor.get("razon_social"),
        "actividad_economica": proveedor.get(
            "actividad_economica"
        ),
        "servicio_cotizado": proveedor.get(
            "servicio_cotizado"
        ),
        "monto": proveedor.get("monto"),
        "moneda": proveedor.get("moneda")
    }, indent=4, ensure_ascii=False))

    print("\nEVALUACIÓN DE GEMINI:")
    print(json.dumps(
        evaluacion,
        indent=4,
        ensure_ascii=False
    ))

    print("\nDICTAMEN DEL MOTOR DE REGLAS:")
    print(json.dumps(
        dictamen,
        indent=4,
        ensure_ascii=False
    ))

    print("\n" + "=" * 55)
    print("AUDITORÍA FINALIZADA")
    print("=" * 55)


if __name__ == "__main__":
    ejecutar_auditoria()
