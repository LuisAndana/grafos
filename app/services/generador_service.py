import re
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

load_dotenv()

from app.models.proyecto import Proyecto
from app.models.stakeholder import Stakeholder
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
from app.models.tipo_usuario_proyecto import TipoUsuarioProyecto
from app.models.caso_uso import CasoUso
from app.models.restriccion import Restriccion
from app.models.validacion import Validacion

MODEL = "models/gemini-2.5-flash"

# ── Cliente Gemini ────────────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY no configurada en el servidor.",
        )
    return genai.Client(api_key=api_key)


# ── Recopilación de datos del proyecto ───────────────────────────────────────

def _recopilar_datos(db: Session, proyecto_id: int) -> dict:
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")

    stakeholders  = db.query(Stakeholder).filter(Stakeholder.proyecto_id == proyecto_id).all()
    rfs           = db.query(RequerimientoFuncional).filter(RequerimientoFuncional.proyecto_id == proyecto_id).all()
    rnfs          = db.query(RequerimientoNoFuncional).filter(RequerimientoNoFuncional.proyecto_id == proyecto_id).all()
    tipos_usuario = db.query(TipoUsuarioProyecto).filter(TipoUsuarioProyecto.proyecto_id == proyecto_id).all()
    casos_uso     = db.query(CasoUso).filter(CasoUso.proyecto_id == proyecto_id).all()
    restricciones = db.query(Restriccion).filter(Restriccion.proyecto_id == proyecto_id).all()
    validacion    = db.query(Validacion).filter(Validacion.proyecto_id == proyecto_id).first()

    return {
        "proyecto":      proyecto,
        "stakeholders":  stakeholders,
        "rfs":           rfs,
        "rnfs":          rnfs,
        "tipos_usuario": tipos_usuario,
        "casos_uso":     casos_uso,
        "restricciones": restricciones,
        "validacion":    validacion,
    }


def _construir_contexto(datos: dict) -> str:
    p = datos["proyecto"]
    lineas = [
        f"## Proyecto: {p.nombre}",
        f"- Código: {p.codigo}",
        f"- Descripción del problema: {p.descripcion_problema or 'N/A'}",
        f"- Objetivo general: {p.objetivo_general or 'N/A'}",
        f"- Analista responsable: {p.analista_responsable or 'N/A'}",
        "",
    ]

    lineas.append("## Stakeholders")
    if datos["stakeholders"]:
        for s in datos["stakeholders"]:
            tipo = str(s.tipo.value) if hasattr(s.tipo, "value") else s.tipo
            influencia = str(s.nivel_influencia.value) if hasattr(s.nivel_influencia, "value") else s.nivel_influencia
            lineas.append(f"- {s.nombre} | Rol: {s.rol} | Tipo: {tipo} | Área: {s.area} | Influencia: {influencia}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Requerimientos Funcionales")
    if datos["rfs"]:
        for r in datos["rfs"]:
            lineas.append(f"- [{r.codigo}] {r.descripcion} | Actor: {r.actor} | Prioridad: {r.prioridad} | Estado: {r.estado}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Requerimientos No Funcionales")
    if datos["rnfs"]:
        for r in datos["rnfs"]:
            tipo = str(r.tipo.value) if hasattr(r.tipo, "value") else r.tipo
            lineas.append(f"- [{r.codigo}] {r.descripcion} | Tipo: {tipo} | Métrica: {r.metrica or 'N/A'}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Tipos de Usuario del Sistema")
    if datos["tipos_usuario"]:
        for t in datos["tipos_usuario"]:
            lineas.append(f"- {t.tipo}: {t.descripcion or 'N/A'}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Casos de Uso")
    if datos["casos_uso"]:
        for c in datos["casos_uso"]:
            lineas.append(f"- {c.nombre} | Actores: {c.actores} | Descripción: {c.descripcion}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Restricciones")
    if datos["restricciones"]:
        for r in datos["restricciones"]:
            lineas.append(f"- [{r.codigo}] Tipo: {r.tipo} | {r.descripcion}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Estado de Validación")
    v = datos["validacion"]
    if v:
        lineas.append(f"- Aprobado: {v.aprobado}")
        lineas.append(f"- Aprobador: {v.aprobador or 'N/A'}")
        lineas.append(f"- Observaciones: {v.observaciones or 'N/A'}")
    else:
        lineas.append("- (sin validación registrada)")

    return "\n".join(lineas)


# ── Parsing de bloques ────────────────────────────────────────────────────────

def _extraer_bloque(texto: str, marcador: str) -> str:
    patron = rf"\[{marcador}\](.*?)(?=\[[A-Z_]+\]|$)"
    match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# ── Generación de código ──────────────────────────────────────────────────────

def generar_codigo(db: Session, proyecto_id: int) -> dict:
    datos = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)
    client = _get_client()

    prompt = f"""Eres un experto en desarrollo de software. A continuación tienes la especificación completa de un proyecto de software:

{contexto}

Con base en esta especificación, genera código de implementación dividido en EXACTAMENTE tres bloques usando los marcadores exactos que se indican:

[FRONTEND]
Código Angular 18+ con standalone components, TypeScript estricto. Incluye el componente principal, servicio HTTP, y modelo de interfaz. Código funcional y completo.

[BACKEND]
Código FastAPI con SQLAlchemy. Incluye el modelo de base de datos, esquemas Pydantic, servicio con lógica de negocio, y router con endpoints CRUD completos.

[DATABASE]
Script SQL completo (MySQL) para crear las tablas necesarias con sus relaciones, índices y restricciones.

IMPORTANTE: Usa EXACTAMENTE los marcadores [FRONTEND], [BACKEND] y [DATABASE]. No agregues texto antes del primer marcador ni después del último bloque."""

    try:
        respuesta = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=65536,
                temperature=0.4,
            ),
        )
    except genai_errors.ServerError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"El modelo de IA está saturado en este momento. Intenta de nuevo en unos segundos. ({e})",
        )
    except genai_errors.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al llamar a la API de Gemini: {e}",
        )

    texto = respuesta.text

    frontend = _extraer_bloque(texto, "FRONTEND")
    backend  = _extraer_bloque(texto, "BACKEND")
    database = _extraer_bloque(texto, "DATABASE")

    if not frontend and not backend and not database:
        backend = texto

    return {"frontend": frontend, "backend": backend, "database": database}


# ── Generación de diagramas Mermaid ──────────────────────────────────────────

_INSTRUCCIONES_DIAGRAMA = {
    "paquetes": (
        "Genera un diagrama de paquetes en sintaxis Mermaid (graph TD) que muestre la arquitectura "
        "del sistema en capas: frontend, backend y base de datos, con sus módulos principales."
    ),
    "clases": (
        "Genera un diagrama de clases en sintaxis Mermaid (classDiagram) con todas las entidades "
        "del sistema, sus atributos principales y las relaciones entre ellas."
    ),
    "secuencia": (
        "Genera un diagrama de secuencia en sintaxis Mermaid (sequenceDiagram) que muestre el flujo "
        "principal de interacción entre el usuario, el frontend, el backend y la base de datos "
        "para el caso de uso más importante del sistema."
    ),
    "casos_uso": (
        "Genera un diagrama de casos de uso en sintaxis Mermaid (graph LR) que muestre todos los "
        "actores del sistema y sus casos de uso con las relaciones include/extend cuando aplique."
    ),
}


def generar_diagrama(db: Session, proyecto_id: int, tipo: str) -> dict:
    datos = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)
    client = _get_client()

    instruccion = _INSTRUCCIONES_DIAGRAMA.get(tipo, "Genera un diagrama Mermaid apropiado.")

    prompt = f"""Eres un experto en diseño de software y diagramas UML. Aquí tienes la especificación del proyecto:

{contexto}

{instruccion}

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con el código Mermaid, sin explicaciones, sin texto adicional, sin bloques de código markdown (no uses ```).
2. El código debe ser sintaxis Mermaid válida y renderizable.
3. Usa nombres en español basados en la especificación del proyecto.
4. El diagrama debe ser coherente con los datos del proyecto proporcionados."""

    try:
        respuesta = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.4,
            ),
        )
    except genai_errors.ServerError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"El modelo de IA está saturado en este momento. Intenta de nuevo en unos segundos. ({e})",
        )
    except genai_errors.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al llamar a la API de Gemini: {e}",
        )

    codigo_mermaid = respuesta.text

    # Limpiar posibles bloques markdown
    codigo_mermaid = re.sub(r"^```(?:mermaid)?\n?", "", codigo_mermaid.strip(), flags=re.MULTILINE)
    codigo_mermaid = re.sub(r"\n?```$", "", codigo_mermaid.strip(), flags=re.MULTILINE)

    return {"tipo": tipo, "codigo_mermaid": codigo_mermaid.strip()}
