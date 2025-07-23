from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func, or_
from app.models.notificacion import Notificacion
from app.models.estudiante import Estudiante
from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.schemas.notificacion import NotificacionCreate, NotificacionUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def crear_notificacion(db: Session, notificacion: NotificacionCreate) -> Notificacion:
    """Crear una nueva notificación (ahora soporta notificaciones directas a estudiantes)"""
    db_notificacion = Notificacion(**notificacion.dict())
    db.add(db_notificacion)
    db.commit()
    db.refresh(db_notificacion)
    logger.info(
        f"Notificación creada: ID {db_notificacion.id}, para_estudiante={db_notificacion.para_estudiante}"
    )
    return db_notificacion


def obtener_notificaciones_estudiante(
    db: Session, estudiante_id: int, limit: int = 50, solo_no_leidas: bool = False
) -> List[dict]:
    """Obtener notificaciones DIRECTAS de un estudiante (para_estudiante=True)"""
    query = (
        db.query(Notificacion)
        .options(
            joinedload(Notificacion.estudiante),
            joinedload(Notificacion.evaluacion).joinedload(Evaluacion.materia),
        )
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
    )

    if solo_no_leidas:
        query = query.filter(Notificacion.leida == False)

    notificaciones = query.order_by(desc(Notificacion.created_at)).limit(limit).all()

    # Formatear respuesta
    resultado = []
    for notif in notificaciones:
        item = {
            "id": notif.id,
            "titulo": notif.titulo,
            "mensaje": notif.mensaje,
            "tipo": notif.tipo,
            "leida": notif.leida,
            "padre_id": notif.padre_id,
            "estudiante_id": notif.estudiante_id,
            "evaluacion_id": notif.evaluacion_id,
            "para_estudiante": notif.para_estudiante,
            "created_at": notif.created_at,
            "updated_at": notif.updated_at,
            "estudiante_nombre": notif.estudiante.nombre if notif.estudiante else None,
            "estudiante_apellido": (
                notif.estudiante.apellido if notif.estudiante else None
            ),
            "materia_nombre": (
                notif.evaluacion.materia.nombre
                if notif.evaluacion and notif.evaluacion.materia
                else None
            ),
            "evaluacion_valor": notif.evaluacion.valor if notif.evaluacion else None,
        }
        resultado.append(item)

    return resultado


def obtener_notificaciones_padre(
    db: Session, padre_id: int, limit: int = 50, solo_no_leidas: bool = False
) -> List[dict]:
    """Obtener notificaciones de un padre (para_estudiante=False y con padre_id)"""
    query = (
        db.query(Notificacion)
        .options(
            joinedload(Notificacion.estudiante),
            joinedload(Notificacion.evaluacion).joinedload(Evaluacion.materia),
        )
        .filter(
            and_(
                Notificacion.padre_id == padre_id, Notificacion.para_estudiante == False
            )
        )
    )

    if solo_no_leidas:
        query = query.filter(Notificacion.leida == False)

    notificaciones = query.order_by(desc(Notificacion.created_at)).limit(limit).all()

    # Formatear respuesta
    resultado = []
    for notif in notificaciones:
        item = {
            "id": notif.id,
            "titulo": notif.titulo,
            "mensaje": notif.mensaje,
            "tipo": notif.tipo,
            "leida": notif.leida,
            "padre_id": notif.padre_id,
            "estudiante_id": notif.estudiante_id,
            "evaluacion_id": notif.evaluacion_id,
            "para_estudiante": notif.para_estudiante,
            "created_at": notif.created_at,
            "updated_at": notif.updated_at,
            "estudiante_nombre": notif.estudiante.nombre if notif.estudiante else None,
            "estudiante_apellido": (
                notif.estudiante.apellido if notif.estudiante else None
            ),
            "materia_nombre": (
                notif.evaluacion.materia.nombre
                if notif.evaluacion and notif.evaluacion.materia
                else None
            ),
            "evaluacion_valor": notif.evaluacion.valor if notif.evaluacion else None,
        }
        resultado.append(item)

    return resultado


def obtener_notificacion_por_id_estudiante(
    db: Session, notificacion_id: int, estudiante_id: int
) -> Optional[Notificacion]:
    """Obtener una notificación específica para un estudiante"""
    return (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.id == notificacion_id,
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
        .first()
    )


def obtener_notificacion_por_id_padre(
    db: Session, notificacion_id: int, padre_id: int
) -> Optional[Notificacion]:
    """Obtener una notificación específica para un padre"""
    return (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.id == notificacion_id,
                Notificacion.padre_id == padre_id,
                Notificacion.para_estudiante == False,
            )
        )
        .first()
    )


def marcar_como_leida_estudiante(
    db: Session, notificacion_id: int, estudiante_id: int
) -> Optional[Notificacion]:
    """Marcar una notificación como leída para un estudiante"""
    notificacion = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.id == notificacion_id,
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
        .first()
    )

    if notificacion:
        notificacion.leida = True
        db.commit()
        db.refresh(notificacion)
        logger.info(
            f"Notificación {notificacion_id} marcada como leída por estudiante {estudiante_id}"
        )

    return notificacion


def marcar_como_leida_padre(
    db: Session, notificacion_id: int, padre_id: int
) -> Optional[Notificacion]:
    """Marcar una notificación como leída para un padre"""
    notificacion = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.id == notificacion_id,
                Notificacion.padre_id == padre_id,
                Notificacion.para_estudiante == False,
            )
        )
        .first()
    )

    if notificacion:
        notificacion.leida = True
        db.commit()
        db.refresh(notificacion)
        logger.info(
            f"Notificación {notificacion_id} marcada como leída por padre {padre_id}"
        )

    return notificacion


def marcar_todas_como_leidas_estudiante(db: Session, estudiante_id: int) -> int:
    """Marcar todas las notificaciones de un estudiante como leídas"""
    count = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
                Notificacion.leida == False,
            )
        )
        .update({"leida": True})
    )

    db.commit()
    logger.info(
        f"{count} notificaciones marcadas como leídas para estudiante {estudiante_id}"
    )
    return count


def marcar_todas_como_leidas_padre(db: Session, padre_id: int) -> int:
    """Marcar todas las notificaciones de un padre como leídas"""
    count = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.padre_id == padre_id,
                Notificacion.para_estudiante == False,
                Notificacion.leida == False,
            )
        )
        .update({"leida": True})
    )

    db.commit()
    logger.info(f"{count} notificaciones marcadas como leídas para padre {padre_id}")
    return count


def contar_notificaciones_no_leidas_estudiante(db: Session, estudiante_id: int) -> int:
    """Contar notificaciones no leídas de un estudiante"""
    return (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
                Notificacion.leida == False,
            )
        )
        .count()
    )


def contar_notificaciones_no_leidas_padre(db: Session, padre_id: int) -> int:
    """Contar notificaciones no leídas de un padre"""
    return (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.padre_id == padre_id,
                Notificacion.para_estudiante == False,
                Notificacion.leida == False,
            )
        )
        .count()
    )


def obtener_estadisticas_notificaciones_estudiante(
    db: Session, estudiante_id: int
) -> dict:
    """Obtener estadísticas de notificaciones de un estudiante"""
    # Contar total de notificaciones
    total = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
        .count()
    )

    # Contar no leídas
    no_leidas = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
                Notificacion.leida == False,
            )
        )
        .count()
    )

    # Contar leídas
    leidas = total - no_leidas

    # Contar por tipo
    tipos_result = (
        db.query(Notificacion.tipo, func.count(Notificacion.id))
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
        .group_by(Notificacion.tipo)
        .all()
    )

    por_tipo = {tipo: count for tipo, count in tipos_result}

    return {
        "total": total,
        "no_leidas": no_leidas,
        "leidas": leidas,
        "por_tipo": por_tipo,
    }


def obtener_estadisticas_notificaciones_padre(db: Session, padre_id: int) -> dict:
    """Obtener estadísticas de notificaciones de un padre"""
    # Contar total de notificaciones
    total = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.padre_id == padre_id, Notificacion.para_estudiante == False
            )
        )
        .count()
    )

    # Contar no leídas
    no_leidas = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.padre_id == padre_id,
                Notificacion.para_estudiante == False,
                Notificacion.leida == False,
            )
        )
        .count()
    )

    # Contar leídas
    leidas = total - no_leidas

    # Contar por tipo
    tipos_result = (
        db.query(Notificacion.tipo, func.count(Notificacion.id))
        .filter(
            and_(
                Notificacion.padre_id == padre_id, Notificacion.para_estudiante == False
            )
        )
        .group_by(Notificacion.tipo)
        .all()
    )

    por_tipo = {tipo: count for tipo, count in tipos_result}

    return {
        "total": total,
        "no_leidas": no_leidas,
        "leidas": leidas,
        "por_tipo": por_tipo,
    }


def eliminar_notificacion_estudiante(
    db: Session, notificacion_id: int, estudiante_id: int
) -> bool:
    """Eliminar una notificación para un estudiante"""
    notificacion = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.id == notificacion_id,
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
        .first()
    )

    if notificacion:
        db.delete(notificacion)
        db.commit()
        logger.info(
            f"Notificación {notificacion_id} eliminada por estudiante {estudiante_id}"
        )
        return True

    return False


def eliminar_notificacion_padre(
    db: Session, notificacion_id: int, padre_id: int
) -> bool:
    """Eliminar una notificación para un padre"""
    notificacion = (
        db.query(Notificacion)
        .filter(
            and_(
                Notificacion.id == notificacion_id,
                Notificacion.padre_id == padre_id,
                Notificacion.para_estudiante == False,
            )
        )
        .first()
    )

    if notificacion:
        db.delete(notificacion)
        db.commit()
        logger.info(f"Notificación {notificacion_id} eliminada por padre {padre_id}")
        return True

    return False


def obtener_notificaciones_estudiante_por_materia(
    db: Session, estudiante_id: int, materia_id: int, limit: int = 20
) -> List[dict]:
    """Obtener notificaciones de un estudiante filtradas por materia"""
    query = (
        db.query(Notificacion)
        .options(
            joinedload(Notificacion.estudiante),
            joinedload(Notificacion.evaluacion).joinedload(Evaluacion.materia),
        )
        .join(Evaluacion, Notificacion.evaluacion_id == Evaluacion.id)
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
                Evaluacion.materia_id == materia_id,
            )
        )
        .order_by(desc(Notificacion.created_at))
        .limit(limit)
    )

    notificaciones = query.all()

    # Formatear respuesta
    resultado = []
    for notif in notificaciones:
        item = {
            "id": notif.id,
            "titulo": notif.titulo,
            "mensaje": notif.mensaje,
            "tipo": notif.tipo,
            "leida": notif.leida,
            "padre_id": notif.padre_id,
            "estudiante_id": notif.estudiante_id,
            "evaluacion_id": notif.evaluacion_id,
            "para_estudiante": notif.para_estudiante,
            "created_at": notif.created_at,
            "updated_at": notif.updated_at,
            "estudiante_nombre": notif.estudiante.nombre if notif.estudiante else None,
            "estudiante_apellido": (
                notif.estudiante.apellido if notif.estudiante else None
            ),
            "materia_nombre": (
                notif.evaluacion.materia.nombre
                if notif.evaluacion and notif.evaluacion.materia
                else None
            ),
            "evaluacion_valor": notif.evaluacion.valor if notif.evaluacion else None,
        }
        resultado.append(item)

    return resultado


def obtener_resumen_notificaciones_por_materias(
    db: Session, estudiante_id: int
) -> List[dict]:
    """Obtener resumen de notificaciones agrupadas por materia para un estudiante"""
    query = (
        db.query(
            Materia.id.label("materia_id"),
            Materia.nombre.label("materia_nombre"),
            func.count(Notificacion.id).label("total_notificaciones"),
            func.sum(func.case([(Notificacion.leida == False, 1)], else_=0)).label(
                "no_leidas"
            ),
            func.max(Notificacion.created_at).label("ultima_notificacion"),
        )
        .join(Evaluacion, Notificacion.evaluacion_id == Evaluacion.id)
        .join(Materia, Evaluacion.materia_id == Materia.id)
        .filter(
            and_(
                Notificacion.estudiante_id == estudiante_id,
                Notificacion.para_estudiante == True,
            )
        )
        .group_by(Materia.id, Materia.nombre)
        .order_by(desc("ultima_notificacion"))
    )

    results = query.all()

    # Formatear respuesta
    resumen = []
    for result in results:
        item = {
            "materia_id": result.materia_id,
            "materia_nombre": result.materia_nombre,
            "total_notificaciones": result.total_notificaciones,
            "no_leidas": result.no_leidas,
            "ultima_notificacion": result.ultima_notificacion,
        }
        resumen.append(item)

    return resumen


# Funciones de compatibilidad (mantener las originales sin modificar)
