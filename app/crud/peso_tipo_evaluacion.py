from sqlalchemy.orm import Session
from app import models
from app.models.peso_tipo_evaluacion import PesoTipoEvaluacion
from app.schemas.peso_tipo_evaluacion import (
    PesoTipoEvaluacionCreate,
    PesoTipoEvaluacionUpdate,
)


def crear_peso(db: Session, datos: PesoTipoEvaluacionCreate):
    nuevo = PesoTipoEvaluacion(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def listar_pesos(db: Session):
    return db.query(PesoTipoEvaluacion).all()


def obtener_por_id(db: Session, peso_id: int):
    return db.query(PesoTipoEvaluacion).filter(PesoTipoEvaluacion.id == peso_id).first()


def actualizar_peso(db: Session, peso_id: int, datos: PesoTipoEvaluacionUpdate):
    p = db.query(PesoTipoEvaluacion).filter(PesoTipoEvaluacion.id == peso_id).first()
    if p:
        for key, value in datos.dict().items():
            setattr(p, key, value)
        db.commit()
        db.refresh(p)
    return p


def eliminar_peso(db: Session, peso_id: int):
    p = db.query(PesoTipoEvaluacion).filter(PesoTipoEvaluacion.id == peso_id).first()
    if p:
        db.delete(p)
        db.commit()
    return p


def listar_por_materia_docente_gestion(
    db: Session, materia_id: int, docente_id: int, gestion_id: int
):
    return (
        db.query(PesoTipoEvaluacion)
        .filter(
            PesoTipoEvaluacion.materia_id == materia_id,
            PesoTipoEvaluacion.docente_id == docente_id,
            PesoTipoEvaluacion.gestion_id == gestion_id,
        )
        .all()
    )


def listar_por_docente_materia(db: Session, docente_id: int, materia_id: int):
    return (
        db.query(PesoTipoEvaluacion)
        .filter(
            PesoTipoEvaluacion.docente_id == docente_id,
            PesoTipoEvaluacion.materia_id == materia_id,
        )
        .all()
    )


def listar_por_materia_gestion(db: Session, materia_id: int, gestion_id: int):
    return (
        db.query(PesoTipoEvaluacion)
        .filter(
            PesoTipoEvaluacion.materia_id == materia_id,
            PesoTipoEvaluacion.gestion_id == gestion_id,
        )
        .all()
    )


def listar_por_docente_gestion(db: Session, docente_id: int, gestion_id: int):
    return (
        db.query(PesoTipoEvaluacion)
        .filter(
            PesoTipoEvaluacion.docente_id == docente_id,
            PesoTipoEvaluacion.gestion_id == gestion_id,
        )
        .all()
    )


def listar_por_docente(db: Session, docente_id: int):
    return (
        db.query(models.PesoTipoEvaluacion)
        .filter(models.PesoTipoEvaluacion.docente_id == docente_id)
        .all()
    )
