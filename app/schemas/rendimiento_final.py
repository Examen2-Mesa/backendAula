from pydantic import BaseModel
from datetime import datetime


class RendimientoFinalBase(BaseModel):
    nota_final: float
    estudiante_id: int
    materia_id: int
    periodo_id: int


class RendimientoFinalCreate(RendimientoFinalBase):
    pass


class RendimientoFinalUpdate(BaseModel):
    nota_final: float


class RendimientoFinalOut(RendimientoFinalBase):
    id: int
    fecha_calculo: datetime

    class Config:
        from_attributes = True
