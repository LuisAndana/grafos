import re
import os
import json
import time
import traceback
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
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

# Modelos disponibles en el free tier de Gemini API (abril 2025)
MODEL_FLASH25      = "models/gemini-2.5-flash"      # 10 RPM · 20 RPD/día  · 65 536 tokens/respuesta
MODEL_FLASH20      = "models/gemini-2.0-flash"       # 15 RPM · 1 500 RPD/día ·  8 192 tokens/respuesta
MODEL_FLASH20_LITE = "models/gemini-2.0-flash-lite"  # 30 RPM · 1 500 RPD/día ·  8 192 tokens/respuesta

# Alias usados por _call_gemini (compatibilidad con generar_diagrama)
MODEL           = MODEL_FLASH25
FALLBACK_MODELS = [MODEL_FLASH20, MODEL_FLASH20_LITE]


def _es_error_cuota(e: Exception) -> bool:
    """True si el error es 429 RESOURCE_EXHAUSTED (límite RPM o cuota diaria)."""
    msg = str(e)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def _extraer_retry_delay(e: Exception) -> float:
    """
    Extrae el tiempo de espera sugerido de un error 429 en segundos.
    El API incluye 'retryDelay': '29s' en los errores de límite por minuto (RPM).
    Devuelve 0.0 si no hay información de delay.
    """
    msg = str(e)
    m = re.search(r'"retryDelay":\s*"([\d.]+)s"', msg)
    if m:
        return float(m.group(1))
    m = re.search(r'retry in ([\d.]+)s', msg, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 0.0


def _call_gemini_modelo(
    client: genai.Client,
    model: str,
    contents: str,
    config: types.GenerateContentConfig,
    max_503_retries: int = 2,
):
    """
    Llama a UN modelo Gemini específico con reintentos robustos.

    - 503 UNAVAILABLE   → hasta max_503_retries intentos con 90 s y 180 s de espera.
                          El servidor tarda varios minutos en recuperarse; esperas cortas no sirven.
    - 429 RPM (≤90 s)   → espera 120 s y reintenta; si falla de nuevo espera 240 s más.
    - 429 cuota diaria  → lanza HTTPException(429) inmediatamente.
    - 404 NOT_FOUND     → lanza HTTPException(404).
    - Otros ClientError → lanza HTTPException(400).
    """
    for attempt in range(1, max_503_retries + 1):
        try:
            print(f"[Gemini] {model} — intento {attempt}/{max_503_retries}...")
            return client.models.generate_content(
                model=model, contents=contents, config=config,
            )
        except genai_errors.ServerError as e:
            if attempt < max_503_retries:
                wait = 90 * attempt   # 90 s → 180 s  (el servidor necesita tiempo real)
                print(f"[Gemini 503] {model} saturado, reintentando en {wait}s...")
                time.sleep(wait)
            else:
                print(f"[Gemini 503] {model} agotó {max_503_retries} reintentos.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Modelo {model} no disponible (503) tras {max_503_retries} intentos.",
                )
        except genai_errors.ClientError as e:
            if _es_error_cuota(e):
                delay = _extraer_retry_delay(e)
                if 0 < delay <= 90:
                    # ── Reintento 1: esperar la ventana completa ──────────────
                    wait1 = max(delay + 10, 120)   # mínimo 2 minutos
                    print(f"[Gemini RPM] {model} límite/min, esperando {wait1:.0f}s (intento 1/2)...")
                    time.sleep(wait1)
                    try:
                        print(f"[Gemini] {model} reintento 1 post-RPM...")
                        return client.models.generate_content(
                            model=model, contents=contents, config=config,
                        )
                    except genai_errors.ClientError as r1:
                        if not _es_error_cuota(r1):
                            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(r1))
                        # ── Reintento 2: ventana de 4 minutos adicionales ─────
                        wait2 = 240
                        print(f"[Gemini RPM] {model} sigue con límite, esperando {wait2}s adicionales (intento 2/2)...")
                        time.sleep(wait2)
                        try:
                            print(f"[Gemini] {model} reintento 2 post-RPM...")
                            return client.models.generate_content(
                                model=model, contents=contents, config=config,
                            )
                        except genai_errors.ClientError as r2:
                            if _es_error_cuota(r2):
                                print(f"[Gemini RPM] {model} agotó 2 reintentos RPM ({wait1+wait2:.0f}s total).")
                                raise HTTPException(429, detail=f"RPM persistente: {model}.")
                            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(r2))
                        except Exception as r2:
                            raise HTTPException(503, detail=str(r2))
                    except Exception as r1:
                        raise HTTPException(503, detail=str(r1))
                else:
                    # Sin delay o delay largo → cuota diaria agotada
                    print(f"[Gemini 429] Cuota diaria agotada en {model}.")
                    raise HTTPException(429, detail=f"Cuota diaria agotada: {model}.")
            elif "404" in str(e) or "NOT_FOUND" in str(e):
                print(f"[Gemini 404] {model} no disponible en esta API.")
                raise HTTPException(404, detail=f"Modelo no encontrado: {model}.")
            else:
                print(f"[Gemini ClientError] {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al llamar a Gemini ({model}): {e}",
                )
        except Exception as e:
            print(f"[Gemini UnknownError] {type(e).__name__}: {e}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado: {type(e).__name__}: {e}",
            )
    raise HTTPException(status_code=503, detail=f"No se pudo contactar a {model}.")


def _call_gemini(
    client: genai.Client,
    contents: str,
    config: types.GenerateContentConfig,
    max_retries: int = 2,   # mantenido por compatibilidad, ya no se usa directamente
):
    """
    Prueba los modelos en secuencia hasta obtener respuesta.
    Usado principalmente por generar_diagrama.

    - 429 / 503 / 404 en un modelo → intenta el siguiente.
    - 400 / 500              → falla de inmediato (error de cliente/servidor real).
    """
    last_error = None
    for model in [MODEL] + FALLBACK_MODELS:
        try:
            return _call_gemini_modelo(client, model, contents, config)
        except HTTPException as e:
            last_error = e
            if e.status_code in (429, 503, 404):
                print(f"[Gemini] {model} → {e.status_code}, probando siguiente modelo...")
                continue
            raise   # 400, 500: error real, no vale la pena probar otro modelo
        except Exception as e:
            raise HTTPException(500, detail=str(e))

    # Todos los modelos fallaron
    detail = (
        "Todos los modelos de IA están con límites de uso. "
        "Espera 5 minutos (límite/min) o intenta mañana (límite diario). "
        "Detalle: " + (last_error.detail if last_error else "desconocido")
    )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail,
    )

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
FORMATO DE RESPUESTA:
Devuelve JSON con array "files". Cada archivo:
  "section": "frontend"|"backend"|"database"
  "path": ruta relativa
  "lines": array de strings — UNA LÍNEA POR ELEMENTO, línea vacía = ""

REGLAS:
- Código COMPLETO, sin TODO, sin placeholders
- NUNCA uses fences markdown ni triple backticks
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
    Genera la aplicación completa con dos estrategias, de más eficiente a más tolerante:

    Estrategia 1 — gemini-2.5-flash, llamada ÚNICA (65 536 tokens de salida):
      • Solo consume 1 RPD en lugar de 3 → menos presión sobre la cuota diaria.
      • 10 RPM es suficiente para uso interactivo normal.
      • Si falla (503 persistente, RPM o cuota diaria) → pasa a Estrategia 2.

    Estrategia 2 — gemini-2.0-flash / gemini-2.0-flash-lite, 3 llamadas de 8 192 tokens:
      • 1 500 RPD disponibles → útil cuando gemini-2.5-flash no responde.
      • Espera 30 s entre partes para respetar el RPM.
    """
    datos    = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)
    client   = _get_client()

    # ── Estrategia 1: llamada única con gemini-2.5-flash (65 K tokens) ──────
    print("[Generador] Estrategia 1 — gemini-2.5-flash, llamada única (65 536 tokens)...")
    config_25 = types.GenerateContentConfig(
        max_output_tokens=65536,
        temperature=0.3,
        response_mime_type="application/json",
        response_schema=_SCHEMA_ARCHIVOS,
    )
    todos_archivos: list = []
    try:
        resp = _call_gemini_modelo(client, MODEL_FLASH25, _prompt_completo(contexto), config_25)
        todos_archivos = (json.loads(resp.text or "{}")).get("files") or []
    except HTTPException as e:
        print(f"[Generador] Estrategia 1 falló ({e.status_code}): {e.detail}")
    except Exception as e:
        print(f"[Generador] Estrategia 1 error inesperado: {e}")

    if todos_archivos:
        print(f"[Generador] Estrategia 1 exitosa — {len(todos_archivos)} archivos generados.")
        return _armar_resultado(todos_archivos)

    # ── Cooldown antes de Estrategia 2 ──────────────────────────────────────
    # Las peticiones fallidas a gemini-2.5-flash pueden haber saturado los
    # límites del proyecto; esperar 60 s da tiempo a que los contadores RPM
    # de los modelos 2.0-flash se limpien completamente.
    print("[Generador] Esperando 60 s de cooldown antes de Estrategia 2...")
    time.sleep(60)

    # ── Estrategia 2: 3 partes con gemini-2.0-flash → gemini-2.0-flash-lite ─
    print("[Generador] Estrategia 2 — modo 3 partes (8 192 tokens cada una)...")
    config_20 = types.GenerateContentConfig(
        max_output_tokens=8192,
        temperature=0.3,
        response_mime_type="application/json",
        response_schema=_SCHEMA_ARCHIVOS,
    )
    partes = [
        ("backend y base de datos", _prompt_backend_db(contexto)),
        ("frontend core",           _prompt_frontend_core(contexto)),
        ("frontend componentes",    _prompt_frontend_componentes(contexto)),
    ]

    for i, (nombre_parte, prompt) in enumerate(partes):
        if i > 0:
            print(f"[Generador] Esperando 30 s antes de parte {i + 1}/{len(partes)}...")
            time.sleep(30)

        archivos_parte: list = []
        for modelo in [MODEL_FLASH20, MODEL_FLASH20_LITE]:
            try:
                resp = _call_gemini_modelo(client, modelo, prompt, config_20)
                archivos_parte = (json.loads(resp.text or "{}")).get("files") or []
                if archivos_parte:
                    print(f"[Generador] Parte '{nombre_parte}' generada con {modelo}.")
                    break
            except HTTPException as e:
                print(f"[Generador] {modelo} falló en parte '{nombre_parte}': {e.detail}")
                continue

        if not archivos_parte:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"No se pudo generar la parte '{nombre_parte}'. "
                    "Todos los modelos de IA están con límites de uso. "
                    "Espera al menos 5 minutos e intenta de nuevo."
                ),
            )
        todos_archivos.extend(archivos_parte)

    if not todos_archivos:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se generó ningún archivo. Intenta de nuevo en unos minutos.",
        )

    print(f"[Generador] Estrategia 2 exitosa — {len(todos_archivos)} archivos generados.")
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

    respuesta = _call_gemini(
        client,
        prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.4,
        ),
    )

    codigo_mermaid = respuesta.text

    # Limpiar posibles bloques markdown
    codigo_mermaid = re.sub(r"^```(?:mermaid)?\n?", "", codigo_mermaid.strip(), flags=re.MULTILINE)
    codigo_mermaid = re.sub(r"\n?```$", "", codigo_mermaid.strip(), flags=re.MULTILINE)

    return {"tipo": tipo, "codigo_mermaid": codigo_mermaid.strip()}
