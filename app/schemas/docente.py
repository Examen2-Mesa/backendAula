from pydantic import BaseModel, EmailStr
from typing import Optional

from app.schemas.curso import CursoOut
from app.schemas.estudiante import EstudianteOut
from app.schemas.materia import MateriaOut


class DocenteBase(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    correo: EmailStr
    genero: str
    is_doc: bool = True


class DocenteCreate(DocenteBase):
    contrasena: str


class DocenteOut(DocenteBase):
    id: int

    class Config:
        from_attributes = True


class DocenteLogin(BaseModel):
    correo: EmailStr
    contrasena: str


class DocenteUpdate(BaseModel):
    nombre: Optional[str]
    apellido: Optional[str]
    telefono: Optional[str]
    genero: Optional[str]
    is_doc: Optional[bool]


class EstudianteAsignadoDetalle(BaseModel):
    estudiante: EstudianteOut
    curso: CursoOut
    materia: MateriaOut

    class Config:
        from_attributes = True
