# app/routes/generador_router.py
"""
Generador IA — genera código funcional y diagramas UML usando Claude AI.
Recopila toda la información del proyecto (requerimientos, stakeholders,
elicitación) para construir un contexto rico antes de llamar a la IA.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.proyecto import Proyecto
from app.services import (
    stakeholder_service,
    requerimiento_funcional_service,
    elicitacion_service,
)

router = APIRouter(prefix="/api/generador", tags=["Generador IA"])


# ── Schemas ────────────────────────────────────────────────────────────────

class DiagramaRequest(BaseModel):
    tipo: str  # clases | secuencia | paquetes | casos_uso


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_client():
    """Retorna el cliente Anthropic o lanza 500 si no está configurado."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="La librería 'anthropic' no está instalada. Ejecuta: pip install anthropic"
        )

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY no está configurada en el servidor. Agrégala al archivo .env"
        )
    import anthropic  # type: ignore
    return anthropic.Anthropic(api_key=api_key)


def _build_context(proyecto_id: int, db: Session, user_id: int) -> str:
    """
    Recopila toda la información disponible del proyecto y la convierte
    en un contexto de texto estructurado para el prompt de Claude.
    """
    # ── Proyecto base ─────────────────────────────────────────────────────
    proyecto = (
        db.query(Proyecto)
        .filter(Proyecto.id_proyecto == proyecto_id, Proyecto.user_id == user_id)
        .first()
    )
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")

    lineas = [
        f"NOMBRE DEL PROYECTO: {proyecto.nombre}",
        f"CÓDIGO: {proyecto.codigo}",
    ]
    if proyecto.descripcion_problema:
        lineas.append(f"DESCRIPCIÓN DEL PROBLEMA: {proyecto.descripcion_problema}")
    if proyecto.objetivo_general:
        lineas.append(f"OBJETIVO GENERAL: {proyecto.objetivo_general}")
    if proyecto.analista_responsable:
        lineas.append(f"ANALISTA RESPONSABLE: {proyecto.analista_responsable}")
    if proyecto.fecha_inicio:
        lineas.append(f"FECHA DE INICIO: {proyecto.fecha_inicio}")

    ctx = "\n".join(lineas)

    # ── Stakeholders ─────────────────────────────────────────────────────
    try:
        stakeholders = stakeholder_service.get_stakeholders_by_proyecto(
            db, proyecto_id, user_id
        )
        if stakeholders:
            ctx += "\n\n--- STAKEHOLDERS ---\n"
            for s in stakeholders:
                parts = [f"{s.nombre} ({s.rol})", f"Tipo: {s.tipo}"]
                if s.area:
                    parts.append(f"Área: {s.area}")
                if s.nivel_influencia:
                    parts.append(f"Influencia: {s.nivel_influencia}")
                if s.interes_sistema:
                    parts.append(f"Interés en el sistema: {s.interes_sistema}")
                ctx += "- " + " | ".join(parts) + "\n"
    except Exception:
        pass

    # ── Requerimientos funcionales ────────────────────────────────────────
    try:
        rfs = requerimiento_funcional_service.get_rfs(db, user_id, proyecto_id)
        if rfs:
            ctx += "\n\n--- REQUERIMIENTOS FUNCIONALES ---\n"
            for r in rfs:
                actor = r.actor or "Sin actor"
                ctx += (
                    f"- [{r.codigo}] {r.descripcion}\n"
                    f"  Actor: {actor} | Prioridad: {r.prioridad} | Estado: {r.estado}\n"
                )
    except Exception:
        pass

    # ── Elicitación ───────────────────────────────────────────────────────
    try:
        entrevistas = elicitacion_service.get_entrevistas(db, user_id, proyecto_id)
        if entrevistas:
            ctx += "\n\n--- ENTREVISTAS DE ELICITACIÓN ---\n"
            for e in entrevistas:
                ctx += f"- Pregunta: {e.pregunta}\n  Respuesta: {e.respuesta}\n"
                if e.observaciones:
                    ctx += f"  Observaciones: {e.observaciones}\n"
    except Exception:
        pass

    try:
        procesos = elicitacion_service.get_procesos(db, user_id, proyecto_id)
        if procesos:
            ctx += "\n\n--- PROCESOS DEL NEGOCIO ---\n"
            for p in procesos:
                ctx += f"- {p.nombre_proceso}: {p.descripcion}\n"
                if p.problemas_detectados:
                    ctx += f"  Problemas detectados: {p.problemas_detectados}\n"
    except Exception:
        pass

    try:
        necesidades = elicitacion_service.get_necesidades(db, user_id, proyecto_id)
        seleccionadas = [n for n in necesidades if n.seleccionada]
        if seleccionadas:
            ctx += "\n\n--- NECESIDADES IDENTIFICADAS ---\n"
            for n in seleccionadas:
                ctx += f"- {n.nombre}\n"
    except Exception:
        pass

    return ctx


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/codigo/{proyecto_id}")
async def generar_codigo(
    proyecto_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Genera código funcional completo (Frontend Angular, Backend FastAPI, SQL)
    usando toda la información recopilada del proyecto.
    """
    client = _get_client()
    context = _build_context(proyecto_id, db, user.id)

    prompt = f"""Eres un arquitecto de software senior. Tu tarea es generar código funcional, completo y listo para usar, basado EXCLUSIVAMENTE en la siguiente información real de un proyecto de software:

{context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCCIONES DE GENERACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Genera los tres componentes de la aplicación. Usa los delimitadores EXACTOS:

===FRONTEND===
Genera un módulo Angular completo y funcional:
• Interfaces TypeScript para TODOS los modelos del dominio del proyecto
• Un servicio Angular (Injectable) con métodos HTTP (GET, POST, PUT, DELETE) para cada entidad
• Un componente principal con su @Component, toda la lógica en el .ts, el template HTML completo con formularios reactivos/template-driven y listados, y estilos CSS
• Manejo de estados: cargando, error, éxito
• Usa HttpClient, FormsModule/ReactiveFormsModule según sea apropiado
• Los nombres de clases, métodos y variables deben reflejar el dominio real del proyecto

===BACKEND===
Genera un router FastAPI completo en Python:
• Modelos SQLAlchemy para TODAS las entidades del sistema
• Schemas Pydantic para request/response con validaciones (Field, validator)
• Endpoints REST completos con operaciones CRUD para cada entidad
• Autenticación JWT (Bearer token) donde corresponda
• Manejo de errores con HTTPException y códigos HTTP correctos
• Comentarios explicativos en cada función

===DATABASE===
Genera el script SQL completo:
• CREATE DATABASE IF NOT EXISTS con el nombre del proyecto
• CREATE TABLE para TODAS las entidades con:
  - Tipos de datos apropiados al dominio
  - PRIMARY KEY, FOREIGN KEY, índices
  - Restricciones NOT NULL, UNIQUE, DEFAULT donde aplique
  - Comentarios en las tablas y columnas
• INSERT INTO con datos de ejemplo realistas y coherentes con el proyecto
• VISTAs útiles para las consultas más comunes del sistema

IMPORTANTE: El código debe ser FUNCIONAL y directamente usable, no un esqueleto ni pseudocódigo.
Adapta TODOS los nombres, entidades y lógica al dominio real del proyecto descrito arriba."""

    try:
        import anthropic  # type: ignore
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamar a Claude API: {str(e)}")

    # ── Parsear secciones ──────────────────────────────────────────────────
    frontend = ""
    backend  = ""
    database = ""

    if "===FRONTEND===" in response_text:
        partes = response_text.split("===FRONTEND===")
        if len(partes) > 1:
            resto = partes[1].split("===BACKEND===")
            frontend = resto[0].strip()
            if len(resto) > 1:
                resto2 = resto[1].split("===DATABASE===")
                backend = resto2[0].strip()
                if len(resto2) > 1:
                    database = resto2[1].strip()

    # Fallback: si no se encontraron delimitadores
    if not frontend and not backend:
        frontend = response_text

    return {
        "data": {
            "frontend": frontend or "// Sin contenido generado",
            "backend":  backend  or "# Sin contenido generado",
            "database": database or "-- Sin contenido generado",
        }
    }


@router.post("/diagrama/{proyecto_id}")
async def generar_diagrama(
    proyecto_id: int,
    body: DiagramaRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Genera un diagrama UML en formato Mermaid usando la información del proyecto.
    Tipos soportados: clases | secuencia | paquetes | casos_uso
    """
    client = _get_client()
    context = _build_context(proyecto_id, db, user.id)

    instrucciones = {
        "clases": (
            "Diagrama de Clases UML",
            """Genera un diagrama de clases Mermaid (classDiagram) con:
- TODAS las clases/entidades del sistema derivadas de los requerimientos, con atributos tipados
- Métodos principales de negocio en cada clase
- Relaciones correctas: herencia (--|>), composición (*--), agregación (o--)  , asociación (-->)
- Cardinalidades explícitas ("1" .. "n", "0..*", etc.)
- Notas (note) explicativas para las clases más importantes""",
        ),
        "secuencia": (
            "Diagrama de Secuencia UML",
            """Genera un diagrama de secuencia Mermaid (sequenceDiagram) del flujo principal:
- Participantes: Usuario, Frontend (Angular), Backend (FastAPI), Base de Datos
- El flujo más representativo del sistema según sus requerimientos funcionales
- Mensajes de request/response con datos reales del dominio
- Bloques alt/opt/loop donde el flujo lo requiera
- Notas explicativas en los pasos clave""",
        ),
        "paquetes": (
            "Diagrama de Paquetes UML",
            """Genera un diagrama de paquetes Mermaid (graph TB) con:
- Paquete Frontend: components, services, models, guards, interceptors
- Paquete Backend: routes, services, models, schemas, core (db, auth, config)
- Paquete Database: tablas agrupadas por módulo funcional
- Dependencias entre paquetes con flechas etiquetadas
- Colores de relleno para diferenciar capas (style)""",
        ),
        "casos_uso": (
            "Diagrama de Casos de Uso UML",
            """Genera un diagrama de casos de uso Mermaid (graph LR) con:
- TODOS los actores identificados en stakeholders y requerimientos
- TODOS los casos de uso derivados de los requerimientos funcionales
- Relaciones include (<<include>>) y extend (<<extend>>) donde aplique
- Agrupa los casos de uso dentro del sistema usando subgraph
- Usa etiquetas descriptivas en español""",
        ),
    }

    if body.tipo not in instrucciones:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de diagrama inválido: '{body.tipo}'. Use: clases, secuencia, paquetes, casos_uso"
        )

    tipo_label, tipo_instrucciones = instrucciones[body.tipo]

    prompt = f"""Eres un experto en modelado UML y diagramas Mermaid.js. Genera el {tipo_label} para el siguiente proyecto de software:

{context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCCIONES ESPECÍFICAS PARA ESTE DIAGRAMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{tipo_instrucciones}

REGLAS DE FORMATO (MUY IMPORTANTE):
1. Responde ÚNICAMENTE con el código Mermaid puro
2. NO incluyas bloques markdown (no uses ```mermaid, no uses ```)
3. NO escribas explicaciones antes ni después del código
4. El diagrama DEBE comenzar directamente con la palabra clave de Mermaid (classDiagram, sequenceDiagram, graph, etc.)
5. Usa nombres en ESPAÑOL para entidades, actores y casos de uso
6. El diagrama debe ser completo, detallado y funcional en Mermaid.js v10+"""

    try:
        import anthropic  # type: ignore
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        codigo_mermaid = message.content[0].text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamar a Claude API: {str(e)}")

    # Limpiar posibles fences de markdown
    if codigo_mermaid.startswith("```"):
        lineas = codigo_mermaid.split("\n")
        lineas = [l for l in lineas if not l.strip().startswith("```")]
        codigo_mermaid = "\n".join(lineas).strip()

    return {
        "data": {
            "codigo_mermaid": codigo_mermaid,
            "tipo": body.tipo,
        }
    }
