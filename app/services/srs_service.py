# app/services/srs_service.py
from sqlalchemy.orm import Session
from app.models.srs_documento import SrsDocumento
from app.models.proyecto import Proyecto
from app.schemas.srs_schema import SrsDocumentoCreate, SrsDocumentoUpdate
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import json


class SrsService:

    @staticmethod
    def create_srs(db: Session, srs_data: SrsDocumentoCreate):
        """Crea un nuevo documento SRS"""
        try:
            new_srs = SrsDocumento(
                proyecto_id=srs_data.proyecto_id,
                nombre_documento=srs_data.nombre_documento,
                introduccion=srs_data.introduccion,
                stakeholders=[s.dict() for s in (srs_data.stakeholders or [])],
                usuarios=[u.dict() for u in (srs_data.usuarios or [])],
                requerimientos_funcionales=[r.dict() for r in (srs_data.requerimientos_funcionales or [])],
                requerimientos_no_funcionales=[r.dict() for r in (srs_data.requerimientos_no_funcionales or [])],
                casos_uso=[c.dict() for c in (srs_data.casos_uso or [])],
                restricciones=[r.dict() for r in (srs_data.restricciones or [])],
                elicitacion=srs_data.elicitacion.dict() if srs_data.elicitacion else None,
                negociaciones=[n.dict() for n in (srs_data.negociaciones or [])],
                validacion_info=srs_data.validacion_info.dict() if srs_data.validacion_info else None,
                artefactos_info=[a.dict() for a in (srs_data.artefactos_info or [])],
            )
            db.add(new_srs)
            db.commit()
            db.refresh(new_srs)
            return new_srs
        except Exception as e:
            db.rollback()
            print(f"Error en create_srs: {str(e)}")
            raise e

    @staticmethod
    def get_srs_by_id(db: Session, srs_id: int):
        """Obtiene un SRS por ID"""
        try:
            return db.query(SrsDocumento).filter(SrsDocumento.id_srs == srs_id).first()
        except Exception as e:
            print(f"Error en get_srs_by_id: {str(e)}")
            raise e

    @staticmethod
    def get_srs_by_proyecto(db: Session, proyecto_id: int):
        """Obtiene todos los SRS de un proyecto"""
        try:
            return db.query(SrsDocumento).filter(
                SrsDocumento.proyecto_id == proyecto_id
            ).all()
        except Exception as e:
            print(f"Error en get_srs_by_proyecto: {str(e)}")
            raise e

    @staticmethod
    def update_srs(db: Session, srs_id: int, srs_data: SrsDocumentoUpdate):
        """Actualiza un SRS"""
        try:
            srs = db.query(SrsDocumento).filter(SrsDocumento.id_srs == srs_id).first()
            if not srs:
                return None

            if srs_data.nombre_documento:
                srs.nombre_documento = srs_data.nombre_documento
            if srs_data.introduccion:
                srs.introduccion = srs_data.introduccion
            if srs_data.stakeholders:
                srs.stakeholders = [s.dict() for s in srs_data.stakeholders]
            if srs_data.usuarios:
                srs.usuarios = [u.dict() for u in srs_data.usuarios]
            if srs_data.requerimientos_funcionales:
                srs.requerimientos_funcionales = [r.dict() for r in srs_data.requerimientos_funcionales]
            if srs_data.requerimientos_no_funcionales:
                srs.requerimientos_no_funcionales = [r.dict() for r in srs_data.requerimientos_no_funcionales]
            if srs_data.casos_uso:
                srs.casos_uso = [c.dict() for c in srs_data.casos_uso]
            if srs_data.restricciones:
                srs.restricciones = [r.dict() for r in srs_data.restricciones]
            if srs_data.elicitacion:
                srs.elicitacion = srs_data.elicitacion.dict()
            if srs_data.negociaciones:
                srs.negociaciones = [n.dict() for n in srs_data.negociaciones]
            if srs_data.validacion_info:
                srs.validacion_info = srs_data.validacion_info.dict()
            if srs_data.artefactos_info:
                srs.artefactos_info = [a.dict() for a in srs_data.artefactos_info]
            if srs_data.estado:
                srs.estado = srs_data.estado
            if srs_data.version:
                srs.version = srs_data.version

            db.commit()
            db.refresh(srs)
            return srs
        except Exception as e:
            db.rollback()
            print(f"Error en update_srs: {str(e)}")
            raise e

    @staticmethod
    def delete_srs(db: Session, srs_id: int):
        """Elimina un SRS"""
        try:
            srs = db.query(SrsDocumento).filter(SrsDocumento.id_srs == srs_id).first()
            if not srs:
                return False

            db.delete(srs)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error en delete_srs: {str(e)}")
            raise e

    # ══════════════════════════════════════════════════════════════════════
    #  AUTO-GENERAR SRS — jala datos de TODOS los módulos del proyecto
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def auto_generar_srs(db: Session, proyecto_id: int):
        """
        Genera (o actualiza) un SRS completo a partir de todos los módulos
        del proyecto: Stakeholders, Elicitación, Requerimientos, RNF,
        Casos de Uso, Restricciones, Negociación, Validación y Artefactos.
        """
        from app.models.stakeholder import Stakeholder
        from app.models.requerimiento_funcional import RequerimientoFuncional
        from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
        from app.models.tipo_usuario_proyecto import TipoUsuarioProyecto
        from app.models.caso_uso import CasoUso
        from app.models.restriccion import Restriccion
        from app.models.validacion import Validacion
        from app.models.elicitacion import (
            ElicitacionEntrevista,
            ElicitacionProceso,
            ElicitacionNecesidad,
        )
        from app.models.negociacion import Negociacion
        from app.models.artefacto import Artefacto

        proyecto = db.query(Proyecto).filter(
            Proyecto.id_proyecto == proyecto_id
        ).first()
        if not proyecto:
            return None

        # ── Consultar TODOS los módulos ──────────────────────────────────
        stakeholders  = db.query(Stakeholder).filter(Stakeholder.proyecto_id == proyecto_id).all()
        rfs           = db.query(RequerimientoFuncional).filter(RequerimientoFuncional.proyecto_id == proyecto_id).all()
        rnfs          = db.query(RequerimientoNoFuncional).filter(RequerimientoNoFuncional.proyecto_id == proyecto_id).all()
        tipos_usuario = db.query(TipoUsuarioProyecto).filter(TipoUsuarioProyecto.proyecto_id == proyecto_id).all()
        casos_uso     = db.query(CasoUso).filter(CasoUso.proyecto_id == proyecto_id).all()
        restricciones = db.query(Restriccion).filter(Restriccion.proyecto_id == proyecto_id).all()
        validacion    = db.query(Validacion).filter(Validacion.proyecto_id == proyecto_id).first()
        entrevistas   = db.query(ElicitacionEntrevista).filter(ElicitacionEntrevista.proyecto_id == proyecto_id).all()
        procesos      = db.query(ElicitacionProceso).filter(ElicitacionProceso.proyecto_id == proyecto_id).all()
        necesidades   = db.query(ElicitacionNecesidad).filter(
            ElicitacionNecesidad.proyecto_id == proyecto_id,
            ElicitacionNecesidad.seleccionada == 1,
        ).all()
        negociaciones = db.query(Negociacion).filter(Negociacion.proyecto_id == proyecto_id).all()
        artefactos    = db.query(Artefacto).filter(Artefacto.proyecto_id == proyecto_id).all()

        # ── Construir introducción ───────────────────────────────────────
        intro_parts = [
            f"Documento de Especificación de Requerimientos de Software (SRS) "
            f"para el proyecto \"{proyecto.nombre}\" ({proyecto.codigo}).",
        ]
        if proyecto.descripcion_problema:
            intro_parts.append(f"\nProblema: {proyecto.descripcion_problema}")
        if proyecto.objetivo_general:
            intro_parts.append(f"\nObjetivo General: {proyecto.objetivo_general}")
        if proyecto.analista_responsable:
            intro_parts.append(f"\nAnalista Responsable: {proyecto.analista_responsable}")
        introduccion = "\n".join(intro_parts)

        # ── Mapear stakeholders ──────────────────────────────────────────
        stakeholders_json = [
            {
                "name": s.nombre,
                "role": s.rol,
                "responsibility": (
                    f"Tipo: {s.tipo.value if hasattr(s.tipo, 'value') else s.tipo}, "
                    f"Área: {s.area or 'N/A'}, "
                    f"Influencia: {s.nivel_influencia.value if hasattr(s.nivel_influencia, 'value') else s.nivel_influencia}"
                ),
            }
            for s in stakeholders
        ]

        # ── Mapear usuarios ──────────────────────────────────────────────
        usuarios_json = [
            {
                "userId": f"USR-{i+1:03d}",
                "userType": t.tipo,
                "description": t.descripcion or "N/A",
            }
            for i, t in enumerate(tipos_usuario)
        ]

        # ── Mapear RFs ───────────────────────────────────────────────────
        rfs_json = [
            {
                "rfId": r.codigo,
                "description": r.descripcion,
                "priority": r.prioridad or "Media",
            }
            for r in rfs
        ]

        # ── Mapear RNFs ──────────────────────────────────────────────────
        rnfs_json = [
            {
                "rnfId": r.codigo,
                "category": str(r.tipo.value) if hasattr(r.tipo, "value") else str(r.tipo),
                "description": r.descripcion,
            }
            for r in rnfs
        ]

        # ── Mapear casos de uso ──────────────────────────────────────────
        casos_uso_json = [
            {
                "useCase": c.nombre,
                "actors": c.actores if isinstance(c.actores, list) else [],
                "description": c.descripcion or "",
                "steps": c.pasos if isinstance(c.pasos, list) else [],
            }
            for c in casos_uso
        ]

        # ── Mapear restricciones ─────────────────────────────────────────
        restricciones_json = [
            {
                "constraintId": r.codigo,
                "type": r.tipo or "General",
                "description": r.descripcion,
            }
            for r in restricciones
        ]

        # ── Mapear elicitación ───────────────────────────────────────────
        elicitacion_json = {
            "entrevistas": [
                {
                    "pregunta": e.pregunta,
                    "respuesta": e.respuesta,
                    "observaciones": e.observaciones,
                }
                for e in entrevistas
            ],
            "procesos": [
                {
                    "nombre_proceso": p.nombre_proceso,
                    "descripcion": p.descripcion,
                    "problemas_detectados": p.problemas_detectados,
                }
                for p in procesos
            ],
            "necesidades": [
                {"nombre": n.nombre}
                for n in necesidades
            ],
        }

        # ── Mapear negociaciones ─────────────────────────────────────────
        negociaciones_json = [
            {
                "nombre": n.nombre,
                "descripcion": n.descripcion,
                "prioridad": n.prioridad,
                "aceptado": bool(n.aceptado),
            }
            for n in negociaciones
        ]

        # ── Mapear validación ────────────────────────────────────────────
        validacion_json = None
        if validacion:
            validacion_json = {
                "aprobado": validacion.aprobado,
                "aprobador": validacion.aprobador,
                "observaciones": validacion.observaciones,
                "checklist_rf": validacion.checklist_rf,
                "checklist_rnf": validacion.checklist_rnf,
                "checklist_casos_uso": validacion.checklist_casos_uso,
                "checklist_restricciones": validacion.checklist_restricciones,
                "checklist_prioridades": validacion.checklist_prioridades,
            }

        # ── Mapear artefactos (metadatos + ruta para extracción en PDF) ──
        artefactos_json = [
            {
                "nombre": a.nombre,
                "categoria": a.categoria,
                "descripcion": a.descripcion,
                "nombre_archivo": a.nombre_archivo,
                "ruta_archivo": a.ruta_archivo,   # necesario para leer contenido en PDF
                "tipo_mime": a.tipo_mime,
            }
            for a in artefactos
        ]

        # ── Crear o actualizar SRS ───────────────────────────────────────
        existing = db.query(SrsDocumento).filter(
            SrsDocumento.proyecto_id == proyecto_id
        ).first()

        if existing:
            existing.nombre_documento = f"SRS — {proyecto.nombre}"
            existing.introduccion = introduccion
            existing.stakeholders = stakeholders_json
            existing.usuarios = usuarios_json
            existing.requerimientos_funcionales = rfs_json
            existing.requerimientos_no_funcionales = rnfs_json
            existing.casos_uso = casos_uso_json
            existing.restricciones = restricciones_json
            existing.elicitacion = elicitacion_json
            existing.negociaciones = negociaciones_json
            existing.validacion_info = validacion_json
            existing.artefactos_info = artefactos_json
            db.commit()
            db.refresh(existing)
            return existing
        else:
            srs = SrsDocumento(
                proyecto_id=proyecto_id,
                nombre_documento=f"SRS — {proyecto.nombre}",
                introduccion=introduccion,
                stakeholders=stakeholders_json,
                usuarios=usuarios_json,
                requerimientos_funcionales=rfs_json,
                requerimientos_no_funcionales=rnfs_json,
                casos_uso=casos_uso_json,
                restricciones=restricciones_json,
                elicitacion=elicitacion_json,
                negociaciones=negociaciones_json,
                validacion_info=validacion_json,
                artefactos_info=artefactos_json,
            )
            db.add(srs)
            db.commit()
            db.refresh(srs)
            return srs

    # ══════════════════════════════════════════════════════════════════════
    #  EXTRACCIÓN DE CONTENIDO DE ARCHIVOS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _extraer_contenido_archivo(ruta_relativa: str, max_chars: int = 6000) -> str | None:
        """
        Intenta leer el contenido textual de un artefacto.
        Soporta: .docx, .txt, .csv, .md, .xml, .json, .html, .pdf
        Retorna el texto extraído o None si no es legible / no existe.
        """
        import os
        from pathlib import Path

        # Buscar el archivo en varias rutas base posibles
        bases = [
            Path("."),                              # CWD del proceso (grafos/)
            Path(__file__).parent.parent.parent,    # raíz de grafos/
            Path(__file__).parent.parent.parent.parent,  # raíz de back_zeolitas/
        ]
        ruta = None
        for base in bases:
            candidate = base / ruta_relativa
            if candidate.exists():
                ruta = candidate
                break

        if not ruta:
            return None

        ext = ruta.suffix.lower()

        try:
            # ── DOCX ──────────────────────────────────────────────────
            if ext == ".docx":
                try:
                    import docx as python_docx
                    doc = python_docx.Document(str(ruta))
                    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                    text = "\n".join(paragraphs)
                    return text[:max_chars] if len(text) > max_chars else text
                except Exception:
                    # Fallback: leer XML interno del ZIP
                    import zipfile
                    import xml.etree.ElementTree as ET
                    with zipfile.ZipFile(str(ruta)) as z:
                        with z.open("word/document.xml") as f:
                            tree = ET.parse(f)
                            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                            texts = [node.text for node in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if node.text]
                            text = " ".join(texts)
                            return text[:max_chars] if len(text) > max_chars else text

            # ── PDF ────────────────────────────────────────────────────
            elif ext == ".pdf":
                try:
                    import pdfplumber
                    with pdfplumber.open(str(ruta)) as pdf:
                        pages_text = []
                        for page in pdf.pages[:10]:  # max 10 páginas
                            t = page.extract_text()
                            if t:
                                pages_text.append(t)
                        text = "\n".join(pages_text)
                        return text[:max_chars] if len(text) > max_chars else text
                except Exception:
                    return None

            # ── TEXTO PLANO (.txt, .csv, .md, .xml, .json, .html) ────
            elif ext in (".txt", ".csv", ".md", ".xml", ".json", ".html", ".htm", ".log", ".dpt"):
                with open(str(ruta), "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(max_chars)
                return text if text.strip() else None

            else:
                return None  # binario no soportado (imágenes, xlsx, etc.)

        except Exception as e:
            print(f"[SRS] No se pudo leer artefacto {ruta}: {e}")
            return None

    # ══════════════════════════════════════════════════════════════════════
    #  PDF PROFESIONAL
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def generate_pdf(db: Session, srs_id: int, proyecto_id: int):
        """Genera un PDF profesional del documento SRS"""
        from reportlab.platypus import HRFlowable, KeepTogether
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

        try:
            srs = db.query(SrsDocumento).filter(SrsDocumento.id_srs == srs_id).first()
            if not srs:
                return None
            proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
            if not proyecto:
                return None

            # ── Colores corporativos ─────────────────────────────────
            AZUL_OSCURO   = colors.HexColor('#0A2540')
            AZUL_MEDIO    = colors.HexColor('#0066CC')
            AZUL_CLARO    = colors.HexColor('#E8F0FE')
            GRIS_CLARO    = colors.HexColor('#F5F7FA')
            GRIS_BORDE    = colors.HexColor('#D1D9E0')
            VERDE         = colors.HexColor('#27AE60')
            ROJO          = colors.HexColor('#E74C3C')
            NARANJA       = colors.HexColor('#E67E22')
            AMARILLO_CLARO= colors.HexColor('#FFFDE7')
            TEXTO_OSCURO  = colors.HexColor('#1A1A2E')
            TEXTO_MEDIO   = colors.HexColor('#555555')

            # ── Buffer y documento ───────────────────────────────────
            pdf_buffer = BytesIO()
            PAGE_W, PAGE_H = A4
            MARGIN = 2.2 * 28.35  # ~2.2 cm

            # Callback para header/footer en cada página
            fecha_doc = datetime.now().strftime('%d/%m/%Y')

            def _on_page(canvas, doc):
                canvas.saveState()
                # Header barra azul
                canvas.setFillColor(AZUL_OSCURO)
                canvas.rect(0, PAGE_H - 22, PAGE_W, 22, fill=1, stroke=0)
                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica-Bold", 7.5)
                canvas.drawString(MARGIN, PAGE_H - 14, "ESPECIFICACIÓN DE REQUERIMIENTOS DE SOFTWARE (SRS)")
                canvas.setFont("Helvetica", 7.5)
                canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 14,
                                       f"{proyecto.nombre} | v{srs.version} | {fecha_doc}")
                # Footer barra azul
                canvas.setFillColor(AZUL_OSCURO)
                canvas.rect(0, 0, PAGE_W, 18, fill=1, stroke=0)
                canvas.setFillColor(colors.white)
                canvas.setFont("Helvetica", 7)
                canvas.drawString(MARGIN, 5, "Documento Confidencial — Generado automáticamente por el Sistema SRS")
                canvas.drawRightString(PAGE_W - MARGIN, 5, f"Página {doc.page}")
                canvas.restoreState()

            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                leftMargin=MARGIN, rightMargin=MARGIN,
                topMargin=MARGIN + 18, bottomMargin=MARGIN + 10,
            )

            styles = getSampleStyleSheet()

            # ── Estilos ──────────────────────────────────────────────
            def s(name, **kw):
                return ParagraphStyle(name, **kw)

            NORMAL = s('SRS_Normal', fontName='Helvetica', fontSize=9.5,
                       textColor=TEXTO_OSCURO, leading=14, spaceAfter=4)
            NORMAL_JUST = s('SRS_NormalJ', fontName='Helvetica', fontSize=9.5,
                            textColor=TEXTO_OSCURO, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
            ITALIC = s('SRS_Italic', fontName='Helvetica-Oblique', fontSize=9,
                       textColor=TEXTO_MEDIO, leading=13, spaceAfter=3)
            BOLD = s('SRS_Bold', fontName='Helvetica-Bold', fontSize=9.5,
                     textColor=TEXTO_OSCURO, leading=14, spaceAfter=2)

            def section_header(numero: str, titulo: str) -> list:
                """Barra completa azul oscuro para títulos de sección."""
                tbl = Table([[Paragraph(
                    f'<font color="white"><b>{numero}. {titulo}</b></font>',
                    s('SH', fontName='Helvetica-Bold', fontSize=12,
                      textColor=colors.white, leading=16)
                )]], colWidths=[doc.width])
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), AZUL_OSCURO),
                    ('TOPPADDING', (0,0), (-1,-1), 7),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ]))
                return [Spacer(1, 10), tbl, Spacer(1, 8)]

            def subsection_header(titulo: str) -> list:
                """Barra azul claro para sub-secciones."""
                tbl = Table([[Paragraph(
                    f'<font color="#004d99"><b>{titulo}</b></font>',
                    s('SSH', fontName='Helvetica-Bold', fontSize=10.5,
                      textColor=AZUL_MEDIO, leading=14)
                )]], colWidths=[doc.width])
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), AZUL_CLARO),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('ROUNDEDCORNERS', [4, 4, 4, 4]),
                ]))
                return [Spacer(1, 6), tbl, Spacer(1, 6)]

            def make_table(headers: list, rows: list, col_widths: list | None = None) -> Table:
                """Tabla con estilo profesional."""
                data = [headers] + rows
                n_cols = len(headers)
                cw = col_widths or [doc.width / n_cols] * n_cols
                tbl = Table(data, colWidths=cw, repeatRows=1)
                style = [
                    # Encabezado
                    ('BACKGROUND', (0,0), (-1,0), AZUL_MEDIO),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 9),
                    ('TOPPADDING', (0,0), (-1,0), 6),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    # Datos
                    ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,1), (-1,-1), 8.5),
                    ('TOPPADDING', (0,1), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 7),
                    ('RIGHTPADDING', (0,0), (-1,-1), 7),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    # Grid
                    ('GRID', (0,0), (-1,-1), 0.5, GRIS_BORDE),
                    ('LINEBELOW', (0,0), (-1,0), 1.5, AZUL_OSCURO),
                ]
                # Filas alternas
                for i in range(1, len(rows) + 1):
                    if i % 2 == 0:
                        style.append(('BACKGROUND', (0,i), (-1,i), GRIS_CLARO))
                tbl.setStyle(TableStyle(style))
                return tbl

            def priority_color(p: str) -> str:
                p_low = str(p).lower()
                if p_low == 'critica':   return '#7B1FA2'
                if p_low == 'alta':       return '#C62828'
                if p_low == 'media':      return '#E65100'
                return '#1565C0'

            def info_box(pairs: list[tuple]) -> Table:
                """Cuadro de metadatos con dos columnas clave:valor."""
                rows = [[
                    Paragraph(f'<b>{k}</b>', BOLD),
                    Paragraph(str(v), NORMAL)
                ] for k, v in pairs]
                tbl = Table(rows, colWidths=[doc.width * 0.28, doc.width * 0.72])
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), GRIS_CLARO),
                    ('BACKGROUND', (1,0), (1,-1), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, GRIS_BORDE),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                ]))
                return tbl

            # ── ═════════════════════════════════════════════════════
            #    PORTADA
            # ═════════════════════════════════════════════════════════
            story = []

            # Barra superior portada
            barra_top = Table([['']], colWidths=[doc.width + MARGIN * 2])
            barra_top.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), AZUL_OSCURO),
                ('TOPPADDING', (0,0), (-1,-1), 40),
                ('BOTTOMPADDING', (0,0), (-1,-1), 40),
            ]))
            story.append(barra_top)
            story.append(Spacer(1, 30))

            # Título portada
            story.append(Paragraph(
                '<font color="#0A2540"><b>ESPECIFICACIÓN DE</b></font>',
                s('PT1', fontName='Helvetica-Bold', fontSize=26,
                  textColor=AZUL_OSCURO, alignment=TA_CENTER, leading=32, spaceAfter=2)
            ))
            story.append(Paragraph(
                '<font color="#0066CC"><b>REQUERIMIENTOS DE SOFTWARE</b></font>',
                s('PT2', fontName='Helvetica-Bold', fontSize=26,
                  textColor=AZUL_MEDIO, alignment=TA_CENTER, leading=32, spaceAfter=4)
            ))
            story.append(Paragraph(
                '(SRS)',
                s('PT3', fontName='Helvetica', fontSize=16,
                  textColor=TEXTO_MEDIO, alignment=TA_CENTER, leading=22, spaceAfter=30)
            ))

            # Línea decorativa
            story.append(HRFlowable(width=doc.width * 0.5, thickness=2,
                                    color=AZUL_MEDIO, hAlign='CENTER', spaceAfter=30))

            # Nombre del proyecto
            story.append(Paragraph(
                f'<b>{proyecto.nombre}</b>',
                s('PN', fontName='Helvetica-Bold', fontSize=20,
                  textColor=AZUL_OSCURO, alignment=TA_CENTER, leading=26, spaceAfter=4)
            ))
            story.append(Paragraph(
                f'Código: {proyecto.codigo}',
                s('PC', fontName='Helvetica', fontSize=12,
                  textColor=TEXTO_MEDIO, alignment=TA_CENTER, leading=18, spaceAfter=40)
            ))

            # Tabla de metadatos portada
            meta = [
                ('Documento', srs.nombre_documento),
                ('Versión', srs.version),
                ('Estado', srs.estado),
                ('Fecha de generación', fecha_doc),
            ]
            if hasattr(proyecto, 'analista_responsable') and proyecto.analista_responsable:
                meta.append(('Analista responsable', proyecto.analista_responsable))

            meta_rows = [[
                Paragraph(f'<b>{k}</b>', s('MK', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)),
                Paragraph(str(v), s('MV', fontName='Helvetica', fontSize=10, textColor=TEXTO_OSCURO))
            ] for k, v in meta]
            meta_tbl = Table(meta_rows, colWidths=[doc.width * 0.35, doc.width * 0.65])
            meta_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), AZUL_MEDIO),
                ('BACKGROUND', (1,0), (1,-1), GRIS_CLARO),
                ('GRID', (0,0), (-1,-1), 0.5, GRIS_BORDE),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(meta_tbl)
            story.append(Spacer(1, 40))

            # Línea decorativa inferior portada
            story.append(HRFlowable(width=doc.width, thickness=1,
                                    color=GRIS_BORDE, hAlign='CENTER', spaceAfter=8))
            story.append(Paragraph(
                'Documento generado automáticamente — Confidencial',
                s('CONF', fontName='Helvetica-Oblique', fontSize=8,
                  textColor=TEXTO_MEDIO, alignment=TA_CENTER)
            ))
            story.append(PageBreak())

            # ── ═════════════════════════════════════════════════════
            #    1. INTRODUCCIÓN
            # ═════════════════════════════════════════════════════════
            story += section_header('1', 'Introducción')
            if srs.introduccion:
                for linea in srs.introduccion.split('\n'):
                    if linea.strip():
                        story.append(Paragraph(linea.strip(), NORMAL_JUST))
                        story.append(Spacer(1, 4))
            else:
                story.append(Paragraph('Sin introducción registrada.', ITALIC))
            story.append(Spacer(1, 8))

            # ── ═════════════════════════════════════════════════════
            #    2. STAKEHOLDERS
            # ═════════════════════════════════════════════════════════
            if srs.stakeholders:
                story.append(PageBreak())
                story += section_header('2', 'Stakeholders')
                headers = [
                    Paragraph('<b>#</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Nombre</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Rol</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Responsabilidad / Info</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                rows = []
                for i, sh in enumerate(srs.stakeholders, 1):
                    rows.append([
                        Paragraph(str(i), NORMAL),
                        Paragraph(sh.get('name', 'N/A'), BOLD),
                        Paragraph(sh.get('role', 'N/A'), NORMAL),
                        Paragraph(sh.get('responsibility', 'N/A'), NORMAL),
                    ])
                story.append(make_table(headers, rows,
                                        [doc.width*0.05, doc.width*0.2, doc.width*0.2, doc.width*0.55]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    3. ELICITACIÓN
            # ═════════════════════════════════════════════════════════
            elicitacion = srs.elicitacion or {}
            entrevistas  = elicitacion.get("entrevistas", [])
            procesos     = elicitacion.get("procesos", [])
            necesidades  = elicitacion.get("necesidades", [])
            if entrevistas or procesos or necesidades:
                story.append(PageBreak())
                story += section_header('3', 'Elicitación de Requerimientos')

                if entrevistas:
                    story += subsection_header('3.1 Entrevistas')
                    for i, ent in enumerate(entrevistas, 1):
                        block = [
                            info_box([
                                (f'Entrevista {i}', ''),
                                ('Pregunta', ent.get('pregunta', '')),
                                ('Respuesta', ent.get('respuesta') or 'Sin registrar'),
                            ])
                        ]
                        if ent.get('observaciones'):
                            block.append(Spacer(1, 3))
                            block.append(Paragraph(f"<i>Observaciones: {ent['observaciones']}</i>", ITALIC))
                        story.append(KeepTogether(block))
                        story.append(Spacer(1, 8))

                if procesos:
                    story += subsection_header('3.2 Procesos de Negocio')
                    proc_headers = [
                        Paragraph('<b>Proceso</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                        Paragraph('<b>Descripción</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                        Paragraph('<b>Problemas detectados</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    ]
                    proc_rows = [[
                        Paragraph(p.get('nombre_proceso', ''), BOLD),
                        Paragraph(p.get('descripcion') or 'N/A', NORMAL),
                        Paragraph(p.get('problemas_detectados') or '—',
                                  s('PROB', fontName='Helvetica-Oblique', fontSize=9,
                                    textColor=colors.HexColor('#C0392B'), leading=13)),
                    ] for p in procesos]
                    story.append(make_table(proc_headers, proc_rows,
                                            [doc.width*0.28, doc.width*0.38, doc.width*0.34]))
                    story.append(Spacer(1, 10))

                if necesidades:
                    story += subsection_header('3.3 Necesidades Identificadas')
                    nec_rows = [[
                        Paragraph(str(i), NORMAL),
                        Paragraph(n.get('nombre', ''), NORMAL),
                    ] for i, n in enumerate(necesidades, 1)]
                    nec_headers = [
                        Paragraph('<b>#</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                        Paragraph('<b>Necesidad</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    ]
                    story.append(make_table(nec_headers, nec_rows, [doc.width*0.08, doc.width*0.92]))
                    story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    4. USUARIOS
            # ═════════════════════════════════════════════════════════
            if srs.usuarios:
                story.append(PageBreak())
                story += section_header('4', 'Usuarios del Sistema')
                usr_headers = [
                    Paragraph('<b>ID</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Tipo de Usuario</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Descripción</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                usr_rows = [[
                    Paragraph(u.get('userId', ''), NORMAL),
                    Paragraph(u.get('userType', 'N/A'), BOLD),
                    Paragraph(u.get('description', 'N/A'), NORMAL),
                ] for u in srs.usuarios]
                story.append(make_table(usr_headers, usr_rows,
                                        [doc.width*0.15, doc.width*0.25, doc.width*0.60]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    5. REQUERIMIENTOS FUNCIONALES
            # ═════════════════════════════════════════════════════════
            if srs.requerimientos_funcionales:
                story.append(PageBreak())
                story += section_header('5', 'Requerimientos Funcionales')
                rf_headers = [
                    Paragraph('<b>Código</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Descripción</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Prioridad</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                rf_rows = []
                for rf in srs.requerimientos_funcionales:
                    prio = rf.get('priority', 'Media')
                    pc = priority_color(prio)
                    rf_rows.append([
                        Paragraph(f'<b>{rf.get("rfId", "RF")}</b>',
                                  s('RFId', fontName='Helvetica-Bold', fontSize=9,
                                    textColor=colors.HexColor('#0D47A1'))),
                        Paragraph(rf.get('description', 'N/A'), NORMAL),
                        Paragraph(f'<font color="{pc}"><b>{prio}</b></font>',
                                  s('PR', fontName='Helvetica-Bold', fontSize=9,
                                    textColor=colors.HexColor(pc))),
                    ])
                story.append(make_table(rf_headers, rf_rows,
                                        [doc.width*0.14, doc.width*0.70, doc.width*0.16]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    6. REQUERIMIENTOS NO FUNCIONALES
            # ═════════════════════════════════════════════════════════
            if srs.requerimientos_no_funcionales:
                story += section_header('6', 'Requerimientos No Funcionales')
                rnf_headers = [
                    Paragraph('<b>Código</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Categoría</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Descripción</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                rnf_rows = [[
                    Paragraph(f'<b>{r.get("rnfId", "RNF")}</b>',
                              s('RNFId', fontName='Helvetica-Bold', fontSize=9,
                                textColor=colors.HexColor('#880E4F'))),
                    Paragraph(r.get('category', 'N/A'), BOLD),
                    Paragraph(r.get('description', 'N/A'), NORMAL),
                ] for r in srs.requerimientos_no_funcionales]
                story.append(make_table(rnf_headers, rnf_rows,
                                        [doc.width*0.14, doc.width*0.22, doc.width*0.64]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    7. CASOS DE USO
            # ═════════════════════════════════════════════════════════
            if srs.casos_uso:
                story.append(PageBreak())
                story += section_header('7', 'Casos de Uso')
                for i, uc in enumerate(srs.casos_uso, 1):
                    actores = ', '.join(uc.get('actors', [])) or 'N/A'
                    pasos   = uc.get('steps', [])
                    block = [info_box([
                        (f'CU-{i:02d}', uc.get('useCase', 'N/A')),
                        ('Actores', actores),
                        ('Descripción', uc.get('description') or 'N/A'),
                    ])]
                    if pasos:
                        paso_txt = '\n'.join(f'{j}. {p}' for j, p in enumerate(pasos, 1))
                        paso_box = Table([[Paragraph(
                            '<b>Flujo principal:</b>', BOLD
                        )], *[
                            [Paragraph(f'  {j}. {p}', NORMAL)] for j, p in enumerate(pasos, 1)
                        ]], colWidths=[doc.width])
                        paso_box.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), AZUL_CLARO),
                            ('BACKGROUND', (0,1), (-1,-1), colors.white),
                            ('GRID', (0,0), (-1,-1), 0.5, GRIS_BORDE),
                            ('LEFTPADDING', (0,0), (-1,-1), 10),
                            ('TOPPADDING', (0,0), (-1,-1), 4),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ]))
                        block.append(paso_box)
                    story.append(KeepTogether(block))
                    story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    8. RESTRICCIONES
            # ═════════════════════════════════════════════════════════
            if srs.restricciones:
                story += section_header('8', 'Restricciones')
                rest_headers = [
                    Paragraph('<b>Código</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Tipo</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Descripción</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                rest_rows = [[
                    Paragraph(f'<b>{r.get("constraintId", "C")}</b>',
                              s('CId', fontName='Helvetica-Bold', fontSize=9,
                                textColor=colors.HexColor('#E65100'))),
                    Paragraph(r.get('type', 'General'), BOLD),
                    Paragraph(r.get('description', 'N/A'), NORMAL),
                ] for r in srs.restricciones]
                story.append(make_table(rest_headers, rest_rows,
                                        [doc.width*0.14, doc.width*0.20, doc.width*0.66]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    9. NEGOCIACIÓN
            # ═════════════════════════════════════════════════════════
            negociaciones = srs.negociaciones or []
            if negociaciones:
                story.append(PageBreak())
                story += section_header('9', 'Negociación de Requerimientos')
                neg_headers = [
                    Paragraph('<b>Requerimiento</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Descripción</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Prioridad</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Estado</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                neg_rows = []
                for neg in negociaciones:
                    prio = neg.get('prioridad', 'Media')
                    pc = priority_color(prio)
                    aceptado = neg.get('aceptado', False)
                    estado_color = '#27AE60' if aceptado else '#E65100'
                    estado_txt   = 'Aceptado' if aceptado else 'Pendiente'
                    neg_rows.append([
                        Paragraph(neg.get('nombre', ''), BOLD),
                        Paragraph(neg.get('descripcion', 'N/A'), NORMAL),
                        Paragraph(f'<font color="{pc}"><b>{prio}</b></font>',
                                  s('NP', fontName='Helvetica-Bold', fontSize=9)),
                        Paragraph(f'<font color="{estado_color}"><b>{estado_txt}</b></font>',
                                  s('NE', fontName='Helvetica-Bold', fontSize=9)),
                    ])
                story.append(make_table(neg_headers, neg_rows,
                                        [doc.width*0.25, doc.width*0.45, doc.width*0.15, doc.width*0.15]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    10. VALIDACIÓN
            # ═════════════════════════════════════════════════════════
            val_info = srs.validacion_info
            if val_info:
                story += section_header('10', 'Estado de Validación')
                aprobado = val_info.get('aprobado', False)
                color_estado = VERDE if aprobado else ROJO
                estado_txt   = 'APROBADO ✓' if aprobado else 'NO APROBADO ✗'

                # Estado principal
                estado_tbl = Table([[
                    Paragraph(f'<font color="white"><b>{estado_txt}</b></font>',
                              s('EST', fontName='Helvetica-Bold', fontSize=14,
                                textColor=colors.white, alignment=TA_CENTER))
                ]], colWidths=[doc.width])
                estado_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), color_estado),
                    ('TOPPADDING', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ]))
                story.append(estado_tbl)
                story.append(Spacer(1, 10))

                story.append(info_box([
                    ('Aprobador', val_info.get('aprobador') or 'No especificado'),
                    ('Observaciones', val_info.get('observaciones') or 'Sin observaciones'),
                ]))
                story.append(Spacer(1, 10))

                # Checklist
                checks = [
                    ('Requerimientos Funcionales', val_info.get('checklist_rf')),
                    ('Requerimientos No Funcionales', val_info.get('checklist_rnf')),
                    ('Casos de Uso', val_info.get('checklist_casos_uso')),
                    ('Restricciones', val_info.get('checklist_restricciones')),
                    ('Prioridades', val_info.get('checklist_prioridades')),
                ]
                check_rows = [[
                    Paragraph(nombre, NORMAL),
                    Paragraph(
                        f'<font color="{"#27AE60" if ok else "#E74C3C"}"><b>{"✓ Verificado" if ok else "✗ Pendiente"}</b></font>',
                        s('CK', fontName='Helvetica-Bold', fontSize=9)
                    ),
                ] for nombre, ok in checks]
                check_headers = [
                    Paragraph('<b>Elemento de Validación</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                    Paragraph('<b>Estado</b>', s('TH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
                ]
                story.append(make_table(check_headers, check_rows,
                                        [doc.width*0.75, doc.width*0.25]))
                story.append(Spacer(1, 10))

            # ── ═════════════════════════════════════════════════════
            #    11. ARTEFACTOS  (con contenido de archivo)
            # ═════════════════════════════════════════════════════════
            artefactos = srs.artefactos_info or []
            if artefactos:
                story.append(PageBreak())
                story += section_header('11', 'Artefactos del Proyecto')

                for i, art in enumerate(artefactos, 1):
                    nombre_art = art.get('nombre', 'Sin nombre')
                    cat        = art.get('categoria', '')
                    desc       = art.get('descripcion', '')
                    archivo    = art.get('nombre_archivo', '')
                    ruta_rel   = art.get('ruta_archivo', '')  # puede venir en artefactos_info o no

                    # Buscar ruta en la DB si no está en el JSON guardado
                    if not ruta_rel:
                        from app.models.artefacto import Artefacto as ArtefactoModel
                        a_db = db.query(ArtefactoModel).filter(
                            ArtefactoModel.nombre_archivo == archivo,
                            ArtefactoModel.proyecto_id == proyecto_id
                        ).first()
                        if a_db:
                            ruta_rel = a_db.ruta_archivo

                    # Extraer contenido del archivo
                    contenido = None
                    if ruta_rel:
                        contenido = SrsService._extraer_contenido_archivo(ruta_rel)

                    # Encabezado del artefacto
                    art_header = Table([[
                        Paragraph(
                            f'<font color="white"><b>{i}. {nombre_art}</b></font>',
                            s('AH', fontName='Helvetica-Bold', fontSize=10.5, textColor=colors.white)
                        ),
                        Paragraph(
                            f'<font color="#B3D4FC"><i>{cat}</i></font>',
                            s('AC', fontName='Helvetica-Oblique', fontSize=9,
                              textColor=colors.HexColor('#B3D4FC'), alignment=TA_RIGHT)
                        ),
                    ]], colWidths=[doc.width * 0.65, doc.width * 0.35])
                    art_header.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#004D99')),
                        ('TOPPADDING', (0,0), (-1,-1), 7),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                        ('LEFTPADDING', (0,0), (-1,-1), 10),
                        ('RIGHTPADDING', (0,0), (-1,-1), 10),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ]))
                    story.append(art_header)

                    # Metadatos
                    meta_pairs = [('Archivo', archivo)]
                    if desc:
                        meta_pairs.append(('Descripción', desc))
                    story.append(info_box(meta_pairs))

                    # Contenido del archivo
                    if contenido:
                        story.append(Spacer(1, 4))
                        story += subsection_header('Contenido del archivo')
                        # Dividir en párrafos por salto de línea
                        lines = contenido.split('\n')
                        content_items = []
                        for line in lines:
                            line = line.strip()
                            if not line:
                                content_items.append(Spacer(1, 4))
                            else:
                                # Escapar caracteres especiales XML
                                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                content_items.append(Paragraph(line, NORMAL))
                        story.extend(content_items)
                        if len(contenido) >= 5900:
                            story.append(Paragraph(
                                '<i>[ Contenido truncado — ver archivo completo adjunto ]</i>', ITALIC))
                    else:
                        story.append(Spacer(1, 4))
                        story.append(Paragraph(
                            '<i>Contenido no disponible (archivo binario, no encontrado, o formato no soportado).</i>',
                            ITALIC
                        ))

                    story.append(Spacer(1, 14))

            # ── Construir PDF ────────────────────────────────────────
            doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
            pdf_buffer.seek(0)
            return pdf_buffer

        except Exception as e:
            import traceback
            print(f"Error en generate_pdf: {e}")
            traceback.print_exc()
            raise e
