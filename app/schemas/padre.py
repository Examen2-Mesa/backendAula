from pydantic import BaseModel, EmailStr
from typing import Optional, List


class PadreBase(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    correo: EmailStr
    genero: str


class PadreCreate(PadreBase):
    contrasena: str
    hijos_ids: List[int] = []  # IDs de estudiantes que son sus hijos


class PadreOut(PadreBase):
    id: int

    class Config:
        from_attributes = True


class PadreUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    genero: Optional[str] = None


class PadreConHijos(PadreOut):
    hijos: List = []

    class Config:
        from_attributes = True
