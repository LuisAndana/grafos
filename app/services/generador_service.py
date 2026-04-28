import re
import os
import json
import time
import logging
<<<<<<< HEAD
=======
import sys
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
import traceback
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIStatusError, AuthenticationError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

<<<<<<< HEAD
# ── Logging — fuerza salida a stdout (mismo stream que SQLAlchemy/uvicorn) ──
import sys as _sys

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
if not log.handlers:
    _sh = logging.StreamHandler(_sys.stdout)
    _sh.setLevel(logging.DEBUG)
    _sh.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    log.addHandler(_sh)
log.propagate = False   # evitar duplicados si root también tiene handler
=======
# ── Logging — handler directo a stdout para garantizar visibilidad ──────────
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
if not log.handlers:
    _sh = logging.StreamHandler(sys.stdout)
    _sh.setLevel(logging.DEBUG)
    _sh.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    log.addHandler(_sh)
log.propagate = False
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50

load_dotenv(override=True)

from app.models.proyecto import Proyecto
from app.models.stakeholder import Stakeholder
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
from app.models.tipo_usuario_proyecto import TipoUsuarioProyecto
from app.models.caso_uso import CasoUso
from app.models.restriccion import Restriccion
from app.models.validacion import Validacion
<<<<<<< HEAD
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

    - 429 RateLimitError  → espera retry-after del header (mínimo 65 s) y reintenta.
    - 5xx APIStatusError  → reintenta con backoff 30 s / 60 s.
    - 401/403 AuthError   → falla de inmediato (token inválido).
    - Otros               → falla de inmediato.

    Devuelve el texto plano de la respuesta.
    """
    system_msg = "Eres un arquitecto de software senior especializado en aplicaciones web full-stack."
    if json_mode:
        system_msg += " Devuelve SIEMPRE únicamente un objeto JSON válido, sin texto adicional."

    for attempt in range(1, 4):   # hasta 3 intentos
        try:
            log.info(f"[AI] {model} — intento {attempt}/3...")
            resp = client.chat.completions.create(
=======

# ── Configuración de proveedor: solo Gemini ──────────────────────────────────
# Un único proveedor elimina inconsistencias entre archivos generados por modelos distintos.

_PROVIDERS = {
    "gemini": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "token_env": "GEMINI_API_KEY",
    },
}

# (proveedor, modelo, soporta_json_mode)
# gemini-2.5-pro: tier de pago, 1M tokens de contexto, hasta 65k tokens de salida.
# No requiere fallbacks — un único modelo garantiza coherencia entre todos los archivos.

_CODE_CHAIN = [
    ("gemini", "gemini-2.5-pro", True),
]

_CODE_CHAIN_LARGE = [
    ("gemini", "gemini-2.5-pro", True),
]

_GEMINI_UI_CHAIN = [
    ("gemini", "gemini-2.5-pro", True),
]

_REASONING_CHAIN = [
    ("gemini", "gemini-2.5-pro", False),
]


def _make_client(provider: str) -> "OpenAI | None":
    """Crea cliente OpenAI para el proveedor. Retorna None si no hay token."""
    load_dotenv(override=True)
    cfg = _PROVIDERS.get(provider)
    if not cfg:
        return None
    token = os.getenv(cfg["token_env"])
    if not token:
        return None
    return OpenAI(base_url=cfg["endpoint"], api_key=token)


def _strip_thinking(text: str) -> str:
    """Elimina bloques <think>...</think> de modelos de razonamiento.
    También elimina bloques incompletos (modelo truncado antes del </think>)."""
    # Bloque completo: <think>...</think>
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Bloque incompleto: <think> sin cierre (respuesta cortada por max_tokens)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def _call_single(client: OpenAI, model: str, prompt: str,
                 max_tokens: int, json_mode: bool) -> str:
    """Llamada única con reintentos por rate-limit."""
    system_msg = ("Eres un arquitecto de software senior especializado en "
                  "aplicaciones web full-stack.")
    if json_mode:
        system_msg += " Devuelve SIEMPRE únicamente un objeto JSON válido, sin texto adicional."

    for attempt in range(1, 4):
        try:
            log.info(f"[AI] {model} intento {attempt}/3...")
            kwargs: dict = dict(
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
<<<<<<< HEAD
                # NO se usa response_format para máxima compatibilidad con GitHub Models
            )
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
                log.warning(f"[AI RPM] {model} límite de tasa, esperando {wait}s...")
                time.sleep(wait)
            else:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit persistente en {model}. Intenta en unos minutos.",
                )
        except APIStatusError as e:
            body = ""
            try:
                body = e.response.text[:400]
            except Exception:
                body = str(e)
            # print directo para garantizar visibilidad independientemente del stream
            print(f"\n>>> [AI Error {e.status_code}] model={model} msg={e.message!r} body={body!r}\n", flush=True)
            log.error(f"[AI Error {e.status_code}] {model}: {e.message} | body: {body}")
            if e.status_code >= 500:
                if attempt < 3:
                    wait = 30 * attempt   # 30 s, 60 s
                    log.warning(f"[AI {e.status_code}] reintentando en {wait}s...")
                    time.sleep(wait)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Servidor no disponible ({model}). Intenta de nuevo en unos minutos.",
                    )
            elif e.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=(
                        "GITHUB_TOKEN inválido, expirado o sin permisos para GitHub Models. "
                        "Asegúrate de que el token tenga acceso a github.com/marketplace/models"
                    ),
                )
            else:
                # 400 u otro error de cliente: incluir el body real en el detail
                raise HTTPException(
                    status_code=e.status_code,
                    detail=f"Error API ({model}) [{e.status_code}]: {e.message} — {body}",
                )
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GITHUB_TOKEN inválido o expirado. Genera un nuevo token en github.com/settings/tokens",
            )
        except Exception as e:
            log.info(f"[AI UnknownError] {type(e).__name__}: {e}")
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
    log.debug(f"[AI] Token cargado: {token[:8]}...{token[-4:]}")
    return OpenAI(base_url=_GITHUB_ENDPOINT, api_key=token)


def test_conexion() -> dict:
    """Prueba rápida de la conexión con GitHub Models sin necesitar proyecto."""
    log.info("[Test] Iniciando prueba de conexión con GitHub Models...")
    client = _get_client()
    try:
        respuesta = _call_ai(
            client,
            "Responde únicamente con la palabra: OK",
            model=MODEL_MAIN,
            max_tokens=10,
            json_mode=False,
        )
        log.info(f"[Test] ✓ Conexión OK — respuesta: {respuesta.strip()!r}")
        return {"status": "ok", "modelo": MODEL_MAIN, "respuesta": respuesta.strip()}
    except HTTPException as e:
        log.error(f"[Test] ✗ Falló ({e.status_code}): {e.detail}")
        return {"status": "error", "codigo": e.status_code, "detalle": e.detail}


# ── Recopilación de datos del proyecto ───────────────────────────────────────
=======
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""

        except RateLimitError as e:
            # Leer retry-after pero NUNCA esperar más de 70 s.
            # Si el servidor pide más tiempo el modelo está bloqueado (cuota diaria agotada)
            # → saltar inmediatamente al siguiente proveedor sin desperdiciar tiempo.
            _MAX_WAIT = 70
            wait = 65
            too_long = False
            try:
                ra = e.response.headers.get("retry-after")
                if ra:
                    ra_val = int(ra)
                    if ra_val > _MAX_WAIT:
                        too_long = True
                    else:
                        wait = ra_val + 5
            except Exception:
                pass

            if too_long:
                log.warning(f"[AI] {model} cuota agotada (retry-after muy alto) — pasando al siguiente modelo")
                raise  # sale de _call_single, _call_chain prueba el siguiente

            if attempt < 3:
                log.warning(f"[AI RPM] {model} rate limit, esperando {wait}s...")
                time.sleep(wait)
            else:
                raise  # propaga al caller para probar siguiente modelo

        except APIStatusError as e:
            body = ""
            try:
                body = e.response.text[:300]
            except Exception:
                body = str(e)
            log.error(f"[AI {e.status_code}] {model}: {e.message} | {body}")
            if e.status_code >= 500 and attempt < 3:
                time.sleep(30 * attempt)
            else:
                raise

        except AuthenticationError:
            raise  # token inválido → saltar proveedor

    raise Exception(f"Max reintentos superados para {model}")


def _call_chain(chain: list, prompt: str, max_tokens: int,
                json_mode: bool = True) -> str:
    """Intenta cada (proveedor, modelo) en orden hasta que uno responda."""
    last_exc: Exception | None = None

    for provider, model, supports_json in chain:
        client = _make_client(provider)
        if client is None:
            log.debug(f"[AI] Saltando {provider}/{model} — token no configurado")
            continue

        use_json = json_mode and supports_json
        try:
            result = _call_single(client, model, prompt, max_tokens, use_json)
            result = _strip_thinking(result)
            log.info(f"[AI] Exito: {provider}/{model}")
            return result
        except (RateLimitError, APIStatusError, AuthenticationError) as e:
            log.warning(f"[AI] {provider}/{model} fallo ({type(e).__name__}), probando siguiente...")
            last_exc = e
            continue
        except Exception as e:
            log.warning(f"[AI] {provider}/{model} error inesperado: {e}")
            last_exc = e
            continue

    raise HTTPException(503,
        detail=f"Todos los modelos fallaron. Configura al menos un token en .env. "
               f"Ultimo error: {last_exc}")


# Alias de compatibilidad para test_conexion
def _get_client() -> OpenAI:
    client = _make_client("gemini")
    if client is None:
        raise HTTPException(503, detail="GEMINI_API_KEY no configurado.")
    return client


def _call_ai(client: OpenAI, prompt: str, model: str = "gpt-4o-mini",
             max_tokens: int = 4096, json_mode: bool = True) -> str:
    """Compatibilidad: usa la cadena completa en lugar de un modelo fijo."""
    return _call_chain(_CODE_CHAIN, prompt, max_tokens, json_mode)


# ── Test de conexión ─────────────────────────────────────────────────────────

def test_conexion() -> dict:
    """Prueba rápida: verifica que al menos un proveedor responde."""
    log.info("[Test] Probando cadena de modelos...")
    try:
        resp = _call_chain(_CODE_CHAIN, "Responde solo: OK", max_tokens=10, json_mode=False)
        log.info(f"[Test] ✓ OK — respuesta: {resp.strip()!r}")
        return {"status": "ok", "respuesta": resp.strip()}
    except HTTPException as e:
        return {"status": "error", "codigo": e.status_code, "detalle": e.detail}


# ── Recopilación de datos ────────────────────────────────────────────────────
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50

def _recopilar_datos(db: Session, proyecto_id: int) -> dict:
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")

<<<<<<< HEAD
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


=======
    return {
        "proyecto":      proyecto,
        "stakeholders":  db.query(Stakeholder).filter(Stakeholder.proyecto_id == proyecto_id).all(),
        "rfs":           db.query(RequerimientoFuncional).filter(RequerimientoFuncional.proyecto_id == proyecto_id).all(),
        "rnfs":          db.query(RequerimientoNoFuncional).filter(RequerimientoNoFuncional.proyecto_id == proyecto_id).all(),
        "tipos_usuario": db.query(TipoUsuarioProyecto).filter(TipoUsuarioProyecto.proyecto_id == proyecto_id).all(),
        "casos_uso":     db.query(CasoUso).filter(CasoUso.proyecto_id == proyecto_id).all(),
        "restricciones": db.query(Restriccion).filter(Restriccion.proyecto_id == proyecto_id).all(),
        "validacion":    db.query(Validacion).filter(Validacion.proyecto_id == proyecto_id).first(),
    }


>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
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

<<<<<<< HEAD
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
=======
    lineas.append("## Stakeholders")
    for s in datos["stakeholders"]:
        tipo = str(s.tipo.value) if hasattr(s.tipo, "value") else s.tipo
        inf  = str(s.nivel_influencia.value) if hasattr(s.nivel_influencia, "value") else s.nivel_influencia
        lineas.append(f"- {s.nombre} | Rol: {s.rol} | Tipo: {tipo} | Área: {s.area} | Influencia: {inf}")
    if not datos["stakeholders"]:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Requerimientos Funcionales")
    for r in datos["rfs"]:
        lineas.append(f"- [{r.codigo}] {r.descripcion} | Actor: {r.actor} | Prioridad: {r.prioridad} | Estado: {r.estado}")
    if not datos["rfs"]:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Requerimientos No Funcionales")
    for r in datos["rnfs"]:
        tipo = str(r.tipo.value) if hasattr(r.tipo, "value") else r.tipo
        lineas.append(f"- [{r.codigo}] {r.descripcion} | Tipo: {tipo} | Métrica: {r.metrica or 'N/A'}")
    if not datos["rnfs"]:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Tipos de Usuario")
    for t in datos["tipos_usuario"]:
        lineas.append(f"- {t.tipo}: {t.descripcion or 'N/A'}")
    if not datos["tipos_usuario"]:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Casos de Uso")
    for c in datos["casos_uso"]:
        lineas.append(f"- {c.nombre} | Actores: {c.actores} | Descripción: {c.descripcion}")
    if not datos["casos_uso"]:
        lineas.append("- (ninguno)")
    lineas.append("")

    lineas.append("## Restricciones")
    for r in datos["restricciones"]:
        lineas.append(f"- [{r.codigo}] Tipo: {r.tipo} | {r.descripcion}")
    if not datos["restricciones"]:
        lineas.append("- (ninguno)")
    lineas.append("")

    v = datos["validacion"]
    lineas.append("## Estado de Validación")
    if v:
        lineas.append(f"- Aprobado: {v.aprobado} | Aprobador: {v.aprobador or 'N/A'}")
        lineas.append(f"- Observaciones: {v.observaciones or 'N/A'}")
    else:
        lineas.append("- (sin validación registrada)")
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50

    return "\n".join(lineas)


<<<<<<< HEAD
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
=======
# ── Extracción de entidades del proyecto ─────────────────────────────────────

def _extraer_entidades(contexto: str) -> str:
    """
    Usa modelos de razonamiento para identificar TODAS las entidades reales del proyecto
    (incluyendo subida de archivos, comparación de espectros, etc. según los requisitos).
    """
    prompt = f"""Eres un analista de software experto. Lee TODOS los requerimientos funcionales, \
casos de uso y restricciones de este proyecto y extrae TODAS las entidades de base de datos necesarias.

{contexto[:8000]}

INSTRUCCIONES CRÍTICAS:
- Lee CADA requerimiento funcional y caso de uso — si dice "subir archivos", \
hay una entidad Archivo; si dice "comparar espectros", hay una entidad Espectro y quizás Similitud/Comparacion
- NO omitas ninguna funcionalidad del proyecto — cada función principal es probablemente una entidad
- Usa nombres en español (singular, CamelCase para la entidad)
- Incluye los campos reales según los requisitos (no genéricos)
- Sin límite de entidades — genera todas las que el proyecto necesite

CRITICO — NOMBRES EN ASCII PURO (Angular falla con cualquier carácter especial):
Los nombres de CAMPOS y TABLAS deben usar SOLO letras ASCII (a-z, A-Z), números (0-9) y guion bajo (_).
NUNCA uses: ñ, á, é, í, ó, ú, ü, à, è ni ningún acento o tilde en nombres de campo o tabla.
Regla de transliteración obligatoria: ñ→n, á→a, é→e, í→i, ó→o, ú→u
CORRECTO: tamano_bytes, descripcion, numero_serie, codigo_analisis, tipo_funcion
INCORRECTO: tamaño_bytes, descripción, número_serie, código_análisis, tipo_función

Responde SOLO con este formato exacto (texto plano, sin explicaciones):
ENTIDAD: NombreEntidad
TABLA: nombre_tabla_plural
CAMPOS: id (BIGINT AUTO_INCREMENT PK), campo1 (VARCHAR(200) NOT NULL), campo2 (TEXT), fecha_creacion (DATETIME DEFAULT CURRENT_TIMESTAMP)
RUTA_API: /api/nombre_plural

ENTIDAD: OtraEntidad
TABLA: otras_entidades
CAMPOS: ...
RUTA_API: /api/otras_entidades"""

    try:
        # gemini-2.5-pro thinking: ~4-6k tokens internos + ~4k para la lista de entidades
        resp = _call_chain(_REASONING_CHAIN, prompt, max_tokens=12000, json_mode=False)
        log.info(f"[Generador] Entidades extraidas:\n{resp}")
        return resp.strip()
    except Exception as e:
        log.warning(f"[Generador] No se pudieron extraer entidades: {e}")
        return ""


# ── Fase 1.5: Análisis de patrones UI ────────────────────────────────────────

def _analizar_patrones_ui(contexto: str, entidades: str) -> str:
    """
    Fase 1.5: Lee los casos de uso y entidades para detectar qué tipo de UI
    necesita cada feature principal del proyecto y qué librerías npm se requieren.
    Detecta: gráficas (Chart.js), upload de archivos, formularios científicos,
    layouts de comparación, tablas de administración.
    """
    prompt = f"""Eres un arquitecto frontend Angular 18. Lee los casos de uso y entidades.
Diseña la arquitectura de componentes: qué componentes crear, qué UI necesita cada uno,
qué librerías adicionales se requieren.

PROYECTO Y CASOS DE USO:
{contexto[:7000]}

ENTIDADES DETECTADAS:
{entidades[:2000]}

Responde EXACTAMENTE en este formato (texto plano, sin explicaciones adicionales):

NOMBRE_COMPONENTE: NombreDescriptivo
RUTA: /ruta-kebab
ARCHIVO: nombre-kebab.component
ENTIDADES: Entidad1, Entidad2
UI_TIPO: tabla | upload_archivos | chart_linea | form_cientifico | tabla_resultados | layout_comparacion | admin_tabla
UI_DETALLE: descripcion breve de la UI especifica

NOMBRE_COMPONENTE: OtroComponente
RUTA: /otra-ruta
ARCHIVO: otro-componente.component
ENTIDADES: OtraEntidad
UI_TIPO: chart_linea
UI_DETALLE: descripcion

LIBRERIA_CHARTS: si | no
LIBRERIA_UPLOAD: si | no

Reglas de deteccion (aplica TODAS):
- Palabras graficar/grafica/visualizar/espectro/chart/plot en casos de uso -> UI_TIPO: chart_linea + LIBRERIA_CHARTS: si
- Palabras cargar/subir/archivo/upload/drag/drop/fichero -> UI_TIPO: upload_archivos + LIBRERIA_UPLOAD: si
- Palabras analisis/similitud/tolerancia/rango/buscar -> UI_TIPO: form_cientifico
- Palabras comparar lado a lado/superponer/dos espectros -> UI_TIPO: layout_comparacion
- Palabras admin/usuarios/roles/estado/panel/administracion -> UI_TIPO: admin_tabla
- Maximo 6 componentes — agrupa funcionalidades relacionadas
- NO incluyas autenticacion/login en los componentes"""

    try:
        # 8000 tokens: el modelo de razonamiento consume ~4-6k internos antes de responder
        resp = _call_chain(_REASONING_CHAIN, prompt, max_tokens=8000, json_mode=False)
        resp_limpio = resp.strip()
        if resp_limpio and len(resp_limpio) > 60:
            log.info(f"[Fase 1.5] Plan UI detectado:\n{resp_limpio}")
            return resp_limpio
        # El AI respondió vacío o muy corto → caer en heurística de palabras clave
        log.warning("[Fase 1.5] Respuesta AI vacía/insuficiente — usando deteccion heuristica")
    except Exception as e:
        log.warning(f"[Fase 1.5] Fallo llamada AI: {e} — usando deteccion heuristica")

    return _heuristica_ui(contexto, entidades)


def _heuristica_ui(contexto: str, entidades: str) -> str:
    """Detección de patrones UI por palabras clave cuando el AI no responde.
    Retorna texto en el mismo formato que _analizar_patrones_ui para que
    _parsear_plan_ui lo procese igual, pero sin definiciones de componentes
    (se usa la arquitectura monolítica con librerías correctas)."""
    texto = (contexto + "\n" + entidades).lower()

    charts  = any(w in texto for w in [
        'graficar', 'grafica', 'gráfica', 'espectro', 'chart', 'plot',
        'visualizar', 'visualizacion', 'curva', 'diagrama', 'grafico', 'gráfico'
    ])
    upload  = any(w in texto for w in [
        'subir', 'cargar archivo', 'upload', 'drag', 'drop',
        'seleccionar archivo', 'importar archivo', '.dpt', '.xlsx archivo'
    ])
    lineas: list[str] = []
    lineas.append(f"LIBRERIA_CHARTS: {'si' if charts else 'no'}")
    lineas.append(f"LIBRERIA_UPLOAD: {'si' if upload else 'no'}")
    resultado = "\n".join(lineas)
    log.info(f"[Fase 1.5 heuristica] {resultado}")
    return resultado


def _parsear_plan_ui(plan_texto: str) -> dict:
    """Convierte el texto del plan UI en un dict estructurado.
    Retorna: {componentes: list, necesita_charts: bool, necesita_upload: bool}"""
    resultado: dict = {
        "componentes": [],
        "necesita_charts": False,
        "necesita_upload": False,
    }
    if not plan_texto:
        return resultado

    if re.search(r'LIBRERIA_CHARTS\s*:\s*si', plan_texto, re.IGNORECASE):
        resultado["necesita_charts"] = True
    if re.search(r'LIBRERIA_UPLOAD\s*:\s*si', plan_texto, re.IGNORECASE):
        resultado["necesita_upload"] = True

    # Cada bloque de componente empieza con NOMBRE_COMPONENTE:
    bloques = re.split(r'(?=NOMBRE_COMPONENTE\s*:)', plan_texto, flags=re.IGNORECASE)
    for bloque in bloques:
        if not re.search(r'NOMBRE_COMPONENTE\s*:', bloque, re.IGNORECASE):
            continue
        comp: dict = {}
        for campo in ['NOMBRE_COMPONENTE', 'RUTA', 'ARCHIVO', 'ENTIDADES', 'UI_TIPO', 'UI_DETALLE']:
            m = re.search(rf'{campo}\s*:\s*(.+)', bloque, re.IGNORECASE)
            if m:
                comp[campo.lower()] = m.group(1).strip()
        if comp.get('nombre_componente'):
            resultado["componentes"].append(comp)

    return resultado


def _generar_routes_ts(componentes: list) -> str:
    """Genera el contenido TypeScript de app.routes.ts basado en los componentes del plan UI.
    Fallback: ruta unica a MainComponent si no hay componentes."""
    if not componentes:
        return (
            "import { Routes } from '@angular/router';\n"
            "export const routes: Routes = [\n"
            "  { path: '', loadComponent: () => "
            "import('./components/main/main.component').then(m => m.MainComponent) },\n"
            "  { path: '**', redirectTo: '' }\n"
            "];"
        )

    lineas: list[str] = []
    primera_ruta = ""
    for i, comp in enumerate(componentes):
        ruta       = comp.get('ruta', f'feature-{i}').lstrip('/')
        archivo    = comp.get('archivo', f'feature-{i}.component').replace('.component', '')
        nombre     = comp.get('nombre_componente', f'Feature{i}')
        class_name = ''.join(w.capitalize() for w in re.split(r'[\s_\-]+', nombre)) + 'Component'
        segmentos  = ruta.split('/')
        folder     = segmentos[0] if segmentos else 'features'
        path_imp   = f"./components/{folder}/{archivo}.component"
        lineas.append(
            f"  {{ path: '{ruta}', "
            f"loadComponent: () => import('{path_imp}').then(m => m.{class_name}) }}"
        )
        if i == 0:
            primera_ruta = ruta

    lineas.append(f"  {{ path: '', redirectTo: '{primera_ruta}', pathMatch: 'full' }}")
    lineas.append(f"  {{ path: '**', redirectTo: '{primera_ruta}' }}")

    return (
        "import { Routes } from '@angular/router';\n"
        "export const routes: Routes = [\n"
        + ",\n".join(lineas)
        + "\n];"
    )


# ── Formato JSON para la generación de código ────────────────────────────────

_FORMATO_COMUN = """\
RESPUESTA: solo JSON → {"files":[{"section":"frontend|backend|database","path":"ruta/archivo","lines":["línea1","línea2"]}]}
Reglas críticas: código completo sin TODO/placeholders; sin triple-backtick dentro del JSON; MySQL+PyMySQL (nunca SQLite); Angular 18 STANDALONE sin NgModule; frontend→http://localhost:8000
⚠️ RUTAS BACKEND OBLIGATORIAS: main.py, database.py, models.py, schemas.py, crud.py, router.py van SIEMPRE en la raíz (sin prefijo src/ ni carpeta). NUNCA uses src/crud.py, src/router.py, src/models.py u otros subdirectorios para archivos backend."""


def _prompt_backend_infra(contexto: str, entidades: str) -> str:
    """Parte 1 del backend: main, database, models, schemas, requirements, .env, schema.sql"""
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

ENTIDADES REALES DEL PROYECTO:
{entidades}

{_FORMATO_COMUN}

Genera exactamente estos 7 archivos. ⚠️ USA los nombres reales de las entidades, no nombres genéricos.

── ARCHIVO 1: main.py (section="backend") ──
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import engine, Base
from router import router

app = FastAPI(title="API del Proyecto")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
Base.metadata.create_all(bind=engine)
app.include_router(router)  # CRITICO: NUNCA comentar esta línea — sin ella todos los endpoints devuelven 404

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

── ARCHIVO 2: database.py (section="backend") ── copia EXACTAMENTE:
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Admin1234!@localhost/app_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

── ARCHIVO 3: models.py (section="backend") ──
Una clase SQLAlchemy por CADA entidad real (hereda de Base).
- __tablename__ = tabla en snake_case
- id = Column(Integer, primary_key=True, autoincrement=True, index=True)
- Usa Column con: String(200), Integer, Text, Boolean, Float
- Fechas: Column(DateTime, default=func.now()) — importar func de sqlalchemy.sql
- CRITICO: nombres de atributos y columnas SOLO en ASCII (a-z, 0-9, _). PROHIBIDO ñ, á, é, í, ó, ú.
  INCORRECTO: tamaño_bytes  → CORRECTO: tamano_bytes
  INCORRECTO: descripción   → CORRECTO: descripcion
- CRITICO: NUNCA uses "metadata" como nombre de columna — es un atributo reservado de SQLAlchemy
  y lanza InvalidRequestError al arrancar. Usa "metadatos", "info_adicional" o "datos_extra".
  INCORRECTO: metadata = Column(JSON)  → CORRECTO: metadatos = Column(JSON)

── ARCHIVO 4: schemas.py (section="backend") ──
TRES clases Pydantic v2 por cada entidad real:
  XxxBase(BaseModel): campos sin id (usa Optional[datetime] para fechas, NO str)
  XxxCreate(XxxBase): solo "pass"
  XxxResponse(XxxBase): id: int + model_config = ConfigDict(from_attributes=True)
Imports necesarios: from pydantic import BaseModel, ConfigDict; from datetime import datetime; from typing import Optional
⚠️ NUNCA orm_mode. NUNCA str para datetime. SIEMPRE define XxxCreate.

── ARCHIVO 5: requirements.txt (section="backend") ──
fastapi
uvicorn[standard]
sqlalchemy
pymysql
python-dotenv
pydantic

── ARCHIVO 6: .env (section="backend") ──
DATABASE_URL=mysql+pymysql://root:Admin1234!@localhost/app_db

── ARCHIVO 7: schema.sql (section="database") ──
REGLAS CRÍTICAS DE SINTAXIS MySQL — sigue el ejemplo EXACTAMENTE:

• NUNCA uses CREATE DATABASE ni USE
• Usa backticks en nombres de tabla y columna: `tabla`, `columna`
• Palabras reservadas como columnas SIEMPRE con backtick: `key`, `type`, `status`, `order`, `name`
• VARCHAR siempre con longitud: VARCHAR(255)
• DECIMAL siempre con precisión: DECIMAL(10,2)
• NUNCA dejes coma en la última columna antes del cierre )
• Termina CADA sentencia con ;
• CRITICO: nombres de columnas SOLO en ASCII (a-z, 0-9, _). NUNCA ñ, á, é, í, ó, ú.
  INCORRECTO: `tamaño_bytes`  → CORRECTO: `tamano_bytes`
  INCORRECTO: `descripción`   → CORRECTO: `descripcion`

EJEMPLO CORRECTO (copia esta estructura para cada entidad real):

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `espectros`;
CREATE TABLE `espectros` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(255) NOT NULL,
  `tipo` VARCHAR(100) DEFAULT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `fecha_creacion` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

Genera UNA tabla por cada entidad real con sus campos reales.
NO incluyas INSERT INTO — la base de datos debe quedar vacía para que el usuario cargue sus propios datos."""


def _prompt_backend_router(contexto: str, entidades: str) -> str:
    """Parte 2 del backend: crud.py + router.py con TODAS las entidades."""
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

ENTIDADES REALES DEL PROYECTO (TODAS deben tener CRUD completo):
{entidades}

{_FORMATO_COMUN}

Genera EXACTAMENTE 2 archivos. Ambos con section="backend".
⚠️ TODAS las entidades listadas arriba DEBEN aparecer en AMBOS archivos.
⚠️ NO omitas ninguna entidad. Si hay 5 entidades → 5 bloques en crud.py y 5 × 5 = 25 rutas en router.py.

═══════════════════════════════════════════
CONTRATO DE CONECTIVIDAD FRONTEND ↔ BACKEND
═══════════════════════════════════════════
El frontend Angular usará ApiService con apiUrl = 'http://localhost:8000/api'.
Los paths del router FastAPI DEBEN coincidir EXACTAMENTE con los que el frontend llamará:

  Entidad "Zeolita" → paths del router: /zeolitas, /zeolitas/{{id}}
  Entidad "EspectroFtir" → paths del router: /espectros_ftir, /espectros_ftir/{{id}}

Reglas de naming de paths:
• SIEMPRE snake_case plural: EspectroFtir → /espectros_ftir, ResultadoBusqueda → /resultados_busqueda
• NUNCA CamelCase en paths: /EspectrosFtir está PROHIBIDO
• La función de lista devuelve List[XxxResponse] — NUNCA un objeto con wrapper {{data: [...]}}
• La función de item individual devuelve XxxResponse directamente — sin wrapper
• Los campos en XxxResponse DEBEN coincidir exactamente con los campos del modelo SQLAlchemy

REGLA CRITICA DE SCHEMAS — incumplir esto causa AttributeError en Python:
La clase XxxUpdate NO EXISTE. schemas.py solo define XxxBase, XxxCreate y XxxResponse.
Para el endpoint PUT usa SIEMPRE schemas.XxxCreate, igual que el POST.
INCORRECTO: data: schemas.UsuarioUpdate  → CORRECTO: data: schemas.UsuarioCreate
En crud.py: update_xxx(db, id, data: schemas.XxxCreate) — NUNCA schemas.XxxUpdate.

════════════════════════════════════════════
ARCHIVO 1: crud.py
════════════════════════════════════════════
from sqlalchemy.orm import Session
import models, schemas

# Para CADA entidad real, estas 5 funciones (ajusta los nombres):
def get_all_zeolitas(db: Session):
    return db.query(models.Zeolita).all()

def get_zeolita(db: Session, item_id: int):
    return db.query(models.Zeolita).filter(models.Zeolita.id == item_id).first()

def create_zeolita(db: Session, data: schemas.ZeolitaCreate):
    item = models.Zeolita(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item); return item

def update_zeolita(db: Session, item_id: int, data: schemas.ZeolitaCreate):
    item = db.query(models.Zeolita).filter(models.Zeolita.id == item_id).first()
    if not item: return None
    for k, v in data.model_dump().items(): setattr(item, k, v)
    db.commit(); db.refresh(item); return item

def delete_zeolita(db: Session, item_id: int):
    item = db.query(models.Zeolita).filter(models.Zeolita.id == item_id).first()
    if not item: return False
    db.delete(item); db.commit(); return True

# REPITE ESTE BLOQUE para cada entidad adicional del proyecto.

════════════════════════════════════════════
ARCHIVO 2: router.py
════════════════════════════════════════════
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import crud
# Importa TODOS los schemas (XxxCreate y XxxResponse por cada entidad):
from schemas import (
    ZeolitaCreate, ZeolitaResponse,
    # ... un par por cada entidad real del proyecto
)

router = APIRouter(prefix="/api")

# Para CADA entidad real, estas 5 rutas (ajusta nombres y paths):
@router.get("/zeolitas", response_model=List[ZeolitaResponse])
def list_zeolitas(db: Session = Depends(get_db)):
    return crud.get_all_zeolitas(db)

@router.get("/zeolitas/{{item_id}}", response_model=ZeolitaResponse)
def get_zeolita(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_zeolita(db, item_id)
    if not item: raise HTTPException(404, detail="No encontrado")
    return item

@router.post("/zeolitas", response_model=ZeolitaResponse)
def create_zeolita(data: ZeolitaCreate, db: Session = Depends(get_db)):
    return crud.create_zeolita(db, data)

@router.put("/zeolitas/{{item_id}}", response_model=ZeolitaResponse)
def update_zeolita(item_id: int, data: ZeolitaCreate, db: Session = Depends(get_db)):
    item = crud.update_zeolita(db, item_id, data)
    if not item: raise HTTPException(404, detail="No encontrado")
    return item

@router.delete("/zeolitas/{{item_id}}")
def delete_zeolita(item_id: int, db: Session = Depends(get_db)):
    if not crud.delete_zeolita(db, item_id): raise HTTPException(404, detail="No encontrado")
    return {{"ok": True}}

# REPITE LAS 5 RUTAS para cada entidad adicional. CADA entidad DEBE tener sus 5 rutas."""


def _prompt_frontend_core(contexto: str, entidades: str, ui_plan: dict | None = None) -> str:
    # Cuando hay arquitectura multicomponente, usar rutas fallback en Fase 3.
    # La Fase 4 (_prompt_ui_multicomponente) generará el app.routes.ts definitivo
    # con los nombres REALES de los archivos que Gemini crea, evitando el mismatch
    # donde app.routes.ts apunta a archivos que no existen.
    tiene_multi = bool(ui_plan and ui_plan.get('componentes'))
    routes_content = _generar_routes_ts([])  # Siempre fallback — Fase 4 lo sobreescribe si aplica
    # Dependencia condicional de Chart.js
    chart_dep = (
        '\n    "chart.js": "^4.4.0",'
        if (ui_plan and ui_plan.get('necesita_charts')) else ''
    )
    _ = tiene_multi  # usado para referencia futura
    return f"""Eres un arquitecto de software senior. Especificación del proyecto:

{contexto}

ENTIDADES DEL PROYECTO (úsalas con sus nombres REALES, no genéricos):
{entidades}

{_FORMATO_COMUN}

Genera exactamente estos 13 archivos de infraestructura y lógica del FRONTEND (Angular 18 STANDALONE).
Todos con section="frontend".

════════════════════
ARCHIVOS LÓGICOS (dependen de las entidades):
════════════════════

1. src/app/models/interfaces.ts
   Una interfaz TypeScript por cada entidad real. Ejemplo:
   export interface Zeolita {{ id: number; nombre: string; descripcion?: string; }}
   Usa los nombres de campo reales de las ENTIDADES arriba.

2. src/app/services/api.service.ts
   ⚠️ USA ÚNICAMENTE "any" en todos los genéricos de Observable — NUNCA uses nombres de tipo (Zeolita, Espectro, etc.)
   porque generaría errores TS2304 al no encontrar el nombre.

   ═══════════════════════════════════════════
   CONTRATO DE CONECTIVIDAD FRONTEND ↔ BACKEND
   ═══════════════════════════════════════════
   El backend FastAPI expone rutas en http://localhost:8000/api con prefix="/api".
   Los paths que uses aquí DEBEN ser snake_case plural y coincidir con router.py:
     Entidad "Zeolita"       → path: /zeolitas
     Entidad "EspectroFtir"  → path: /espectros_ftir
     Entidad "ResultadoBusqueda" → path: /resultados_busqueda
   NUNCA uses CamelCase en los paths: `/EspectrosFtir` es incorrecto.
   El apiUrl ya incluye /api, así que el path de cada método NO debe repetirlo.

   Estructura EXACTA del archivo:
   import {{ Injectable }} from '@angular/core';
   import {{ HttpClient }} from '@angular/common/http';
   import {{ Observable }} from 'rxjs';

   @Injectable({{ providedIn: 'root' }})
   export class ApiService {{
     private apiUrl = 'http://localhost:8000/api';
     constructor(private http: HttpClient) {{}}

     // REGLA CRITICA DE NOMBRES (violarla causa errores TypeScript TS2554/TS2551):
     // • getXxxs()          → CERO argumentos, devuelve Observable<any[]> → getter de LISTA
     // • getXxx(id: number) → UN argumento,    devuelve Observable<any>   → getter de ITEM
     // • cargarXxxs() en el componente SIEMPRE llama getXxxs() sin argumento
     // • NUNCA definas getXxxs(id: number) ni getXxx() — la firma debe ser exacta
     // • Pluralización: ResultadoSimilitud → lista: getResultadosSimilitudes(), single: getResultadoSimilitud(id)
     //   Espectro → lista: getEspectros(), single: getEspectro(id)

     // Para CADA entidad real, exactamente estos 5 métodos con "any" en TODOS los genéricos:
     getZeolitas(): Observable<any[]>             {{ return this.http.get<any[]>(`${{this.apiUrl}}/zeolitas`); }}
     getZeolita(id: number): Observable<any>      {{ return this.http.get<any>(`${{this.apiUrl}}/zeolitas/${{id}}`); }}
     createZeolita(d: any): Observable<any>       {{ return this.http.post<any>(`${{this.apiUrl}}/zeolitas`, d); }}
     updateZeolita(id: number, d: any): Observable<any> {{ return this.http.put<any>(`${{this.apiUrl}}/zeolitas/${{id}}`, d); }}
     deleteZeolita(id: number): Observable<any>   {{ return this.http.delete<any>(`${{this.apiUrl}}/zeolitas/${{id}}`); }}
     // Repite los 5 métodos para CADA entidad real. SIEMPRE Observable<any> o Observable<any[]>.
     // VERIFICA que cada path aquí coincida exactamente con las rutas del router.py del backend.
   }}

════════════════════
ARCHIVOS FIJOS (contenido EXACTO, no modificar):
════════════════════

3. src/app/app.component.ts
import {{ Component }} from '@angular/core';
import {{ RouterOutlet }} from '@angular/router';
@Component({{ selector: 'app-root', standalone: true, imports: [RouterOutlet], template: '<router-outlet />' }})
export class AppComponent {{ title = 'frontend'; }}

4. src/app/app.routes.ts — copia EXACTAMENTE:
{routes_content}

5. src/app/app.config.ts
import {{ ApplicationConfig, provideZoneChangeDetection }} from '@angular/core';
import {{ provideRouter }} from '@angular/router';
import {{ provideHttpClient }} from '@angular/common/http';
import {{ routes }} from './app.routes';
export const appConfig: ApplicationConfig = {{
  providers: [
    provideZoneChangeDetection({{ eventCoalescing: true }}),
    provideRouter(routes),
    provideHttpClient()
  ]
}};

6. src/environments/environment.ts
export const environment = {{ production: false, apiUrl: 'http://localhost:8000/api' }};

7. src/main.ts
import 'zone.js';
import {{ bootstrapApplication }} from '@angular/platform-browser';
import {{ AppComponent }} from './app/app.component';
import {{ appConfig }} from './app/app.config';
bootstrapApplication(AppComponent, appConfig).catch(err => console.error(err));

8. src/index.html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sistema de Gestión</title>
  <base href="/">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body><app-root></app-root></body>
</html>

9. src/styles.css
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth;-webkit-text-size-adjust:100%}}
body{{height:100%;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;background:#f1f5f9;color:#0f172a}}
::-webkit-scrollbar{{width:6px;height:6px}}
::-webkit-scrollbar-track{{background:#f1f5f9}}
::-webkit-scrollbar-thumb{{background:#cbd5e1;border-radius:3px}}
::-webkit-scrollbar-thumb:hover{{background:#94a3b8}}

10. package.json
{{
  "name": "frontend",
  "version": "0.0.0",
  "scripts": {{ "ng": "ng", "start": "ng serve", "build": "ng build", "test": "ng test" }},
  "private": true,
  "dependencies": {{
    "@angular/animations": "^18.0.0",
    "@angular/common": "^18.0.0",
    "@angular/compiler": "^18.0.0",
    "@angular/core": "^18.0.0",
    "@angular/forms": "^18.0.0",
    "@angular/platform-browser": "^18.0.0",
    "@angular/platform-browser-dynamic": "^18.0.0",
    "@angular/router": "^18.0.0",
    "rxjs": "~7.8.0",{chart_dep}
    "tslib": "^2.3.0",
    "zone.js": "~0.14.0"
  }},
  "devDependencies": {{
    "@angular-devkit/build-angular": "^18.0.0",
    "@angular/cli": "^18.0.0",
    "@angular/compiler-cli": "^18.0.0",
    "typescript": "~5.4.0"
  }}
}}

11. angular.json — usa EXACTAMENTE:
{_ANGULAR_JSON_TEMPLATE}

12. tsconfig.json — usa EXACTAMENTE:
{_TSCONFIG_TEMPLATE}

13. tsconfig.app.json — usa EXACTAMENTE:
{_TSCONFIG_APP_TEMPLATE}"""


_TSCONFIG_TEMPLATE = """\
   {
     "compileOnSave": false,
     "compilerOptions": {
       "outDir": "./out-tsc/app",
       "sourceMap": true,
       "declaration": false,
       "experimentalDecorators": true,
       "emitDecoratorMetadata": true,
       "moduleResolution": "bundler",
       "module": "ES2022",
       "target": "ES2022",
       "useDefineForClassFields": false,
       "strict": false,
       "lib": ["ES2022", "dom", "dom.iterable"],
       "skipLibCheck": true
     }
   }"""

_TSCONFIG_APP_TEMPLATE = """\
   {
     "extends": "./tsconfig.json",
     "compilerOptions": {
       "outDir": "./out-tsc/app",
       "types": []
     },
     "files": ["src/main.ts"],
     "include": ["src/**/*.d.ts"]
   }"""

_ANGULAR_JSON_TEMPLATE = """\
   {
     "version": 1,
     "newProjectRoot": "projects",
     "projects": {
       "frontend": {
         "projectType": "application",
         "root": "",
         "sourceRoot": "src",
         "prefix": "app",
         "architect": {
           "build": {
             "builder": "@angular-devkit/build-angular:application",
             "options": {
               "outputPath": "dist/frontend",
               "index": "src/index.html",
               "browser": "src/main.ts",
               "tsConfig": "tsconfig.app.json",
               "styles": ["src/styles.css"],
               "scripts": [],
               "assets": []
             },
             "configurations": {
               "production": { "optimization": true },
               "development": { "optimization": false }
             },
             "defaultConfiguration": "development"
           },
           "serve": {
             "builder": "@angular-devkit/build-angular:dev-server",
             "configurations": {
               "production": { "buildTarget": "frontend:build:production" },
               "development": { "buildTarget": "frontend:build:development" }
             },
             "defaultConfiguration": "development"
           }
         }
       }
     }
   }"""


# CSS profesional hardcodeado — no se delega a la IA para garantizar calidad consistente.
# Es el mismo CSS que produce el dashboard con sidebar oscuro, tabla con header gradiente,
# modal con backdrop blur, spinner, toast y responsive.
_COMPONENT_CSS = """\
:root{--primary:#6366f1;--primary-dark:#4f46e5;--primary-light:#e0e7ff;--sidebar-bg:#0f172a;--sidebar-text:#94a3b8;--sidebar-hover:rgba(255,255,255,.08);--sidebar-border:rgba(255,255,255,.1);--bg:#f1f5f9;--surface:#ffffff;--border:#e2e8f0;--text:#0f172a;--text-muted:#64748b;--danger:#ef4444;--success:#10b981;--radius:12px;--shadow:0 1px 3px rgba(0,0,0,.1),0 1px 2px rgba(0,0,0,.06);--shadow-md:0 4px 6px rgba(0,0,0,.07),0 2px 4px rgba(0,0,0,.06);--shadow-lg:0 10px 15px rgba(0,0,0,.1),0 4px 6px rgba(0,0,0,.05)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.app-layout{display:flex;height:100vh;overflow:hidden;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg)}
.sidebar{width:260px;min-width:260px;background:var(--sidebar-bg);display:flex;flex-direction:column;height:100vh;overflow-y:auto;position:relative;z-index:10;flex-shrink:0}
.sidebar-brand{display:flex;align-items:center;gap:12px;padding:22px 20px;border-bottom:1px solid var(--sidebar-border)}
.brand-dot{width:10px;height:10px;background:var(--primary);border-radius:50%;flex-shrink:0;box-shadow:0 0 0 3px rgba(99,102,241,.3)}
.brand-name{font-size:15px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.2px}
.sidebar-nav{flex:1;padding:16px 10px;display:flex;flex-direction:column;gap:3px}
.nav-section-label{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1.2px;color:var(--sidebar-text);opacity:.45;padding:10px 10px 6px;display:block}
.nav-item{display:flex;align-items:center;padding:10px 16px;border-radius:9px;color:var(--sidebar-text);cursor:pointer;transition:all .15s ease;border:none;background:none;width:100%;text-align:left;font-size:14px;font-weight:500;font-family:inherit;text-decoration:none}
.nav-item:hover{background:var(--sidebar-hover);color:#e2e8f0}
.nav-item.active{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;box-shadow:0 3px 10px rgba(99,102,241,.45)}
.sidebar-footer{padding:14px 20px;border-top:1px solid var(--sidebar-border);font-size:11px;color:var(--sidebar-text);opacity:.5;text-align:center}
.main-content{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:64px;min-height:64px;background:var(--surface);border-bottom:1px solid var(--border);box-shadow:var(--shadow);flex-shrink:0}
.topbar-left{display:flex;align-items:center;gap:12px}
.page-title{font-size:18px;font-weight:700;color:var(--text);letter-spacing:-.3px}
.record-count{background:var(--primary-light);color:var(--primary-dark);font-size:12px;font-weight:700;padding:3px 12px;border-radius:999px;letter-spacing:.3px}
.topbar-right{display:flex;align-items:center;gap:12px}
.search-input{padding:9px 16px;border:1.5px solid var(--border);border-radius:9px;font-size:14px;background:var(--bg);color:var(--text);width:240px;transition:all .2s;outline:none;font-family:inherit}
.search-input:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.15);background:var(--surface)}
.search-input::placeholder{color:#a0aec0}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 20px;border-radius:9px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:all .18s ease;font-family:inherit;line-height:1;white-space:nowrap}
.btn-primary{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;box-shadow:0 2px 6px rgba(99,102,241,.35)}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 5px 14px rgba(99,102,241,.45)}
.btn-primary:active{transform:translateY(0)}
.btn-secondary{background:var(--surface);color:var(--text);border:1.5px solid var(--border)}
.btn-secondary:hover{background:#f8fafc;border-color:#cbd5e1}
.btn-icon{padding:7px 11px;font-size:14px;border-radius:8px;line-height:1}
.btn-edit{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe}
.btn-edit:hover{background:#dbeafe;transform:translateY(-1px)}
.btn-delete{background:#fef2f2;color:var(--danger);border:1px solid #fecaca}
.btn-delete:hover{background:#fee2e2;transform:translateY(-1px)}
.content-area{flex:1;overflow-y:auto;padding:28px;background:var(--bg)}
.content-section{animation:fadeIn .25s ease}
.table-card{background:var(--surface);border-radius:var(--radius);border:1px solid var(--border);box-shadow:var(--shadow-md);overflow:hidden}
.table-card-header{padding:16px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#f8fafc 0%,var(--surface) 100%)}
.table-card-title{font-size:14px;font-weight:700;color:var(--text)}
.table-count{font-size:12px;color:var(--text-muted);font-weight:500}
.data-table{width:100%;border-collapse:collapse}
.data-table thead tr{background:linear-gradient(135deg,var(--primary) 0%,var(--primary-dark) 100%)}
.data-table thead th{padding:13px 18px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:rgba(255,255,255,.92);white-space:nowrap}
.data-table tbody tr{border-bottom:1px solid #f1f5f9;transition:background .12s ease}
.data-table tbody tr:last-child{border-bottom:none}
.data-table tbody tr:hover{background:#f8fafc}
.data-table tbody td{padding:14px 18px;font-size:14px;color:var(--text);vertical-align:middle}
.cell-id{font-weight:700;color:var(--text-muted);font-size:12px;width:40px}
.actions-cell{display:flex;gap:8px;align-items:center}
.loading-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;gap:18px;color:var(--text-muted);font-size:14px}
.spinner{width:44px;height:44px;border:3px solid var(--primary-light);border-top-color:var(--primary);border-radius:50%;animation:spin .75s linear infinite}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;gap:14px;text-align:center}
.empty-title{font-size:17px;font-weight:700;color:var(--text)}
.empty-desc{font-size:14px;color:var(--text-muted);max-width:300px}
.modal-overlay{position:fixed;inset:0;z-index:200;background:rgba(15,23,42,.55);backdrop-filter:blur(5px);-webkit-backdrop-filter:blur(5px);display:flex;align-items:center;justify-content:center;padding:20px;animation:fadeIn .18s ease}
.modal-dialog{background:var(--surface);border-radius:18px;width:100%;max-width:580px;max-height:92vh;display:flex;flex-direction:column;box-shadow:0 28px 60px rgba(0,0,0,.28);animation:slideUp .22s cubic-bezier(.34,1.56,.64,1)}
.modal-header{display:flex;align-items:center;justify-content:space-between;padding:22px 26px;border-bottom:1px solid var(--border);background:linear-gradient(135deg,#f8fafc,var(--surface));border-radius:18px 18px 0 0}
.modal-title{font-size:16px;font-weight:700;color:var(--text)}
.modal-close{width:34px;height:34px;border-radius:9px;border:none;background:var(--bg);color:var(--text-muted);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;transition:all .15s;font-family:inherit;line-height:1}
.modal-close:hover{background:#fee2e2;color:var(--danger)}
.modal-body{padding:26px;overflow-y:auto;flex:1}
.modal-footer{display:flex;justify-content:flex-end;gap:10px;padding:18px 26px;border-top:1px solid var(--border);background:#f8fafc;border-radius:0 0 18px 18px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.form-group{display:flex;flex-direction:column;gap:7px}
.form-group.full-width{grid-column:1/-1}
.form-label{font-size:13px;font-weight:600;color:var(--text-muted);letter-spacing:.2px}
.form-control{padding:10px 13px;border:1.5px solid var(--border);border-radius:9px;font-size:14px;color:var(--text);background:var(--surface);outline:none;transition:all .18s;width:100%;font-family:inherit}
.form-control:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.15)}
.form-control::placeholder{color:#a0aec0}
textarea.form-control{resize:vertical;min-height:88px;line-height:1.5}
select.form-control{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%2364748b' d='M6 8L0 0h12z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 13px center;padding-right:36px;cursor:pointer}
.toast{position:fixed;bottom:28px;right:28px;z-index:9999;display:flex;align-items:center;gap:14px;padding:15px 22px;border-radius:12px;min-width:300px;max-width:420px;box-shadow:0 8px 24px rgba(0,0,0,.18);animation:slideIn .3s cubic-bezier(.34,1.56,.64,1);font-size:14px;font-weight:600}
.toast-exito{background:#ecfdf5;color:#065f46;border-left:4px solid var(--success)}
.toast-error{background:#fef2f2;color:#991b1b;border-left:4px solid var(--danger)}
.toast-label{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;flex-shrink:0;opacity:.75}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{opacity:0;transform:translateY(24px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes slideIn{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:translateX(0)}}
@media (max-width:768px){.sidebar{display:none}.form-grid{grid-template-columns:1fr}.search-input{width:160px}.content-area{padding:16px}}"""


def _prompt_frontend_componentes(contexto: str, entidades: str) -> str:
    return f"""Eres un experto en Angular 18, UI moderna y diseño de dashboards profesionales. Proyecto:

{contexto}

ENTIDADES — usa EXACTAMENTE estos nombres (sin genéricos):
{entidades}

{_FORMATO_COMUN}

Genera EXACTAMENTE 3 archivos (section="frontend"). Código REAL, COMPLETO y funcional — sin TODO ni placeholders.

══════════════════════════════════════════════════════════════════
ARCHIVO 1 — src/app/components/main/main.component.ts
══════════════════════════════════════════════════════════════════

IMPORTS — copia EXACTAMENTE estas 4 líneas (rutas y módulos fijos):
import {{ Component, OnInit }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';
import {{ FormsModule }} from '@angular/forms';
import {{ ApiService }} from '../../services/api.service';

@Component({{
  selector: 'app-main', standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.css']
}})
export class MainComponent implements OnInit {{

  constructor(private api: ApiService) {{}}

  /* ── Una propiedad any[] = [] por cada entidad real ─────────────────
     Ejemplo si las entidades son Espectro, Archivo, Comparacion:
       espectros: any[] = [];
       archivos: any[] = [];
       comparaciones: any[] = [];
     IMPORTANTE: el nombre PLURAL en camelCase debe coincidir EXACTAMENTE
     con el que uses en seccionActiva, *ngIf y *ngFor del template.     ──────────────────────────────────────────────────────────────── */

  itemActual: any = {{}};
  editando = false;
  editandoId: number | null = null;
  mostrarModal = false;
  cargando = false;
  busqueda = '';
  toast: {{ mensaje: string; tipo: 'exito' | 'error' }} | null = null;

  /* seccionActiva: PLURAL EN MINÚSCULAS de la primera entidad real.
     Ejemplo: 'espectros'  (NO 'Espectros', NO 'espectro')  */
  seccionActiva = 'PRIMERA_ENTIDAD_PLURAL_MINUSCULAS';

  /* Devuelve el array de la sección activa → usado en el badge de conteo.
     Rellena con un case por cada entidad real. */
  getRegistrosActuales(): any[] {{
    switch (this.seccionActiva) {{
      /* case 'espectros': return this.espectros;
         case 'archivos':  return this.archivos;
         case 'comparaciones': return this.comparaciones; */
      default: return [];
    }}
  }}

  ngOnInit(): void {{
    /* Llama a cargar<Entidad>() de cada entidad.
       Ejemplo: this.cargarEspectros(); this.cargarArchivos(); */
  }}

  mostrarToast(mensaje: string, tipo: 'exito' | 'error'): void {{
    this.toast = {{ mensaje, tipo }};
    setTimeout(() => this.toast = null, 3500);
  }}

  abrirModal(item?: any): void {{
    this.itemActual = item ? {{ ...item }} : {{}};
    this.editando = !!item;
    this.editandoId = item?.id ?? null;
    this.mostrarModal = true;
  }}

  cerrarModal(): void {{
    this.mostrarModal = false;
    this.itemActual = {{}};
  }}

  guardarEntidadActual(): void {{
    /* switch(this.seccionActiva) {{ case 'espectros': this.guardarEspectro(); break; ... }} */
  }}

  eliminarEntidad(id: number): void {{
    if (!confirm('¿Eliminar este registro?')) return;
    /* switch(this.seccionActiva) {{ case 'espectros': this.eliminarEspectro(id); break; ... }} */
  }}

  /* ── Patrón para cada entidad (reemplaza <E>/e con nombres reales): ──────
     cargar<E>s(): void {{
       this.cargando = true;
       this.api.get<E>s().subscribe({{
         next: data => {{ this.<e>s = data; this.cargando = false; }},
         error: ()  => {{ this.mostrarToast('Error al cargar', 'error'); this.cargando = false; }}
       }});
     }}
     guardar<E>(): void {{
       const op = this.editando
         ? this.api.update<E>(this.editandoId!, this.itemActual)
         : this.api.create<E>(this.itemActual);
       op.subscribe({{
         next: () => {{ this.mostrarToast(this.editando ? 'Actualizado' : 'Creado', 'exito'); this.cerrarModal(); this.cargar<E>s(); }},
         error: ()  => this.mostrarToast('Error al guardar', 'error')
       }});
     }}
     eliminar<E>(id: number): void {{
       this.api.delete<E>(id).subscribe({{
         next: () => {{ this.mostrarToast('Eliminado', 'exito'); this.cargar<E>s(); }},
         error: ()  => this.mostrarToast('Error al eliminar', 'error')
       }});
     }}
  ──────────────────────────────────────────────────────────────────── */
}}

══════════════════════════════════════════════════════════════════
ARCHIVO 2 — src/app/components/main/main.component.html
══════════════════════════════════════════════════════════════════

SIN EMOJIS ni HTML entities para iconos. Usa solo texto plano, letras y signos ASCII.
NO uses emojis en ninguna parte del HTML generado.

USA esta estructura EXACTA. Reemplaza solo las partes marcadas con comentarios:

<div class="app-layout">

  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-dot"></div>
      <span class="brand-name">NOMBRE DEL PROYECTO</span>
    </div>
    <nav class="sidebar-nav">
      <span class="nav-section-label">Modulos</span>

      <!-- GENERA un <button class="nav-item"> por cada entidad real.
           Usa el MISMO string en [class.active], (click) y en seccionActiva (plural minusculas).
           Ejemplo:
           <button class="nav-item" [class.active]="seccionActiva==='espectros'"
             (click)="seccionActiva='espectros'; cargarEspectros()">Espectros</button>
           <button class="nav-item" [class.active]="seccionActiva==='archivos'"
             (click)="seccionActiva='archivos'; cargarArchivos()">Archivos</button>
      -->

    </nav>
    <div class="sidebar-footer">v1.0</div>
  </aside>

  <!-- MAIN -->
  <div class="main-content">

    <header class="topbar">
      <div class="topbar-left">
        <h1 class="page-title">{{{{seccionActiva | titlecase}}}}</h1>
        <span class="record-count">{{{{getRegistrosActuales().length}}}} registros</span>
      </div>
      <div class="topbar-right">
        <input class="search-input" type="text" [(ngModel)]="busqueda" placeholder="Buscar...">
        <button class="btn btn-primary" (click)="abrirModal()">+ Nuevo</button>
      </div>
    </header>

    <main class="content-area">

      <!-- GENERA una <section *ngIf="..."> por cada entidad real.
           CRITICO: el string en *ngIf DEBE ser IDENTICO al de seccionActiva y nav-item.
           Ejemplo para Espectros (repite para CADA entidad):

      <section *ngIf="seccionActiva==='espectros'" class="content-section">

        <div *ngIf="cargando" class="loading-state">
          <div class="spinner"></div>
          <span>Cargando...</span>
        </div>

        <div *ngIf="!cargando && espectros.length===0" class="empty-state">
          <p class="empty-title">Sin registros</p>
          <p class="empty-desc">Agrega el primer elemento para comenzar</p>
          <button class="btn btn-primary" style="margin-top:12px" (click)="abrirModal()">+ Nuevo</button>
        </div>

        <div *ngIf="!cargando && espectros.length>0" class="table-card">
          <div class="table-card-header">
            <span class="table-card-title">Espectros</span>
            <span class="table-count">{{{{espectros.length}}}} registros</span>
          </div>
          <table class="data-table">
            <thead><tr>
              <th>#</th>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Fecha</th>
              <th>Acciones</th>
            </tr></thead>
            <tbody>
              <tr *ngFor="let item of espectros">
                <td class="cell-id">{{{{item.id}}}}</td>
                <td><strong>{{{{item.nombre}}}}</strong></td>
                <td>{{{{item.tipo}}}}</td>
                <td>{{{{item.fecha_creacion | date:'dd/MM/yyyy'}}}}</td>
                <td class="actions-cell">
                  <button class="btn btn-icon btn-edit" (click)="abrirModal(item)">Editar</button>
                  <button class="btn btn-icon btn-delete" (click)="eliminarEntidad(item.id)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </section>

      Repite el bloque <section> para CADA entidad real. -->

    </main>
  </div>

  <!-- MODAL -->
  <div class="modal-overlay" *ngIf="mostrarModal" (click)="cerrarModal()">
    <div class="modal-dialog" (click)="$event.stopPropagation()">

      <div class="modal-header">
        <h2 class="modal-title">{{{{editando ? 'Editar registro' : 'Nuevo registro'}}}}</h2>
        <button class="modal-close" (click)="cerrarModal()">&times;</button>
      </div>

      <div class="modal-body">
        <!-- GENERA un <div *ngIf="seccionActiva==='x'" class="form-grid"> por entidad.
             Un <div class="form-group"> por cada campo real.
             Ejemplo:
             <div *ngIf="seccionActiva==='espectros'" class="form-grid">
               <div class="form-group">
                 <label class="form-label">Nombre</label>
                 <input class="form-control" [(ngModel)]="itemActual.nombre" placeholder="Nombre">
               </div>
               <div class="form-group">
                 <label class="form-label">Tipo</label>
                 <input class="form-control" [(ngModel)]="itemActual.tipo" placeholder="Tipo">
               </div>
               <div class="form-group full-width">
                 <label class="form-label">Descripcion</label>
                 <textarea class="form-control" [(ngModel)]="itemActual.descripcion" rows="3"></textarea>
               </div>
             </div>
        -->
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" (click)="cerrarModal()">Cancelar</button>
        <button class="btn btn-primary" (click)="guardarEntidadActual()">
          {{{{editando ? 'Guardar cambios' : 'Crear registro'}}}}
        </button>
      </div>

    </div>
  </div>

  <!-- TOAST -->
  <div class="toast" *ngIf="toast"
    [class.toast-exito]="toast.tipo==='exito'"
    [class.toast-error]="toast.tipo==='error'">
    <span class="toast-label">{{{{toast.tipo==='exito' ? 'OK' : 'Error'}}}}</span>
    <span>{{{{toast.mensaje}}}}</span>
  </div>

</div>

══════════════════════════════════════════════════════════════════
ARCHIVO 3 — src/app/components/main/main.component.css
══════════════════════════════════════════════════════════════════

COPIA ESTE CSS EXACTAMENTE Y COMPLETO — no omitas ni resumas ninguna regla.
Este CSS produce un dashboard moderno de nivel profesional:

:root{{--primary:#6366f1;--primary-dark:#4f46e5;--primary-light:#e0e7ff;--sidebar-bg:#0f172a;--sidebar-text:#94a3b8;--sidebar-hover:rgba(255,255,255,.08);--sidebar-border:rgba(255,255,255,.1);--bg:#f1f5f9;--surface:#ffffff;--border:#e2e8f0;--text:#0f172a;--text-muted:#64748b;--danger:#ef4444;--success:#10b981;--radius:12px;--shadow:0 1px 3px rgba(0,0,0,.1),0 1px 2px rgba(0,0,0,.06);--shadow-md:0 4px 6px rgba(0,0,0,.07),0 2px 4px rgba(0,0,0,.06);--shadow-lg:0 10px 15px rgba(0,0,0,.1),0 4px 6px rgba(0,0,0,.05)}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
.app-layout{{display:flex;height:100vh;overflow:hidden;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg)}}
.sidebar{{width:260px;min-width:260px;background:var(--sidebar-bg);display:flex;flex-direction:column;height:100vh;overflow-y:auto;position:relative;z-index:10;flex-shrink:0}}
.sidebar-brand{{display:flex;align-items:center;gap:12px;padding:22px 20px;border-bottom:1px solid var(--sidebar-border)}}
.brand-dot{{width:10px;height:10px;background:var(--primary);border-radius:50%;flex-shrink:0;box-shadow:0 0 0 3px rgba(99,102,241,.3)}}
.brand-name{{font-size:15px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.2px}}
.sidebar-nav{{flex:1;padding:16px 10px;display:flex;flex-direction:column;gap:3px}}
.nav-section-label{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1.2px;color:var(--sidebar-text);opacity:.45;padding:10px 10px 6px;display:block}}
.nav-item{{display:flex;align-items:center;padding:10px 16px;border-radius:9px;color:var(--sidebar-text);cursor:pointer;transition:all .15s ease;border:none;background:none;width:100%;text-align:left;font-size:14px;font-weight:500;font-family:inherit;text-decoration:none}}
.nav-item:hover{{background:var(--sidebar-hover);color:#e2e8f0}}
.nav-item.active{{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;box-shadow:0 3px 10px rgba(99,102,241,.45)}}
.sidebar-footer{{padding:14px 20px;border-top:1px solid var(--sidebar-border);font-size:11px;color:var(--sidebar-text);opacity:.5;text-align:center}}
.main-content{{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}}
.topbar{{display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:64px;min-height:64px;background:var(--surface);border-bottom:1px solid var(--border);box-shadow:var(--shadow);flex-shrink:0}}
.topbar-left{{display:flex;align-items:center;gap:12px}}
.page-title{{font-size:18px;font-weight:700;color:var(--text);letter-spacing:-.3px}}
.record-count{{background:var(--primary-light);color:var(--primary-dark);font-size:12px;font-weight:700;padding:3px 12px;border-radius:999px;letter-spacing:.3px}}
.topbar-right{{display:flex;align-items:center;gap:12px}}
.search-input{{padding:9px 16px;border:1.5px solid var(--border);border-radius:9px;font-size:14px;background:var(--bg);color:var(--text);width:240px;transition:all .2s;outline:none;font-family:inherit}}
.search-input:focus{{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.15);background:var(--surface)}}
.search-input::placeholder{{color:#a0aec0}}
.btn{{display:inline-flex;align-items:center;gap:6px;padding:9px 20px;border-radius:9px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:all .18s ease;font-family:inherit;line-height:1;white-space:nowrap}}
.btn-primary{{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;box-shadow:0 2px 6px rgba(99,102,241,.35)}}
.btn-primary:hover{{transform:translateY(-1px);box-shadow:0 5px 14px rgba(99,102,241,.45)}}
.btn-primary:active{{transform:translateY(0)}}
.btn-secondary{{background:var(--surface);color:var(--text);border:1.5px solid var(--border)}}
.btn-secondary:hover{{background:#f8fafc;border-color:#cbd5e1}}
.btn-icon{{padding:7px 11px;font-size:14px;border-radius:8px;line-height:1}}
.btn-edit{{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe}}
.btn-edit:hover{{background:#dbeafe;transform:translateY(-1px)}}
.btn-delete{{background:#fef2f2;color:var(--danger);border:1px solid #fecaca}}
.btn-delete:hover{{background:#fee2e2;transform:translateY(-1px)}}
.content-area{{flex:1;overflow-y:auto;padding:28px;background:var(--bg)}}
.content-section{{animation:fadeIn .25s ease}}
.table-card{{background:var(--surface);border-radius:var(--radius);border:1px solid var(--border);box-shadow:var(--shadow-md);overflow:hidden}}
.table-card-header{{padding:16px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#f8fafc 0%,var(--surface) 100%)}}
.table-card-title{{font-size:14px;font-weight:700;color:var(--text)}}
.table-count{{font-size:12px;color:var(--text-muted);font-weight:500}}
.data-table{{width:100%;border-collapse:collapse}}
.data-table thead tr{{background:linear-gradient(135deg,var(--primary) 0%,var(--primary-dark) 100%)}}
.data-table thead th{{padding:13px 18px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:rgba(255,255,255,.92);white-space:nowrap}}
.data-table tbody tr{{border-bottom:1px solid #f1f5f9;transition:background .12s ease}}
.data-table tbody tr:last-child{{border-bottom:none}}
.data-table tbody tr:hover{{background:#f8fafc}}
.data-table tbody td{{padding:14px 18px;font-size:14px;color:var(--text);vertical-align:middle}}
.cell-id{{font-weight:700;color:var(--text-muted);font-size:12px;width:40px}}
.actions-cell{{display:flex;gap:8px;align-items:center}}
.loading-state{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;gap:18px;color:var(--text-muted);font-size:14px}}
.spinner{{width:44px;height:44px;border:3px solid var(--primary-light);border-top-color:var(--primary);border-radius:50%;animation:spin .75s linear infinite}}
.empty-state{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;gap:14px;text-align:center}}
.empty-title{{font-size:17px;font-weight:700;color:var(--text)}}
.empty-desc{{font-size:14px;color:var(--text-muted);max-width:300px}}
.modal-overlay{{position:fixed;inset:0;z-index:200;background:rgba(15,23,42,.55);backdrop-filter:blur(5px);-webkit-backdrop-filter:blur(5px);display:flex;align-items:center;justify-content:center;padding:20px;animation:fadeIn .18s ease}}
.modal-dialog{{background:var(--surface);border-radius:18px;width:100%;max-width:580px;max-height:92vh;display:flex;flex-direction:column;box-shadow:0 28px 60px rgba(0,0,0,.28);animation:slideUp .22s cubic-bezier(.34,1.56,.64,1)}}
.modal-header{{display:flex;align-items:center;justify-content:space-between;padding:22px 26px;border-bottom:1px solid var(--border);background:linear-gradient(135deg,#f8fafc,var(--surface));border-radius:18px 18px 0 0}}
.modal-title{{font-size:16px;font-weight:700;color:var(--text)}}
.modal-close{{width:34px;height:34px;border-radius:9px;border:none;background:var(--bg);color:var(--text-muted);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;transition:all .15s;font-family:inherit;line-height:1}}
.modal-close:hover{{background:#fee2e2;color:var(--danger)}}
.modal-body{{padding:26px;overflow-y:auto;flex:1}}
.modal-footer{{display:flex;justify-content:flex-end;gap:10px;padding:18px 26px;border-top:1px solid var(--border);background:#f8fafc;border-radius:0 0 18px 18px}}
.form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.form-group{{display:flex;flex-direction:column;gap:7px}}
.form-group.full-width{{grid-column:1/-1}}
.form-label{{font-size:13px;font-weight:600;color:var(--text-muted);letter-spacing:.2px}}
.form-control{{padding:10px 13px;border:1.5px solid var(--border);border-radius:9px;font-size:14px;color:var(--text);background:var(--surface);outline:none;transition:all .18s;width:100%;font-family:inherit}}
.form-control:focus{{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.15)}}
.form-control::placeholder{{color:#a0aec0}}
textarea.form-control{{resize:vertical;min-height:88px;line-height:1.5}}
select.form-control{{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%2364748b' d='M6 8L0 0h12z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 13px center;padding-right:36px;cursor:pointer}}
.toast{{position:fixed;bottom:28px;right:28px;z-index:9999;display:flex;align-items:center;gap:14px;padding:15px 22px;border-radius:12px;min-width:300px;max-width:420px;box-shadow:0 8px 24px rgba(0,0,0,.18);animation:slideIn .3s cubic-bezier(.34,1.56,.64,1);font-size:14px;font-weight:600}}
.toast-exito{{background:#ecfdf5;color:#065f46;border-left:4px solid var(--success)}}
.toast-error{{background:#fef2f2;color:#991b1b;border-left:4px solid var(--danger)}}
.toast-label{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;flex-shrink:0;opacity:.75}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(24px) scale(.97)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
@keyframes slideIn{{from{{opacity:0;transform:translateX(24px)}}to{{opacity:1;transform:translateX(0)}}}}
@media (max-width:768px){{.sidebar{{display:none}}.form-grid{{grid-template-columns:1fr}}.search-input{{width:160px}}.content-area{{padding:16px}}}}

⚠ SOLO ESTOS 3 ARCHIVOS. No generes package.json, angular.json ni tsconfig (ya generados en paso anterior)."""


# ── Helpers de orquestación ──────────────────────────────────────────────────

def _generar_parte(nombre: str, prompt: str, max_tok: int, chain: list) -> list:
    """Itera la cadena de modelos hasta obtener JSON válido con archivos.
    Lanza HTTPException 503 si todos los modelos fallan o devuelven JSON vacío."""
    for provider, model, supports_json in chain:
        client = _make_client(provider)
        if client is None:
            log.debug(f"[Generador] Saltando {provider}/{model} — token no configurado")
            continue
        try:
            texto = _call_single(client, model, prompt, max_tok, supports_json)
            texto = _strip_thinking(texto)
        except (RateLimitError, APIStatusError, AuthenticationError, Exception) as e:
            log.warning(f"[Generador] {provider}/{model} fallo API ({type(e).__name__}) en '{nombre}' — probando siguiente")
            continue

        try:
            texto_limpio = texto.strip()
            if texto_limpio.startswith("```"):
                texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio, flags=re.IGNORECASE)
                texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
            data = json.loads(texto_limpio)
            if isinstance(data, list):
                candidatos = data
            else:
                candidatos = data.get("files") or []
            if candidatos:
                log.info(f"[Generador] OK '{nombre}' via {provider}/{model} → {len(candidatos)} archivos")
                return candidatos
            log.warning(f"[Generador] JSON vacío de {provider}/{model} en '{nombre}' — probando siguiente")
        except json.JSONDecodeError as exc:
            log.warning(f"[Generador] JSON truncado/inválido de {provider}/{model} en '{nombre}': {exc} — probando siguiente")
            continue

    raise HTTPException(503,
        detail=f"No se pudo generar '{nombre}'. Todos los modelos fallaron o devolvieron JSON inválido.")


def _evaluar_calidad_ui(archivos: list) -> tuple[int, list[str]]:
    """Fase 5: evalúa la calidad de la UI generada.
    Retorna (score 0–100, lista de problemas encontrados)."""
    html = css = ts = ""
    for arch in archivos:
        path = arch.get("path", "")
        lines = arch.get("lines", [])
        contenido = "\n".join(lines) if isinstance(lines, list) else arch.get("content", "")
        if path.endswith(".html"):
            html = contenido
        elif path.endswith(".css"):
            css = contenido
        elif path.endswith(".ts") and "component" in path:
            ts = contenido

    score = 100
    issues: list[str] = []

    # ── Crítico: emojis en HTML → error NG5002 en Angular ──────────────────
    if re.search(r"[\U0001F300-\U0001FFFF]", html):
        score -= 30
        issues.append("HTML contiene emojis directos (causa error NG5002 en Angular — usa solo texto ASCII)")
    if "️" in html:
        score -= 25
        issues.append("HTML contiene variation selector U+FE0F (emoji corrupto — causa NG5002)")

    # ── Crítico: caracteres no-ASCII en expresiones Angular → NG5002 en cascada ──
    non_ascii_interp = re.findall(r'\{\{[^}]*[ñáéíóúüÁÉÍÓÚÜÀÈ][^}]*\}\}', html)
    if non_ascii_interp:
        score -= 35
        issues.append(
            f"HTML tiene {len(non_ascii_interp)} expresión(es) {{ }} con caracteres no-ASCII "
            f"(ej: {non_ascii_interp[0][:60]!r}) — causa NG5002 en cascada para TODO el template. "
            "Usa solo ASCII en nombres de campo: tamano → tamano, descripcion → descripcion"
        )
    non_ascii_ngmodel = re.findall(r'\[\(ngModel\)\]="itemActual\.[^"]*[ñáéíóúüÁÉÍÓÚÜÀÈ][^"]*"', html)
    if non_ascii_ngmodel:
        score -= 35
        issues.append(
            f"ngModel usa campos con caracteres no-ASCII ({non_ascii_ngmodel[:2]}) — "
            "causa NG5002. Usa solo letras ASCII en nombres de campo: tamano_bytes NO tamaño_bytes"
        )

    # ── Placeholders sin reemplazar ─────────────────────────────────────────
    if "PRIMERA_ENTIDAD_PLURAL_REAL" in ts or "PRIMERA_ENTIDAD_PLURAL" in ts:
        score -= 25
        issues.append("seccionActiva tiene el placeholder sin reemplazar — debe ser el plural real de la primera entidad")
    if "NOMBRE DEL SISTEMA" in html:
        score -= 5
        issues.append("brand-name tiene el placeholder 'NOMBRE DEL SISTEMA' sin reemplazar")

    # ── Estructura HTML mínima ───────────────────────────────────────────────
    if "sidebar" not in html and "<aside" not in html:
        score -= 15
        issues.append("HTML sin sidebar/navegación lateral (clase 'sidebar' o tag <aside> ausente)")
    if "modal-overlay" not in html and "modal" not in html.lower():
        score -= 15
        issues.append("HTML sin modal-overlay para crear/editar registros")
    if "*ngFor" not in html and "ngFor" not in html:
        score -= 15
        issues.append("HTML sin *ngFor — las tablas no pueden renderizar filas de datos")

    # ── TypeScript mínimo funcional ─────────────────────────────────────────
    if "cargar" not in ts:
        score -= 10
        issues.append("TypeScript sin métodos cargar*() — no hay forma de obtener datos del API")
    if "guardar" not in ts:
        score -= 5
        issues.append("TypeScript sin métodos guardar*() — no hay forma de crear/actualizar registros")
    if "seccionActiva" not in ts:
        score -= 5
        issues.append("TypeScript sin propiedad seccionActiva — la navegación entre módulos no funcionará")

    # CSS no se evalúa aquí porque es hardcodeado (_COMPONENT_CSS) y siempre es correcto.

    return max(0, score), issues


# ── Armar resultado final ────────────────────────────────────────────────────

# package.json hardcoded — usado como fallback cuando la IA genera JSON inválido
_PACKAGE_JSON_HARDCODED = """{
  "name": "frontend",
  "version": "0.0.0",
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build",
    "test": "ng test"
  },
  "private": true,
  "dependencies": {
    "@angular/animations": "^18.0.0",
    "@angular/common": "^18.0.0",
    "@angular/compiler": "^18.0.0",
    "@angular/core": "^18.0.0",
    "@angular/forms": "^18.0.0",
    "@angular/platform-browser": "^18.0.0",
    "@angular/platform-browser-dynamic": "^18.0.0",
    "@angular/router": "^18.0.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.14.0"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^18.0.0",
    "@angular/cli": "^18.0.0",
    "@angular/compiler-cli": "^18.0.0",
    "typescript": "~5.4.0"
  }
}"""


def _fix_contenido(ruta: str, contenido: str) -> str:
    if "<NEWLINE>" in contenido:
        contenido = contenido.replace("<NEWLINE>", "\n")
    return contenido


def _armar_resultado(todos_archivos: list) -> dict:
    bloques: dict = {"frontend": [], "backend": [], "database": []}
    pkg_json_incluido = False

    for arch in todos_archivos:
        seccion  = (arch.get("section") or "").lower()
        ruta     = (arch.get("path") or "").strip()
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
        if seccion not in bloques or not ruta:
            continue
        lines    = arch.get("lines")
        contenido = "\n".join(lines) if isinstance(lines, list) else (arch.get("content") or "")
        contenido = _fix_contenido(ruta, contenido)
<<<<<<< HEAD
        bloques[seccion].append(f"@@FILE: {ruta}@@\n{contenido}")
=======

        # Validar package.json — la IA a veces omite comas y rompe JSON
        if ruta == "package.json":
            try:
                json.loads(contenido)
                pkg_json_incluido = True
                log.info("[Generador] package.json generado por IA es JSON válido ✓")
            except json.JSONDecodeError as exc:
                log.warning(f"[Generador] package.json inválido de IA ({exc}) — usando versión hardcoded")
                contenido = _PACKAGE_JSON_HARDCODED
                pkg_json_incluido = True

        bloques[seccion].append(f"@@FILE: {ruta}@@\n{contenido}")

    # Si la IA no incluyó package.json en absoluto, inyectarlo
    if not pkg_json_incluido:
        log.warning("[Generador] package.json no generado — inyectando versión hardcoded")
        bloques["frontend"].insert(0, f"@@FILE: package.json@@\n{_PACKAGE_JSON_HARDCODED}")

>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
    return {
        "frontend": "\n\n".join(bloques["frontend"]),
        "backend":  "\n\n".join(bloques["backend"]),
        "database": "\n\n".join(bloques["database"]),
    }


<<<<<<< HEAD
def generar_codigo(db: Session, proyecto_id: int) -> dict:
    """
    Genera la aplicación completa en 3 partes usando GitHub Models (Azure).

    Modelo principal : gpt-4o-mini  (15 RPM · 150 RPD · estable)
    Modelo fallback  : gpt-4o       (10 RPM ·  50 RPD · mayor calidad)

    Se divide en 3 partes para mantenerse dentro del límite de tokens de salida
    por petición (~4 096 tokens en el free tier de GitHub Models).
=======
# ── Fase 4: prompt UI/UX optimizado para Gemini ─────────────────────────────

def _prompt_ui_gemini(contexto: str, entidades: str,
                      correcciones: list[str] | None = None) -> str:
    """Prompt optimizado para Gemini: genera SOLO TypeScript + HTML (2 archivos).
    El CSS es hardcodeado en _COMPONENT_CSS y se inyecta en Python después.
    En reintentos se añaden las correcciones específicas detectadas por _evaluar_calidad_ui."""
    bloque_correcciones = ""
    if correcciones:
        bloque_correcciones = (
            "\n\n🔴 CORRECCIONES OBLIGATORIAS (fallos del intento anterior — corrígelos todos):\n"
            + "\n".join(f"  • {c}" for c in correcciones)
        )

    return f"""Eres un desarrollador Angular 18 senior. Genera el código TypeScript y HTML \
de un dashboard CRUD completo con diseño profesional tipo SaaS.

Especificación del proyecto:
{contexto}

ENTIDADES (usa EXACTAMENTE estos nombres — cero genéricos):
{entidades}
{bloque_correcciones}

{_FORMATO_COMUN}

Genera EXACTAMENTE 2 archivos con section="frontend". Código COMPLETO, funcional, sin TODO ni placeholders.
El CSS ya está generado — NO incluyas un tercer archivo .css.

Las clases CSS disponibles son: app-layout, sidebar, sidebar-brand, brand-dot, brand-name,
sidebar-nav, nav-section-label, nav-item (+ .active), sidebar-footer, main-content, topbar,
topbar-left, topbar-right, page-title, record-count, search-input, btn, btn-primary, btn-secondary,
btn-icon, btn-edit, btn-delete, content-area, content-section, table-card, table-card-header,
table-card-title, table-count, data-table, cell-id, actions-cell, loading-state, spinner,
empty-state, empty-title, empty-desc, modal-overlay, modal-dialog, modal-header, modal-title,
modal-close, modal-body, modal-footer, form-grid, form-group, form-group.full-width,
form-label, form-control, toast, toast-exito, toast-error, toast-label.

══ ARCHIVO 1: src/app/components/main/main.component.ts ══

Imports EXACTOS (no cambiar rutas):
import {{ Component, OnInit }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';
import {{ FormsModule }} from '@angular/forms';
import {{ ApiService }} from '../../services/api.service';

@Component({{
  selector: 'app-main', standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.css']
}})
export class MainComponent implements OnInit {{
  constructor(private api: ApiService) {{}}

  // GENERA una propiedad any[] = [] por cada entidad en plural camelCase:
  // espectros: any[] = [];
  // archivos: any[] = [];

  itemActual: any = {{}};
  editando = false;
  editandoId: number | null = null;
  mostrarModal = false;
  cargando = false;
  busqueda = '';
  toast: {{ mensaje: string; tipo: 'exito' | 'error' }} | null = null;
  // REEMPLAZA con el plural real de la primera entidad:
  seccionActiva = 'PRIMERA_ENTIDAD_PLURAL_REAL';

  getRegistrosActuales(): any[] {{
    switch (this.seccionActiva) {{
      // GENERA un case por cada entidad:
      // case 'espectros': return this.espectros;
      default: return [];
    }}
  }}

  ngOnInit(): void {{
    // LLAMA a cargar<Entidad>s() por cada entidad:
    // this.cargarEspectros();
  }}

  mostrarToast(m: string, t: 'exito' | 'error'): void {{
    this.toast = {{ mensaje: m, tipo: t }};
    setTimeout(() => this.toast = null, 3500);
  }}
  abrirModal(item?: any): void {{
    this.itemActual = item ? {{ ...item }} : {{}};
    this.editando = !!item;
    this.editandoId = item?.id ?? null;
    this.mostrarModal = true;
  }}
  cerrarModal(): void {{ this.mostrarModal = false; this.itemActual = {{}}; }}

  guardarEntidadActual(): void {{
    // GENERA switch con case por cada entidad:
    // switch(this.seccionActiva) {{ case 'espectros': this.guardarEspectro(); break; }}
  }}
  eliminarEntidad(id: number): void {{
    if (!confirm('¿Eliminar este registro?')) return;
    // GENERA switch con case por cada entidad:
    // switch(this.seccionActiva) {{ case 'espectros': this.eliminarEspectro(id); break; }}
  }}

  // GENERA los 3 métodos siguientes por CADA entidad (reemplaza X y xs):
  // CRITICO: cargarXs() llama SIEMPRE this.api.getXs() SIN argumentos (getter de lista).
  // NUNCA llames this.api.getX(id) desde cargarXs — ese getter requiere un id específico.
  // Si cometes este error obtienes TS2554 "Expected 1 arguments, but got 0".
  // cargarXs(): void {{
  //   this.cargando = true;
  //   this.api.getXs().subscribe({{   // <-- getXs() SIN argumento = lista completa
  //     next: d => {{ this.xs = d; this.cargando = false; }},
  //     error: () => {{ this.mostrarToast('Error al cargar', 'error'); this.cargando = false; }}
  //   }});
  // }}
  // guardarX(): void {{
  //   const op = this.editando
  //     ? this.api.updateX(this.editandoId!, this.itemActual)
  //     : this.api.createX(this.itemActual);
  //   op.subscribe({{
  //     next: () => {{ this.mostrarToast(this.editando ? 'Actualizado' : 'Creado', 'exito'); this.cerrarModal(); this.cargarXs(); }},
  //     error: () => this.mostrarToast('Error al guardar', 'error')
  //   }});
  // }}
  // eliminarX(id: number): void {{
  //   this.api.deleteX(id).subscribe({{
  //     next: () => {{ this.mostrarToast('Eliminado', 'exito'); this.cargarXs(); }},
  //     error: () => this.mostrarToast('Error al eliminar', 'error')
  //   }});
  // }}
}}

══ ARCHIVO 2: src/app/components/main/main.component.html ══

REGLAS ABSOLUTAS:
• CERO emojis — ni Unicode directo ni variante de texto — causa error NG5002 en Angular
• CERO caracteres no-ASCII en [(ngModel)] — los nombres de campo deben ser SOLO a-z, 0-9, _
  CORRECTO: [(ngModel)]="itemActual.tamano_bytes"   INCORRECTO: [(ngModel)]="itemActual.tamaño_bytes"
  Un solo campo con ñ o tilde en ngModel rompe TODAS las expresiones del template en cascada.
• CERO caracteres no-ASCII en {{ item.campo }} — misma regla: solo ASCII en expresiones de template
• Usa EXACTAMENTE las clases CSS listadas arriba (sidebar, nav-item, table-card, etc.)
• El string de seccionActiva, [class.active] y *ngIf DEBEN ser idénticos (ej: 'espectros')
• Formularios: EXCLUYE campos auto-generados (id, fecha_*, *_at, *_id foráneo) — solo campos editables por el usuario
• NUNCA uses el operador ** en TypeScript — usa Math.pow(base, exp) (ej: -Math.pow(x-1200, 2) no -(x-1200)**2)
  Razon: TypeScript strict mode rechaza unario '-' antes de ** con error TS17006

<div class="app-layout">

  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-dot"></div>
      <span class="brand-name">NOMBRE DEL SISTEMA</span>
    </div>
    <nav class="sidebar-nav">
      <span class="nav-section-label">Modulos</span>
      <!-- GENERA un button por cada entidad:
           <button class="nav-item" [class.active]="seccionActiva==='espectros'"
             (click)="seccionActiva='espectros'; cargarEspectros()">Espectros</button> -->
    </nav>
    <div class="sidebar-footer">v1.0</div>
  </aside>

  <div class="main-content">
    <header class="topbar">
      <div class="topbar-left">
        <h1 class="page-title">{{{{seccionActiva | titlecase}}}}</h1>
        <span class="record-count">{{{{getRegistrosActuales().length}}}} registros</span>
      </div>
      <div class="topbar-right">
        <input class="search-input" type="text" [(ngModel)]="busqueda" placeholder="Buscar...">
        <button class="btn btn-primary" (click)="abrirModal()">+ Nuevo</button>
      </div>
    </header>

    <main class="content-area">

      <!-- GENERA una section por cada entidad. Ejemplo completo para Espectros:

      <section *ngIf="seccionActiva==='espectros'" class="content-section">
        <div *ngIf="cargando" class="loading-state">
          <div class="spinner"></div><span>Cargando...</span>
        </div>
        <div *ngIf="!cargando && espectros.length===0" class="empty-state">
          <p class="empty-title">Sin registros</p>
          <p class="empty-desc">Agrega el primer espectro para comenzar</p>
          <button class="btn btn-primary" style="margin-top:12px" (click)="abrirModal()">+ Nuevo</button>
        </div>
        <div *ngIf="!cargando && espectros.length>0" class="table-card">
          <div class="table-card-header">
            <span class="table-card-title">Espectros</span>
            <span class="table-count">{{{{espectros.length}}}} registros</span>
          </div>
          <table class="data-table">
            <thead><tr>
              <th>#</th><th>Nombre</th><th>Tipo</th><th>Fecha</th><th>Acciones</th>
            </tr></thead>
            <tbody>
              <tr *ngFor="let item of espectros">
                <td class="cell-id">{{{{item.id}}}}</td>
                <td><strong>{{{{item.nombre}}}}</strong></td>
                <td>{{{{item.tipo}}}}</td>
                <td>{{{{item.fecha_creacion | date:'dd/MM/yyyy'}}}}</td>
                <td class="actions-cell">
                  <button class="btn btn-icon btn-edit" (click)="abrirModal(item)">Editar</button>
                  <button class="btn btn-icon btn-delete" (click)="eliminarEntidad(item.id)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      Repite para cada entidad adicional. -->

    </main>
  </div>

  <div class="modal-overlay" *ngIf="mostrarModal" (click)="cerrarModal()">
    <div class="modal-dialog" (click)="$event.stopPropagation()">
      <div class="modal-header">
        <h2 class="modal-title">{{{{editando ? 'Editar registro' : 'Nuevo registro'}}}}</h2>
        <button class="modal-close" (click)="cerrarModal()">&times;</button>
      </div>
      <div class="modal-body">
        <!-- GENERA un <div *ngIf="seccionActiva==='x'" class="form-grid"> por entidad.
             Por cada campo EDITABLE (excluye id, fecha_*, *_at, claves foráneas numéricas):
             <div class="form-group">
               <label class="form-label">Nombre del campo</label>
               <input class="form-control" [(ngModel)]="itemActual.campo" placeholder="...">
             </div>
             Para TEXT usa <textarea class="form-control"> con rows="3".
             Para campos tipo rol/estado usa <select class="form-control"> con options reales.
        -->
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" (click)="cerrarModal()">Cancelar</button>
        <button class="btn btn-primary" (click)="guardarEntidadActual()">
          {{{{editando ? 'Guardar cambios' : 'Crear registro'}}}}
        </button>
      </div>
    </div>
  </div>

  <div class="toast" *ngIf="toast"
    [class.toast-exito]="toast.tipo==='exito'"
    [class.toast-error]="toast.tipo==='error'">
    <span class="toast-label">{{{{toast.tipo === 'exito' ? 'OK' : 'Error'}}}}</span>
    <span>{{{{toast.mensaje}}}}</span>
  </div>

</div>"""


# ── Fase 4+5: orquestador de UI con validación automática ────────────────────

def _inyectar_css(archivos: list) -> list:
    """Reemplaza cualquier archivo .css de componente con _COMPONENT_CSS hardcodeado.
    Si la IA no generó .css (porque el prompt pide solo 2 archivos), lo añade."""
    css_path = "src/app/components/main/main.component.css"
    archivos_sin_css = [a for a in archivos if not (a.get("path", "").endswith(".css")
                                                      and "main.component" in a.get("path", ""))]
    archivos_sin_css.append({
        "section": "frontend",
        "path": css_path,
        "lines": [_COMPONENT_CSS],
    })
    return archivos_sin_css


def _generar_ui_con_validacion(contexto: str, entidades: str) -> list:
    """Fase 4: genera TS + HTML con Gemini; inyecta CSS hardcodeado.
    Fase 5: evalúa calidad del TS/HTML; si es baja, regenera con correcciones (max 3 intentos)."""
    correcciones: list[str] = []

    for intento in range(1, 4):
        log.info(f"[Fase 4] Intento {intento}/3 — generando TS+HTML con Gemini...")
        prompt = _prompt_ui_gemini(contexto, entidades, correcciones if intento > 1 else None)

        archivos: list | None = None
        try:
            archivos = _generar_parte(f"UI/UX intento {intento}", prompt, 65000, _GEMINI_UI_CHAIN)
        except HTTPException:
            log.warning(f"[Fase 4] Gemini no disponible en intento {intento} — usando _CODE_CHAIN_LARGE como fallback")
            try:
                archivos = _generar_parte(f"UI/UX fallback {intento}", prompt, 55000, _CODE_CHAIN_LARGE)
            except HTTPException:
                raise HTTPException(503, detail="Ningún modelo pudo generar la UI/UX.")

        # Inyectar CSS hardcodeado siempre (independientemente del modelo usado)
        archivos = _inyectar_css(archivos)

        # Fase 5 — validación de calidad del TS + HTML
        score, issues = _evaluar_calidad_ui(archivos)
        log.info(f"[Fase 5] Calidad UI intento {intento}: {score}/100 | problemas: {issues or 'ninguno'}")

        if score >= 60:
            log.info(f"[Fase 5] UI aprobada ({score}/100) en intento {intento}")
            return archivos

        if intento == 3:
            log.warning(f"[Fase 5] UI con calidad baja ({score}/100) pero se agotaron los intentos — usando igual")
            return archivos

        correcciones = issues
        log.warning(f"[Fase 5] UI rechazada (score={score}/100) — regenerando con {len(issues)} correcciones")

    return archivos  # no debería llegar aquí


def _prompt_ui_multicomponente(contexto: str, entidades: str,
                                ui_plan: dict, plan_texto: str) -> str:
    """
    Genera componentes Angular especializados por ruta según el plan UI.
    Cada feature recibe su propio componente con la UI adecuada (charts, upload, forms).
    El sidebar usa routerLink en lugar del patrón seccionActiva+ngIf.
    """
    # Construir descripción de componentes
    componentes = ui_plan.get("componentes", [])
    comp_desc = ""
    for c in componentes:
        comp_desc += (
            f"\n- {c.get('nombre_componente','?')} | Ruta: {c.get('ruta','?')} | "
            f"Archivo: {c.get('archivo','?')} | UI: {c.get('ui_tipo','tabla')} | "
            f"{c.get('ui_detalle','')} | Entidades: {c.get('entidades','')}"
        )

    # Instrucciones específicas por tipo de UI
    instr_charts = ""
    if ui_plan.get("necesita_charts"):
        instr_charts = """
CHART.JS — Para componentes con UI_TIPO chart_linea o layout_comparacion:
- Imports: import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
           import { Chart, registerables } from 'chart.js'; Chart.register(...registerables);
- En ngAfterViewInit(): this.chart = new Chart(this.canvasRef.nativeElement, { type: 'line', data: {...}, options: {...} })
- HTML: <div class="chart-wrapper"><canvas #canvasRef></canvas></div>
- CSS inline: .chart-wrapper { width:100%; height:400px; position:relative; }
- Eje X: wavenumber/numero de onda; Eje Y: intensidad/absorbancia
- options.scales.x.reverse = true (convencion espectroscopica — eje X invertido)
- Los datos vienen del API: this.api.getXxxs().subscribe(data => { this.chart.data.datasets = ...; this.chart.update(); })
"""

    instr_upload = ""
    if ui_plan.get("necesita_upload"):
        instr_upload = """
FILE UPLOAD — Para componentes con UI_TIPO upload_archivos:
- HTML: zona drag-drop con clases CSS del proyecto + <input type="file" #fileInput style="display:none" (change)="onFileChange($event)" multiple>
- Zona: <div class="drop-zone" (dragover)="onDragOver($event)" (dragleave)="onDragLeave($event)" (drop)="onDrop($event)" [class.drag-over]="dragging">
- Boton: <button class="btn btn-primary" (click)="fileInput.click()">Seleccionar Archivos</button>
- TypeScript: dragging=false; onDragOver(e:DragEvent){e.preventDefault();this.dragging=true;}
              onDrop(e:DragEvent){e.preventDefault();this.dragging=false;const f=e.dataTransfer?.files;if(f)this.procesarArchivos(f);}
              procesarArchivos(files:FileList){/* enviar al API via FormData */}
- Muestra tabla de archivos cargados con columnas reales de la entidad
"""

    # Generar descripción de rutas para el sidebar
    nav_links = "\n".join(
        f"  - routerLink='{c.get('ruta','')}' texto='{c.get('nombre_componente','')}'  "
        for c in componentes
    )

    return f"""Eres un experto en Angular 18 standalone. Proyecto:

{contexto[:5000]}

ENTIDADES:
{entidades[:2000]}

PLAN DE ARQUITECTURA UI:
{plan_texto[:1500]}
{instr_charts}
{instr_upload}

{_FORMATO_COMUN}

Genera section="frontend" para TODOS estos archivos (en este orden exacto):

== 0. app.routes.ts (CRITICO — genera PRIMERO) ==
Archivo: src/app/app.routes.ts
DEBES generar este archivo ANTES que los componentes.
Los paths en los imports DEBEN coincidir EXACTAMENTE con los archivos .component.ts que vas a crear.

Formato de cada ruta:
  {{ path: 'ruta-url', loadComponent: () => import('./components/carpeta/archivo.component').then(m => m.ClaseComponent) }}

Reglas:
- El path del import usa SIEMPRE la ruta relativa desde src/app/ (sin .ts al final)
- La clase usa CamelCase: si el archivo es 'cargar-espectro.component' → clase 'CargarEspectroComponent'
- Primer ruta = la mas importante del proyecto (no admin)
- Agrega al final: {{ path: '', redirectTo: '/primera-ruta', pathMatch: 'full' }}, {{ path: '**', redirectTo: '/primera-ruta' }}

== 1. SIDEBAR COMPARTIDO ==
Archivos: src/app/components/sidebar/sidebar.component.ts
          src/app/components/sidebar/sidebar.component.html

sidebar.component.ts:
import {{ Component }} from '@angular/core';
import {{ RouterLink, RouterLinkActive }} from '@angular/router';
@Component({{ selector: 'app-sidebar', standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html' }})
export class SidebarComponent {{}}

sidebar.component.html — usa clases CSS: sidebar, sidebar-brand, brand-dot, brand-name,
sidebar-nav, nav-section-label, nav-item (+ routerLinkActive="active"), sidebar-footer.
Genera un <a class="nav-item" routerLink="..." routerLinkActive="active"> por cada ruta:
{nav_links}
Texto del brand-name = nombre del proyecto.

== 2. COMPONENTES DE FEATURE ==
Por cada feature del plan, genera .ts + .html:
{comp_desc}

Para CADA componente:
.ts — imports: Component, OnInit, CommonModule, FormsModule, ApiService + AfterViewInit/ViewChild/ElementRef si es chart
      @Component({{ selector: 'app-[nombre]', standalone: true,
        imports: [CommonModule, FormsModule],  templateUrl: '...' }})
      Propiedades, metodos CRUD reales (cargar, guardar, eliminar), ngOnInit que llama cargarXxxs()
.html — usa clases CSS del proyecto: content-area, table-card, data-table, modal-overlay, form-grid, etc.
        Incluye el <app-sidebar> como primer elemento del layout

REGLAS ABSOLUTAS (violar cualquiera rompe el build):
• CERO emojis en HTML — causa NG5002
• CERO caracteres no-ASCII (ñ, á, é, í, ó, ú) en [(ngModel)], {{ }}, nombres de variable
• Cada componente comienza con <div class="app-layout"><app-sidebar></app-sidebar><div class="main-content">...
• Para UI_TIPO upload_archivos: implementa zona drag-drop REAL (no solo un <input>)
• Para UI_TIPO chart_linea: usa Chart.js con <canvas> REAL (no una tabla)
• Para UI_TIPO form_cientifico: usa <input type="range"> para sliders, <select> para metodos
• Para UI_TIPO layout_comparacion: CSS grid dos columnas, cada columna con su chart/datos
• Para UI_TIPO admin_tabla: badges de estado con <span> coloreados, dropdown de rol
• NUNCA schemas.XxxUpdate — usa XxxCreate para PUT
• getXxxs() CERO args (lista), getXxx(id) UN arg (item)
• cargarXxxs() llama SIEMPRE this.api.getXxxs() sin argumento
• NUNCA uses el operador ** (exponenciacion) en TypeScript — usa Math.pow(base, exp) en su lugar
  INCORRECTO: -(x - 1200) ** 2   CORRECTO: -Math.pow(x - 1200, 2)
  Razon: TypeScript strict mode no permite unario '-' antes de ** (error TS17006)"""


def _generar_ui_multicomponente(contexto: str, entidades: str,
                                 ui_plan: dict, plan_texto: str) -> list:
    """
    Fase 4 (arquitectura multicomponente): Genera sidebar + componentes especializados.
    Inyecta el CSS hardcodeado en src/styles.css (global) en lugar de main.component.css.
    Hace hasta 2 intentos si la calidad es baja.
    """
    for intento in range(1, 3):
        log.info(f"[Fase 4 Multi] Intento {intento}/2 — generando componentes especializados...")
        prompt = _prompt_ui_multicomponente(contexto, entidades, ui_plan, plan_texto)

        try:
            archivos = _generar_parte(
                f"UI multicomponente intento {intento}",
                prompt, 65000, _GEMINI_UI_CHAIN
            )
        except HTTPException:
            try:
                archivos = _generar_parte(
                    f"UI multicomponente fallback {intento}",
                    prompt, 60000, _CODE_CHAIN_LARGE
                )
            except HTTPException:
                raise HTTPException(503, detail="Ningún modelo pudo generar la UI multicomponente.")

        # Inyectar CSS como estilos globales (src/styles.css) en lugar de main.component.css
        css_path = "src/styles.css"
        archivos = [a for a in archivos if not (
            a.get("path", "").endswith(".css") and "styles" in a.get("path", "")
        )]
        archivos.append({
            "section": "frontend",
            "path": css_path,
            "lines": [_COMPONENT_CSS],
        })

        # Validación básica: detectar emojis y placeholders
        score, issues = _evaluar_calidad_ui(archivos)
        log.info(f"[Fase 4 Multi] Calidad intento {intento}: {score}/100")
        if score >= 55 or intento == 2:
            if issues:
                log.warning(f"[Fase 4 Multi] Issues detectados: {issues}")
            return archivos

    return archivos  # fallback


# ── Generación de código ─────────────────────────────────────────────────────

def generar_codigo(db: Session, proyecto_id: int) -> dict:
    """Orquestador principal. Divide la generación en 5 fases especializadas:

    Fase 1 — Extracción de entidades   → modelo de razonamiento
    Fase 2 — Backend (infra + CRUD)    → cadena de modelos de código
    Fase 3 — Frontend base (servicios, configs, rutas)  → cadena de código
    Fase 4 — UI/UX (componentes)       → Gemini obligatorio
    Fase 5 — Validación automática      → regenera si la UI no cumple estándares
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
    """
    datos    = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)

<<<<<<< HEAD
    # ── Guard de longitud: GitHub Models free tier ≈ 8 k tokens totales ──────
    # Reservamos ~3 500 tokens para instrucciones + salida; el resto es contexto.
    # 1 token ≈ 4 caracteres (estimación conservadora para español)
    MAX_CONTEXTO_CHARS = 16_000   # ≈ 4 000 tokens
    ctx_len = len(contexto)
    log.info(f"[Generador] Contexto: {ctx_len} chars (~{ctx_len // 4} tokens estimados)")
    if ctx_len > MAX_CONTEXTO_CHARS:
        log.warning(
            f"[Generador] Contexto demasiado largo ({ctx_len} chars), "
            f"truncando a {MAX_CONTEXTO_CHARS} chars..."
        )
        contexto = contexto[:MAX_CONTEXTO_CHARS] + "\n\n[CONTEXTO TRUNCADO POR LONGITUD]"

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
            log.info(f"[Generador] Esperando 5 s antes de parte {i + 1}/{len(partes)}...")
            time.sleep(5)

        archivos_parte: list = []
        for modelo in [MODEL_MAIN, MODEL_FALLBACK]:
            try:
                log.info(f"[Generador] Parte '{nombre_parte}' con {modelo}...")
                texto = _call_ai(client, prompt, model=modelo, max_tokens=4096)
                data  = json.loads(texto)
                archivos_parte = data.get("files") or []
                if archivos_parte:
                    log.info(f"[Generador] ✓ Parte '{nombre_parte}' — {len(archivos_parte)} archivos.")
                    break
                else:
                    log.info(f"[Generador] {modelo} devolvió JSON vacío en '{nombre_parte}', probando fallback...")
            except HTTPException as e:
                log.info(f"[Generador] {modelo} falló en '{nombre_parte}' ({e.status_code}): {e.detail}")
                if e.status_code in (429, 503):
                    continue   # intenta el siguiente modelo
                raise
            except json.JSONDecodeError as exc:
                log.info(f"[Generador] JSON inválido de {modelo}: {exc}")
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

    log.info(f"[Generador] ✓ Generación completa — {len(todos_archivos)} archivos en total.")
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
=======
    ctx_len = len(contexto)
    log.info(f"[Generador] Contexto: {ctx_len} chars (~{ctx_len // 4} tokens est.)")
    if ctx_len > 16_000:
        log.warning("[Generador] Contexto largo, truncando a 16 000 chars...")
        contexto = contexto[:16_000] + "\n\n[CONTEXTO TRUNCADO]"

    # ── FASE 1: Extracción de entidades ──────────────────────────────────────
    log.info("[Fase 1] Extrayendo entidades con modelo de razonamiento...")
    entidades = _extraer_entidades(contexto)
    log.info(f"[Fase 1] Entidades detectadas:\n{entidades}")

    # ── FASE 1.5: Análisis de patrones UI ────────────────────────────────────
    log.info("[Fase 1.5] Analizando patrones UI del proyecto...")
    plan_ui_texto = _analizar_patrones_ui(contexto, entidades)
    ui_plan = _parsear_plan_ui(plan_ui_texto)
    tiene_multicomponente = bool(ui_plan.get("componentes"))
    log.info(
        f"[Fase 1.5] Componentes detectados: {len(ui_plan['componentes'])} | "
        f"Charts: {ui_plan['necesita_charts']} | Upload: {ui_plan['necesita_upload']}"
    )

    todos_archivos: list = []

    # ── FASE 2: Backend ───────────────────────────────────────────────────────
    log.info("[Fase 2] Generando backend (infraestructura + CRUD/router)...")
    todos_archivos.extend(
        _generar_parte("backend infraestructura",
                       _prompt_backend_infra(contexto, entidades), 65000, _CODE_CHAIN)
    )
    todos_archivos.extend(
        _generar_parte("backend crud+router",
                       _prompt_backend_router(contexto, entidades), 65000, _CODE_CHAIN)
    )

    # ── FASE 3: Frontend base (sin UI detallada) ──────────────────────────────
    log.info("[Fase 3] Generando frontend base (interfaces, servicios, configuración)...")
    todos_archivos.extend(
        _generar_parte("frontend core",
                       _prompt_frontend_core(contexto, entidades, ui_plan), 50000, _CODE_CHAIN)
    )

    # ── FASE 4+5: UI/UX — multicomponente o monolítico según el plan ─────────
    if tiene_multicomponente:
        log.info(
            f"[Fase 4] Generando {len(ui_plan['componentes'])} componentes especializados..."
        )
        archivos_ui = _generar_ui_multicomponente(
            contexto, entidades, ui_plan, plan_ui_texto
        )
    else:
        log.info("[Fase 4] Sin plan UI detectado — generando componente monolítico...")
        archivos_ui = _generar_ui_con_validacion(contexto, entidades)
    todos_archivos.extend(archivos_ui)

    # Deduplicar por ruta: si Fase 4 generó app.routes.ts propio, reemplaza al de Fase 3.
    # El último archivo con la misma ruta gana (preserva el orden de inserción).
    seen: dict[str, dict] = {}
    for arch in todos_archivos:
        ruta = arch.get("path", "")
        if ruta:
            seen[ruta] = arch   # sobreescribe duplicados; el último (Fase 4) prevalece
    todos_archivos = list(seen.values())

    log.info(f"[Generador] Completado — {len(todos_archivos)} archivos totales (deduplicados).")
    return _armar_resultado(todos_archivos)


# ── Generación de diagramas ──────────────────────────────────────────────────

_INSTRUCCIONES_DIAGRAMA = {
    "paquetes":   "Genera un diagrama de paquetes en sintaxis Mermaid (graph TD) con la arquitectura en capas: frontend, backend y base de datos.",
    "clases":     "Genera un diagrama de clases en sintaxis Mermaid (classDiagram) con todas las entidades, atributos y relaciones.",
    "secuencia":  "Genera un diagrama de secuencia en sintaxis Mermaid (sequenceDiagram) del flujo principal entre usuario, frontend, backend y base de datos.",
    "casos_uso":  """Genera un diagrama de casos de uso en sintaxis Mermaid usando flowchart LR.
REGLAS ESTRICTAS DE SINTAXIS (Mermaid no soporta UML nativo; usa flowchart con formas):
- Actores como óvalos:  Usuario(("👤 Usuario"))   Admin(("👤 Administrador"))
- Casos de uso como rectángulos redondeados:  CU1("Nombre del caso de uso")
- Limita el sistema con subgraph:  subgraph sistema["Sistema"]\n  CU1 ... \nend
- Relaciones con -->
- PROHIBIDO: la palabra 'actor' — es solo válida en sequenceDiagram, no en flowchart/graph
- PROHIBIDO: classDiagram, sequenceDiagram u otros tipos
- PROHIBIDO: bloques markdown o explicaciones — solo código Mermaid puro

Ejemplo de formato correcto:
flowchart LR
    U(("👤 Usuario"))
    A(("👤 Admin"))
    subgraph sis["Sistema"]
        CU1("Registrarse")
        CU2("Iniciar sesion")
        CU3("Gestionar usuarios")
    end
    U --> CU1
    U --> CU2
    A --> CU3""",
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
}


def generar_diagrama(db: Session, proyecto_id: int, tipo: str) -> dict:
    datos    = _recopilar_datos(db, proyecto_id)
    contexto = _construir_contexto(datos)
<<<<<<< HEAD

    MAX_CONTEXTO_CHARS = 16_000
    if len(contexto) > MAX_CONTEXTO_CHARS:
        contexto = contexto[:MAX_CONTEXTO_CHARS] + "\n\n[CONTEXTO TRUNCADO POR LONGITUD]"

    client   = _get_client()

    instruccion = _INSTRUCCIONES_DIAGRAMA.get(tipo, "Genera un diagrama Mermaid apropiado.")

    prompt = f"""Eres un experto en diseño de software y diagramas UML. Aquí tienes la especificación del proyecto:
=======
    if len(contexto) > 16_000:
        contexto = contexto[:16_000] + "\n\n[CONTEXTO TRUNCADO]"
    client   = _get_client()

    instruccion = _INSTRUCCIONES_DIAGRAMA.get(tipo, "Genera un diagrama Mermaid apropiado.")
    prompt = f"""Especificación del proyecto:
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50

{contexto}

{instruccion}

<<<<<<< HEAD
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
=======
REGLAS: Responde ÚNICAMENTE con código Mermaid válido, sin explicaciones, sin bloques markdown (no uses ```)."""

    codigo = _call_chain(_CODE_CHAIN, prompt, max_tokens=8000, json_mode=False)
    codigo = re.sub(r"^```(?:mermaid)?\n?", "", codigo.strip(), flags=re.MULTILINE)
    codigo = re.sub(r"\n?```$", "", codigo.strip(), flags=re.MULTILINE)

    return {"tipo": tipo, "codigo_mermaid": codigo.strip()}
>>>>>>> 19fca05b3dab164eb585e0015991ce43c835db50
