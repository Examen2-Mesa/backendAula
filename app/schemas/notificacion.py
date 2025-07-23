from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificacionBase(BaseModel):
    titulo: str
    mensaje: str
    tipo: str


class NotificacionCreate(NotificacionBase):
    padre_id: Optional[int] = None  # Ahora es opcional
    estudiante_id: int
    evaluacion_id: Optional[int] = None
    para_estudiante: bool = False  # Nuevo campo


class NotificacionOut(NotificacionBase):
    id: int
    leida: bool
    padre_id: Optional[int]  # Ahora es opcional
    estudiante_id: int
    evaluacion_id: Optional[int]
    para_estudiante: bool  # Nuevo campo
    created_at: datetime
    updated_at: Optional[datetime]

    # Información adicional del estudiante y evaluación
    estudiante_nombre: Optional[str] = None
    estudiante_apellido: Optional[str] = None
    materia_nombre: Optional[str] = None
    evaluacion_valor: Optional[float] = None

    class Config:
        from_attributes = True


class NotificacionUpdate(BaseModel):
    leida: Optional[bool] = None


class NotificacionStats(BaseModel):
    total: int
    no_leidas: int
    leidas: int
    por_tipo: dict


class NotificacionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[NotificacionOut] = None


class NotificacionListResponse(BaseModel):
    success: bool
    message: str
    data: list[NotificacionOut]
    total: int
