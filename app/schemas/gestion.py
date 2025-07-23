from pydantic import BaseModel


class GestionBase(BaseModel):
    anio: str
    descripcion: str


class GestionCreate(GestionBase):
    pass


class GestionUpdate(GestionBase):
    pass


class GestionOut(GestionBase):
    id: int

    class Config:
        from_attributes = True
