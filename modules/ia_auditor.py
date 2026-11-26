
import json
import os
from typing import Literal

from google.genai import errors
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field, ValidationError


load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-4-hydrogen")


class ResultadoAuditoria(BaseModel):
    coherencia_comercial: Literal[
        "coherente",
        "parcialmente_coherente",
        "incoherente",
        "insuficiente"
    ]

    nivel_riesgo: Literal["bajo", "medio", "alto"]

    puntaje_confianza: int = Field(ge=0, le=100)

    justificacion: str

    alertas: list[str]

    recomendacion: Literal[
        "favorable",
        "revisar",
        "desfavorable"
    ]


class AuditorIA:

    def __init__(self, api_key=None, client=None):

        api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not client and not api_key:
            raise ValueError(
                "No se encontró GEMINI_API_KEY en el archivo .env"
            )

        self.client = client or genai.Client(api_key=api_key)

    def evaluar_proveedor(self, proveedor):

        datos = {
            "razon_social": proveedor.get("razon_social"),
            "ruc": proveedor.get("ruc"),
            "servicio_cotizado": proveedor.get("servicio_cotizado"),
            "monto": proveedor.get("monto"),
            "moneda": proveedor.get("moneda"),
            "estado": proveedor.get("estado"),
            "condicion": proveedor.get("condicion"),
            "actividad_economica": proveedor.get("actividad_economica"),
            "tipo_contribuyente": proveedor.get("tipo_contribuyente"),
            "numero_trabajadores": proveedor.get("numero_trabajadores"),
            "fuente_actividad_economica": proveedor.get(
                "fuente_actividad_economica"
            ),
            "actividad_economica_verificada": proveedor.get(
                "actividad_economica_verificada", False
            )
        }

        system_prompt = """
        Eres un auditor especializado en evaluación comercial
        de proveedores empresariales en Perú.

        Tu tarea es analizar la coherencia comercial entre:

        1. La actividad económica REAL del proveedor.
        2. El servicio o producto cotizado.
        3. El monto de la cotización.

        REGLAS OBLIGATORIAS:

        - No deduzcas la actividad económica únicamente
        por la razón social o nombre de la empresa.
        - No inventes actividades económicas.
        - No asumas que una empresa bancaria solamente
        puede prestar servicios bancarios.
        - Si no existe información sobre la actividad
        económica real, utiliza coherencia_comercial
        = "insuficiente".
        - Cuando la información sea insuficiente,
        utiliza nivel_riesgo = "medio".
        - Cuando la información sea insuficiente,
        utiliza recomendacion = "revisar".
        - No confundas falta de información con
        evidencia de fraude.
        - No determines la validez tributaria.
        - No asumas que un monto elevado constituye fraude.
        - No inventes información externa.

        REGLAS SOBRE EL MONTO Y LA MONEDA:

        - Revisa los campos "monto" y "moneda" por separado.
        - Si el campo "moneda" contiene un código válido,
        considera que la moneda está especificada.
        - PEN significa soles peruanos (S/).
        - USD significa dólares estadounidenses (US$).
        - EUR significa euros (€).
        - Si el campo moneda contiene PEN, interpreta
        el monto como una cantidad expresada en soles peruanos.
        - No generes alertas por falta de moneda cuando
        el campo moneda tenga un valor válido.
        - Solo solicita aclaración sobre la moneda cuando
        el campo esté vacío, sea null o no contenga
        un código o denominación reconocible.
        - No confundas la ausencia de moneda con la ausencia
        del monto.
        - No inventes ni modifiques el monto o la moneda.

        CRITERIOS DE EVALUACIÓN:

        coherente:
        Existe evidencia suficiente de relación entre
        la actividad económica y el servicio.

        parcialmente_coherente:
        Existe relación parcial, pero hay aspectos
        que necesitan verificación.

        incoherente:
        Existe evidencia suficiente de incompatibilidad
        entre la actividad económica y el servicio.

        insuficiente:
        No existe información suficiente para determinar
        la coherencia comercial.

        Evalúa con prudencia y justifica tus conclusiones.

        INFORMACIÓN EMPRESARIAL ADICIONAL:

        - Utiliza actividad_economica como evidencia principal
        para evaluar el giro empresarial.
        - Considera la fuente de información proporcionada.
        - No deduzcas actividades a partir del nombre de la empresa.
        - Si actividad_economica_verificada es false,
        utiliza coherencia_comercial = "insuficiente".
        - Si la actividad económica está disponible, compara
        su relación con el servicio cotizado.
        - No confundas el número de trabajadores con una prueba
        de capacidad técnica.
        """

        user_prompt = f"""
        Analiza el siguiente proveedor:

        {json.dumps(datos, ensure_ascii=False, default=str)}

        IMPORTANTE:
        Verifica expresamente el campo "moneda" antes de generar
        alertas relacionadas con la cotización.

        Determina la coherencia comercial, el nivel de riesgo,
        las alertas y una recomendación.
        """

        esquema = ResultadoAuditoria.model_json_schema()

        try:
            respuesta = self.client.models.generate_content(
                model=MODEL,
                contents=[
                    system_prompt,
                    user_prompt
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": esquema
                }
            )

        except errors.APIError as error:

            if error.code == 503:
                raise RuntimeError(
                    "Gemini está temporalmente sobrecargado. "
                    "Intenta nuevamente en unos minutos."
                ) from error

            elif error.code == 429:
                raise RuntimeError(
                    "Se alcanzó un límite de solicitudes de Gemini. "
                    "Revisa tu cuota gratuita."
                ) from error

            else:
                raise RuntimeError(
                    f"Error en Gemini API: {error}"
                ) from error

        contenido = respuesta.text

        if not contenido:
            raise ValueError(
                "Gemini devolvió una respuesta vacía."
            )

        try:
            resultado = ResultadoAuditoria.model_validate_json(
                contenido
            )

        except ValidationError as error:
            raise ValueError(
                f"La respuesta de Gemini no cumple el esquema: {error}"
            ) from error

        return resultado.model_dump()
