from sqlalchemy.orm import Session
from app.models.curso import Curso
from app.models.curso_materia import CursoMateria
from app.models.docente_materia import DocenteMateria
from app.models.materia import Materia
from app.schemas.curso_materia import CursoMateriaCreate, CursoMateriaUpdate


def crear_asignacion(db: Session, datos: CursoMateriaCreate):
    asignacion = CursoMateria(**datos.dict())
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion


def listar_asignaciones(db: Session):
    return db.query(CursoMateria).all()


def obtener_por_id(db: Session, asignacion_id: int):
    return db.query(CursoMateria).filter(CursoMateria.id == asignacion_id).first()


def actualizar_asignacion(db: Session, asignacion_id: int, datos: CursoMateriaUpdate):
    asignacion = db.query(CursoMateria).filter(CursoMateria.id == asignacion_id).first()
    if asignacion:
        for key, value in datos.dict().items():
            setattr(asignacion, key, value)
        db.commit()
        db.refresh(asignacion)
    return asignacion


def eliminar_asignacion(db: Session, asignacion_id: int):
    asignacion = db.query(CursoMateria).filter(CursoMateria.id == asignacion_id).first()
    if asignacion:
        db.delete(asignacion)
        db.commit()
    return asignacion


def listar_materias_por_curso(db: Session, curso_id: int):
    return db.query(CursoMateria).filter(CursoMateria.curso_id == curso_id).all()


def listar_cursos_por_materia(db: Session, materia_id: int):
    return db.query(CursoMateria).filter(CursoMateria.materia_id == materia_id).all()


def listar_materias_con_curso_por_docente(db: Session, docente_id: int):
    return (
        db.query(
            Curso.id.label("curso_id"),
            Curso.nombre.label("curso_nombre"),
            Curso.nivel.label("curso_nivel"),
            Curso.paralelo.label("curso_paralelo"),
            Curso.turno.label("curso_turno"),
            Materia.id.label("materia_id"),
            Materia.nombre.label("materia_nombre"),
            Materia.descripcion.label("materia_descripcion"),
        )
        .join(DocenteMateria, DocenteMateria.materia_id == Materia.id)
        .join(CursoMateria, CursoMateria.materia_id == Materia.id)
        .join(Curso, Curso.id == CursoMateria.curso_id)
        .filter(DocenteMateria.docente_id == docente_id)
        .distinct()
        .all()
    )
