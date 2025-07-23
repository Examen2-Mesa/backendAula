from sqlalchemy.orm import Session
from app.models.padre import Padre
from app.models.estudiante import Estudiante
from app.models.padre_estudiante import PadreEstudiante
from app.schemas.padre import PadreCreate, PadreUpdate
from app.seguridad import hash_contrasena
from typing import List, Optional


def crear_padre(db: Session, padre: PadreCreate) -> Padre:
    """Crear un nuevo padre"""
    # Hash de la contraseña
    contrasena_hash = hash_contrasena(padre.contrasena)

    # Crear padre
    db_padre = Padre(
        nombre=padre.nombre,
        apellido=padre.apellido,
        telefono=padre.telefono,
        correo=padre.correo,
        genero=padre.genero,
        contrasena=contrasena_hash,
    )

    db.add(db_padre)
    db.commit()
    db.refresh(db_padre)

    # Asignar hijos si se proporcionaron
    if padre.hijos_ids:
        for hijo_id in padre.hijos_ids:
            asignar_hijo_a_padre(db, db_padre.id, hijo_id)

    return db_padre


def obtener_padres(db: Session) -> List[Padre]:
    """Obtener todos los padres"""
    return db.query(Padre).all()


def obtener_padre_por_id(db: Session, padre_id: int) -> Optional[Padre]:
    """Obtener padre por ID"""
    return db.query(Padre).filter(Padre.id == padre_id).first()


def obtener_padre_por_correo(db: Session, correo: str) -> Optional[Padre]:
    """Obtener padre por correo"""
    return db.query(Padre).filter(Padre.correo == correo).first()


def actualizar_padre(db: Session, padre_id: int, datos: PadreUpdate) -> Optional[Padre]:
    """Actualizar datos del padre"""
    padre = db.query(Padre).filter(Padre.id == padre_id).first()
    if not padre:
        return None

    # Actualizar solo campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(padre, campo, valor)

    db.commit()
    db.refresh(padre)
    return padre


def eliminar_padre(db: Session, padre_id: int) -> Optional[Padre]:
    """Eliminar padre"""
    padre = db.query(Padre).filter(Padre.id == padre_id).first()
    if not padre:
        return None

    db.delete(padre)
    db.commit()
    return padre


def obtener_hijos_del_padre(db: Session, padre_id: int) -> List[Estudiante]:
    """Obtener todos los hijos de un padre"""
    relaciones = (
        db.query(PadreEstudiante).filter(PadreEstudiante.padre_id == padre_id).all()
    )
    return [rel.estudiante for rel in relaciones]


def asignar_hijo_a_padre(db: Session, padre_id: int, estudiante_id: int) -> bool:
    """Asignar un hijo a un padre"""
    # Verificar que no exista ya la relación
    relacion_existente = (
        db.query(PadreEstudiante)
        .filter(
            PadreEstudiante.padre_id == padre_id,
            PadreEstudiante.estudiante_id == estudiante_id,
        )
        .first()
    )

    if relacion_existente:
        return False

    # Crear nueva relación
    nueva_relacion = PadreEstudiante(padre_id=padre_id, estudiante_id=estudiante_id)

    db.add(nueva_relacion)
    db.commit()
    return True


def desasignar_hijo_de_padre(db: Session, padre_id: int, estudiante_id: int) -> bool:
    """Desasignar un hijo de un padre"""
    relacion = (
        db.query(PadreEstudiante)
        .filter(
            PadreEstudiante.padre_id == padre_id,
            PadreEstudiante.estudiante_id == estudiante_id,
        )
        .first()
    )

    if not relacion:
        return False

    db.delete(relacion)
    db.commit()
    return True


def es_padre_del_estudiante(db: Session, padre_id: int, estudiante_id: int) -> bool:
    """Verificar si un padre es padre de un estudiante específico"""
    relacion = (
        db.query(PadreEstudiante)
        .filter(
            PadreEstudiante.padre_id == padre_id,
            PadreEstudiante.estudiante_id == estudiante_id,
        )
        .first()
    )
    return relacion is not None
