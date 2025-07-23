# app/crud/estudiante_info_academica.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.estudiante import Estudiante
from app.models.inscripcion import Inscripcion
from app.models.curso import Curso
from app.models.curso_materia import CursoMateria
from app.models.materia import Materia
from app.models.docente_materia import DocenteMateria
from app.models.docente import Docente
from app.models.gestion import Gestion
from sqlalchemy.orm import joinedload
from typing import Dict, List, Optional


def obtener_estudiante_por_correo(db: Session, correo: str) -> Optional[Estudiante]:
    """
    Obtiene un estudiante por su correo electrónico
    """
    return db.query(Estudiante).filter(Estudiante.correo == correo).first()


def obtener_estudiante_por_id(db: Session, estudiante_id: int) -> Optional[Estudiante]:
    """
    Obtiene un estudiante por su ID
    """
    return db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()


def obtener_info_academica_estudiante(
    db: Session, estudiante_id: int, gestion_id: Optional[int] = None
) -> Dict:
    """
    Obtiene toda la información académica del estudiante:
    - Su curso actual
    - Las materias del curso
    - Los docentes de cada materia
    """

    # Si no se especifica gestión, usar la gestión activa/más reciente
    if not gestion_id:
        gestion_activa = db.query(Gestion).order_by(Gestion.id.desc()).first()
        if not gestion_activa:
            return {"error": "No hay gestión activa"}
        gestion_id = gestion_activa.id

    # Verificar que el estudiante existe
    estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not estudiante:
        return {"error": "Estudiante no encontrado"}

    # Obtener la inscripción del estudiante en la gestión especificada
    inscripcion = (
        db.query(Inscripcion)
        .options(joinedload(Inscripcion.curso), joinedload(Inscripcion.gestion))
        .filter(
            Inscripcion.estudiante_id == estudiante_id,
            Inscripcion.gestion_id == gestion_id,
        )
        .first()
    )

    if not inscripcion:
        return {"error": "El estudiante no está inscrito en esta gestión"}

    # Obtener las materias del curso
    materias_curso = (
        db.query(CursoMateria)
        .options(joinedload(CursoMateria.materia))
        .filter(CursoMateria.curso_id == inscripcion.curso_id)
        .all()
    )

    # Para cada materia, obtener su docente
    materias_con_docentes = []
    for curso_materia in materias_curso:
        materia = curso_materia.materia

        # Buscar el docente asignado a esta materia
        docente_materia = (
            db.query(DocenteMateria)
            .options(joinedload(DocenteMateria.docente))
            .filter(DocenteMateria.materia_id == materia.id)
            .first()
        )

        docente_info = None
        if docente_materia and docente_materia.docente:
            docente_info = {
                "id": docente_materia.docente.id,
                "nombre": docente_materia.docente.nombre,
                "apellido": docente_materia.docente.apellido,
                "correo": docente_materia.docente.correo,
                "telefono": docente_materia.docente.telefono,
            }

        materias_con_docentes.append(
            {
                "materia": {
                    "id": materia.id,
                    "nombre": materia.nombre,
                    "descripcion": materia.descripcion,
                    "sigla": getattr(materia, "sigla", None),
                },
                "docente": docente_info,
            }
        )

    return {
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "correo": estudiante.correo,
        },
        "inscripcion": {
            "id": inscripcion.id,
            "descripcion": inscripcion.descripcion,
            "fecha": inscripcion.fecha,
        },
        "curso": {
            "id": inscripcion.curso.id,
            "nombre": inscripcion.curso.nombre,
            "nivel": inscripcion.curso.nivel,
            "paralelo": inscripcion.curso.paralelo,
            "turno": inscripcion.curso.turno,
        },
        "gestion": {
            "id": inscripcion.gestion.id,
            "anio": inscripcion.gestion.anio,
            "descripcion": inscripcion.gestion.descripcion,
        },
        "materias": materias_con_docentes,
    }


def obtener_curso_estudiante(
    db: Session, estudiante_id: int, gestion_id: Optional[int] = None
) -> Optional[Dict]:
    """
    Obtiene solo el curso del estudiante en una gestión específica
    """
    if not gestion_id:
        gestion_activa = db.query(Gestion).order_by(Gestion.id.desc()).first()
        if not gestion_activa:
            return None
        gestion_id = gestion_activa.id

    inscripcion = (
        db.query(Inscripcion)
        .options(joinedload(Inscripcion.curso))
        .filter(
            Inscripcion.estudiante_id == estudiante_id,
            Inscripcion.gestion_id == gestion_id,
        )
        .first()
    )

    if not inscripcion:
        return None

    return {
        "id": inscripcion.curso.id,
        "nombre": inscripcion.curso.nombre,
        "nivel": inscripcion.curso.nivel,
        "paralelo": inscripcion.curso.paralelo,
        "turno": inscripcion.curso.turno,
    }


def obtener_materias_estudiante(
    db: Session, estudiante_id: int, gestion_id: Optional[int] = None
) -> List[Dict]:
    """
    Obtiene las materias del estudiante con sus docentes
    """
    if not gestion_id:
        gestion_activa = db.query(Gestion).order_by(Gestion.id.desc()).first()
        if not gestion_activa:
            return []
        gestion_id = gestion_activa.id

    # Obtener el curso del estudiante
    inscripcion = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.estudiante_id == estudiante_id,
            Inscripcion.gestion_id == gestion_id,
        )
        .first()
    )

    if not inscripcion:
        return []

    # Obtener materias del curso con sus docentes
    materias_query = (
        db.query(Materia, Docente)
        .join(CursoMateria, Materia.id == CursoMateria.materia_id)
        .outerjoin(DocenteMateria, Materia.id == DocenteMateria.materia_id)
        .outerjoin(Docente, DocenteMateria.docente_id == Docente.id)
        .filter(CursoMateria.curso_id == inscripcion.curso_id)
        .all()
    )

    materias_con_docentes = []
    for materia, docente in materias_query:
        docente_info = None
        if docente:
            docente_info = {
                "id": docente.id,
                "nombre": docente.nombre,
                "apellido": docente.apellido,
                "correo": docente.correo,
                "telefono": docente.telefono,
            }

        materias_con_docentes.append(
            {
                "materia": {
                    "id": materia.id,
                    "nombre": materia.nombre,
                    "descripcion": materia.descripcion,
                    "sigla": getattr(materia, "sigla", None),
                },
                "docente": docente_info,
            }
        )

    return materias_con_docentes


def obtener_docentes_estudiante(
    db: Session, estudiante_id: int, gestion_id: Optional[int] = None
) -> List[Dict]:
    """
    Obtiene todos los docentes que enseñan al estudiante
    """
    if not gestion_id:
        gestion_activa = db.query(Gestion).order_by(Gestion.id.desc()).first()
        if not gestion_activa:
            return []
        gestion_id = gestion_activa.id

    # Obtener el curso del estudiante
    inscripcion = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.estudiante_id == estudiante_id,
            Inscripcion.gestion_id == gestion_id,
        )
        .first()
    )

    if not inscripcion:
        return []

    # Obtener docentes que enseñan materias en el curso del estudiante
    docentes_query = (
        db.query(Docente, Materia)
        .join(DocenteMateria, Docente.id == DocenteMateria.docente_id)
        .join(Materia, DocenteMateria.materia_id == Materia.id)
        .join(CursoMateria, Materia.id == CursoMateria.materia_id)
        .filter(CursoMateria.curso_id == inscripcion.curso_id)
        .distinct()
        .all()
    )

    docentes_con_materias = {}
    for docente, materia in docentes_query:
        if docente.id not in docentes_con_materias:
            docentes_con_materias[docente.id] = {
                "id": docente.id,
                "nombre": docente.nombre,
                "apellido": docente.apellido,
                "correo": docente.correo,
                "telefono": docente.telefono,
                "materias": [],
            }

        docentes_con_materias[docente.id]["materias"].append(
            {
                "id": materia.id,
                "nombre": materia.nombre,
                "descripcion": materia.descripcion,
            }
        )

    return list(docentes_con_materias.values())
