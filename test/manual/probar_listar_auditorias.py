
from database.repositories.auditoria_repository import listar_auditorias

try:
    auditorias = listar_auditorias()

    print("\n===== AUDITORÍAS REGISTRADAS =====")
    print(f"Total encontrado: {len(auditorias)}")

    for auditoria in auditorias:
        print("-" * 50)
        print(f"ID: {auditoria['auditoria_id']}")
        print(f"RUC: {auditoria['ruc']}")
        print(f"Proveedor: {auditoria['razon_social']}")
        print(f"Servicio: {auditoria['servicio_cotizado']}")
        print(f"Dictamen: {auditoria['dictamen']}")
        print(f"Estado Gemini: {auditoria['estado_gemini']}")

    print("\nConsulta ejecutada correctamente.")

except Exception as error:
    print(f"Error: {error}")
