from sqlalchemy.orm import Session
from app.models.docente_materia import DocenteMateria
from app.schemas.docente_materia import AsignacionCreate
from app.models.docente_materia import DocenteMateria
from app.models.materia import Materia
from app.models.docente import Docente


def asignar_docente_materia(db: Session, datos: AsignacionCreate):
    asignacion = DocenteMateria(**datos.dict())
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion


def obtener_asignaciones(db: Session):
    return db.query(DocenteMateria).all()


def eliminar_asignacion(db: Session, asignacion_id: int):
    asig = db.query(DocenteMateria).filter(DocenteMateria.id == asignacion_id).first()
    if asig:
        db.delete(asig)
        db.commit()
    return asig


def obtener_materias_por_docente(db: Session, docente_id: int):
    return (
        db.query(DocenteMateria)
        .join(Materia)
        .filter(DocenteMateria.docente_id == docente_id)
        .all()
    )


def obtener_docentes_por_materia(db: Session, materia_id: int):
    return (
        db.query(DocenteMateria)
        .join(Docente)
        .filter(DocenteMateria.materia_id == materia_id)
        .all()
    )
