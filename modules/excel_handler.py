
import pandas as pd
import re
import unicodedata

from pathlib import Path


COLUMNAS_REQUERIDAS = [
    "ruc",
    "servicio_cotizado",
    "monto"
]

MONEDAS_VALIDAS = ["PEN", "USD", "EUR"]

ALIAS_COLUMNAS = {
    "ruc": "ruc",
    "numero_ruc": "ruc",
    "nro_ruc": "ruc",
    "servicio": "servicio_cotizado",
    "servicio_cotizado": "servicio_cotizado",
    "descripcion_servicio": "servicio_cotizado",
    "monto": "monto",
    "monto_soles": "monto",
    "importe": "monto",
    "moneda": "moneda",
    "tipo_moneda": "moneda",
    "currency": "moneda"
}


def normalizar_nombre_columna(nombre):
    nombre = str(nombre).strip().lower()

    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = "".join(
        caracter
        for caracter in nombre
        if not unicodedata.combining(caracter)
    )

    nombre = re.sub(r"\s+", "_", nombre)

    return ALIAS_COLUMNAS.get(nombre, nombre)


def normalizar_ruc(valor):
    if pd.isna(valor):
        return ""

    valor = str(valor).strip()

    if valor.endswith(".0"):
        valor = valor[:-2]

    return re.sub(r"\s+", "", valor)


def validar_registro(fila):

    errores = []

    ruc = fila["ruc"]
    servicio = fila["servicio_cotizado"]
    monto = fila["monto"]
    moneda = fila["moneda"]

    # Validación básica del RUC.
    if not ruc:
        errores.append("RUC vacío.")
    elif not ruc.isdigit() or len(ruc) != 11:
        errores.append("El RUC debe contener exactamente 11 dígitos.")

    # La validación completa del RUC se realizará posteriormente
    # mediante el módulo de validación tributaria.

    if not servicio:
        errores.append("Servicio o producto no especificado.")

    if pd.isna(monto):
        errores.append("Monto vacío o no numérico.")
    elif monto <= 0:
        errores.append("El monto debe ser mayor que cero.")

    if moneda not in MONEDAS_VALIDAS:
        errores.append(
            f"Moneda no válida: {moneda}. "
            f"Valores permitidos: {', '.join(MONEDAS_VALIDAS)}."
        )

    return errores


def cargar_proveedores(archivo):

    # Acepta tanto rutas de archivos como archivos cargados
    # directamente mediante st.file_uploader.

    if hasattr(archivo, "name"):
        nombre_archivo = archivo.name
    else:
        nombre_archivo = str(archivo)

        if not Path(nombre_archivo).exists():
            raise FileNotFoundError(
                f"No se encontró el archivo: {nombre_archivo}"
            )

    extension = Path(nombre_archivo).suffix.lower()

    if extension != ".xlsx":
        raise ValueError(
            "El archivo debe tener formato Excel .xlsx."
        )

    try:
        if hasattr(archivo, "seek"):
            archivo.seek(0)

        df = pd.read_excel(
            archivo,
            dtype=str,
            engine="openpyxl"
        )

    except Exception as error:
        raise ValueError(
            f"No se pudo leer el archivo Excel: {error}"
        ) from error

    if df.empty:
        raise ValueError("El archivo Excel está vacío.")

    # Normalizar nombres de columnas.
    df.columns = [
        normalizar_nombre_columna(columna)
        for columna in df.columns
    ]

    # Verificar columnas obligatorias.
    faltantes = [
        columna
        for columna in COLUMNAS_REQUERIDAS
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas obligatorias: {faltantes}"
        )

    # La moneda es opcional para mantener compatibilidad
    # con plantillas anteriores.
    if "moneda" not in df.columns:
        df["moneda"] = "PEN"

    df = df[
        ["ruc", "servicio_cotizado", "monto", "moneda"]
    ].copy()

    # Normalización de datos.
    df["ruc"] = df["ruc"].apply(normalizar_ruc)

    df["servicio_cotizado"] = (
        df["servicio_cotizado"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["monto"] = pd.to_numeric(
        df["monto"],
        errors="coerce"
    )

    df["moneda"] = (
        df["moneda"]
        .fillna("PEN")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df.loc[df["moneda"] == "", "moneda"] = "PEN"

    # Conservar el número de fila original de Excel.
    df["fila_excel"] = df.index + 2

    # Validación individual de cada registro.
    df["errores_validacion"] = df.apply(
        validar_registro,
        axis=1
    )

    df["registro_valido"] = (
        df["errores_validacion"].apply(len) == 0
    )

    return df.reset_index(drop=True)


def crear_plantilla_excel(
    destino="data/plantilla_proveedores.xlsx"
):

    ruta = Path(destino)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    datos = pd.DataFrame({
        "ruc": [
            "20100047218",
            "20131312955"
        ],
        "servicio_cotizado": [
            "Servicios de intermediación financiera",
            "Servicios de consultoría"
        ],
        "monto": [
            15000.00,
            3500.00
        ],
        "moneda": [
            "PEN",
            "PEN"
        ]
    })

    with pd.ExcelWriter(
        ruta,
        engine="openpyxl"
    ) as writer:

        datos.to_excel(
            writer,
            index=False,
            sheet_name="Proveedores"
        )

        hoja = writer.sheets["Proveedores"]

        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions

        anchos = {
            "A": 16,
            "B": 48,
            "C": 16,
            "D": 14
        }

        for columna, ancho in anchos.items():
            hoja.column_dimensions[columna].width = ancho

    return ruta
