from sqlalchemy.orm import Session
from app.models.curso import Curso
from app.schemas.curso import CursoCreate, CursoUpdate


def crear_curso(db: Session, curso: CursoCreate):
    nuevo = Curso(**curso.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def obtener_cursos(db: Session):
    return db.query(Curso).all()


def obtener_curso_por_id(db: Session, curso_id: int):
    return db.query(Curso).filter(Curso.id == curso_id).first()


def actualizar_curso(db: Session, curso_id: int, datos: CursoUpdate):
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if curso:
        for key, value in datos.dict(exclude_unset=True).items():
            setattr(curso, key, value)
        db.commit()
        db.refresh(curso)
    return curso


def eliminar_curso(db: Session, curso_id: int):
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if curso:
        db.delete(curso)
        db.commit()
    return curso
