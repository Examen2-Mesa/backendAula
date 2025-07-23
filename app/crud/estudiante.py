from typing import Optional
from app.seguridad import hash_contrasena
from sqlalchemy.orm import Session
from app.models.estudiante import Estudiante
from app.schemas.estudiante import EstudianteCreate, EstudianteUpdate


def crear_estudiante(db: Session, estudiante: EstudianteUpdate) -> Estudiante:
    """Crear un nuevo estudiante"""
    # Preparar datos
    datos = estudiante.dict(exclude_unset=True)

    # Hash de la contraseña si se proporciona
    if datos.get("contrasena"):
        datos["contrasena"] = hash_contrasena(datos["contrasena"])

    db_estudiante = Estudiante(**datos)
    db.add(db_estudiante)
    db.commit()
    db.refresh(db_estudiante)
    return db_estudiante


def obtener_estudiantes(db: Session):
    return db.query(Estudiante).all()


def obtener_estudiante(db: Session, estudiante_id: int):
    return db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()


def actualizar_estudiante(
    db: Session, estudiante_id: int, datos: EstudianteUpdate
) -> Optional[Estudiante]:
    """Actualizar datos del estudiante"""
    estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not estudiante:
        return None

    # Procesar datos
    datos_dict = datos.dict(exclude_unset=True)

    # Hash de la contraseña si se actualiza
    if datos_dict.get("contrasena"):
        datos_dict["contrasena"] = hash_contrasena(datos_dict["contrasena"])

    # Actualizar campos
    for campo, valor in datos_dict.items():
        setattr(estudiante, campo, valor)

    db.commit()
    db.refresh(estudiante)
    return estudiante


def eliminar_estudiante(db: Session, estudiante_id: int):
    est = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if est:
        db.delete(est)
        db.commit()
    return est
