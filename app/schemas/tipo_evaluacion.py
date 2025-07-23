from pydantic import BaseModel


class TipoEvaluacionBase(BaseModel):
    nombre: str


class TipoEvaluacionCreate(TipoEvaluacionBase):
    pass


class TipoEvaluacionUpdate(TipoEvaluacionBase):
    pass


class TipoEvaluacionOut(TipoEvaluacionBase):
    id: int

    class Config:
        from_attributes = True
