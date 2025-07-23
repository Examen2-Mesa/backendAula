from pydantic import BaseModel


class PesoTipoEvaluacionBase(BaseModel):
    porcentaje: float
    docente_id: int
    materia_id: int
    gestion_id: int
    tipo_evaluacion_id: int


class PesoTipoEvaluacionCreate(PesoTipoEvaluacionBase):
    pass


class PesoTipoEvaluacionUpdate(PesoTipoEvaluacionBase):
    pass


class PesoTipoEvaluacionOut(PesoTipoEvaluacionBase):
    id: int

    class Config:
        from_attributes = True
