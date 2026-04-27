from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class ValidacionCreate(BaseModel):
    proyecto_id:              int
    checklist_rf:             bool = False
    checklist_rnf:            bool = False
    checklist_casos_uso:      bool = False
    checklist_restricciones:  bool = False
    checklist_prioridades:    bool = False
    observaciones:            Optional[str] = None
    aprobador:                Optional[str] = None
    fecha:                    Optional[date] = None
    firma_digital:            Optional[str] = None
    aprobado:                 bool = False


class ValidacionUpdate(BaseModel):
    checklist_rf:             Optional[bool] = None
    checklist_rnf:            Optional[bool] = None
    checklist_casos_uso:      Optional[bool] = None
    checklist_restricciones:  Optional[bool] = None
    checklist_prioridades:    Optional[bool] = None
    observaciones:            Optional[str] = None
    aprobador:                Optional[str] = None
    fecha:                    Optional[date] = None
    firma_digital:            Optional[str] = None
    aprobado:                 Optional[bool] = None


class ValidacionResponse(BaseModel):
    id_validacion:            int
    proyecto_id:              int
    checklist_rf:             bool
    checklist_rnf:            bool
    checklist_casos_uso:      bool
    checklist_restricciones:  bool
    checklist_prioridades:    bool
    observaciones:            Optional[str] = None
    aprobador:                Optional[str] = None
    fecha:                    Optional[date] = None
    firma_digital:            Optional[str] = None
    aprobado:                 bool
    created_at:               datetime
    updated_at:               datetime

    class Config:
        from_attributes = True
