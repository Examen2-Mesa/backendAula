from sqlalchemy.orm import Session
from app.models import PrediccionRendimiento
from app.schemas.prediccion_rendimiento import PrediccionRendimientoCreate


def crear_prediccion(db: Session, datos: PrediccionRendimientoCreate):
    pred = PrediccionRendimiento(**datos.dict())
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred


def obtener_predicciones_por_estudiante(db: Session, estudiante_id: int):
    return db.query(PrediccionRendimiento).filter_by(estudiante_id=estudiante_id).all()


def obtener_predicciones_por_materia(db: Session, materia_id: int):
    return db.query(PrediccionRendimiento).filter_by(materia_id=materia_id).all()


def obtener_predicciones_por_periodo(db: Session, periodo_id: int):
    return db.query(PrediccionRendimiento).filter_by(periodo_id=periodo_id).all()
