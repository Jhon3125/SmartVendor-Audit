
import os
import mysql.connector

from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Establece una conexión con la base de datos MySQL.
    """

    password = os.getenv("DB_PASSWORD")

    if password is None:
        raise ValueError(
            "No se encontró DB_PASSWORD en el archivo .env"
        )

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=password,
        database=os.getenv("DB_NAME", "smartvendor_audit"),
        connection_timeout=5
    )

    return connection


def test_connection():
    """
    Comprueba la conexión y devuelve información del servidor.
    """

    connection = None

    try:
        connection = get_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT VERSION(), DATABASE()")

        version, database = cursor.fetchone()

        return {
            "success": True,
            "version": version,
            "database": database
        }

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
