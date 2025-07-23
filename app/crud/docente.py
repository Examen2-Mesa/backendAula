from sqlalchemy.orm import Session
from app.models.curso import Curso
from app.models.curso_materia import CursoMateria
from app.models.docente import Docente
from app.models.docente_materia import DocenteMateria
from app.models.estudiante import Estudiante
from app.models.inscripcion import Inscripcion
from app.models.materia import Materia
from app.schemas.docente import DocenteCreate, DocenteUpdate
from passlib.hash import bcrypt  # type: ignore


def crear_docente(db: Session, docente: DocenteCreate):
    hashed = bcrypt.hash(docente.contrasena)
    nuevo = Docente(**docente.dict(exclude={"contrasena"}), contrasena=hashed)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def autenticar_docente(db: Session, correo: str, contrasena: str):
    docente = db.query(Docente).filter(Docente.correo == correo).first()
    if docente and bcrypt.verify(contrasena, docente.contrasena):
        return docente
    return None


def obtener_por_correo(db: Session, correo: str):
    return db.query(Docente).filter(Docente.correo == correo).first()


def actualizar_docente(db: Session, docente_id: int, datos: DocenteUpdate):
    doc = db.query(Docente).filter(Docente.id == docente_id).first()
    if doc:
        for key, value in datos.dict(exclude_unset=True).items():
            setattr(doc, key, value)
        db.commit()
        db.refresh(doc)
    return doc


def eliminar_docente(db: Session, docente_id: int):
    doc = db.query(Docente).filter(Docente.id == docente_id).first()
    if doc:
        db.delete(doc)
        db.commit()
    return doc


def obtener_docentes(db: Session):
    return db.query(Docente).filter(Docente.is_doc == True).all()


def obtener_admins(db: Session):
    return db.query(Docente).filter(Docente.is_doc == False).all()


def obtener_docente_por_id(db: Session, docente_id: int):
    return db.query(Docente).filter(Docente.id == docente_id).first()


def obtener_materias_del_docente(db: Session, docente_id: int):
    return (
        db.query(Materia)
        .join(DocenteMateria)
        .filter(DocenteMateria.docente_id == docente_id)
        .all()
    )


def obtener_cursos_del_docente(db: Session, docente_id: int):
    return (
        db.query(Curso)
        .join(CursoMateria, Curso.id == CursoMateria.curso_id)
        .join(DocenteMateria, CursoMateria.materia_id == DocenteMateria.materia_id)
        .filter(DocenteMateria.docente_id == docente_id)
        .distinct()
        .all()
    )


def obtener_estudiantes_de_materia_curso(
    db: Session, docente_id: int, curso_id: int, materia_id: int
):
    existe = (
        db.query(DocenteMateria)
        .filter(
            DocenteMateria.docente_id == docente_id,
            DocenteMateria.materia_id == materia_id,
        )
        .first()
    )

    if not existe:
        return []

    return (
        db.query(Estudiante)
        .join(Inscripcion)
        .filter(Inscripcion.curso_id == curso_id)
        .distinct()
        .all()
    )


def obtener_materias_docente_en_curso(db: Session, docente_id: int, curso_id: int):
    return (
        db.query(Materia)
        .join(DocenteMateria, DocenteMateria.materia_id == Materia.id)
        .join(CursoMateria, CursoMateria.materia_id == Materia.id)
        .filter(
            DocenteMateria.docente_id == docente_id, CursoMateria.curso_id == curso_id
        )
        .distinct()
        .all()
    )


def obtener_estudiantes_de_docente(
    db: Session,
    docente_id: int,
    curso_id: int = None,
    materia_id: int = None,
    nombre: str = None,
):
    query = (
        db.query(Estudiante, Curso, Materia)
        .join(Inscripcion, Inscripcion.estudiante_id == Estudiante.id)
        .join(Curso, Curso.id == Inscripcion.curso_id)
        .join(CursoMateria, CursoMateria.curso_id == Curso.id)
        .join(Materia, Materia.id == CursoMateria.materia_id)
        .join(DocenteMateria, DocenteMateria.materia_id == Materia.id)
        .filter(DocenteMateria.docente_id == docente_id)
    )

    if curso_id:
        query = query.filter(Curso.id == curso_id)
    if materia_id:
        query = query.filter(Materia.id == materia_id)
    if nombre:
        query = query.filter(Estudiante.nombre.ilike(f"%{nombre}%"))

    resultados = query.all()

    return [
        {"estudiante": estudiante, "curso": curso, "materia": materia}
        for estudiante, curso, materia in resultados
    ]
