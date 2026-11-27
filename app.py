import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

from modules.provider_service import ProviderService
from modules.ia_auditor import AuditorIA
from modules.risk_engine import generar_dictamen
from modules.excel_handler import cargar_proveedores


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

    historial = st.session_state.historial
    df = pd.DataFrame(historial) if historial else pd.DataFrame()

    total = len(historial)
    aprobados = (
        int((df["dictamen"] == "APROBADO").sum()) if total else 0
    )
    observados = (
        int((df["dictamen"] == "OBSERVADO").sum()) if total else 0
    )
    rechazados = (
        int((df["dictamen"] == "RECHAZADO").sum()) if total else 0
    )
    pendientes = (
        int((df["dictamen"] == "PENDIENTE_VALIDACION").sum()) if total else 0
    )

    st.markdown("#### Indicadores principales")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta_resumen("Auditorías realizadas", total, "Registros en esta sesión", "▦")
    with c2:
        tarjeta_resumen("Proveedores aprobados", aprobados, "Dictamen favorable", "✓")
    with c3:
        tarjeta_resumen("Proveedores observados", observados, "Requieren revisión", "!")
    with c4:
        tarjeta_resumen("Proveedores rechazados", rechazados, "Riesgo no aceptable", "×")

    st.markdown("")
    izquierda, derecha = st.columns([1.15, 1])

    with izquierda:
        st.markdown(
            '<div class="sv-section-title">Distribución de dictámenes</div>'
            '<div class="sv-section-caption">Resultados de las auditorías de esta sesión</div>',
            unsafe_allow_html=True,
        )

        if total:
            conteo = pd.DataFrame(
                {
                    "Dictamen": ["Aprobados", "Observados", "Rechazados", "Pendientes"],
                    "Cantidad": [aprobados, observados, rechazados, pendientes],
                }
            )
            st.bar_chart(conteo.set_index("Dictamen"), height=250)
        else:
            st.info("Cuando ejecutes auditorías, aquí aparecerá la distribución de dictámenes.")

    with derecha:
        st.markdown(
            '<div class="sv-section-title">Actividad reciente</div>'
            '<div class="sv-section-caption">Últimas auditorías registradas</div>',
            unsafe_allow_html=True,
        )

        if total:
            recientes = df.tail(5).iloc[::-1]
            for _, fila in recientes.iterrows():
                st.markdown(
                    f"""
                    <div class="sv-panel" style="padding:13px 15px; margin-bottom:9px;">
                        <div style="display:flex; justify-content:space-between; gap:10px;">
                            <b style="color:#edf4ff;">{fila.get('razon_social') or 'Proveedor sin nombre'}</b>
                            <span class="sv-pill">{fila.get('dictamen', 'N/D')}</span>
                        </div>
                        <div class="sv-muted" style="margin-top:6px;">
                            RUC {fila.get('ruc', '')} · {fila.get('fecha', '')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Aún no hay actividad registrada.")

    st.markdown("---")
    st.markdown("#### Acceso rápido")

    q1, q2 = st.columns(2)

    with q1:
        st.button(
            "＋  Iniciar nueva auditoría",
            use_container_width=True,
            on_click=ir_a_nueva_auditoria,
        )

    with q2:
        st.button(
            "▤  Consultar historial",
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
                with st.status("Ejecutando auditoría del proveedor...", expanded=True) as estado:
                    st.write("**1 de 3 · Consulta empresarial**")
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

                    st.write("Información empresarial obtenida.")

                    st.write("**2 de 3 · Evaluación con inteligencia artificial**")
                    evaluacion = auditor_ia.evaluar_proveedor(perfil)
                    st.write("Evaluación de Gemini completada.")

                    st.write("**3 de 3 · Generación del dictamen**")
                    dictamen = generar_dictamen(perfil, evaluacion)

                    estado.update(
                        label="Auditoría finalizada correctamente",
                        state="complete",
                        expanded=False,
                    )

                resultado = {
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "perfil": perfil,
                    "evaluacion": evaluacion,
                    "dictamen": dictamen,
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
                        "puntaje_confianza": dictamen.get("puntaje_confianza", 0),
                    }
                )

                st.success("La auditoría se completó correctamente.")

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
                    barra = st.progress(0)
                    texto_progreso = st.empty()

                    for posicion, (_, fila) in enumerate(df_validos.iterrows(), start=1):
                        ruc_actual = str(fila["ruc"]).strip()
                        servicio_actual = str(fila["servicio_cotizado"]).strip()
                        monto_actual = float(fila["monto"])
                        moneda_actual = str(fila["moneda"]).strip().upper()

                        texto_progreso.write(
                            f"Procesando registro {posicion} de {len(df_validos)} · RUC {ruc_actual}"
                        )

                        try:
                            if ruc_actual not in perfiles_por_ruc:
                                perfiles_por_ruc[ruc_actual] = provider_service.consultar_proveedor(
                                    ruc_actual,
                                    forzar_consulta=False,
                                )

                            perfil = perfiles_por_ruc[ruc_actual].copy()
                            perfil["servicio_cotizado"] = servicio_actual
                            perfil["monto"] = monto_actual
                            perfil["moneda"] = moneda_actual

                            if not perfil.get("consulta_tributaria_exitosa"):
                                evaluacion = {
                                    "coherencia_comercial": "insufficient",
                                    "nivel_riesgo": "high",
                                    "puntaje_confianza": 0,
                                    "justificacion": "No se pudo verificar la información tributaria del proveedor.",
                                    "alertas": ["Consulta tributaria no exitosa."],
                                    "recomendacion": "revisar",
                                }
                            else:
                                evaluacion = auditor_ia.evaluar_proveedor(perfil)

                            dictamen = generar_dictamen(perfil, evaluacion)

                            resultados_lote.append({
                                "Fila Excel": int(fila["fila_excel"]),
                                "RUC": ruc_actual,
                                "Razón social": perfil.get("razon_social"),
                                "Estado tributario": perfil.get("estado"),
                                "Condición": perfil.get("condicion"),
                                "Actividad económica": perfil.get("actividad_economica"),
                                "Servicio cotizado": servicio_actual,
                                "Monto": monto_actual,
                                "Moneda": moneda_actual,
                                "Coherencia comercial": evaluacion.get("coherencia_comercial"),
                                "Riesgo IA": evaluacion.get("nivel_riesgo"),
                                "Recomendación IA": evaluacion.get("recomendacion"),
                                "Confianza IA": dictamen.get("puntaje_confianza", evaluacion.get("puntaje_confianza", 0)),
                                "Dictamen final": dictamen.get("dictamen"),
                                "Riesgo final": dictamen.get("nivel_riesgo"),
                                "Motivo": dictamen.get("motivo"),
                                "Alertas": " | ".join(dictamen.get("alertas", [])),
                                "Error de proceso": "",
                            })

                            st.session_state.historial.append({
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                "ruc": ruc_actual,
                                "razon_social": perfil.get("razon_social"),
                                "servicio": servicio_actual,
                                "monto": monto_actual,
                                "moneda": moneda_actual,
                                "dictamen": dictamen.get("dictamen"),
                                "nivel_riesgo": dictamen.get("nivel_riesgo"),
                                "puntaje_confianza": dictamen.get("puntaje_confianza", 0),
                            })

                        except Exception as error:
                            resultados_lote.append({
                                "Fila Excel": int(fila["fila_excel"]),
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
                                "Motivo": "No se pudo completar la auditoría de este registro.",
                                "Alertas": "",
                                "Error de proceso": str(error),
                            })

                        barra.progress(posicion / len(df_validos))

                    st.session_state["resultados_auditoria_masiva"] = resultados_lote
                    st.session_state["invalidos_auditoria_masiva"] = df_invalidos.to_dict("records")
                    texto_progreso.success(
                        f"Proceso finalizado: {len(resultados_lote)} registros procesados."
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
        "Consulta, filtra y exporta los resultados generados durante esta sesión.",
        "REGISTRO DE ACTIVIDAD",
    )

    historial = st.session_state.historial

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

        st.markdown("---")

        confirmar_limpieza = st.checkbox(
            "Confirmo que deseo limpiar el historial de esta sesión."
        )

        if st.button(
            "Limpiar historial",
            disabled=not confirmar_limpieza,
        ):
            st.session_state.historial = []
            st.session_state.ultimo_resultado = None
            st.rerun()
