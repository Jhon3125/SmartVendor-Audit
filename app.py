import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

import os
import json

from modules.provider_service import ProviderService
from modules.ia_auditor import AuditorIA
from modules.risk_engine import generar_dictamen
from modules.excel_handler import cargar_proveedores

from database.repositories.proveedor_repository import (
    guardar_o_actualizar,
)
from database.repositories.cotizacion_repository import (
    guardar as guardar_cotizacion,
)
from database.repositories.auditoria_repository import (
    crear_auditoria,
    crear_evaluacion_ia,
    guardar_resultado_ia,
    registrar_error_ia,
    registrar_intento_gemini,
    finalizar_intento_gemini,
    actualizar_dictamen,
    listar_auditorias,
    obtener_auditoria,
    listar_evaluaciones,
    listar_intentos,
    listar_historial,
)

from database.repositories.lote_repository import (
    crear_lote,
    actualizar_estado_lote,
    guardar_registro_lote,
)

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SmartVendor Audit",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SERVICIOS
# ============================================================

@st.cache_resource
def obtener_servicios():
    """Mantiene una instancia de los servicios durante la sesión de la app."""
    return ProviderService(), AuditorIA()


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --sv-bg: #0b1220;
        --sv-panel: #111c2e;
        --sv-panel-soft: #16243a;
        --sv-border: rgba(148, 163, 184, .16);
        --sv-text: #e8eef8;
        --sv-muted: #91a2bb;
        --sv-blue: #4f8cff;
        --sv-cyan: #38c6d9;
        --sv-green: #24c78a;
        --sv-amber: #f5b942;
        --sv-red: #f06b75;
    }

    .stApp {
        background:
            radial-gradient(circle at 85% 0%, rgba(43, 100, 180, .13), transparent 28%),
            var(--sv-bg);
        color: var(--sv-text);
    }

    [data-testid="stHeader"] {
        background: rgba(11, 18, 32, .75);
    }

    .block-container {
        max-width: 1440px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #0e192a;
        border-right: 1px solid var(--sv-border);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.8rem;
    }

    .sv-brand {
        display: flex;
        align-items: center;
        gap: 11px;
        margin-bottom: 4px;
    }

    .sv-brand-icon {
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 13px;
        background: linear-gradient(135deg, #2864c7, #36bfd0);
        color: white;
        font-size: 22px;
        box-shadow: 0 8px 24px rgba(45, 125, 210, .25);
    }

    .sv-brand-name {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -.5px;
        color: #f3f7ff;
    }

    .sv-brand-sub {
        color: var(--sv-muted);
        font-size: 12px;
        line-height: 1.5;
        margin: 8px 0 22px;
    }

    .sv-sidebar-label {
        color: #7185a2;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.4px;
        margin: 18px 0 8px;
    }

    .sv-version {
        color: #7185a2;
        font-size: 11px;
        border-top: 1px solid var(--sv-border);
        padding-top: 16px;
        margin-top: 28px;
    }

    .sv-eyebrow {
        color: var(--sv-cyan);
        text-transform: uppercase;
        letter-spacing: 1.7px;
        font-size: 10px;
        font-weight: 800;
        margin-bottom: 7px;
    }

    .sv-page-title {
        color: #f4f7fc;
        font-size: clamp(26px, 3vw, 34px);
        line-height: 1.15;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
    }

    .sv-page-subtitle {
        color: var(--sv-muted);
        font-size: 14px;
        margin-top: 8px;
        margin-bottom: 24px;
    }

    .sv-section-title {
        color: #eef4ff;
        font-size: 17px;
        font-weight: 750;
        margin: 0 0 4px;
    }

    .sv-section-caption {
        color: var(--sv-muted);
        font-size: 12px;
        margin-bottom: 14px;
    }

    .sv-card {
        background: linear-gradient(145deg, rgba(22, 36, 58, .96), rgba(16, 28, 46, .96));
        border: 1px solid var(--sv-border);
        border-radius: 15px;
        padding: 18px 19px;
        min-height: 105px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, .12);
    }

    .sv-card-label {
        color: #9aabc3;
        font-size: 11px;
        font-weight: 650;
        margin-bottom: 11px;
    }

    .sv-card-value {
        color: #f3f7ff;
        font-size: 27px;
        font-weight: 800;
        letter-spacing: -.7px;
        line-height: 1.1;
    }

    .sv-card-note {
        color: #8498b4;
        font-size: 11px;
        margin-top: 8px;
    }

    .sv-panel {
        background: rgba(17, 28, 46, .78);
        border: 1px solid var(--sv-border);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .sv-step {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #dce7f7;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 4px;
    }

    .sv-step-number {
        display: inline-flex;
        width: 27px;
        height: 27px;
        border-radius: 9px;
        align-items: center;
        justify-content: center;
        background: rgba(79, 140, 255, .17);
        color: #83b2ff;
        font-size: 12px;
        font-weight: 800;
    }

    .sv-result {
        border-radius: 16px;
        padding: 19px 21px;
        border: 1px solid var(--sv-border);
        margin: 8px 0 18px;
        background: rgba(22, 36, 58, .82);
    }

    .sv-result-approved {
        border-color: rgba(36, 199, 138, .35);
        background: linear-gradient(100deg, rgba(18, 91, 72, .32), rgba(17, 28, 46, .85));
    }

    .sv-result-observed {
        border-color: rgba(245, 185, 66, .35);
        background: linear-gradient(100deg, rgba(111, 76, 19, .28), rgba(17, 28, 46, .85));
    }

    .sv-result-rejected {
        border-color: rgba(240, 107, 117, .4);
        background: linear-gradient(100deg, rgba(112, 35, 48, .3), rgba(17, 28, 46, .85));
    }

    .sv-result-title {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 5px;
        color: #f5f8ff;
    }

    .sv-result-text {
        color: #aebed3;
        font-size: 12px;
        line-height: 1.6;
    }

    .sv-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .5px;
        background: rgba(79, 140, 255, .15);
        color: #9cc1ff;
        border: 1px solid rgba(79, 140, 255, .24);
    }

    .sv-muted {
        color: var(--sv-muted);
        font-size: 12px;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #16243a, #111c2e);
        border: 1px solid var(--sv-border);
        border-radius: 14px;
        padding: 15px 17px;
    }

    div[data-testid="stMetricLabel"] {
        color: #9aabc3;
    }

    div[data-testid="stMetricValue"] {
        color: #f3f7ff;
    }

    div[data-testid="stForm"] {
        background: rgba(17, 28, 46, .72);
        border: 1px solid var(--sv-border);
        border-radius: 16px;
        padding: 20px 20px 8px;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    div[data-baseweb="select"] > div {
        background-color: #111e31 !important;
        border-color: rgba(148, 163, 184, .22) !important;
        border-radius: 9px !important;
    }

    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        border-radius: 10px;
        font-weight: 700;
        min-height: 42px;
        transition: all .18s ease;
    }

    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #3478e5, #287fc7);
        border: 0;
        color: white;
    }

    [data-testid="stFormSubmitButton"] > button:hover {
        border: 0;
        filter: brightness(1.12);
        box-shadow: 0 7px 20px rgba(52, 120, 229, .24);
    }

    div[data-testid="stTabs"] button {
        font-weight: 700;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--sv-border);
        border-radius: 12px;
        overflow: hidden;
    }

    hr {
        border-color: var(--sv-border);
    }

    .stAlert {
        border-radius: 11px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

if "historial" not in st.session_state:
    st.session_state.historial = []

if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None

if "nav_pagina" not in st.session_state:
    st.session_state.nav_pagina = "Dashboard"

if "perfiles_auditoria_masiva" not in st.session_state:
    st.session_state.perfiles_auditoria_masiva = {}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def formato_moneda(monto, moneda):
    simbolos = {
        "PEN": "S/",
        "USD": "US$",
        "EUR": "€",
    }
    simbolo = simbolos.get(moneda, moneda or "")
    return f"{simbolo} {float(monto):,.2f}"


def generar_excel(registros, nombre_hoja="Auditorias"):
    df = pd.DataFrame(registros)
    salida = BytesIO()

    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=nombre_hoja)

    salida.seek(0)
    return salida


def generar_excel_masivo(auditorias, invalidos):
    """Genera un Excel con resultados y registros que no superaron la validación."""
    salida = BytesIO()
    df_auditorias = pd.DataFrame(auditorias)
    df_invalidos = pd.DataFrame(invalidos)

    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        if df_auditorias.empty:
            pd.DataFrame(columns=["RUC", "Dictamen final"]).to_excel(
                writer, index=False, sheet_name="Auditorias"
            )
        else:
            df_auditorias.to_excel(writer, index=False, sheet_name="Auditorias")

        if df_invalidos.empty:
            pd.DataFrame(columns=["fila_excel", "errores_validacion"]).to_excel(
                writer, index=False, sheet_name="Registros_invalidos"
            )
        else:
            df_invalidos.to_excel(
                writer, index=False, sheet_name="Registros_invalidos"
            )

    salida.seek(0)
    return salida


def mostrar_encabezado(titulo, descripcion, etiqueta="CENTRO DE CONTROL"):
    st.markdown(
        f"""
        <div class="sv-eyebrow">{etiqueta}</div>
        <h1 class="sv-page-title">{titulo}</h1>
        <div class="sv-page-subtitle">{descripcion}</div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_resumen(etiqueta, valor, nota="", icono=""):
    st.markdown(
        f"""
        <div class="sv-card">
            <div class="sv-card-label">{icono} {etiqueta}</div>
            <div class="sv-card-value">{valor}</div>
            <div class="sv-card-note">{nota}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def etiqueta_dictamen(dictamen):
    return {
        "APROBADO": "🟢 APROBADO",
        "OBSERVADO": "🟠 OBSERVADO",
        "RECHAZADO": "🔴 RECHAZADO",
        "PENDIENTE_VALIDACION": "⚪ PENDIENTE",
    }.get(dictamen, dictamen or "SIN DICTAMEN")


def exportar_resultado_individual(resultado):
    perfil = resultado["perfil"]
    evaluacion = resultado["evaluacion"]
    dictamen = resultado["dictamen"]

    registro = {
        "Fecha": resultado["fecha"],
        "RUC": perfil.get("ruc"),
        "Razón social": perfil.get("razon_social"),
        "Estado tributario": perfil.get("estado"),
        "Condición": perfil.get("condicion"),
        "Actividad económica": perfil.get("actividad_economica"),
        "Servicio cotizado": perfil.get("servicio_cotizado"),
        "Monto": perfil.get("monto"),
        "Moneda": perfil.get("moneda"),
        "Coherencia comercial": evaluacion.get("coherencia_comercial"),
        "Riesgo IA": evaluacion.get("nivel_riesgo"),
        "Recomendación IA": evaluacion.get("recomendacion"),
        "Dictamen final": dictamen.get("dictamen"),
        "Riesgo final": dictamen.get("nivel_riesgo"),
        "Confianza IA": dictamen.get("puntaje_confianza"),
        "Motivo": dictamen.get("motivo"),
        "Alertas": " | ".join(dictamen.get("alertas", [])),
    }

    return generar_excel([registro], "Auditoria")


def ir_a_nueva_auditoria():
    st.session_state.nav_pagina = "Nueva auditoría"


def ir_a_historial():
    st.session_state.nav_pagina = "Historial"

def normalizar_valor_excel(valor):
    """Convierte valores de pandas y NumPy a datos compatibles con JSON."""

    if isinstance(valor, dict):
        return {
            clave: normalizar_valor_excel(dato)
            for clave, dato in valor.items()
        }

    if isinstance(valor, (list, tuple)):
        return [
            normalizar_valor_excel(dato)
            for dato in valor
        ]

    # Convierte arreglos NumPy sin evaluarlos como booleanos.
    if hasattr(valor, "tolist") and not pd.api.types.is_scalar(valor):
        return normalizar_valor_excel(valor.tolist())

    # Solo comprobar valores nulos cuando son escalares.
    if pd.api.types.is_scalar(valor) and pd.isna(valor):
        return None

    return valor

def convertir_json(valor, valor_predeterminado=None):
    """Convierte una cadena JSON a Python sin interrumpir la interfaz."""

    if valor_predeterminado is None:
        valor_predeterminado = {}

    if valor is None:
        return valor_predeterminado

    if isinstance(valor, (dict, list)):
        return valor

    if isinstance(valor, str):
        try:
            return json.loads(valor)
        except (json.JSONDecodeError, TypeError):
            return valor_predeterminado

    return valor_predeterminado

def obtener_historial_desde_db():
    """Obtiene y adapta las auditorías almacenadas en MySQL."""

    auditorias = listar_auditorias()
    historial = []

    for auditoria in auditorias:
        fecha = (
            auditoria.get("actualizada_en")
            or auditoria.get("creada_en")
        )

        if fecha:
            fecha = fecha.strftime("%d/%m/%Y %H:%M:%S")
        else:
            fecha = "Sin fecha"

        historial.append({
            "auditoria_id": auditoria.get("auditoria_id"),
            "fecha": fecha,
            "ruc": auditoria.get("ruc"),
            "razon_social": auditoria.get("razon_social"),
            "servicio": auditoria.get("servicio_cotizado"),
            "monto": auditoria.get("monto"),
            "moneda": auditoria.get("moneda"),
            "dictamen": auditoria.get("dictamen"),
            "nivel_riesgo": auditoria.get("nivel_riesgo"),
            "puntaje_confianza": auditoria.get("puntaje_confianza", 0),
            "estado": auditoria.get("estado"),
            "lote_id": auditoria.get("lote_id"),
            "coherencia_comercial": auditoria.get(
                "coherencia_comercial"
            ),
            "riesgo_ia": auditoria.get("riesgo_ia"),
            "recomendacion": auditoria.get("recomendacion"),
            "estado_gemini": auditoria.get("estado_gemini"),
            "motivo": auditoria.get("motivo"),
        })

    return historial


# ============================================================
# SIDEBAR / NAVEGACIÓN
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sv-brand">
            <div class="sv-brand-icon">🛡</div>
            <div class="sv-brand-name">SmartVendor</div>
        </div>
        <div class="sv-brand-sub">
            Plataforma inteligente de evaluación y auditoría de proveedores.
        </div>
        <div class="sv-sidebar-label">MENÚ PRINCIPAL</div>
        """,
        unsafe_allow_html=True,
    )

    paginas = [
        "Dashboard",
        "Nueva auditoría",
        "Auditoría masiva",
        "Historial",
    ]

    pagina_actual = st.radio(
        "Navegación",
        paginas,
        key="nav_pagina",
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="sv-version">
            <b>SMARTVENDOR AUDIT</b><br>
            Versión 1.0 · Sistema de auditoría inteligente
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SERVICIOS
# ============================================================

try:
    provider_service, auditor_ia = obtener_servicios()
    servicios_disponibles = True
    error_servicios = None
except Exception as error:
    servicios_disponibles = False
    error_servicios = str(error)



# ============================================================
# DASHBOARD
# ============================================================

if pagina_actual == "Dashboard":

    mostrar_encabezado(
        "Dashboard",
        "Resumen general de actividad y evaluación de proveedores.",
        "VISTA GENERAL",
    )

    # --------------------------------------------------------
    # CONSULTAR INFORMACIÓN DESDE MYSQL
    # --------------------------------------------------------

    try:
        historial = obtener_historial_desde_db()
    except Exception as error:
        st.error(f"No se pudo recuperar el Dashboard desde MySQL: {error}")
        historial = []

    df = pd.DataFrame(historial) if historial else pd.DataFrame()

    total = len(df)

    if total:
        aprobados = int((df["dictamen"] == "APROBADO").sum())
        observados = int((df["dictamen"] == "OBSERVADO").sum())
        rechazados = int((df["dictamen"] == "RECHAZADO").sum())
        pendientes = int(
            (df["dictamen"] == "PENDIENTE_VALIDACION").sum()
        )
    else:
        aprobados = observados = rechazados = pendientes = 0

    porcentaje_aprobados = (
        round((aprobados / total) * 100) if total else 0
    )

    # --------------------------------------------------------
    # INDICADORES PRINCIPALES
    # --------------------------------------------------------

    st.markdown("#### Indicadores principales")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        with st.container(border=True):
            st.caption("▦ AUDITORÍAS REALIZADAS")
            st.metric("Total de auditorías", total)
            st.caption("Registros almacenados en MySQL")

    with c2:
        with st.container(border=True):
            st.caption("✓ APROBADOS")
            st.metric("Proveedores aprobados", aprobados)
            st.caption(f"{porcentaje_aprobados}% del total")

    with c3:
        with st.container(border=True):
            st.caption("! OBSERVADOS")
            st.metric("Requieren revisión", observados)
            st.caption("Necesitan evaluación adicional")

    with c4:
        with st.container(border=True):
            st.caption("× RECHAZADOS")
            st.metric("Riesgo no aceptable", rechazados)
            st.caption("No cumplen los criterios")

    # --------------------------------------------------------
    # DISTRIBUCIÓN Y ACTIVIDAD RECIENTE
    # --------------------------------------------------------

    st.markdown("")

    izquierda, derecha = st.columns([1, 1.05], gap="large")

    # --------------------------------------------------------
    # DISTRIBUCIÓN DE DICTÁMENES
    # --------------------------------------------------------

    with izquierda:

        st.markdown("#### Distribución de dictámenes")
        st.caption("Cantidad de auditorías por resultado · Datos de MySQL")

        categorias = [
            ("Aprobados", aprobados, "#36C995"),
            ("Observados", observados, "#EAB85C"),
            ("Pendientes", pendientes, "#65B9F3"),
            ("Rechazados", rechazados, "#E77C8C"),
        ]

        if total:

            for nombre, cantidad, color in categorias:

                porcentaje = round((cantidad / total) * 100)

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        margin-top:14px;
                        margin-bottom:5px;
                    ">
                        <span style="color:#D8E3F0;font-size:14px;">
                            {nombre}
                        </span>
                        <span style="
                            color:#FFFFFF;
                            font-weight:600;
                            font-size:14px;
                        ">
                            {cantidad} · {porcentaje}%
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.progress(porcentaje / 100)

            with st.container(border=True):
                st.markdown("Total de auditorías: " + str(total))
                st.caption(
                    f"Porcentaje de aprobación: {porcentaje_aprobados}%"
                )

        else:
            st.info("Todavía no hay auditorías registradas.")

    # --------------------------------------------------------
    # ACTIVIDAD RECIENTE
    # --------------------------------------------------------

    with derecha:

        st.markdown("#### Actividad reciente")
        st.caption("Las últimas cinco auditorías registradas")


        if total:

            # Paginación: 3 auditorías por página
            registros_por_pagina = 3

            if "pagina_actividad" not in st.session_state:
                st.session_state.pagina_actividad = 0

            total_paginas = max(
                1,
                (total + registros_por_pagina - 1)
                // registros_por_pagina
            )

            # Evitar páginas fuera del rango disponible
            st.session_state.pagina_actividad = min(
                st.session_state.pagina_actividad,
                total_paginas - 1
            )

            pagina = st.session_state.pagina_actividad

            inicio = pagina * registros_por_pagina
            fin = inicio + registros_por_pagina

            recientes = df.iloc[inicio:fin]

            for _, fila in recientes.iterrows():

                dictamen = fila.get("dictamen") or "N/D"
                proveedor = fila.get("razon_social") or "Proveedor sin nombre"
                servicio = fila.get("servicio") or "Servicio no especificado"
                ruc = fila.get("ruc") or "Sin RUC"
                fecha = fila.get("fecha") or "Sin fecha"

                try:
                    monto = float(fila.get("monto") or 0)
                    moneda = fila.get("moneda") or "PEN"
                    monto_texto = f"{moneda} {monto:,.2f}"
                except (ValueError, TypeError):
                    monto_texto = "Monto no disponible"

                colores = {
                    "APROBADO": ("#123D32", "#43D6A0"),
                    "OBSERVADO": ("#49391D", "#EAB85C"),
                    "RECHAZADO": ("#48232C", "#E77C8C"),
                    "PENDIENTE_VALIDACION": ("#183653", "#65B9F3"),
                }

                fondo, texto = colores.get(
                    dictamen,
                    ("#263448", "#B8C9DC")
                )

                with st.container(border=True):

                    encabezado, estado = st.columns([3, 1.3])

                    with encabezado:
                        st.markdown(f"**{proveedor}**")

                    with estado:
                        st.markdown(
                            f"""
                            <div style="
                                background:{fondo};
                                color:{texto};
                                padding:5px 8px;
                                border-radius:20px;
                                text-align:center;
                                font-size:10px;
                                font-weight:700;
                            ">
                                {dictamen}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f"""
                        <div style="color:#A9BDD3;font-size:12px;">
                            {servicio}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    dato1, dato2 = st.columns(2)

                    with dato1:
                        st.caption(f"RUC: {ruc}")

                    with dato2:
                        st.caption(monto_texto)

                    st.caption(f"Fecha: {fecha}")

            # Controles de paginación
            st.markdown("")

            anterior, indicador, siguiente = st.columns([1, 2, 1])

            with anterior:
                if st.button(
                    "← Anterior",
                    disabled=(pagina == 0),
                    use_container_width=True,
                    key="actividad_anterior",
                ):
                    st.session_state.pagina_actividad -= 1
                    st.rerun()

            with indicador:
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        padding:8px;
                        color:#A9BDD3;
                        font-size:13px;
                    ">
                        Página {pagina + 1} de {total_paginas}
                        <br>
                        <span style="font-size:11px;">
                            {total} auditorías registradas
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with siguiente:
                if st.button(
                    "Siguiente →",
                    disabled=(pagina >= total_paginas - 1),
                    use_container_width=True,
                    key="actividad_siguiente",
                ):
                    st.session_state.pagina_actividad += 1
                    st.rerun()

        else:
            st.info("Aún no hay actividad registrada.")


    # --------------------------------------------------------
    # ACCESOS RÁPIDOS
    # --------------------------------------------------------

    st.markdown("---")
    st.markdown("#### Acceso rápido")

    q1, q2 = st.columns(2)

    with q1:
        st.button(
            "＋ Iniciar nueva auditoría",
            use_container_width=True,
            on_click=ir_a_nueva_auditoria,
        )

    with q2:
        st.button(
            "▤ Consultar historial",
            use_container_width=True,
            on_click=ir_a_historial,
        )


# ============================================================
# NUEVA AUDITORÍA
# ============================================================

elif pagina_actual == "Nueva auditoría":

    mostrar_encabezado(
        "Nueva auditoría",
        "Registra los datos de la cotización y evalúa la confiabilidad del proveedor.",
        "EVALUACIÓN DE PROVEEDORES",
    )

    if not servicios_disponibles:
        st.error(f"No se pudieron inicializar los servicios: {error_servicios}")
        st.stop()

    st.markdown(
        """
        <div class="sv-panel">
            <div class="sv-step"><span class="sv-step-number">01</span> Información del proveedor</div>
            <div class="sv-section-caption">Identifica a la empresa que deseas evaluar mediante su RUC.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_auditoria"):
        ruc = st.text_input(
            "RUC del proveedor",
            placeholder="Ingresa los 11 dígitos del RUC",
            max_chars=11,
        )

        st.markdown(
            """
            <div style="height:8px"></div>
            <div class="sv-step"><span class="sv-step-number">02</span> Información de la cotización</div>
            <div class="sv-section-caption">Describe el servicio o producto y especifica el importe cotizado.</div>
            """,
            unsafe_allow_html=True,
        )

        servicio = st.text_area(
            "Servicio o producto cotizado",
            placeholder="Ej. Servicios de mantenimiento preventivo de equipos...",
            height=100,
        )

        col_monto, col_moneda = st.columns([1.2, 1])

        with col_monto:
            monto = st.number_input(
                "Monto cotizado",
                min_value=0.01,
                value=15000.00,
                step=100.00,
                format="%.2f",
            )

        with col_moneda:
            moneda = st.selectbox(
                "Moneda",
                ["PEN", "USD", "EUR"],
                format_func=lambda x: {
                    "PEN": "PEN · Soles peruanos",
                    "USD": "USD · Dólares estadounidenses",
                    "EUR": "EUR · Euros",
                }[x],
            )

        st.markdown(
            """
            <div style="height:8px"></div>
            <div class="sv-step"><span class="sv-step-number">03</span> Opciones de consulta</div>
            <div class="sv-section-caption">Puedes utilizar la información almacenada en caché o forzar una nueva consulta.</div>
            """,
            unsafe_allow_html=True,
        )

        forzar_consulta = st.checkbox(
            "Forzar consulta a las fuentes externas (ignorar caché)",
            help="Esta opción puede consumir solicitudes de la API de Decolecta.",
        )

        ejecutar = st.form_submit_button(
            "🔎  Ejecutar auditoría",
            type="primary",
            use_container_width=True,
        )


    if ejecutar:
        ruc = ruc.strip()

        if not ruc.isdigit() or len(ruc) != 11:
            st.error("El RUC debe contener exactamente 11 dígitos.")
        elif not servicio.strip():
            st.error("Ingresa el servicio o producto cotizado.")
        else:
            try:
                with st.status(
                    "Ejecutando auditoría del proveedor...",
                    expanded=True,
                ) as estado:
                    # 1. Consulta de información empresarial
                    st.write("**1 de 4 · Consulta empresarial**")

                    perfil = provider_service.consultar_proveedor(
                        ruc,
                        forzar_consulta=forzar_consulta,
                    )

                    if not perfil.get("consulta_tributaria_exitosa"):
                        errores = perfil.get("errores_fuentes", {})
                        detalle = " ".join(
                            str(v) for v in errores.values() if v
                        )
                        raise RuntimeError(
                            "No se pudo verificar la información tributaria. "
                            + detalle
                        )

                    perfil["servicio_cotizado"] = servicio.strip()
                    perfil["monto"] = monto
                    perfil["moneda"] = moneda

                    # 2. Persistencia inicial en MySQL
                    st.write("**2 de 4 · Registro en la base de datos**")

                    proveedor_db = guardar_o_actualizar(perfil)

                    cotizacion_id = guardar_cotizacion(
                        proveedor_id=proveedor_db["id"],
                        servicio_cotizado=servicio.strip(),
                        monto=monto,
                        moneda=moneda,
                    )

                    auditoria_id = crear_auditoria(cotizacion_id)

                    modelo_gemini = os.getenv(
                        "GEMINI_MODEL",
                        "gemini-4-hydrogen",
                    )

                    evaluacion_id = crear_evaluacion_ia(
                        auditoria_id,
                        modelo_gemini,
                    )

                    st.write(
                        f"Registro creado. Auditoría N.º {auditoria_id}."
                    )

                    # 3. Evaluación de Gemini y trazabilidad del intento
                    st.write("**3 de 4 · Evaluación con Gemini**")

                    intento_id = registrar_intento_gemini(
                        evaluacion_id=evaluacion_id,
                        numero_intento=1,
                        estado="EN_PROCESO",
                    )

                    try:
                        evaluacion = auditor_ia.evaluar_proveedor(perfil)

                    except Exception as error_gemini:
                        finalizar_intento_gemini(
                            intento_id=intento_id,
                            estado="ERROR",
                            codigo_error="GEMINI_ERROR",
                            detalle_error=str(error_gemini),
                        )

                        registrar_error_ia(
                            evaluacion_id,
                            str(error_gemini),
                        )

                        raise

                    finalizar_intento_gemini(
                        intento_id=intento_id,
                        estado="EXITOSO",
                    )

                    if hasattr(evaluacion, "model_dump"):
                        evaluacion_db = evaluacion.model_dump()
                    elif hasattr(evaluacion, "dict"):
                        evaluacion_db = evaluacion.dict()
                    else:
                        evaluacion_db = evaluacion

                    guardar_resultado_ia(
                        evaluacion_id,
                        evaluacion_db,
                    )

                    # 4. Generación y persistencia del dictamen
                    st.write("**4 de 4 · Generación del dictamen**")

                    dictamen = generar_dictamen(perfil, evaluacion)

                    actualizar_dictamen(
                        auditoria_id=auditoria_id,
                        dictamen=dictamen.get("dictamen"),
                        nivel_riesgo=(
                            str(dictamen.get("nivel_riesgo", "No determinado"))
                            .upper()
                        ),
                        puntaje_confianza=int(
                            dictamen.get("puntaje_confianza", 0)
                        ),
                        motivo=(
                            dictamen.get("motivo")
                            or dictamen.get("justificacion")
                            or evaluacion_db.get("justificacion")
                        ),
                        observacion="Auditoría individual registrada desde SmartVendor Audit.",
                        accion="EVALUACION",
                    )

                    estado.update(
                        label="Auditoría guardada correctamente en MySQL",
                        state="complete",
                        expanded=False,
                    )

                resultado = {
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "perfil": perfil,
                    "evaluacion": evaluacion,
                    "dictamen": dictamen,
                    "auditoria_id": auditoria_id,
                }

                st.session_state.ultimo_resultado = resultado

                st.session_state.historial.append(
                    {
                        "fecha": resultado["fecha"],
                        "ruc": perfil.get("ruc"),
                        "razon_social": perfil.get("razon_social"),
                        "servicio": servicio.strip(),
                        "monto": monto,
                        "moneda": moneda,
                        "dictamen": dictamen.get("dictamen"),
                        "nivel_riesgo": dictamen.get("nivel_riesgo"),
                        "puntaje_confianza": dictamen.get(
                            "puntaje_confianza", 0
                        ),
                    }
                )

                st.success(
                    f"Auditoría N.º {auditoria_id} completada y guardada en MySQL."
                )

            except Exception as error:
                st.error(f"No se pudo completar la auditoría: {error}")


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    resultado = st.session_state.ultimo_resultado

    if resultado:
        perfil = resultado["perfil"]
        evaluacion = resultado["evaluacion"]
        dictamen = resultado["dictamen"]

        st.markdown("---")
        st.markdown("#### Resultado de la auditoría")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Dictamen", dictamen.get("dictamen", "N/D"))
        col2.metric("Nivel de riesgo", dictamen.get("nivel_riesgo", "N/D"))
        col3.metric(
            "Confianza IA",
            f"{dictamen.get('puntaje_confianza', 0)}/100",
        )
        col4.metric(
            "Monto cotizado",
            formato_moneda(perfil.get("monto", 0), perfil.get("moneda", "PEN")),
        )

        estado_dictamen = dictamen.get("dictamen", "")
        clase = (
            "sv-result-approved"
            if estado_dictamen == "APROBADO"
            else "sv-result-rejected"
            if estado_dictamen == "RECHAZADO"
            else "sv-result-observed"
        )

        mensajes = {
            "APROBADO": "El proveedor cumple las condiciones evaluadas por el sistema.",
            "OBSERVADO": "El proveedor requiere una revisión adicional antes de tomar una decisión.",
            "RECHAZADO": "Se identificaron condiciones que impiden aprobar al proveedor.",
            "PENDIENTE_VALIDACION": "No se pudo completar la verificación tributaria.",
        }

        st.markdown(
            f"""
            <div class="sv-result {clase}">
                <div class="sv-result-title">{etiqueta_dictamen(estado_dictamen)}</div>
                <div class="sv-result-text">{mensajes.get(estado_dictamen, 'Revisa los detalles del dictamen.')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_empresa, tab_ia, tab_dictamen = st.tabs(
            ["▣  Información empresarial", "✦  Evaluación de Gemini", "◈  Dictamen final"]
        )

        with tab_empresa:
            st.markdown("#### Perfil empresarial")

            datos_empresa = {
                "RUC": perfil.get("ruc"),
                "Razón social": perfil.get("razon_social"),
                "Estado tributario": perfil.get("estado"),
                "Condición": perfil.get("condicion"),
                "Dirección": perfil.get("direccion"),
                "Actividad económica": perfil.get("actividad_economica"),
                "Tipo de contribuyente": perfil.get("tipo_contribuyente"),
                "Número de trabajadores": perfil.get("numero_trabajadores"),
                "Fuente de actividad económica": perfil.get("fuente_actividad_economica"),
            }

            info_df = pd.DataFrame(
                [
                    {"Campo": campo, "Información": valor or "No disponible"}
                    for campo, valor in datos_empresa.items()
                ]
            )
            st.dataframe(info_df, use_container_width=True, hide_index=True)

            st.markdown("#### Fuentes consultadas")
            fuentes = perfil.get("fuentes", {})
            f1, f2, f3 = st.columns(3)

            f1.metric("OpenRUC", "Disponible" if fuentes.get("openruc") else "No disponible")
            f2.metric("Decolecta", "Disponible" if fuentes.get("decolecta") else "No disponible")
            f3.metric("Origen", "Caché" if perfil.get("desde_cache") else "Consulta externa")

        with tab_ia:
            st.markdown("#### Análisis de coherencia comercial")

            c1, c2, c3 = st.columns(3)
            c1.metric("Coherencia", evaluacion.get("coherencia_comercial", "N/D"))
            c2.metric("Riesgo IA", evaluacion.get("nivel_riesgo", "N/D"))
            c3.metric("Recomendación", evaluacion.get("recomendacion", "N/D"))

            confianza = int(evaluacion.get("puntaje_confianza", 0) or 0)
            st.markdown("**Puntaje de confianza**")
            st.progress(max(0, min(confianza, 100)) / 100)
            st.caption(f"{confianza} de 100 puntos")

            st.markdown("#### Justificación")
            st.write(evaluacion.get("justificacion", "Sin justificación disponible."))

            st.markdown("#### Alertas identificadas por Gemini")
            alertas_ia = evaluacion.get("alertas", [])

            if alertas_ia:
                for alerta in alertas_ia:
                    st.warning(alerta)
            else:
                st.success("No se identificaron alertas.")

        with tab_dictamen:
            st.markdown("#### Resultado del motor de reglas")

            d1, d2 = st.columns(2)
            d1.metric("Dictamen final", dictamen.get("dictamen", "N/D"))
            d2.metric("Riesgo final", dictamen.get("nivel_riesgo", "N/D"))

            st.markdown("#### Motivo")
            st.write(dictamen.get("motivo", "Sin información disponible."))

            st.markdown("#### Alertas finales")
            alertas_finales = dictamen.get("alertas", [])

            if alertas_finales:
                for alerta in alertas_finales:
                    st.warning(alerta)
            else:
                st.success("No existen alertas pendientes.")

        st.download_button(
            "⬇  Descargar informe de esta auditoría",
            data=exportar_resultado_individual(resultado),
            file_name=f"smartvendor_auditoria_{perfil.get('ruc')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ============================================================
# AUDITORÍA MASIVA
# ============================================================

elif pagina_actual == "Auditoría masiva":

    mostrar_encabezado(
        "Auditoría masiva",
        "Carga un archivo Excel para evaluar múltiples proveedores en un solo proceso.",
        "PROCESAMIENTO POR LOTES",
    )

    if not servicios_disponibles:
        st.error(f"No se pudieron inicializar los servicios: {error_servicios}")
        st.stop()

    st.markdown(
        """
        <div class="sv-panel">
            <div class="sv-step"><span class="sv-step-number">01</span> Carga del archivo</div>
            <div class="sv-section-caption">
                El archivo debe ser Excel (.xlsx) e incluir RUC, servicio_cotizado y monto.
                La columna moneda es opcional; si no existe, se utilizará PEN.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    plantilla = generar_excel(
        [{
            "ruc": "20100047218",
            "servicio_cotizado": "Servicios de intermediación financiera",
            "monto": 15000,
            "moneda": "PEN",
        }],
        "Proveedores",
    )
    st.download_button(
        "⬇ Descargar plantilla de Excel",
        data=plantilla,
        file_name="plantilla_smartvendor.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    archivo = st.file_uploader(
        "Selecciona el archivo de proveedores",
        type=["xlsx"],
        help="Sube un archivo .xlsx con las cotizaciones que deseas auditar.",
    )

    if archivo is not None:
        try:
            df_carga = cargar_proveedores(archivo)

            total_filas = len(df_carga)
            df_validos = df_carga[df_carga["registro_valido"] == True].copy()
            df_invalidos = df_carga[df_carga["registro_valido"] == False].copy()

            st.markdown("---")
            st.markdown("#### 02 · Validación de registros")

            m1, m2, m3 = st.columns(3)
            m1.metric("Registros encontrados", total_filas)
            m2.metric("Registros válidos", len(df_validos))
            m3.metric("Registros inválidos", len(df_invalidos))

            if not df_validos.empty:
                st.markdown("**Vista previa de registros válidos**")
                st.dataframe(
                    df_validos[
                        ["fila_excel", "ruc", "servicio_cotizado", "monto", "moneda"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            if not df_invalidos.empty:
                st.markdown("**Registros que necesitan corrección**")
                vista_invalidos = df_invalidos[
                    ["fila_excel", "ruc", "servicio_cotizado", "monto", "moneda",
                     "errores_validacion"]
                ].copy()
                vista_invalidos["errores_validacion"] = vista_invalidos[
                    "errores_validacion"
                ].apply(lambda errores: " | ".join(errores) if isinstance(errores, list) else str(errores))
                st.dataframe(
                    vista_invalidos,
                    use_container_width=True,
                    hide_index=True,
                )

            if df_validos.empty:
                st.warning("No hay registros válidos para auditar. Corrige el Excel y vuelve a cargarlo.")
            else:
                st.info(
                    f"Se procesarán {len(df_validos)} cotizaciones válidas. "
                    "Los datos tributarios de un mismo RUC se consultarán una sola vez "
                    "durante este lote. No se forzarán consultas externas."
                )


                if st.button(
                    "▶ Iniciar auditoría masiva",
                    type="primary",
                    use_container_width=True,
                    key="iniciar_auditoria_masiva",
                ):
                    resultados_lote = []
                    perfiles_por_ruc = {}
                    perfiles_por_registro = {}
                    auditorias_por_registro = {}

                    errores_lote = 0
                    barra = st.progress(0)
                    texto_progreso = st.empty()

                    # 1. Crear el lote en MySQL
                    lote_id = crear_lote(
                        nombre_archivo=archivo.name,
                        total_registros=total_filas,
                        registros_validos=len(df_validos),
                        registros_invalidos=len(df_invalidos),
                    )

                    actualizar_estado_lote(lote_id, "PROCESANDO")

                    st.session_state["lote_auditoria_actual"] = lote_id

                    try:
                        # 2. Guardar todas las filas inválidas
                        for _, fila_invalida in df_invalidos.iterrows():
                            datos_originales = {
                                campo: normalizar_valor_excel(valor)
                                for campo, valor in fila_invalida.to_dict().items()
                            }

                            guardar_registro_lote(
                                lote_id=lote_id,
                                fila_excel=int(fila_invalida["fila_excel"]),
                                datos_originales=datos_originales,
                                estado_validacion="INVALIDO",
                                errores_validacion=fila_invalida[
                                    "errores_validacion"
                                ],
                            )

                        # 3. Procesar los registros válidos
                        for posicion, (_, fila) in enumerate(
                            df_validos.iterrows(),
                            start=1,
                        ):
                            ruc_actual = str(fila["ruc"]).strip()
                            servicio_actual = str(
                                fila["servicio_cotizado"]
                            ).strip()
                            monto_actual = float(fila["monto"])
                            moneda_actual = str(
                                fila["moneda"]
                            ).strip().upper()
                            fila_excel = int(fila["fila_excel"])

                            clave_registro = (
                                f"{fila_excel}|{ruc_actual}"
                            )

                            texto_progreso.write(
                                f"Procesando registro {posicion} de "
                                f"{len(df_validos)} · RUC {ruc_actual}"
                            )

                            auditoria_id = None
                            evaluacion_id = None

                            try:
                                # Consultar datos tributarios una sola vez
                                # por RUC durante el lote.
                                if ruc_actual not in perfiles_por_ruc:
                                    perfiles_por_ruc[ruc_actual] = (
                                        provider_service.consultar_proveedor(
                                            ruc_actual,
                                            forzar_consulta=False,
                                        )
                                    )

                                perfil = perfiles_por_ruc[ruc_actual].copy()

                                perfil["ruc"] = ruc_actual
                                perfil["servicio_cotizado"] = servicio_actual
                                perfil["monto"] = monto_actual
                                perfil["moneda"] = moneda_actual

                                perfiles_por_registro[
                                    clave_registro
                                ] = perfil.copy()

                                # Guardar proveedor y cotización
                                proveedor_db = guardar_o_actualizar(perfil)

                                cotizacion_id = guardar_cotizacion(
                                    proveedor_id=proveedor_db["id"],
                                    servicio_cotizado=servicio_actual,
                                    monto=monto_actual,
                                    moneda=moneda_actual,
                                    lote_id=lote_id,
                                )

                                # Guardar la fila válida vinculada
                                # a su cotización.
                                guardar_registro_lote(
                                    lote_id=lote_id,
                                    fila_excel=fila_excel,
                                    datos_originales={
                                        campo: normalizar_valor_excel(valor)
                                        for campo, valor in fila.to_dict().items()
                                    },
                                    estado_validacion="VALIDO",
                                    cotizacion_id=cotizacion_id,
                                )

                                # Crear auditoría y evaluación inicial
                                auditoria_id = crear_auditoria(
                                    cotizacion_id
                                )

                                modelo_gemini = os.getenv(
                                    "GEMINI_MODEL",
                                    "gemini-4-hydrogen",
                                )

                                evaluacion_id = crear_evaluacion_ia(
                                    auditoria_id,
                                    modelo_gemini,
                                )

                                auditorias_por_registro[
                                    clave_registro
                                ] = {
                                    "auditoria_id": auditoria_id,
                                    "evaluacion_id": evaluacion_id,
                                }

                                # Si no hay verificación tributaria,
                                # se conserva la auditoría pendiente.
                                if not perfil.get(
                                    "consulta_tributaria_exitosa"
                                ):
                                    errores = perfil.get(
                                        "errores_fuentes", {}
                                    )

                                    detalle = " ".join(
                                        str(v)
                                        for v in errores.values()
                                        if v
                                    )

                                    mensaje = (
                                        "No se pudo verificar la "
                                        "información tributaria. "
                                        + detalle
                                    )

                                    registrar_error_ia(
                                        evaluacion_id,
                                        mensaje,
                                    )

                                    dictamen = {
                                        "dictamen": "PENDIENTE_VALIDACION",
                                        "nivel_riesgo": "No determinado",
                                        "puntaje_confianza": 0,
                                        "motivo": mensaje,
                                        "alertas": [
                                            "Consulta tributaria no exitosa."
                                        ],
                                    }

                                    evaluacion = {
                                        "coherencia_comercial": "insuficiente",
                                        "nivel_riesgo": "alto",
                                        "puntaje_confianza": 0,
                                        "justificacion": mensaje,
                                        "alertas": [
                                            "Consulta tributaria no exitosa."
                                        ],
                                        "recomendacion": "revisar",
                                    }

                                    errores_lote += 1

                                else:
                                    # Registrar el intento de Gemini
                                    intento_id = registrar_intento_gemini(
                                        evaluacion_id=evaluacion_id,
                                        numero_intento=1,
                                        estado="EN_PROCESO",
                                    )

                                    try:
                                        evaluacion = (
                                            auditor_ia.evaluar_proveedor(
                                                perfil
                                            )
                                        )

                                        if hasattr(
                                            evaluacion, "model_dump"
                                        ):
                                            evaluacion_db = (
                                                evaluacion.model_dump()
                                            )
                                        elif hasattr(evaluacion, "dict"):
                                            evaluacion_db = evaluacion.dict()
                                        else:
                                            evaluacion_db = evaluacion

                                        guardar_resultado_ia(
                                            evaluacion_id,
                                            evaluacion_db,
                                        )

                                        finalizar_intento_gemini(
                                            intento_id=intento_id,
                                            estado="EXITOSO",
                                        )

                                        dictamen = generar_dictamen(
                                            perfil,
                                            evaluacion,
                                        )

                                        actualizar_dictamen(
                                            auditoria_id=auditoria_id,
                                            dictamen=dictamen.get(
                                                "dictamen"
                                            ),
                                            nivel_riesgo=str(
                                                dictamen.get(
                                                    "nivel_riesgo",
                                                    "No determinado",
                                                )
                                            ).upper(),
                                            puntaje_confianza=int(
                                                dictamen.get(
                                                    "puntaje_confianza",
                                                    0,
                                                )
                                            ),
                                            motivo=(
                                                dictamen.get("motivo")
                                                or evaluacion_db.get(
                                                    "justificacion"
                                                )
                                            ),
                                            observacion=(
                                                "Auditoría masiva desde Excel."
                                            ),
                                            accion="EVALUACION",
                                        )

                                    except Exception as error_gemini:
                                        finalizar_intento_gemini(
                                            intento_id=intento_id,
                                            estado="ERROR",
                                            codigo_error="GEMINI_ERROR",
                                            detalle_error=str(error_gemini),
                                        )

                                        registrar_error_ia(
                                            evaluacion_id,
                                            str(error_gemini),
                                        )

                                        raise

                                # Guardar resultado para la interfaz
                                resultados_lote.append({
                                    "Fila Excel": fila_excel,
                                    "RUC": ruc_actual,
                                    "Razón social": perfil.get("razon_social"),
                                    "Estado tributario": perfil.get("estado"),
                                    "Condición": perfil.get("condicion"),
                                    "Actividad económica": perfil.get(
                                        "actividad_economica"
                                    ),
                                    "Servicio cotizado": servicio_actual,
                                    "Monto": monto_actual,
                                    "Moneda": moneda_actual,
                                    "Coherencia comercial": evaluacion.get(
                                        "coherencia_comercial"
                                    ),
                                    "Riesgo IA": evaluacion.get(
                                        "nivel_riesgo"
                                    ),
                                    "Recomendación IA": evaluacion.get(
                                        "recomendacion"
                                    ),
                                    "Confianza IA": dictamen.get(
                                        "puntaje_confianza",
                                        evaluacion.get(
                                            "puntaje_confianza", 0
                                        ),
                                    ),
                                    "Dictamen final": dictamen.get(
                                        "dictamen"
                                    ),
                                    "Riesgo final": dictamen.get(
                                        "nivel_riesgo"
                                    ),
                                    "Motivo": dictamen.get("motivo"),
                                    "Alertas": " | ".join(
                                        dictamen.get("alertas", [])
                                    ),
                                    "Error de proceso": (
                                        dictamen.get("motivo")
                                        if dictamen.get("dictamen")
                                        == "PENDIENTE_VALIDACION"
                                        else ""
                                    ),
                                })

                                st.session_state.historial.append({
                                    "fecha": datetime.now().strftime(
                                        "%d/%m/%Y %H:%M:%S"
                                    ),
                                    "ruc": ruc_actual,
                                    "razon_social": perfil.get(
                                        "razon_social"
                                    ),
                                    "servicio": servicio_actual,
                                    "monto": monto_actual,
                                    "moneda": moneda_actual,
                                    "dictamen": dictamen.get("dictamen"),
                                    "nivel_riesgo": dictamen.get(
                                        "nivel_riesgo"
                                    ),
                                    "puntaje_confianza": dictamen.get(
                                        "puntaje_confianza", 0
                                    ),
                                })

                            except Exception as error:
                                errores_lote += 1

                                resultados_lote.append({
                                    "Fila Excel": fila_excel,
                                    "RUC": ruc_actual,
                                    "Razón social": "",
                                    "Estado tributario": "",
                                    "Condición": "",
                                    "Actividad económica": "",
                                    "Servicio cotizado": servicio_actual,
                                    "Monto": monto_actual,
                                    "Moneda": moneda_actual,
                                    "Coherencia comercial": "",
                                    "Riesgo IA": "No evaluado",
                                    "Recomendación IA": "Revisar",
                                    "Confianza IA": 0,
                                    "Dictamen final": "PENDIENTE_VALIDACION",
                                    "Riesgo final": "No determinado",
                                    "Motivo": (
                                        "No se pudo completar la auditoría "
                                        "de este registro."
                                    ),
                                    "Alertas": "",
                                    "Error de proceso": str(error),
                                })

                            barra.progress(
                                posicion / len(df_validos)
                            )

                        # 4. Guardar resultados y referencias para reprocesar
                        st.session_state[
                            "resultados_auditoria_masiva"
                        ] = resultados_lote

                        st.session_state[
                            "invalidos_auditoria_masiva"
                        ] = df_invalidos.to_dict("records")

                        st.session_state.perfiles_auditoria_masiva = (
                            perfiles_por_registro
                        )

                        st.session_state[
                            "auditorias_masivas_db"
                        ] = auditorias_por_registro

                        # 5. Finalizar lote
                        estado_final = (
                            "COMPLETADO_CON_ERRORES"
                            if errores_lote > 0
                            else "COMPLETADO"
                        )

                        actualizar_estado_lote(
                            lote_id,
                            estado_final,
                        )

                        texto_progreso.success(
                            f"Lote N.º {lote_id} finalizado: "
                            f"{len(resultados_lote)} registros procesados."
                        )

                    except Exception as error_lote:
                        actualizar_estado_lote(lote_id, "ERROR")
                        st.error(
                            f"No se pudo completar el lote N.º "
                            f"{lote_id}: {error_lote}"
                        )


            # Mostrar y exportar el último lote procesado mientras el archivo siga cargado.
            resultados_guardados = st.session_state.get("resultados_auditoria_masiva", [])
            if resultados_guardados:
                st.markdown("---")
                st.markdown("#### 03 · Resultados de la auditoría masiva")

                df_resultados = pd.DataFrame(resultados_guardados)
                total_procesados = len(df_resultados)
                aprobados_lote = int((df_resultados["Dictamen final"] == "APROBADO").sum())
                observados_lote = int((df_resultados["Dictamen final"] == "OBSERVADO").sum())
                rechazados_lote = int((df_resultados["Dictamen final"] == "RECHAZADO").sum())
                pendientes_lote = int((df_resultados["Dictamen final"] == "PENDIENTE_VALIDACION").sum())

                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Procesados", total_procesados)
                r2.metric("Aprobados", aprobados_lote)
                r3.metric("Observados", observados_lote)
                r4.metric("Rechazados / pendientes", rechazados_lote + pendientes_lote)

                st.dataframe(df_resultados, use_container_width=True, hide_index=True)

                # ------------------------------------------------
                # REPROCESAMIENTO DE AUDITORÍAS PENDIENTES
                # ------------------------------------------------
                st.markdown("#### 04 · Reprocesar auditorías pendientes")

                perfiles_guardados = st.session_state.get(
                    "perfiles_auditoria_masiva", {}
                )


                auditorias_db = st.session_state.get(
                    "auditorias_masivas_db", {}
                )

                pendientes_reintentables = []

                for registro in resultados_guardados:
                    if registro.get("Dictamen final") != "PENDIENTE_VALIDACION":
                        continue

                    clave = (
                        f"{registro.get('Fila Excel')}|{registro.get('RUC')}"
                    )

                    perfil_guardado = perfiles_guardados.get(clave, {})
                    referencias_db = auditorias_db.get(clave, {})

                    if (
                        clave in perfiles_guardados
                        and referencias_db.get("auditoria_id")
                        and perfil_guardado.get("consulta_tributaria_exitosa")
                    ):
                        pendientes_reintentables.append(clave)


                if pendientes_reintentables:
                    st.info(
                        "Puedes volver a ejecutar Gemini para estos registros. "
                        "Se reutilizará el perfil tributario guardado y no se "
                        "consultarán nuevamente OpenRUC ni Decolecta."
                    )

                    seleccionados = st.multiselect(
                        "Selecciona los registros que deseas reprocesar",
                        options=pendientes_reintentables,
                        format_func=lambda clave: (
                            f"Fila {clave.split('|')[0]} · RUC {clave.split('|')[1]}"
                        ),
                        key="seleccion_pendientes_reintento",
                    )

                    if st.button(
                        "↻ Reprocesar seleccionados",
                        type="primary",
                        disabled=not seleccionados,
                        use_container_width=True,
                        key="reprocesar_pendientes",
                    ):
                        progreso_reintento = st.progress(0)
                        estado_reintento = st.empty()

                        for indice, clave in enumerate(seleccionados, start=1):
                            fila_excel, ruc_reintento = clave.split("|", 1)
                            perfil_reintento = perfiles_guardados[clave].copy()

                            estado_reintento.write(
                                f"Reprocesando fila {fila_excel} · RUC {ruc_reintento}"
                            )


                            try:
                                referencias = auditorias_db.get(clave)

                                if not referencias:
                                    raise RuntimeError(
                                        "No se encontraron los identificadores "
                                        "de la auditoría en MySQL."
                                    )

                                auditoria_id = referencias["auditoria_id"]

                                # Crear una nueva evaluación asociada
                                # a la misma auditoría.
                                modelo_gemini = os.getenv(
                                    "GEMINI_MODEL",
                                    "gemini-4-hydrogen",
                                )

                                nueva_evaluacion_id = crear_evaluacion_ia(
                                    auditoria_id,
                                    modelo_gemini,
                                )

                                intento_id = registrar_intento_gemini(
                                    evaluacion_id=nueva_evaluacion_id,
                                    numero_intento=1,
                                    estado="EN_PROCESO",
                                )

                                try:
                                    evaluacion_reintento = (
                                        auditor_ia.evaluar_proveedor(
                                            perfil_reintento
                                        )
                                    )

                                    if hasattr(
                                        evaluacion_reintento,
                                        "model_dump",
                                    ):
                                        evaluacion_db = (
                                            evaluacion_reintento.model_dump()
                                        )
                                    elif hasattr(
                                        evaluacion_reintento,
                                        "dict",
                                    ):
                                        evaluacion_db = (
                                            evaluacion_reintento.dict()
                                        )
                                    else:
                                        evaluacion_db = evaluacion_reintento

                                    guardar_resultado_ia(
                                        nueva_evaluacion_id,
                                        evaluacion_db,
                                    )

                                    finalizar_intento_gemini(
                                        intento_id=intento_id,
                                        estado="EXITOSO",
                                    )

                                except Exception as error_gemini:
                                    finalizar_intento_gemini(
                                        intento_id=intento_id,
                                        estado="ERROR",
                                        codigo_error="GEMINI_ERROR",
                                        detalle_error=str(error_gemini),
                                    )

                                    registrar_error_ia(
                                        nueva_evaluacion_id,
                                        str(error_gemini),
                                    )

                                    raise

                                dictamen_reintento = generar_dictamen(
                                    perfil_reintento,
                                    evaluacion_reintento,
                                )

                                # Actualizar el dictamen de la misma
                                # auditoría y registrar el reprocesamiento.
                                actualizar_dictamen(
                                    auditoria_id=auditoria_id,
                                    dictamen=dictamen_reintento.get(
                                        "dictamen"
                                    ),
                                    nivel_riesgo=str(
                                        dictamen_reintento.get(
                                            "nivel_riesgo",
                                            "No determinado",
                                        )
                                    ).upper(),
                                    puntaje_confianza=int(
                                        dictamen_reintento.get(
                                            "puntaje_confianza",
                                            0,
                                        )
                                    ),
                                    motivo=(
                                        dictamen_reintento.get("motivo")
                                        or evaluacion_db.get("justificacion")
                                    ),
                                    observacion=(
                                        "Reprocesamiento de auditoría "
                                        "masiva mediante Gemini."
                                    ),
                                    accion="REPROCESAMIENTO",
                                )

                                # Actualizar la referencia a la evaluación
                                # más reciente, manteniendo la auditoría.
                                auditorias_db[clave][
                                    "evaluacion_id"
                                ] = nueva_evaluacion_id

                                for registro in resultados_guardados:
                                    if (
                                        str(registro.get("Fila Excel"))
                                        == fila_excel
                                        and str(registro.get("RUC"))
                                        == ruc_reintento
                                    ):
                                        registro.update({
                                            "Razón social": perfil_reintento.get(
                                                "razon_social"
                                            ),
                                            "Estado tributario": perfil_reintento.get(
                                                "estado"
                                            ),
                                            "Condición": perfil_reintento.get(
                                                "condicion"
                                            ),
                                            "Actividad económica": perfil_reintento.get(
                                                "actividad_economica"
                                            ),
                                            "Coherencia comercial": (
                                                evaluacion_db.get(
                                                    "coherencia_comercial"
                                                )
                                            ),
                                            "Riesgo IA": evaluacion_db.get(
                                                "nivel_riesgo"
                                            ),
                                            "Recomendación IA": evaluacion_db.get(
                                                "recomendacion"
                                            ),
                                            "Confianza IA": dictamen_reintento.get(
                                                "puntaje_confianza",
                                                evaluacion_db.get(
                                                    "puntaje_confianza", 0
                                                ),
                                            ),
                                            "Dictamen final": (
                                                dictamen_reintento.get(
                                                    "dictamen"
                                                )
                                            ),
                                            "Riesgo final": (
                                                dictamen_reintento.get(
                                                    "nivel_riesgo"
                                                )
                                            ),
                                            "Motivo": dictamen_reintento.get(
                                                "motivo"
                                            ),
                                            "Alertas": " | ".join(
                                                dictamen_reintento.get(
                                                    "alertas", []
                                                )
                                            ),
                                            "Error de proceso": "",
                                        })
                                        break

                            except Exception as error:
                                for registro in resultados_guardados:
                                    if (
                                        str(registro.get("Fila Excel"))
                                        == fila_excel
                                        and str(registro.get("RUC"))
                                        == ruc_reintento
                                    ):
                                        registro["Error de proceso"] = str(
                                            error
                                        )
                                        break

                                # Actualizar el historial existente o agregarlo si no existía.
                                coincidencias = [
                                    item for item in st.session_state.historial
                                    if (
                                        str(item.get("ruc")) == ruc_reintento
                                        and str(item.get("servicio")) == str(perfil_reintento.get("servicio_cotizado"))
                                        and float(item.get("monto", 0) or 0) == float(perfil_reintento.get("monto", 0) or 0)
                                    )
                                ]

                                datos_historial = {
                                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                    "ruc": ruc_reintento,
                                    "razon_social": perfil_reintento.get("razon_social"),
                                    "servicio": perfil_reintento.get("servicio_cotizado"),
                                    "monto": perfil_reintento.get("monto"),
                                    "moneda": perfil_reintento.get("moneda"),
                                    "dictamen": dictamen_reintento.get("dictamen"),
                                    "nivel_riesgo": dictamen_reintento.get("nivel_riesgo"),
                                    "puntaje_confianza": dictamen_reintento.get("puntaje_confianza", 0),
                                }

                                if coincidencias:
                                    coincidencias[-1].update(datos_historial)
                                else:
                                    st.session_state.historial.append(datos_historial)

                            except Exception as error:
                                for registro in resultados_guardados:
                                    if (
                                        str(registro.get("Fila Excel")) == fila_excel
                                        and str(registro.get("RUC")) == ruc_reintento
                                    ):
                                        registro["Error de proceso"] = str(error)
                                        break

                            progreso_reintento.progress(
                                indice / len(seleccionados)
                            )

                        st.session_state["resultados_auditoria_masiva"] = resultados_guardados
                        st.session_state["auditorias_masivas_db"] = auditorias_db
                        estado_reintento.success("Reprocesamiento finalizado.")
                        st.rerun()

                else:
                    st.caption(
                        "No hay auditorías pendientes con perfil tributario disponible "
                        "para reprocesar. Los registros sin perfil guardado requieren "
                        "una nueva consulta empresarial."
                    )

                invalidos_guardados = st.session_state.get("invalidos_auditoria_masiva", [])
                invalidos_exportables = []
                for registro in invalidos_guardados:
                    copia = dict(registro)
                    errores = copia.get("errores_validacion", [])
                    copia["errores_validacion"] = (
                        " | ".join(errores) if isinstance(errores, list) else str(errores)
                    )
                    invalidos_exportables.append(copia)

                st.download_button(
                    "⬇ Descargar informe completo en Excel",
                    data=generar_excel_masivo(resultados_guardados, invalidos_exportables),
                    file_name="smartvendor_resultados_auditoria_masiva.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        except Exception as error:
            st.error(f"No se pudo leer el archivo Excel: {error}")


# ============================================================
# HISTORIAL
# ============================================================

elif pagina_actual == "Historial":

    mostrar_encabezado(
        "Historial de auditorías",
        "Consulta, filtra y exporta todos los resultados almacenados en MySQL.",
        "REGISTRO DE ACTIVIDAD",
    )

    try:
        historial = obtener_historial_desde_db()
    except Exception as error:
        st.error(f"No se pudo recuperar el historial desde MySQL: {error}")
        historial = []

    if not historial:
        st.info("Todavía no se han ejecutado auditorías en esta sesión.")
    else:
        df_historial = pd.DataFrame(historial)

        total = len(df_historial)
        aprobados = int((df_historial["dictamen"] == "APROBADO").sum())
        observados = int((df_historial["dictamen"] == "OBSERVADO").sum())
        rechazados = int((df_historial["dictamen"] == "RECHAZADO").sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de auditorías", total)
        c2.metric("Aprobados", aprobados)
        c3.metric("Observados", observados)
        c4.metric("Rechazados", rechazados)

        st.markdown("---")
        st.markdown("#### Buscar y filtrar")

        filtro1, filtro2 = st.columns([1.3, 1])

        with filtro1:
            busqueda = st.text_input(
                "Buscar proveedor",
                placeholder="RUC o razón social",
            )

        with filtro2:
            opciones = ["Todos"] + sorted(
                df_historial["dictamen"].dropna().unique().tolist()
            )
            filtro_dictamen = st.selectbox("Dictamen", opciones)

        filtrado = df_historial.copy()

        if busqueda.strip():
            termino = busqueda.strip().lower()
            filtrado = filtrado[
                filtrado["ruc"].astype(str).str.lower().str.contains(termino)
                | filtrado["razon_social"].astype(str).str.lower().str.contains(termino)
            ]

        if filtro_dictamen != "Todos":
            filtrado = filtrado[filtrado["dictamen"] == filtro_dictamen]

        st.markdown(
            f'<div class="sv-muted">Mostrando {len(filtrado)} de {total} auditorías.</div>',
            unsafe_allow_html=True,
        )

        columnas = [
            "fecha",
            "ruc",
            "razon_social",
            "servicio",
            "monto",
            "moneda",
            "dictamen",
            "nivel_riesgo",
            "puntaje_confianza",
        ]

        st.dataframe(
            filtrado[columnas],
            use_container_width=True,
            hide_index=True,
        )

        if not filtrado.empty:
            st.download_button(
                "⬇  Exportar resultados filtrados a Excel",
                data=generar_excel(filtrado.to_dict("records")),
                file_name="smartvendor_historial.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


        # --------------------------------------------------------
        # DETALLE DE AUDITORÍA
        # --------------------------------------------------------

        st.markdown("---")
        st.markdown("### Consultar detalle de auditoría")
        st.caption(
            "Selecciona una auditoría para consultar su información "
            "empresarial, evaluación de Gemini y trazabilidad."
        )

        if not filtrado.empty:

            opciones_auditorias = {
                int(fila["auditoria_id"]): (
                    f'ID {fila["auditoria_id"]} · '
                    f'{fila["razon_social"]} · '
                    f'{fila["ruc"]} · '
                    f'{fila["dictamen"]}'
                )
                for _, fila in filtrado.iterrows()
                if pd.notna(fila.get("auditoria_id"))
            }

            if opciones_auditorias:

                auditoria_seleccionada = st.selectbox(
                    "Selecciona la auditoría",
                    options=list(opciones_auditorias.keys()),
                    format_func=lambda auditoria_id: (
                        opciones_auditorias[auditoria_id]
                    ),
                    key="auditoria_detalle_seleccionada",
                )

                if st.button(
                    "Consultar detalle",
                    type="primary",
                    use_container_width=True,
                    key="consultar_detalle_auditoria",
                ):
                    st.session_state["mostrar_detalle_auditoria"] = True

                if st.session_state.get("mostrar_detalle_auditoria"):

                    auditoria_id = auditoria_seleccionada

                    try:
                        auditoria = obtener_auditoria(auditoria_id)

                        if not auditoria:
                            st.warning(
                                "No se encontró la auditoría seleccionada."
                            )
                        else:
                            evaluaciones = listar_evaluaciones(auditoria_id)
                            historial_cambios = listar_historial(auditoria_id)

                            st.markdown("---")
                            st.markdown(
                                f"## Auditoría N.º {auditoria_id}"
                            )

                            # Información general
                            st.markdown("#### 01 · Información general")

                            g1, g2, g3, g4 = st.columns(4)

                            g1.metric(
                                "Dictamen",
                                auditoria.get("dictamen") or "N/D",
                            )
                            g2.metric(
                                "Riesgo",
                                auditoria.get("nivel_riesgo") or "N/D",
                            )
                            g3.metric(
                                "Confianza",
                                f'{auditoria.get("puntaje_confianza", 0)}/100',
                            )
                            g4.metric(
                                "Estado",
                                auditoria.get("estado") or "N/D",
                            )

                            # Información del proveedor y cotización
                            st.markdown("#### 02 · Proveedor y cotización")

                            datos_auditoria = {
                                "RUC": auditoria.get("ruc"),
                                "Razón social": auditoria.get("razon_social"),
                                "Servicio cotizado": auditoria.get(
                                    "servicio_cotizado"
                                ),
                                "Monto": formato_moneda(
                                    auditoria.get("monto") or 0,
                                    auditoria.get("moneda") or "PEN",
                                ),
                                "Motivo del dictamen": auditoria.get("motivo"),
                                "Fecha de creación": auditoria.get("creada_en"),
                                "Última actualización": auditoria.get(
                                    "actualizada_en"
                                ),
                            }

                            df_datos = pd.DataFrame(
                                [
                                    {
                                        "Campo": campo,
                                        "Información": (
                                            str(valor)
                                            if valor is not None
                                            else "No disponible"
                                        ),
                                    }
                                    for campo, valor in datos_auditoria.items()
                                ]
                            )

                            st.dataframe(
                                df_datos,
                                use_container_width=True,
                                hide_index=True,
                            )

                            # Evaluaciones de Gemini
                            st.markdown("#### 03 · Evaluaciones de Gemini")

                            if evaluaciones:

                                for numero, evaluacion in enumerate(
                                    evaluaciones,
                                    start=1,
                                ):
                                    with st.expander(
                                        f'Evaluación {numero} · '
                                        f'{evaluacion.get("estado", "N/D")} · '
                                        f'{evaluacion.get("modelo", "Modelo no disponible")}',
                                        expanded=(numero == 1),
                                    ):
                                        e1, e2, e3 = st.columns(3)

                                        e1.metric(
                                            "Coherencia",
                                            evaluacion.get(
                                                "coherencia_comercial"
                                            ) or "N/D",
                                        )
                                        e2.metric(
                                            "Riesgo IA",
                                            evaluacion.get(
                                                "nivel_riesgo"
                                            ) or "N/D",
                                        )
                                        e3.metric(
                                            "Confianza IA",
                                            f'{evaluacion.get("puntaje_confianza") or 0}/100',
                                        )

                                        st.markdown("**Recomendación**")
                                        st.write(
                                            evaluacion.get("recomendacion")
                                            or "No disponible"
                                        )

                                        st.markdown("**Justificación**")
                                        st.write(
                                            evaluacion.get("justificacion")
                                            or "No disponible"
                                        )

                                        alertas = convertir_json(
                                            evaluacion.get("alertas"),
                                            [],
                                        )

                                        st.markdown("**Alertas identificadas**")

                                        if alertas:
                                            for alerta in alertas:
                                                st.warning(str(alerta))
                                        else:
                                            st.success(
                                                "No se registraron alertas."
                                            )

                                        if evaluacion.get("error"):
                                            st.error(
                                                f'Error registrado: '
                                                f'{evaluacion["error"]}'
                                            )

                                        # Respuesta completa de Gemini
                                        respuesta = convertir_json(
                                            evaluacion.get("respuesta"),
                                            {},
                                        )

                                        if respuesta:
                                            with st.expander(
                                                "Ver respuesta completa de Gemini"
                                            ):
                                                st.json(respuesta)

                                        # Intentos de comunicación
                                        intentos = listar_intentos(
                                            evaluacion["id"]
                                        )

                                        st.markdown("**Intentos de Gemini**")

                                        if intentos:
                                            df_intentos = pd.DataFrame(
                                                [
                                                    {
                                                        "N.º intento": intento.get(
                                                            "numero_intento"
                                                        ),
                                                        "Estado": intento.get(
                                                            "estado"
                                                        ),
                                                        "Código de error": intento.get(
                                                            "codigo_error"
                                                        ),
                                                        "Detalle": intento.get(
                                                            "detalle_error"
                                                        ),
                                                        "Inicio": intento.get(
                                                            "iniciado_en"
                                                        ),
                                                        "Finalización": intento.get(
                                                            "finalizado_en"
                                                        ),
                                                    }
                                                    for intento in intentos
                                                ]
                                            )

                                            st.dataframe(
                                                df_intentos,
                                                use_container_width=True,
                                                hide_index=True,
                                            )
                                        else:
                                            st.caption(
                                                "No hay intentos registrados."
                                            )

                            else:
                                st.info(
                                    "Esta auditoría todavía no tiene "
                                    "evaluaciones de Gemini registradas."
                                )

                            # Historial de cambios
                            st.markdown("#### 04 · Historial de cambios")

                            if historial_cambios:

                                df_cambios = pd.DataFrame(
                                    [
                                        {
                                            "Fecha": cambio.get("creado_en"),
                                            "Dictamen anterior": cambio.get(
                                                "dictamen_anterior"
                                            ),
                                            "Dictamen nuevo": cambio.get(
                                                "dictamen_nuevo"
                                            ),
                                            "Acción": cambio.get("accion"),
                                            "Observación": cambio.get(
                                                "observacion"
                                            ),
                                        }
                                        for cambio in historial_cambios
                                    ]
                                )

                                st.dataframe(
                                    df_cambios,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            else:
                                st.info(
                                    "No existen cambios registrados "
                                    "para esta auditoría."
                                )

                    except Exception as error:
                        st.error(
                            f"No se pudo consultar el detalle: {error}"
                        )

            else:
                st.info(
                    "No hay identificadores de auditoría disponibles "
                    "en los resultados filtrados."
                )
        else:
            st.info(
                "No hay resultados que permitan consultar un detalle."
            )
