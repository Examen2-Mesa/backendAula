from pydantic import BaseModel
from datetime import date


class EvaluacionBase(BaseModel):
    fecha: date
    descripcion: str
    valor: float
    estudiante_id: int
    materia_id: int
    tipo_evaluacion_id: int
    periodo_id: int


class EvaluacionCreate(EvaluacionBase):
    pass


class EvaluacionUpdate(EvaluacionBase):
    pass


class EvaluacionOut(EvaluacionBase):
    id: int

    class Config:
        from_attributes = True
