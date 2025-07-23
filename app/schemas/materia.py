from pydantic import BaseModel


class MateriaBase(BaseModel):
    nombre: str
    descripcion: str


class MateriaCreate(MateriaBase):
    pass


class MateriaUpdate(MateriaBase):
    pass


class MateriaOut(MateriaBase):
    id: int

    class Config:
        from_attributes = True
