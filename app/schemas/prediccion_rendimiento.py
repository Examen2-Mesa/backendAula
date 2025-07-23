from pydantic import BaseModel
from datetime import datetime


class PrediccionRendimientoBase(BaseModel):
    promedio_notas: float
    porcentaje_asistencia: float
    promedio_participacion: float
    resultado_numerico: float
    clasificacion: str
    estudiante_id: int
    materia_id: int
    periodo_id: int


class PrediccionRendimientoCreate(PrediccionRendimientoBase):
    pass


class PrediccionRendimientoOut(PrediccionRendimientoBase):
    id: int
    fecha_generada: datetime

    class Config:
        from_attributes = True
