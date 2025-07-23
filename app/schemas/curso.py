from pydantic import BaseModel


class CursoBase(BaseModel):
    nombre: str
    nivel: str
    paralelo: str
    turno: str

class CursoCreate(CursoBase):
    pass


class CursoUpdate(CursoBase):
    pass


class CursoOut(CursoBase):
    id: int

    class Config:
        from_attributes = True
