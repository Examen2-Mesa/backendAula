from sqlalchemy.orm import Session
from app.models.evaluacion import Evaluacion
from app.schemas.evaluacion import EvaluacionCreate, EvaluacionUpdate


def crear_evaluacion(db: Session, datos: EvaluacionCreate):
    nueva = Evaluacion(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def listar_evaluaciones(db: Session):
    return db.query(Evaluacion).all()


def obtener_por_id(db: Session, evaluacion_id: int):
    return db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()


def actualizar_evaluacion(db: Session, evaluacion_id: int, datos: EvaluacionUpdate):
    e = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if e:
        for key, value in datos.dict().items():
            setattr(e, key, value)
        db.commit()
        db.refresh(e)
    return e


def eliminar_evaluacion(db: Session, evaluacion_id: int):
    e = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if e:
        db.delete(e)
        db.commit()
    return e
