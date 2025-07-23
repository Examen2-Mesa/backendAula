from pydantic import BaseModel
from app.schemas.curso import CursoOut
from app.schemas.materia import MateriaOut


class CursoMateriaBase(BaseModel):
    curso_id: int
    materia_id: int


class CursoMateriaCreate(CursoMateriaBase):
    pass


class CursoMateriaUpdate(CursoMateriaBase):
    pass


class CursoMateriaOut(CursoMateriaBase):
    id: int

    class Config:
        from_attributes = True


# Para respuestas enriquecidas
class CursoMateriaDetalle(BaseModel):
    id: int
    curso: CursoOut
    materia: MateriaOut

    class Config:
        from_attributes = True


class MateriaConCurso(BaseModel):
    curso_id: int
    curso_nombre: str
    curso_nivel: str
    curso_paralelo: str
    curso_turno: str
    materia_id: int
    materia_nombre: str
    materia_descripcion: str

    class Config:
        from_attributes = True
