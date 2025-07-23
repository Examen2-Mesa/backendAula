from pydantic import BaseModel
from datetime import date
from app.schemas.gestion import GestionOut


class PeriodoBase(BaseModel):
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    gestion_id: int


class PeriodoCreate(PeriodoBase):
    pass


class PeriodoUpdate(PeriodoBase):
    pass


class PeriodoOut(PeriodoBase):
    id: int

    class Config:
        from_attributes = True


class PeriodoDetalle(BaseModel):
    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    gestion: GestionOut

    class Config:
        from_attributes = True
