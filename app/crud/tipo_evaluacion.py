from sqlalchemy.orm import Session
from app.models.tipo_evaluacion import TipoEvaluacion
from app.schemas.tipo_evaluacion import TipoEvaluacionCreate, TipoEvaluacionUpdate


def crear_tipo(db: Session, datos: TipoEvaluacionCreate):
    nuevo = TipoEvaluacion(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def listar_tipos(db: Session):
    return db.query(TipoEvaluacion).all()


def obtener_por_id(db: Session, tipo_id: int):
    return db.query(TipoEvaluacion).filter(TipoEvaluacion.id == tipo_id).first()


def actualizar_tipo(db: Session, tipo_id: int, datos: TipoEvaluacionUpdate):
    tipo = db.query(TipoEvaluacion).filter(TipoEvaluacion.id == tipo_id).first()
    if tipo:
        for key, value in datos.dict().items():
            setattr(tipo, key, value)
        db.commit()
        db.refresh(tipo)
    return tipo


def eliminar_tipo(db: Session, tipo_id: int):
    tipo = db.query(TipoEvaluacion).filter(TipoEvaluacion.id == tipo_id).first()
    if tipo:
        db.delete(tipo)
        db.commit()
    return tipo
