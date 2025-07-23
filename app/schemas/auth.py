from pydantic import BaseModel, EmailStr
from typing import Optional, Literal


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str
    tipo_usuario: Optional[Literal["docente", "estudiante", "padre"]] = None  # ✨ OPCIONAL


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_type: str  # "docente", "estudiante", "padre", "admin"
    user_id: int
    is_doc: Optional[bool] = None  # Solo para docentes/admins


class UserProfileResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    correo: str
    user_type: str
    genero: str
    telefono: Optional[str] = None
    url_imagen: Optional[str] = None
    is_doc: Optional[bool] = None