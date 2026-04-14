from pydantic import BaseModel
from typing import Literal


class GeneradorCodigoResponse(BaseModel):
    frontend: str
    backend: str
    database: str


class GeneradorDiagramaRequest(BaseModel):
    tipo: Literal["paquetes", "clases", "secuencia", "casos_uso"]


class GeneradorDiagramaResponse(BaseModel):
    tipo: str
    codigo_mermaid: str
