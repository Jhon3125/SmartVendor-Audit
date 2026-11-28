from database.connection import test_connection

try:
    resultado = test_connection()

    print("CONEXIÓN EXITOSA")
    print("Base de datos:", resultado["database"])
    print("Versión MySQL:", resultado["version"])

except Exception as error:
    print("ERROR DE CONEXIÓN:")
    print(error)