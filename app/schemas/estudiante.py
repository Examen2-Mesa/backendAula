from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


class EstudianteBase(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date
    genero: str
    url_imagen: Optional[str] = None
    nombre_tutor: Optional[str] = None
    telefono_tutor: Optional[str] = None
    direccion_casa: Optional[str] = None


class EstudianteCreate(EstudianteBase):
    # 🆕 Campos opcionales para autenticación
    correo: Optional[EmailStr] = None
    contrasena: Optional[str] = None


class EstudianteUpdate(EstudianteBase):
    pass


class EstudianteOut(EstudianteBase):
    id: int
    correo: Optional[str] = None  # 🆕 Mostrar correo si existe

    class Config:
        from_attributes = True


class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    url_imagen: Optional[str] = None
    nombre_tutor: Optional[str] = None
    telefono_tutor: Optional[str] = None
    direccion_casa: Optional[str] = None
    # 🆕 Campos opcionales para autenticación
    correo: Optional[EmailStr] = None
    contrasena: Optional[str] = None


class EstudianteLogin(BaseModel):
    correo: EmailStr
    contrasena: str
