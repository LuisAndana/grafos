import re
import os
import json
import time
import traceback
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIStatusError, AuthenticationError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

load_dotenv(override=True)

from app.models.proyecto import Proyecto
from app.models.stakeholder import Stakeholder
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
from app.models.tipo_usuario_proyecto import TipoUsuarioProyecto
from app.models.caso_uso import CasoUso
from app.models.restriccion import Restriccion
from app.models.validacion import Validacion
# ── Modelos adicionales para contexto completo ──
from app.models.elicitacion import (
    ElicitacionEntrevista,
    ElicitacionProceso,
    ElicitacionNecesidad,
)
from app.models.negociacion import Negociacion
from app.models.srs_documento import SrsDocumento
from app.models.artefacto import Artefacto

# ── GitHub Models (Azure) — mucho más estable que Gemini free tier ──────────
_GITHUB_ENDPOINT = "https://models.inference.ai.azure.com"
MODEL_MAIN     = "gpt-4o-mini"  # 15 RPM · 150 RPD · rápido y económico
MODEL_FALLBACK = "gpt-4o"       # 10 RPM ·  50 RPD · mayor calidad


def _call_ai(
    client: OpenAI,
    prompt: str,
    model: str = MODEL_MAIN,
    max_tokens: int = 4096,
    json_mode: bool = True,
) -> str:
    """
    Llama a un modelo de GitHub Models (Azure) con reintentos automáticos.

    - 429 RateLimitError  → espera el retry-after del header (mínimo 65 s) y reintenta.
    - 5xx APIStatusError  → reintenta con backoff 30 s / 60 s.
    - 401 AuthError       → falla de inmediato (token inválido).
    - Otros               → falla de inmediato.

    Devuelve el texto plano de la respuesta.
    """
    system_msg = (
        "Eres un arquitecto de software senior especializado en aplicaciones web full-stack. "
        + ("Devuelve SIEMPRE un objeto JSON válido como se indica en las instrucciones." if json_mode else "")
    )
    kwargs: dict = dict(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(1, 4):   # hasta 3 intentos
        try:
            print(f"[AI] {model} — intento {attempt}/3...")
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except RateLimitError as e:
            wait = 65
            try:
                ra = e.response.headers.get("retry-after")
                if ra:
                    wait = int(ra) + 5
            except Exception:
                pass
            if attempt < 3:
                print(f"[AI RPM] {model} límite de tasa, esperando {wait}s...")
                time.sleep(wait)
            else:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit persistente en {model}. Intenta en unos minutos.",
                )
        except APIStatusError as e:
            if e.status_code >= 500:
                if attempt < 3:
                    wait = 30 * attempt   # 30 s, 60 s
                    print(f"[AI {e.status_code}] {model} error servidor, reintentando en {wait}s...")
                    time.sleep(wait)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Servidor no disponible ({model}). Intenta de nuevo en unos minutos.",
                    )
            else:
                print(f"[AI Error {e.status_code}] {e}")
                raise HTTPException(status_code=e.status_code, detail=str(e))
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GITHUB_TOKEN inválido o expirado. Genera un nuevo token en github.com/settings/tokens",
            )
        except Exception as e:
            print(f"[AI UnknownError] {type(e).__name__}: {e}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado: {type(e).__name__}: {e}",
            )
    raise HTTPException(status_code=503, detail=f"No se pudo contactar a {model}.")

# ── Lectura de artefactos de texto ──────────────────────────────────────────
_EXTENSIONES_TEXTO = {
    "txt", "csv", "md", "json", "xml", "html", "yml", "yaml",
    "py", "js", "ts", "sql", "css", "scss", "java", "c", "cpp",
    "h", "rb", "php", "sh", "bat", "cfg", "ini", "toml", "env",
    "log", "rst", "tex", "dpt",
}
_MAX_CHARS_POR_ARTEFACTO = 3000   # reducido para ahorrar tokens de entrada
_MAX_ARTEFACTOS_TEXTO = 4         # reducido para ahorrar tokens de entrada

# ── Cliente Gemini ────────────────────────────────────────────────────────────

def _get_client() -> OpenAI:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GITHUB_TOKEN no configurado. Agrégalo al archivo .env",
        )
    return OpenAI(base_url=_GITHUB_ENDPOINT, api_key=token)


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

    # ── Datos de Elicitación ──
    entrevistas   = db.query(ElicitacionEntrevista).filter(
        ElicitacionEntrevista.proyecto_id == proyecto_id
    ).all()
    procesos      = db.query(ElicitacionProceso).filter(
        ElicitacionProceso.proyecto_id == proyecto_id
    ).all()
    necesidades   = db.query(ElicitacionNecesidad).filter(
        ElicitacionNecesidad.proyecto_id == proyecto_id,
        ElicitacionNecesidad.seleccionada == 1,
    ).all()

    # ── Negociación ──
    negociaciones = db.query(Negociacion).filter(
        Negociacion.proyecto_id == proyecto_id
    ).all()

    # ── SRS existente ──
    srs_docs      = db.query(SrsDocumento).filter(
        SrsDocumento.proyecto_id == proyecto_id
    ).all()

    # ── Artefactos ──
    artefactos    = db.query(Artefacto).filter(
        Artefacto.proyecto_id == proyecto_id
    ).all()

    return {
        "proyecto":      proyecto,
        "stakeholders":  stakeholders,
        "rfs":           rfs,
        "rnfs":          rnfs,
        "tipos_usuario": tipos_usuario,
        "casos_uso":     casos_uso,
        "restricciones": restricciones,
        "validacion":    validacion,
        "entrevistas":   entrevistas,
        "procesos":      procesos,
        "necesidades":   necesidades,
        "negociaciones": negociaciones,
        "srs_docs":      srs_docs,
        "artefactos":    artefactos,
    }


def _leer_contenido_artefacto(artefacto) -> str | None:
    """Lee el contenido de un artefacto si es archivo de texto. Devuelve None si es binario o no existe."""
    from pathlib import Path as _Path

    nombre = artefacto.nombre_archivo or ""
    ext = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
    if ext not in _EXTENSIONES_TEXTO:
        return None

    ruta = _Path(artefacto.ruta_archivo)
    if not ruta.exists():
        return None

    try:
        contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        if len(contenido) > _MAX_CHARS_POR_ARTEFACTO:
            contenido = contenido[:_MAX_CHARS_POR_ARTEFACTO] + "\n... (contenido truncado)"
        return contenido
    except Exception:
        return None


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

    # ── Stakeholders ──────────────────────────────────────────────────────
    lineas.append("## Stakeholders")
    if datos["stakeholders"]:
        for s in datos["stakeholders"]:
            tipo = str(s.tipo.value) if hasattr(s.tipo, "value") else s.tipo
            influencia = str(s.nivel_influencia.value) if hasattr(s.nivel_influencia, "value") else s.nivel_influencia
            lineas.append(f"- {s.nombre} | Rol: {s.rol} | Tipo: {tipo} | Área: {s.area} | Influencia: {influencia}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Elicitación — Entrevistas ─────────────────────────────────────────
    lineas.append("## Elicitación — Entrevistas con Usuarios")
    if datos.get("entrevistas"):
        for e in datos["entrevistas"]:
            lineas.append(f"- Pregunta: {e.pregunta}")
            lineas.append(f"  Respuesta: {e.respuesta or 'N/A'}")
            if e.observaciones:
                lineas.append(f"  Observaciones: {e.observaciones}")
    else:
        lineas.append("- (ninguna)")
    lineas.append("")

    # ── Elicitación — Procesos de Negocio ─────────────────────────────────
    lineas.append("## Elicitación — Procesos de Negocio")
    if datos.get("procesos"):
        for proc in datos["procesos"]:
            lineas.append(f"- {proc.nombre_proceso}: {proc.descripcion or 'N/A'}")
            if proc.problemas_detectados:
                lineas.append(f"  Problemas detectados: {proc.problemas_detectados}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Elicitación — Necesidades Identificadas ──────────────────────────
    lineas.append("## Elicitación — Necesidades Identificadas")
    if datos.get("necesidades"):
        for n in datos["necesidades"]:
            lineas.append(f"- {n.nombre}")
    else:
        lineas.append("- (ninguna)")
    lineas.append("")

    # ── Requerimientos Funcionales ────────────────────────────────────────
    lineas.append("## Requerimientos Funcionales")
    if datos["rfs"]:
        for r in datos["rfs"]:
            lineas.append(f"- [{r.codigo}] {r.descripcion} | Actor: {r.actor} | Prioridad: {r.prioridad} | Estado: {r.estado}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Requerimientos No Funcionales ─────────────────────────────────────
    lineas.append("## Requerimientos No Funcionales")
    if datos["rnfs"]:
        for r in datos["rnfs"]:
            tipo = str(r.tipo.value) if hasattr(r.tipo, "value") else r.tipo
            lineas.append(f"- [{r.codigo}] {r.descripcion} | Tipo: {tipo} | Métrica: {r.metrica or 'N/A'}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Tipos de Usuario ─────────────────────────────────────────────────
    lineas.append("## Tipos de Usuario del Sistema")
    if datos["tipos_usuario"]:
        for t in datos["tipos_usuario"]:
            lineas.append(f"- {t.tipo}: {t.descripcion or 'N/A'}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Casos de Uso ─────────────────────────────────────────────────────
    lineas.append("## Casos de Uso")
    if datos["casos_uso"]:
        for c in datos["casos_uso"]:
            lineas.append(f"- {c.nombre} | Actores: {c.actores} | Descripción: {c.descripcion}")
            pasos = c.pasos if isinstance(c.pasos, list) else []
            for i, paso in enumerate(pasos, 1):
                lineas.append(f"  {i}. {paso}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Restricciones ────────────────────────────────────────────────────
    lineas.append("## Restricciones")
    if datos["restricciones"]:
        for r in datos["restricciones"]:
            lineas.append(f"- [{r.codigo}] Tipo: {r.tipo} | {r.descripcion}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")

    # ── Negociación de Requerimientos ────────────────────────────────────
    lineas.append("## Negociación de Requerimientos")
    if datos.get("negociaciones"):
        for n in datos["negociaciones"]:
            estado = "Aceptado" if n.aceptado else "Pendiente"
            lineas.append(f"- {n.nombre} | {estado} | Prioridad: {n.prioridad}")
            lineas.append(f"  Descripción: {n.descripcion}")
    else:
        lineas.append("- (ninguna)")
    lineas.append("")

    # ── Estado de Validación ─────────────────────────────────────────────
    lineas.append("## Estado de Validación")
    v = datos["validacion"]
    if v:
        lineas.append(f"- Aprobado: {v.aprobado}")
        lineas.append(f"- Aprobador: {v.aprobador or 'N/A'}")
        lineas.append(f"- Observaciones: {v.observaciones or 'N/A'}")
        checklist = []
        if v.checklist_rf:             checklist.append("Req. Funcionales")
        if v.checklist_rnf:            checklist.append("Req. No Funcionales")
        if v.checklist_casos_uso:      checklist.append("Casos de Uso")
        if v.checklist_restricciones:  checklist.append("Restricciones")
        if v.checklist_prioridades:    checklist.append("Prioridades")
        lineas.append(f"- Checklist validado: {', '.join(checklist) if checklist else 'ninguno'}")
    else:
        lineas.append("- (sin validación registrada)")
    lineas.append("")

    # ── Documentos SRS existentes ────────────────────────────────────────
    srs_docs = datos.get("srs_docs", [])
    if srs_docs:
        lineas.append("## Documentos SRS del Proyecto")
        for srs in srs_docs:
            lineas.append(f"- {srs.nombre_documento} (v{srs.version}, estado: {srs.estado})")
            if srs.introduccion:
                lineas.append(f"  Introducción: {srs.introduccion[:500]}")
        lineas.append("")

    # ── Artefactos del proyecto (metadatos + contenido texto) ────────────
    artefactos = datos.get("artefactos", [])
    if artefactos:
        lineas.append("## Artefactos / Documentos Adjuntos del Proyecto")
        textos_incluidos = 0
        for a in artefactos:
            lineas.append(f"- {a.nombre} ({a.categoria}) — archivo: {a.nombre_archivo} [{a.tipo_mime}]")
            if a.descripcion:
                lineas.append(f"  Descripción: {a.descripcion}")

            # Leer contenido de archivos de texto para dar más contexto a la IA
            if textos_incluidos < _MAX_ARTEFACTOS_TEXTO:
                contenido = _leer_contenido_artefacto(a)
                if contenido:
                    textos_incluidos += 1
                    lineas.append(f"  ─── Contenido de {a.nombre_archivo} ───")
                    lineas.append(contenido)
                    lineas.append(f"  ─── Fin {a.nombre_archivo} ───")
        lineas.append("")

    return "\n".join(lineas)


# ── Post-procesamiento de contenido ──────────────────────────────────────────

def _fix_contenido(ruta: str, contenido: str) -> str:
    """
    Corrige problemas comunes en el contenido generado por Gemini:
    1. Reemplaza marcadores <NEWLINE> con saltos de línea reales
    2. requirements.txt con todos los paquetes en una sola línea
    3. .env con todas las variables pegadas
    """
    # ── Paso 1: Reemplazar marcadores <NEWLINE> ──────────────────────────
    if "<NEWLINE>" in contenido:
        contenido = contenido.replace("<NEWLINE>", "\n")

    nombre = ruta.rsplit("/", 1)[-1].lower() if "/" in ruta else ruta.lower()

    # ── Paso 2: Fallback para requirements.txt sin saltos ────────────────
    if nombre == "requirements.txt" and "\n" not in contenido.strip():
        contenido = re.sub(
            r'([0-9]+(?:\.[0-9]+)*)((?:[a-zA-Z][\w-]*)(?:==|>=|<=|~=|!=))',
            r'\1\n\2',
            contenido,
        )

    # ── Paso 3: Fallback para .env sin saltos ────────────────────────────
    if nombre == ".env" and "\n" not in contenido.strip():
        contenido = re.sub(
            r'([^\n=]+=[^\n=]+?)(?=(?:[A-Z_]+=))',
            r'\1\n',
            contenido,
        )

    return contenido


# ── Parsing de bloques ────────────────────────────────────────────────────────

def _extraer_bloque(texto: str, marcador: str) -> str:
    patron = rf"\[{marcador}\](.*?)(?=\[[A-Z_]+\]|$)"
    match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# ── Prompts de generación (divididos en 3 partes para ahorrar tokens) ─────────

_FORMATO_COMUN = """\
FORMATO DE RESPUESTA (JSON ESTRICTO):
Devuelve ÚNICAMENTE un objeto JSON con la clave "files" que contiene un array.
Cada elemento del array representa un archivo:
  "section": "frontend" | "backend" | "database"
  "path":    ruta relativa del archivo (ej: "main.py", "src/app/app.component.ts")
  "lines":   array de strings — UNA LÍNEA POR ELEMENTO, línea vacía = ""

Ejemplo de estructura correcta:
{
  "files": [
    {"section": "backend",  "path": "main.py",        "lines": ["from fastapi import FastAPI", "app = FastAPI()"]},
    {"section": "database", "path": "schema.sql",     "lines": ["CREATE TABLE users (id INT PRIMARY KEY);"]},
    {"section": "frontend", "path": "src/main.ts",    "lines": ["import { bootstrapApplication } from '@angular/platform-browser';"]}
  ]
}

REGLAS:
- Código COMPLETO, sin TODO, sin placeholders
- NUNCA uses fences markdown ni triple backticks dentro del contenido
- Backend: imports absolutos (from database import ..., from models import ...)
- Frontend conecta a http://localhost:8000"""


def _prompt_backend_db(contexto: str) -> str:
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

{_FORMATO_COMUN}

Genera estos 9 archivos de BACKEND y BASE DE DATOS:

BACKEND (section="backend"):
 1. main.py        — FastAPI con CORSMiddleware(allow_origins=["*"]), include_router, puerto 8000
 2. database.py    — SQLAlchemy engine, SessionLocal, Base, get_db()
 3. models.py      — modelos SQLAlchemy (usa LONGTEXT para campos JSON/texto largo, nunca TEXT)
 4. schemas.py     — schemas Pydantic request/response con Optional para updates
 5. crud.py        — CRUD completo: get, list, create, update, delete; json.dumps/loads para LONGTEXT
 6. router.py      — APIRouter con GET/POST/PUT/DELETE para cada entidad
 7. requirements.txt — una dependencia por línea: fastapi, uvicorn[standard], sqlalchemy, pymysql, python-dotenv, pydantic
 8. .env           — DATABASE_URL=mysql+pymysql://root:Admin1234!@localhost/<nombre_bd>

DATABASE (section="database"):
 9. schema.sql     — SOLO: DROP TABLE IF EXISTS + CREATE TABLE (LONGTEXT para JSON) + INSERT ejemplo
                    NO incluir CREATE DATABASE ni USE <db>"""


def _prompt_frontend_core(contexto: str) -> str:
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

{_FORMATO_COMUN}

Genera estos 7 archivos de la capa lógica del FRONTEND (Angular 18 standalone):

section="frontend" para todos:
 1. src/app/models/interfaces.ts         — interfaces TypeScript de todas las entidades del dominio
 2. src/app/services/api.service.ts      — Injectable con HttpClient, métodos CRUD para cada entidad
 3. src/app/app.component.ts             — raíz standalone, selector 'app-root', template con <router-outlet>
 4. src/app/app.routes.ts                — Routes[], path '' carga MainComponent con loadComponent
 5. src/app/app.config.ts                — ApplicationConfig: provideRouter, provideHttpClient, provideZoneChangeDetection
 6. src/environments/environment.ts      — export const environment = {{ apiUrl: 'http://localhost:8000' }}
 7. src/main.ts                          — bootstrapApplication(AppComponent, appConfig)"""


def _prompt_frontend_componentes(contexto: str) -> str:
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

{_FORMATO_COMUN}

Genera estos 9 archivos de componentes y configuración del FRONTEND (Angular 18 standalone):

section="frontend" para todos:
 1. src/app/components/main/main.component.ts    — standalone, lógica CRUD (listar, crear, editar, eliminar)
 2. src/app/components/main/main.component.html  — template con formulario, tabla de datos y botones
 3. src/app/components/main/main.component.css   — estilos modernos y responsivos
 4. src/index.html                               — HTML raíz, charset utf-8, <base href="/">, <app-root>
 5. src/styles.css                               — estilos globales (reset, variables CSS de color)
 6. package.json                                 — name: frontend, scripts start/build, @angular/core ^18.0.0, @angular/cli ^18.0.0
 7. angular.json                                 — version 1, sourceRoot "src", index "src/index.html", browser "src/main.ts", tsConfig "tsconfig.app.json"
 8. tsconfig.json                                — target ES2022, module ES2022, strict false
 9. tsconfig.app.json                            — extends "./tsconfig.json", include ["src/**/*.ts"]"""


def _prompt_completo(contexto: str) -> str:
    """
    Prompt unificado para generar los 25 archivos en UNA SOLA llamada.
    Requiere un modelo con >= 65 K tokens de salida (gemini-2.5-flash).
    """
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

{_FORMATO_COMUN}

Genera los siguientes 25 ARCHIVOS COMPLETOS para una aplicación web full-stack:

BACKEND (section="backend") — 8 archivos:
 1. main.py         — FastAPI con CORSMiddleware(allow_origins=["*"]), include_router, uvicorn puerto 8000
 2. database.py     — SQLAlchemy engine, SessionLocal, Base, función get_db()
 3. models.py       — modelos SQLAlchemy (usa LONGTEXT para campos JSON/texto largo, nunca TEXT simple)
 4. schemas.py      — schemas Pydantic v2 con Optional para campos de update
 5. crud.py         — CRUD completo: get_by_id, list_all, create, update, delete
 6. router.py       — APIRouter con endpoints GET/POST/PUT/DELETE para cada entidad
 7. requirements.txt — una dependencia por línea: fastapi, uvicorn[standard], sqlalchemy, pymysql, python-dotenv, pydantic
 8. .env            — DATABASE_URL=mysql+pymysql://root:Admin1234!@localhost/<nombre_bd_del_proyecto>

DATABASE (section="database") — 1 archivo:
 9. schema.sql      — SOLO: DROP TABLE IF EXISTS + CREATE TABLE (LONGTEXT para JSON) + INSERT de ejemplo
                     NO incluir CREATE DATABASE ni USE <db>

FRONTEND Angular 18 standalone (section="frontend") — 16 archivos:
10. src/app/models/interfaces.ts               — interfaces TypeScript de todas las entidades
11. src/app/services/api.service.ts            — @Injectable HttpClient, métodos CRUD para cada entidad
12. src/app/app.component.ts                   — standalone root, selector 'app-root', <router-outlet>
13. src/app/app.routes.ts                      — Routes[], ruta '' carga MainComponent con loadComponent
14. src/app/app.config.ts                      — ApplicationConfig: provideRouter, provideHttpClient, provideZoneChangeDetection
15. src/environments/environment.ts            — export const environment = {{ apiUrl: 'http://localhost:8000' }}
16. src/main.ts                                — bootstrapApplication(AppComponent, appConfig)
17. src/app/components/main/main.component.ts  — standalone, lógica CRUD completa (listar, crear, editar, eliminar)
18. src/app/components/main/main.component.html — template: formulario + tabla con botones editar/eliminar
19. src/app/components/main/main.component.css  — estilos modernos y responsivos
20. src/index.html                             — HTML raíz: charset utf-8, <base href="/">, <app-root>
21. src/styles.css                             — estilos globales (reset CSS, variables de color)
22. package.json                               — name: "frontend", scripts start/build, @angular/core ^18.0.0
23. angular.json                               — version 1, sourceRoot "src", index "src/index.html", browser "src/main.ts", tsConfig "tsconfig.app.json"
24. tsconfig.json                              — target ES2022, module ES2022, strict false
25. tsconfig.app.json                          — extends "./tsconfig.json", include ["src/**/*.ts"]"""


_SCHEMA_ARCHIVOS = {
    "type": "object",
    "required": ["files"],
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["section", "path", "lines"],
                "properties": {
                    "section": {"type": "string", "enum": ["frontend", "backend", "database"]},
                    "path":    {"type": "string"},
                    "lines":   {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}


# ── Generación de código ──────────────────────────────────────────────────────

def _armar_resultado(todos_archivos: list) -> dict:
    """Convierte la lista plana de archivos JSON en el resultado {frontend, backend, database}."""
    bloques: dict = {"frontend": [], "backend": [], "database": []}
    for arch in todos_archivos:
        seccion = (arch.get("section") or "").lower()
        ruta    = (arch.get("path") or "").strip()
        if seccion not in bloques or not ruta:
            continue
        lines    = arch.get("lines")
        contenido = "\n".join(lines) if isinstance(lines, list) else (arch.get("content") or "")
        contenido = _fix_contenido(ruta, contenido)
        bloques[seccion].append(f"@@FILE: {ruta}@@\n{contenido}")
    return {
        "frontend": "\n\n".join(bloques["frontend"]),
        "backend":  "\n\n".join(bloques["backend"]),
        "database": "\n\n".join(bloques["database"]),
    }


def generar_codigo(db: Session, proyecto_id: int) -> dict:
    """
    Genera la aplicación completa en 3 partes usando GitHub Models (Azure).

    Modelo principal : gpt-4o-mini  (15 RPM · 150 RPD · estable)
    Modelo fallback  : gpt-4o       (10 RPM ·  50 RPD · mayor calidad)

    Se divide en 3 partes para mantenerse dentro del límite de tokens de salida
    por petición (~4 096 tokens en el free tier de GitHub Models).
    """
    datos    = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)
    client   = _get_client()

    partes = [
        ("backend y base de datos", _prompt_backend_db(contexto)),
        ("frontend core",           _prompt_frontend_core(contexto)),
        ("frontend componentes",    _prompt_frontend_componentes(contexto)),
    ]

    todos_archivos: list = []

    for i, (nombre_parte, prompt) in enumerate(partes):
        if i > 0:
            # Pequeña pausa entre llamadas para respetar el RPM
            print(f"[Generador] Esperando 5 s antes de parte {i + 1}/{len(partes)}...")
            time.sleep(5)

        archivos_parte: list = []
        for modelo in [MODEL_MAIN, MODEL_FALLBACK]:
            try:
                print(f"[Generador] Parte '{nombre_parte}' con {modelo}...")
                texto = _call_ai(client, prompt, model=modelo, max_tokens=4096)
                data  = json.loads(texto)
                archivos_parte = data.get("files") or []
                if archivos_parte:
                    print(f"[Generador] ✓ Parte '{nombre_parte}' — {len(archivos_parte)} archivos.")
                    break
                else:
                    print(f"[Generador] {modelo} devolvió JSON vacío en '{nombre_parte}', probando fallback...")
            except HTTPException as e:
                print(f"[Generador] {modelo} falló en '{nombre_parte}' ({e.status_code}): {e.detail}")
                if e.status_code in (429, 503):
                    continue   # intenta el siguiente modelo
                raise
            except json.JSONDecodeError as exc:
                print(f"[Generador] JSON inválido de {modelo}: {exc}")
                continue

        if not archivos_parte:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"No se pudo generar la parte '{nombre_parte}'. "
                    "Verifica que GITHUB_TOKEN esté configurado y sea válido. "
                    "Intenta de nuevo en unos minutos si es un error temporal."
                ),
            )
        todos_archivos.extend(archivos_parte)

    if not todos_archivos:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se generó ningún archivo. Intenta de nuevo.",
        )

    print(f"[Generador] ✓ Generación completa — {len(todos_archivos)} archivos en total.")
    return _armar_resultado(todos_archivos)


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
    datos    = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)
    client   = _get_client()

    instruccion = _INSTRUCCIONES_DIAGRAMA.get(tipo, "Genera un diagrama Mermaid apropiado.")

    prompt = f"""Eres un experto en diseño de software y diagramas UML. Aquí tienes la especificación del proyecto:

{contexto}

{instruccion}

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con el código Mermaid, sin explicaciones, sin texto adicional, sin bloques de código markdown (no uses ```).
2. El código debe ser sintaxis Mermaid válida y renderizable.
3. Usa nombres en español basados en la especificación del proyecto.
4. El diagrama debe ser coherente con los datos del proyecto proporcionados."""

    codigo_mermaid = _call_ai(
        client, prompt, model=MODEL_MAIN, max_tokens=2048, json_mode=False,
    )

    # Limpiar posibles bloques markdown residuales
    codigo_mermaid = re.sub(r"^```(?:mermaid)?\n?", "", codigo_mermaid.strip(), flags=re.MULTILINE)
    codigo_mermaid = re.sub(r"\n?```$", "", codigo_mermaid.strip(), flags=re.MULTILINE)

    return {"tipo": tipo, "codigo_mermaid": codigo_mermaid.strip()}
