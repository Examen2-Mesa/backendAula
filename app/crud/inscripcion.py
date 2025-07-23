from sqlalchemy.orm import Session
from app.models.inscripcion import Inscripcion
from app.schemas.inscripcion import InscripcionCreate, InscripcionUpdate


def crear_inscripcion(db: Session, datos: InscripcionCreate):
    insc = Inscripcion(**datos.dict())
    db.add(insc)
    db.commit()
    db.refresh(insc)
    return insc


def listar_inscripciones(db: Session):
    return db.query(Inscripcion).all()


def obtener_por_id(db: Session, inscripcion_id: int):
    return db.query(Inscripcion).filter(Inscripcion.id == inscripcion_id).first()


def actualizar_inscripcion(db: Session, inscripcion_id: int, datos: InscripcionUpdate):
    insc = db.query(Inscripcion).filter(Inscripcion.id == inscripcion_id).first()
    if insc:
        for key, value in datos.dict().items():
            setattr(insc, key, value)
        db.commit()
        db.refresh(insc)
    return insc


def eliminar_inscripcion(db: Session, inscripcion_id: int):
    insc = db.query(Inscripcion).filter(Inscripcion.id == inscripcion_id).first()
    if insc:
        db.delete(insc)
        db.commit()
    return insc


def listar_por_estudiante(db: Session, estudiante_id: int):
    return (
        db.query(Inscripcion).filter(Inscripcion.estudiante_id == estudiante_id).all()
    )


def listar_por_curso(db: Session, curso_id: int):
    return db.query(Inscripcion).filter(Inscripcion.curso_id == curso_id).all()


def listar_por_gestion(db: Session, gestion_id: int):
    return db.query(Inscripcion).filter(Inscripcion.gestion_id == gestion_id).all()
