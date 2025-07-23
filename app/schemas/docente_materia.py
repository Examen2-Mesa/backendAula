from pydantic import BaseModel
from app.schemas.materia import MateriaOut
from app.schemas.docente import DocenteOut


class AsignacionBase(BaseModel):
    docente_id: int
    materia_id: int


class AsignacionCreate(AsignacionBase):
    pass


class AsignacionOut(AsignacionBase):
    id: int

    class Config:
        from_attributes = True


# Nuevos esquemas enriquecidos
class MateriaAsignada(BaseModel):
    id: int
    materia_id: int
    materia: MateriaOut

    class Config:
        from_attributes = True


class DocenteAsignado(BaseModel):
    id: int
    docente_id: int
    docente: DocenteOut

    class Config:
        from_attributes = True
