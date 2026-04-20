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

        # ── Mapear artefactos (solo metadatos) ───────────────────────────
        artefactos_json = [
            {
                "nombre": a.nombre,
                "categoria": a.categoria,
                "descripcion": a.descripcion,
                "nombre_archivo": a.nombre_archivo,
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
    #  PDF
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def generate_pdf(db: Session, srs_id: int, proyecto_id: int):
        """Genera un PDF del documento SRS"""
        try:
            # Obtener datos del SRS
            srs = db.query(SrsDocumento).filter(SrsDocumento.id_srs == srs_id).first()
            if not srs:
                return None

            # Obtener datos del proyecto
            proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
            if not proyecto:
                return None

            # Crear PDF en memoria
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#0066cc'),
                spaceAfter=12,
                alignment=1
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#004d99'),
                spaceAfter=10,
                spaceBefore=12
            )

            # Título
            story.append(Paragraph("Documento de Especificación de Requerimientos (SRS)", title_style))
            story.append(Spacer(1, 12))

            # Información del proyecto
            story.append(Paragraph(f"<b>Proyecto:</b> {proyecto.nombre}", styles['Normal']))
            story.append(Paragraph(f"<b>Código:</b> {proyecto.codigo}", styles['Normal']))
            story.append(Paragraph(f"<b>Documento:</b> {srs.nombre_documento}", styles['Normal']))
            story.append(Paragraph(f"<b>Versión:</b> {srs.version}", styles['Normal']))
            story.append(Paragraph(f"<b>Estado:</b> {srs.estado}", styles['Normal']))
            story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
            story.append(Spacer(1, 20))

            # 1. Introducción
            story.append(Paragraph("1. Introducción", heading_style))
            if srs.introduccion:
                story.append(Paragraph(srs.introduccion, styles['Normal']))
            story.append(Spacer(1, 12))

            # 2. Stakeholders
            if srs.stakeholders:
                story.append(Paragraph("2. Stakeholders", heading_style))
                for i, sh in enumerate(srs.stakeholders, 1):
                    story.append(Paragraph(f"<b>{i}. {sh.get('name', 'N/A')}</b>", styles['Normal']))
                    story.append(Paragraph(f"Rol: {sh.get('role', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"Responsabilidad: {sh.get('responsibility', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 8))

            # 3. Usuarios
            if srs.usuarios:
                story.append(PageBreak())
                story.append(Paragraph("3. Usuarios", heading_style))
                for i, user in enumerate(srs.usuarios, 1):
                    story.append(Paragraph(f"<b>{i}. {user.get('userType', 'N/A')} ({user.get('userId', 'N/A')})</b>",
                                           styles['Normal']))
                    story.append(Paragraph(user.get('description', 'N/A'), styles['Normal']))
                    story.append(Spacer(1, 8))

            # 4. Elicitación
            elicitacion = srs.elicitacion or {}
            entrevistas = elicitacion.get("entrevistas", [])
            procesos = elicitacion.get("procesos", [])
            necesidades = elicitacion.get("necesidades", [])
            if entrevistas or procesos or necesidades:
                story.append(PageBreak())
                story.append(Paragraph("4. Elicitación de Requerimientos", heading_style))

                if entrevistas:
                    story.append(Paragraph("<b>4.1 Entrevistas</b>", styles['Normal']))
                    for i, ent in enumerate(entrevistas, 1):
                        story.append(Paragraph(f"<b>Pregunta {i}:</b> {ent.get('pregunta', '')}", styles['Normal']))
                        story.append(Paragraph(f"Respuesta: {ent.get('respuesta', 'N/A')}", styles['Normal']))
                        if ent.get("observaciones"):
                            story.append(Paragraph(f"<i>Obs: {ent['observaciones']}</i>", styles['Normal']))
                        story.append(Spacer(1, 6))

                if procesos:
                    story.append(Paragraph("<b>4.2 Procesos de Negocio</b>", styles['Normal']))
                    for i, proc in enumerate(procesos, 1):
                        story.append(Paragraph(f"<b>{i}. {proc.get('nombre_proceso', '')}</b>", styles['Normal']))
                        story.append(Paragraph(proc.get('descripcion', 'N/A'), styles['Normal']))
                        if proc.get("problemas_detectados"):
                            story.append(Paragraph(f"<i>Problemas: {proc['problemas_detectados']}</i>", styles['Normal']))
                        story.append(Spacer(1, 6))

                if necesidades:
                    story.append(Paragraph("<b>4.3 Necesidades Identificadas</b>", styles['Normal']))
                    for nec in necesidades:
                        story.append(Paragraph(f"• {nec.get('nombre', '')}", styles['Normal']))
                    story.append(Spacer(1, 6))

            # 5. Requerimientos Funcionales
            if srs.requerimientos_funcionales:
                story.append(PageBreak())
                story.append(Paragraph("5. Requerimientos Funcionales", heading_style))
                for i, rf in enumerate(srs.requerimientos_funcionales, 1):
                    story.append(Paragraph(f"<b>{rf.get('rfId', 'RF-' + str(i))}</b>", styles['Normal']))
                    story.append(Paragraph(rf.get('description', 'N/A'), styles['Normal']))
                    story.append(Paragraph(f"<i>Prioridad: {rf.get('priority', 'Media')}</i>", styles['Normal']))
                    story.append(Spacer(1, 8))

            # 6. Requerimientos No Funcionales
            if srs.requerimientos_no_funcionales:
                story.append(PageBreak())
                story.append(Paragraph("6. Requerimientos No Funcionales", heading_style))
                for i, rnf in enumerate(srs.requerimientos_no_funcionales, 1):
                    story.append(Paragraph(f"<b>{rnf.get('rnfId', 'RNF-' + str(i))} - {rnf.get('category', 'N/A')}</b>",
                                           styles['Normal']))
                    story.append(Paragraph(rnf.get('description', 'N/A'), styles['Normal']))
                    story.append(Spacer(1, 8))

            # 7. Casos de Uso
            if srs.casos_uso:
                story.append(PageBreak())
                story.append(Paragraph("7. Casos de Uso", heading_style))
                for i, uc in enumerate(srs.casos_uso, 1):
                    story.append(Paragraph(f"<b>{i}. {uc.get('useCase', 'N/A')}</b>", styles['Normal']))
                    story.append(Paragraph(f"Actores: {', '.join(uc.get('actors', []))}", styles['Normal']))
                    story.append(Paragraph(uc.get('description', 'N/A'), styles['Normal']))
                    if uc.get('steps'):
                        story.append(Paragraph("<b>Pasos:</b>", styles['Normal']))
                        for j, step in enumerate(uc.get('steps', []), 1):
                            story.append(Paragraph(f"{j}. {step}", styles['Normal']))
                    story.append(Spacer(1, 8))

            # 8. Restricciones
            if srs.restricciones:
                story.append(PageBreak())
                story.append(Paragraph("8. Restricciones", heading_style))
                for i, cons in enumerate(srs.restricciones, 1):
                    story.append(
                        Paragraph(f"<b>{cons.get('constraintId', 'C-' + str(i))} ({cons.get('type', 'N/A')})</b>",
                                  styles['Normal']))
                    story.append(Paragraph(cons.get('description', 'N/A'), styles['Normal']))
                    story.append(Spacer(1, 8))

            # 9. Negociación
            negociaciones = srs.negociaciones or []
            if negociaciones:
                story.append(PageBreak())
                story.append(Paragraph("9. Negociación de Requerimientos", heading_style))
                for i, neg in enumerate(negociaciones, 1):
                    estado = "Aceptado" if neg.get("aceptado") else "Pendiente"
                    story.append(Paragraph(
                        f"<b>{i}. {neg.get('nombre', '')} [{estado}] — Prioridad: {neg.get('prioridad', 'Media')}</b>",
                        styles['Normal'],
                    ))
                    story.append(Paragraph(neg.get("descripcion", "N/A"), styles['Normal']))
                    story.append(Spacer(1, 8))

            # 10. Validación
            val_info = srs.validacion_info
            if val_info:
                story.append(Paragraph("10. Estado de Validación", heading_style))
                story.append(Paragraph(f"Aprobado: {'Sí' if val_info.get('aprobado') else 'No'}", styles['Normal']))
                story.append(Paragraph(f"Aprobador: {val_info.get('aprobador', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"Observaciones: {val_info.get('observaciones', 'N/A')}", styles['Normal']))
                story.append(Spacer(1, 8))

            # 11. Artefactos
            artefactos = srs.artefactos_info or []
            if artefactos:
                story.append(Paragraph("11. Artefactos del Proyecto", heading_style))
                for i, art in enumerate(artefactos, 1):
                    story.append(Paragraph(
                        f"<b>{i}. {art.get('nombre', '')} ({art.get('categoria', '')})</b>",
                        styles['Normal'],
                    ))
                    story.append(Paragraph(f"Archivo: {art.get('nombre_archivo', '')}", styles['Normal']))
                    if art.get("descripcion"):
                        story.append(Paragraph(art["descripcion"], styles['Normal']))
                    story.append(Spacer(1, 6))

            # Construir PDF
            doc.build(story)
            pdf_buffer.seek(0)

            return pdf_buffer
        except Exception as e:
            print(f"Error en generate_pdf: {str(e)}")
            raise e
