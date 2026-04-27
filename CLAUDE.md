# CLAUDE.md — Backend: Generador de Código con IA

## Qué hace este proyecto

Backend FastAPI que recibe datos de un SRS (Software Requirements Specification) y genera un proyecto full-stack completo (Angular 18 + FastAPI + MySQL) usando una cadena de proveedores de IA con fallback automático.

**Flujo principal:**
1. El usuario llena RF, RNF, stakeholders, casos de uso, etc. en el frontend
2. `POST /api/generador/codigo/{proyecto_id}` dispara la generación
3. Se extraen entidades de base de datos del SRS con IA
4. Se generan 4 partes en secuencia: infra backend → CRUD backend → core frontend → componentes frontend
5. Se devuelve un ZIP con los archivos separados por sección (`frontend`, `backend`, `database`)

---

## Estructura del proyecto

```
grafos/
├── main.py                        # FastAPI app, CORS, registro de 14 routers
├── requirements.txt
├── .env                           # API keys + MySQL URL
├── uploads/                       # Archivos subidos por usuarios
└── app/
    ├── core/
    │   ├── config.py              # Settings (carga .env)
    │   ├── database.py            # Engine SQLAlchemy + get_db()
    │   ├── dependencies.py        # get_current_user() desde JWT
    │   └── security.py            # Hash passwords, sign/verify tokens
    ├── models/                    # 23 modelos SQLAlchemy ORM
    ├── routes/                    # 14 routers FastAPI
    ├── schemas/                   # Pydantic v2 (Base/Create/Response)
    └── services/
        ├── generador_service.py   # ← ARCHIVO CRÍTICO (1355 líneas)
        └── ...                    # Un service por entidad de dominio
```

---

## Archivo crítico: `app/services/generador_service.py`

Todo el pipeline de IA vive aquí. Funciones clave:

| Función | Qué hace |
|---------|----------|
| `_call_single()` | Una llamada a un proveedor, 3 reintentos en rate limit |
| `_call_chain()` | Itera la cadena de proveedores; salta al siguiente si falla |
| `_strip_thinking()` | Elimina bloques `<think>...</think>` de modelos de razonamiento |
| `_recopilar_datos()` | Consulta DB: RF, RNF, stakeholders, casos de uso, restricciones |
| `_construir_contexto()` | Formatea el dict de datos como markdown (~2000 tokens) |
| `_extraer_entidades()` | Usa `_REASONING_CHAIN` para identificar entidades de BD |
| `_prompt_backend_infra()` | Parte 1: 7 archivos (main, database, models, schemas, sql…) |
| `_prompt_backend_router()` | Parte 2: crud.py + router.py con CRUD completo |
| `_prompt_frontend_core()` | Parte 3: interfaces.ts, api.service.ts, 11 configs Angular |
| `_prompt_frontend_componentes()` | Parte 4: main.component.ts/html/css |
| `generar_codigo()` | Orquesta las 4 partes y devuelve `GeneradorCodigoResponse` |

### Cadenas de proveedores

```python
_CODE_CHAIN = [
    ("groq",   "llama-3.3-70b-versatile",        True),
    ("github", "DeepSeek-V3-0324",               True),
    ("gemini", "gemini-2.5-flash",               True),
    ("github", "gpt-4o",                         True),   # fallback
    ("github", "gpt-4o-mini",                    True),   # fallback final
]

_CODE_CHAIN_LARGE = [                                      # Para componentes grandes
    ("github", "gpt-4o",                         True),
    ("gemini", "gemini-2.5-flash",               True),
    ("github", "gpt-4o-mini",                    True),
]

_REASONING_CHAIN = [                                       # Para extracción de entidades
    ("github", "DeepSeek-R1",                    False),
    ("groq",   "deepseek-r1-distill-llama-70b",  False),
    ("groq",   "qwen-qwq-32b",                   False),
    ("gemini", "gemini-2.5-flash",               False),
    ("github", "gpt-4o",                         True),
    ("github", "gpt-4o-mini",                    True),
]
```

### Formato actual de entidades (texto libre — problema conocido)

`_extraer_entidades()` devuelve texto plano:
```
ENTIDAD: Espectro
TABLA: espectros
CAMPOS: nombre VARCHAR(255), tipo VARCHAR(100), descripcion TEXT
RUTA_API: /api/espectros
```
Este formato es re-interpretado por cada llamada subsiguiente → fuente de inconsistencias.

---

## Problemas conocidos y soluciones planificadas

### 🔴 Problema 1 — Sin contrato estructurado entre llamadas IA

**Causa:** Las 4 llamadas comparten entidades como texto plano. Cada modelo re-interpreta los nombres de forma diferente (ej: `tabla_espectros` vs `Espectros`), generando mismatches silenciosos que solo se detectan en runtime.

**Síntoma real:** el nombre `seccionActiva` no coincide con el `*ngIf` del template → vista en blanco.

**Solución planificada:** `_extraer_entidades()` debe retornar un manifest JSON estructurado:

```python
{
  "entities": [
    {
      "class_name": "Espectro",         # Python/Angular class
      "table": "espectros",             # MySQL table
      "api_path": "/api/espectros",     # FastAPI route prefix
      "prop_name": "espectros",         # Angular array property (camelCase plural)
      "service_prefix": "Espectro",     # ApiService method prefix
      "fields": [
        {"name": "nombre", "sql_type": "VARCHAR(255)", "nullable": False, "sa_type": "String(255)"},
        {"name": "tipo",   "sql_type": "VARCHAR(100)", "nullable": True,  "sa_type": "String(100)"}
      ]
    }
  ]
}
```

Con este manifest, SQL / SQLAlchemy models / TypeScript interfaces se generan en Python puro — sin IA para las partes mecánicas.

---

### 🔴 Problema 2 — SQL generado por IA cuando puede generarse programáticamente

**Causa:** `schema.sql` lo escribe la IA. Errores frecuentes:
- Backticks faltantes en palabras reservadas (`order`, `type`, `key`)
- `FOREIGN KEY` que referencia tablas creadas después (error MySQL 1215)
- Trailing comma antes del cierre del `CREATE TABLE`

**Solución planificada:** Función `_generar_sql_desde_manifest(manifest)` en Python puro:

```python
def _generar_sql_desde_manifest(manifest: dict) -> str:
    lines = ["SET FOREIGN_KEY_CHECKS = 0;"]
    for entity in manifest["entities"]:
        table = entity["table"]
        lines.append(f"\nDROP TABLE IF EXISTS `{table}`;")
        lines.append(f"CREATE TABLE `{table}` (")
        lines.append("  `id` INT NOT NULL AUTO_INCREMENT,")
        for field in entity["fields"]:
            null = "DEFAULT NULL" if field["nullable"] else "NOT NULL"
            lines.append(f"  `{field['name']}` {field['sql_type']} {null},")
        lines.append("  `fecha_creacion` DATETIME DEFAULT CURRENT_TIMESTAMP,")
        lines.append("  PRIMARY KEY (`id`)")
        lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
    lines.append("\nSET FOREIGN_KEY_CHECKS = 1;")
    return "\n".join(lines)
```

Elimina el 100% de los errores SQL 1064 — Python escribe el SQL, no la IA.

---

### 🟠 Problema 3 — Un solo componente para todas las entidades

**Causa:** `main.component.ts` + `.html` + `.css` contienen todas las entidades. Para 5 entidades: HTML > 800 líneas, TS > 400 líneas. Todo debe caber en `max_tokens=16000`.

**Síntomas:**
- JSON truncado → error de parseo
- La IA "olvida" entidades en la mitad del template
- Nombres inconsistentes entre TS y HTML

**Solución planificada:** Un componente por entidad:

```
frontend/src/app/components/
├── shell/
│   ├── shell.component.ts      # Sidebar + router-outlet (generado en Python, sin IA)
│   └── shell.component.css
├── espectros/
│   └── espectros.component.ts  # ~150 líneas, solo Espectros
└── archivos/
    └── archivos.component.ts   # ~150 líneas, solo Archivos
```

Cada componente: ~1500 tokens de salida → cabe en cualquier modelo. Se pueden generar en paralelo (5 llamadas simultáneas).

---

### 🟠 Problema 4 — Scaffold con comentarios como instrucciones para la IA

**Causa:** `_prompt_frontend_componentes` entrega un scaffold con comentarios que le dicen a la IA qué generar:

```typescript
/* case 'espectros': return this.espectros;
   case 'archivos':  return this.archivos; */
```

La IA debe leer el comentario, generar el switch, usar los nombres correctos, para TODAS las entidades. Si falla un paso → error en runtime.

**Solución planificada:** Función `_generar_scaffold_ts(manifest)` en Python:

```python
def _generar_scaffold_ts(manifest: dict) -> str:
    entities = manifest["entities"]
    props = "\n  ".join(f"{e['prop_name']}: any[] = [];" for e in entities)
    cases = "\n      ".join(
        f"case '{e['prop_name']}': return this.{e['prop_name']};" for e in entities
    )
    init_calls = "\n    ".join(f"this.cargar{e['class_name']}s();" for e in entities)
    guardar_cases = "\n      ".join(
        f"case '{e['prop_name']}': this.guardar{e['class_name']}(); break;" for e in entities
    )
    # ... retorna el scaffold completo con switch, seccionActiva, ngOnInit correctos
```

La IA solo genera los métodos simples (`cargarEspectros()`, `guardarEspectro()`). El switch y los nombres vienen de Python → elimina toda la categoría de errores de inconsistencia de nombres.

---

### 🟡 Problema 5 — Sin pipeline de validación

**Causa:** El código generado va directo al ZIP sin ninguna verificación. Los errores solo se descubren cuando el usuario ejecuta el proyecto.

**Soluciones planificadas (por orden de esfuerzo):**

**5a. Python — `ast.parse()`:**
```python
def _validar_python(contenido: str, ruta: str) -> bool:
    try:
        ast.parse(contenido)
        return True
    except SyntaxError as e:
        log.error(f"[Validación] {ruta} tiene error de sintaxis: {e}")
        return False
```

**5b. HTML Angular — tags y emojis:**
```python
def _validar_html_angular(html: str) -> list[str]:
    errores = []
    if '️' in html:
        errores.append("Contiene variation selector U+FE0F (emoji corrupto)")
    emoji_pattern = re.compile("[\U0001F300-\U0001FFFF]", flags=re.UNICODE)
    if emoji_pattern.search(html):
        errores.append("Contiene emojis Unicode directos")
    return errores
```

**5c. SQL — estructura básica:**
```python
def _validar_sql(sql: str) -> list[str]:
    errores = []
    if 'FOREIGN_KEY_CHECKS = 0' not in sql:
        errores.append("Falta SET FOREIGN_KEY_CHECKS = 0")
    if re.search(r',\s*\n\s*\)', sql):
        errores.append("Trailing comma detectada en CREATE TABLE")
    tablas = re.findall(r'CREATE TABLE.*?;', sql, re.DOTALL)
    for t in tablas:
        if 'PRIMARY KEY' not in t:
            errores.append("CREATE TABLE sin PRIMARY KEY")
    return errores
```

---

### 🟡 Problema 6 — Token budget insuficiente para extracción de entidades

**Causa actual:**
```python
resp = _call_chain(_REASONING_CHAIN, prompt, max_tokens=3000, json_mode=False)
```
Los modelos de razonamiento (DeepSeek-R1, qwen-qwq-32b) consumen 1500–2000 tokens en `<think>` antes de responder. Con `max_tokens=3000`, solo quedan ~1000 tokens para la lista real de entidades. Para proyectos con 6–8 entidades, la respuesta se trunca.

**Solución planificada:** Aumentar a 5000–6000 tokens, o usar una cadena separada sin modelos de razonamiento para extracción estructurada (es pattern-matching, no requiere razonamiento complejo):

```python
_EXTRACTION_CHAIN = [
    ("github", "gpt-4o",                  True),   # JSON mode → salida estructurada garantizada
    ("groq",   "llama-3.3-70b-versatile", True),
    ("gemini", "gemini-2.5-flash",        True),
]
```

Y pedir el JSON directamente en el prompt en lugar de formato `ENTIDAD:/TABLA:`.

---

### 🟡 Problema 7 — Nombres de ejemplo conflictivos en prompts

**Causa:** Los prompts usan `Zeolita/zeolitas` en `_prompt_backend_router` y `Espectro/espectros` en `_prompt_frontend_componentes`. Si el proyecto real tiene una entidad llamada "Zeolita", la IA puede mezclar el ejemplo con la entidad real.

**Solución planificada:** Usar nombres claramente ficticios que nunca aparezcan en proyectos reales:
- `Zeolita` → `FooEntity` / `foo_entities`
- `Espectro` → `BarRecord` / `bar_records`

---

## Patrones de desarrollo establecidos

### Autenticación
- JWT: `access_token` 15 min, `refresh_token` 7 días
- Header: `Authorization: Bearer <token>`
- Dependency: `get_current_user()` en `app/core/dependencies.py`
- Todos los endpoints de datos requieren autenticación y filtran por `user_id`

### Servicios CRUD
```python
# Patrón estándar en todos los services
def create_X(db, data, user_id) → Model
def get_Xs_by_proyecto(db, proyecto_id, user_id) → list
def get_X_by_id(db, id, user_id) → Model | None
def update_X(db, obj, data) → Model
def delete_X(db, obj) → None
```

### Schemas Pydantic v2
```python
class EntidadBase(BaseModel): ...
class EntidadCreate(EntidadBase): ...
class EntidadResponse(EntidadBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### Respuesta de generación
```python
class GeneradorCodigoResponse(BaseModel):
    frontend: str   # archivos concatenados con marcadores @@FILE: path/to/file.ts
    backend: str
    database: str
```

---

## Variables de entorno requeridas (.env)

```env
DATABASE_URL=mysql+pymysql://root:<password>@localhost/srs_manager
SECRET_KEY=<jwt-secret>
GITHUB_TOKEN=<github-models-token>
GROQ_API_KEY=<groq-token>
GEMINI_API_KEY=<gemini-token>
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

---

## Comandos frecuentes

```bash
# Instalar dependencias
pip install -r requirements.txt

# Arrancar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Documentación interactiva
# http://localhost:8000/docs

# Test rápido de conectividad con IA
# GET /api/generador/test-conexion
```

---

## Endpoints principales del generador

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/generador/test-conexion` | Verifica que al menos un proveedor IA responde |
| `POST` | `/api/generador/codigo/{proyecto_id}` | Genera el proyecto completo (4 partes en secuencia) |
| `POST` | `/api/generador/diagrama/{proyecto_id}` | Genera diagrama Mermaid (`paquetes`, `clases`, `secuencia`, `casos_uso`) |

---

## Prioridad de mejoras

1. **Problema 1 + 2** (manifest JSON + SQL programático) — eliminan la mayor fuente de errores silenciosos
2. **Problema 6** (token budget extracción) — fix inmediato: cambiar `max_tokens=3000` a `5000`
3. **Problema 5a** (validación `ast.parse`) — bajo esfuerzo, alto valor
4. **Problema 4** (scaffold en Python) — necesita el manifest del Problema 1 primero
5. **Problema 3** (componente por entidad) — mayor refactor, necesita Problemas 1 y 4 primero
6. **Problema 7** (nombres ficticios en prompts) — cambio trivial, hacerlo junto con cualquier otra modificación a prompts
