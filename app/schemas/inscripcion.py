from pydantic import BaseModel
from datetime import date
from app.schemas.estudiante import EstudianteOut
from app.schemas.curso import CursoOut
from app.schemas.gestion import GestionOut


class InscripcionBase(BaseModel):
    descripcion: str
    fecha: date
    estudiante_id: int
    curso_id: int
    gestion_id: int


class InscripcionCreate(InscripcionBase):
    pass


class InscripcionUpdate(InscripcionBase):
    pass


class InscripcionOut(InscripcionBase):
    id: int

    class Config:
        from_attributes = True


class InscripcionDetalle(BaseModel):
    id: int
    descripcion: str
    fecha: date
    estudiante: EstudianteOut
    curso: CursoOut
    gestion: GestionOut

    class Config:
        from_attributes = True
