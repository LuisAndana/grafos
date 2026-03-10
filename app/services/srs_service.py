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
                restricciones=[r.dict() for r in (srs_data.restricciones or [])]
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

            # Introducción
            story.append(Paragraph("1. Introducción", heading_style))
            if srs.introduccion:
                story.append(Paragraph(srs.introduccion, styles['Normal']))
            story.append(Spacer(1, 12))

            # Stakeholders
            if srs.stakeholders:
                story.append(Paragraph("2. Stakeholders", heading_style))
                for i, sh in enumerate(srs.stakeholders, 1):
                    story.append(Paragraph(f"<b>{i}. {sh.get('name', 'N/A')}</b>", styles['Normal']))
                    story.append(Paragraph(f"Rol: {sh.get('role', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"Responsabilidad: {sh.get('responsibility', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 8))

            # Usuarios
            if srs.usuarios:
                story.append(PageBreak())
                story.append(Paragraph("3. Usuarios", heading_style))
                for i, user in enumerate(srs.usuarios, 1):
                    story.append(Paragraph(f"<b>{i}. {user.get('userType', 'N/A')} ({user.get('userId', 'N/A')})</b>",
                                           styles['Normal']))
                    story.append(Paragraph(user.get('description', 'N/A'), styles['Normal']))
                    story.append(Spacer(1, 8))

            # Requerimientos Funcionales
            if srs.requerimientos_funcionales:
                story.append(PageBreak())
                story.append(Paragraph("4. Requerimientos Funcionales", heading_style))
                for i, rf in enumerate(srs.requerimientos_funcionales, 1):
                    story.append(Paragraph(f"<b>{rf.get('rfId', 'RF-' + str(i))}</b>", styles['Normal']))
                    story.append(Paragraph(rf.get('description', 'N/A'), styles['Normal']))
                    story.append(Paragraph(f"<i>Prioridad: {rf.get('priority', 'Media')}</i>", styles['Normal']))
                    story.append(Spacer(1, 8))

            # Requerimientos No Funcionales
            if srs.requerimientos_no_funcionales:
                story.append(PageBreak())
                story.append(Paragraph("5. Requerimientos No Funcionales", heading_style))
                for i, rnf in enumerate(srs.requerimientos_no_funcionales, 1):
                    story.append(Paragraph(f"<b>{rnf.get('rnfId', 'RNF-' + str(i))} - {rnf.get('category', 'N/A')}</b>",
                                           styles['Normal']))
                    story.append(Paragraph(rnf.get('description', 'N/A'), styles['Normal']))
                    story.append(Spacer(1, 8))

            # Casos de Uso
            if srs.casos_uso:
                story.append(PageBreak())
                story.append(Paragraph("6. Casos de Uso", heading_style))
                for i, uc in enumerate(srs.casos_uso, 1):
                    story.append(Paragraph(f"<b>{i}. {uc.get('useCase', 'N/A')}</b>", styles['Normal']))
                    story.append(Paragraph(f"Actores: {', '.join(uc.get('actors', []))}", styles['Normal']))
                    story.append(Paragraph(uc.get('description', 'N/A'), styles['Normal']))
                    if uc.get('steps'):
                        story.append(Paragraph("<b>Pasos:</b>", styles['Normal']))
                        for j, step in enumerate(uc.get('steps', []), 1):
                            story.append(Paragraph(f"{j}. {step}", styles['Normal']))
                    story.append(Spacer(1, 8))

            # Restricciones
            if srs.restricciones:
                story.append(PageBreak())
                story.append(Paragraph("7. Restricciones", heading_style))
                for i, cons in enumerate(srs.restricciones, 1):
                    story.append(
                        Paragraph(f"<b>{cons.get('constraintId', 'C-' + str(i))} ({cons.get('type', 'N/A')})</b>",
                                  styles['Normal']))
                    story.append(Paragraph(cons.get('description', 'N/A'), styles['Normal']))
                    story.append(Spacer(1, 8))

            # Construir PDF
            doc.build(story)
            pdf_buffer.seek(0)

            return pdf_buffer
        except Exception as e:
            print(f"Error en generate_pdf: {str(e)}")
            raise e