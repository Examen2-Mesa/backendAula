# app/schemas/estudiante_info_academica.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class EstudianteBasico(BaseModel):
    """Información básica del estudiante"""

    id: int
    nombre: str
    apellido: str
    correo: Optional[str] = None

    class Config:
        from_attributes = True


class DocenteBasico(BaseModel):
    """Información básica del docente"""

    id: int
    nombre: str
    apellido: str
    correo: str
    telefono: Optional[str] = None

    class Config:
        from_attributes = True


class MateriaBasica(BaseModel):
    """Información básica de la materia"""

    id: int
    nombre: str
    descripcion: Optional[str] = None
    sigla: Optional[str] = None

    class Config:
        from_attributes = True


class CursoBasico(BaseModel):
    """Información básica del curso"""

    id: int
    nombre: str
    nivel: str
    paralelo: str
    turno: str

    class Config:
        from_attributes = True


class GestionBasica(BaseModel):
    """Información básica de la gestión"""

    id: int
    anio: int
    descripcion: str

    class Config:
        from_attributes = True


class InscripcionBasica(BaseModel):
    """Información básica de la inscripción"""

    id: int
    descripcion: str
    fecha: date

    class Config:
        from_attributes = True


class MateriaConDocente(BaseModel):
    """Materia con su docente asignado"""

    materia: MateriaBasica
    docente: Optional[DocenteBasico] = None

    class Config:
        from_attributes = True


class DocenteConMaterias(BaseModel):
    """Docente con sus materias asignadas"""

    id: int
    nombre: str
    apellido: str
    correo: str
    telefono: Optional[str] = None
    materias: List[MateriaBasica]

    class Config:
        from_attributes = True


class InfoAcademicaCompleta(BaseModel):
    """Información académica completa del estudiante"""

    estudiante: EstudianteBasico
    inscripcion: InscripcionBasica
    curso: CursoBasico
    gestion: GestionBasica
    materias: List[MateriaConDocente]

    class Config:
        from_attributes = True


class InfoAcademicaResumen(BaseModel):
    """Resumen de información académica del estudiante"""

    curso: CursoBasico
    total_materias: int
    total_docentes: int
    gestion_actual: GestionBasica

    class Config:
        from_attributes = True


# Schemas de respuesta para endpoints específicos
class CursoEstudianteResponse(BaseModel):
    """Respuesta para el curso del estudiante"""

    success: bool
    curso: Optional[CursoBasico] = None
    mensaje: Optional[str] = None

    class Config:
        from_attributes = True


class MateriasEstudianteResponse(BaseModel):
    """Respuesta para las materias del estudiante"""

    success: bool
    materias: List[MateriaConDocente] = []
    total: int
    mensaje: Optional[str] = None

    class Config:
        from_attributes = True


class DocentesEstudianteResponse(BaseModel):
    """Respuesta para los docentes del estudiante"""

    success: bool
    docentes: List[DocenteConMaterias] = []
    total: int
    mensaje: Optional[str] = None

    class Config:
        from_attributes = True


class InfoAcademicaResponse(BaseModel):
    """Respuesta completa de información académica"""

    success: bool
    data: Optional[InfoAcademicaCompleta] = None
    mensaje: Optional[str] = None

    class Config:
        from_attributes = True
