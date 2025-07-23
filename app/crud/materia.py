from sqlalchemy.orm import Session
from app.models.materia import Materia
from app.schemas.materia import MateriaCreate, MateriaUpdate


def crear_materia(db: Session, materia: MateriaCreate):
    nueva = Materia(**materia.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def obtener_materias(db: Session):
    return db.query(Materia).all()


def obtener_materia_por_id(db: Session, materia_id: int):
    return db.query(Materia).filter(Materia.id == materia_id).first()


def actualizar_materia(db: Session, materia_id: int, datos: MateriaUpdate):
    mat = db.query(Materia).filter(Materia.id == materia_id).first()
    if mat:
        for key, value in datos.dict(exclude_unset=True).items():
            setattr(mat, key, value)
        db.commit()
        db.refresh(mat)
    return mat


def eliminar_materia(db: Session, materia_id: int):
    mat = db.query(Materia).filter(Materia.id == materia_id).first()
    if mat:
        db.delete(mat)
        db.commit()
    return mat
