
import pandas as pd
import re
from pathlib import Path


COLUMNAS_REQUERIDAS = [
    "ruc",
    "servicio_cotizado",
    "monto"
]

ALIAS_COLUMNAS = {
    "ruc": "ruc",
    "numero_ruc": "ruc",
    "nro_ruc": "ruc",
    "servicio": "servicio_cotizado",
    "servicio_cotizado": "servicio_cotizado",
    "descripcion_servicio": "servicio_cotizado",
    "monto": "monto",
    "monto_soles": "monto",
    "importe": "monto"
}


def normalizar_nombre_columna(nombre):
    nombre = str(nombre).strip().lower()
    nombre = nombre.replace(" ", "_")
    nombre = nombre.replace("ó", "o")
    nombre = nombre.replace("í", "i")
    nombre = nombre.replace("á", "a")
    nombre = nombre.replace("é", "e")
    nombre = nombre.replace("ú", "u")
    return ALIAS_COLUMNAS.get(nombre, nombre)


def normalizar_ruc(valor):
    if pd.isna(valor):
        return ""

    # Evitar que Excel convierta el RUC en un número decimal.
    valor = str(valor).strip()

    if valor.endswith(".0"):
        valor = valor[:-2]

    return re.sub(r"\s+", "", valor)


def cargar_proveedores(archivo):
    ruta = Path(archivo)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}"
        )

    if ruta.suffix.lower() not in [".xlsx", ".xls"]:
        raise ValueError(
            "El archivo debe tener formato Excel (.xlsx o .xls)."
        )

    try:
        df = pd.read_excel(ruta, dtype={"ruc": str})
    except Exception as error:
        raise ValueError(
            f"No se pudo leer el archivo Excel: {error}"
        )

    if df.empty:
        raise ValueError("El archivo Excel está vacío.")

    df.columns = [
        normalizar_nombre_columna(columna)
        for columna in df.columns
    ]

    faltantes = [
        columna
        for columna in COLUMNAS_REQUERIDAS
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas obligatorias: {faltantes}"
        )

    df = df[COLUMNAS_REQUERIDAS].copy()

    df["ruc"] = df["ruc"].apply(normalizar_ruc)
    df["servicio_cotizado"] = (
        df["servicio_cotizado"].fillna("").astype(str).str.strip()
    )
    df["monto"] = pd.to_numeric(
        df["monto"], errors="coerce"
    )

    df["fila_excel"] = df.index + 2

    return df


def crear_plantilla_excel(destino="data/plantilla_proveedores.xlsx"):
    ruta = Path(destino)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    datos = pd.DataFrame({
        "ruc": ["20100047218", "20131312955"],
        "servicio_cotizado": [
            "Servicios de mantenimiento",
            "Servicios de consultoría"
        ],
        "monto": [1500.00, 3500.00]
    })

    datos.to_excel(ruta, index=False)

    return ruta
