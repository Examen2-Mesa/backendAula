# app/routers/notificaciones.py - ROUTER FINAL CON SISTEMA DUAL

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.auth.roles import (
    usuario_autenticado,
    admin_required,
    docente_o_admin_required,
)
from app.schemas.notificacion import (
    NotificacionOut,
    NotificacionStats,
    NotificacionResponse,
    NotificacionListResponse,
)
from app.crud import notificacion as crud_notificacion
from app.services.notification_service import NotificationService
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notificaciones", tags=["📢 Notificaciones Duales (Padres + Estudiantes)"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== ENDPOINTS UNIFICADOS PARA PADRES Y ESTUDIANTES ==========


@router.get("/mis-notificaciones", response_model=List[NotificacionOut])
def obtener_mis_notificaciones(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de notificaciones"),
    solo_no_leidas: bool = Query(False, description="Solo mostrar no leídas"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📱 Obtener mis notificaciones (padres ven de hijos con umbral, estudiantes ven todas las suyas)"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403,
            detail="Solo padres y estudiantes pueden acceder a este endpoint",
        )

    try:
        if user_type == "padre":
            # Padres ven notificaciones de calificaciones bajas de sus hijos
            notificaciones = crud_notificacion.obtener_notificaciones_padre(
                db, user_id, limit, solo_no_leidas
            )
            logger.info(
                f"Padre {user_id} consultó {len(notificaciones)} notificaciones"
            )
        else:  # estudiante
            # Estudiantes ven TODAS sus evaluaciones
            notificaciones = crud_notificacion.obtener_notificaciones_estudiante(
                db, user_id, limit, solo_no_leidas
            )
            logger.info(
                f"Estudiante {user_id} consultó {len(notificaciones)} notificaciones"
            )

        return notificaciones

    except Exception as e:
        logger.error(
            f"Error obteniendo notificaciones para {user_type} {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/count-no-leidas")
def contar_notificaciones_no_leidas(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """🔢 Obtener cantidad de notificaciones no leídas (para badges)"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403, detail="Solo padres y estudiantes pueden acceder"
        )

    try:
        if user_type == "padre":
            count = crud_notificacion.contar_notificaciones_no_leidas_padre(db, user_id)
        else:  # estudiante
            count = crud_notificacion.contar_notificaciones_no_leidas_estudiante(
                db, user_id
            )

        return {"count": count, "user_type": user_type}

    except Exception as e:
        logger.error(
            f"Error contando notificaciones no leídas para {user_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/{notificacion_id}/marcar-leida")
def marcar_notificacion_como_leida(
    notificacion_id: int,
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """✅ Marcar notificación como leída"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403, detail="Solo padres y estudiantes pueden acceder"
        )

    try:
        if user_type == "padre":
            notificacion = crud_notificacion.marcar_como_leida_padre(
                db, notificacion_id, user_id
            )
        else:  # estudiante
            notificacion = crud_notificacion.marcar_como_leida_estudiante(
                db, notificacion_id, user_id
            )

        if not notificacion:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

        return {"success": True, "mensaje": "Notificación marcada como leída"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error marcando notificación {notificacion_id} como leída para {user_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/marcar-todas-leidas")
def marcar_todas_las_notificaciones_como_leidas(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """✅ Marcar todas mis notificaciones como leídas"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403, detail="Solo padres y estudiantes pueden acceder"
        )

    try:
        if user_type == "padre":
            count = crud_notificacion.marcar_todas_como_leidas_padre(db, user_id)
        else:  # estudiante
            count = crud_notificacion.marcar_todas_como_leidas_estudiante(db, user_id)

        return {
            "success": True,
            "mensaje": f"{count} notificaciones marcadas como leídas",
            "count": count,
        }

    except Exception as e:
        logger.error(
            f"Error marcando todas las notificaciones como leídas para {user_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/estadisticas", response_model=NotificacionStats)
def obtener_estadisticas_notificaciones(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📊 Obtener estadísticas de mis notificaciones"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403, detail="Solo padres y estudiantes pueden acceder"
        )

    try:
        if user_type == "padre":
            stats = crud_notificacion.obtener_estadisticas_notificaciones_padre(
                db, user_id
            )
        else:  # estudiante
            stats = crud_notificacion.obtener_estadisticas_notificaciones_estudiante(
                db, user_id
            )

        return stats

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas para {user_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{notificacion_id}", response_model=NotificacionOut)
def obtener_notificacion_detalle(
    notificacion_id: int,
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """👁️ Obtener detalle de una notificación específica"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403, detail="Solo padres y estudiantes pueden acceder"
        )

    try:
        if user_type == "padre":
            notificacion = crud_notificacion.obtener_notificacion_por_id_padre(
                db, notificacion_id, user_id
            )
        else:  # estudiante
            notificacion = crud_notificacion.obtener_notificacion_por_id_estudiante(
                db, notificacion_id, user_id
            )

        if not notificacion:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

        # Marcar como leída automáticamente al ver el detalle
        if not notificacion.leida:
            if user_type == "padre":
                crud_notificacion.marcar_como_leida_padre(db, notificacion_id, user_id)
            else:  # estudiante
                crud_notificacion.marcar_como_leida_estudiante(
                    db, notificacion_id, user_id
                )

        return notificacion

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error obteniendo detalle de notificación {notificacion_id} para {user_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/{notificacion_id}")
def eliminar_notificacion(
    notificacion_id: int,
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """🗑️ Eliminar una notificación"""
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type not in ["padre", "estudiante"]:
        raise HTTPException(
            status_code=403, detail="Solo padres y estudiantes pueden acceder"
        )

    try:
        if user_type == "padre":
            eliminada = crud_notificacion.eliminar_notificacion_padre(
                db, notificacion_id, user_id
            )
        else:  # estudiante
            eliminada = crud_notificacion.eliminar_notificacion_estudiante(
                db, notificacion_id, user_id
            )

        if not eliminada:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

        return {"success": True, "mensaje": "Notificación eliminada correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error eliminando notificación {notificacion_id} para {user_type}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ========== ENDPOINTS ESPECÍFICOS PARA ESTUDIANTES ==========


@router.get("/estudiante/por-materia/{materia_id}")
def obtener_notificaciones_por_materia(
    materia_id: int,
    limit: int = Query(20, ge=1, le=50, description="Número máximo de notificaciones"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📚 Obtener notificaciones de una materia específica (Solo estudiantes)"""
    if payload.get("user_type") != "estudiante":
        raise HTTPException(
            status_code=403, detail="Solo estudiantes pueden acceder a este endpoint"
        )

    estudiante_id = payload.get("user_id")

    try:
        notificaciones = (
            crud_notificacion.obtener_notificaciones_estudiante_por_materia(
                db, estudiante_id, materia_id, limit
            )
        )

        return {
            "success": True,
            "data": notificaciones,
            "total": len(notificaciones),
            "materia_id": materia_id,
        }

    except Exception as e:
        logger.error(
            f"Error obteniendo notificaciones por materia {materia_id} para estudiante {estudiante_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/estudiante/resumen-por-materias")
def obtener_resumen_notificaciones_por_materias(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📈 Obtener resumen de notificaciones agrupadas por materia (Solo estudiantes)"""
    if payload.get("user_type") != "estudiante":
        raise HTTPException(
            status_code=403, detail="Solo estudiantes pueden acceder a este endpoint"
        )

    estudiante_id = payload.get("user_id")

    try:
        resumen = crud_notificacion.obtener_resumen_notificaciones_por_materias(
            db, estudiante_id
        )

        return {
            "success": True,
            "data": resumen,
            "mensaje": f"Resumen de notificaciones por {len(resumen)} materias",
        }

    except Exception as e:
        logger.error(
            f"Error obteniendo resumen por materias para estudiante {estudiante_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ========== ENDPOINTS PARA DOCENTES - SISTEMA DUAL ==========


@router.post("/docente/notificar-evaluacion/{evaluacion_id}")
def notificar_evaluacion_sistema_dual(
    evaluacion_id: int,
    umbral_padres: float = Query(
        50.0,
        ge=0,
        le=100,
        description="Umbral para notificar a padres (estudiantes siempre reciben notificación)",
    ),
    payload: dict = Depends(docente_o_admin_required),
    db: Session = Depends(get_db),
):
    """👨‍🏫 Notificar evaluación con sistema dual: SIEMPRE al estudiante, solo a padres si está debajo del umbral"""
    try:
        resultado = NotificationService.notificar_evaluacion_completa(
            db, evaluacion_id, umbral_padres
        )

        if "error" in resultado:
            raise HTTPException(status_code=400, detail=resultado["error"])

        return {
            "success": True,
            "mensaje": f"Sistema dual activado: {len(resultado['estudiante'])} notif. estudiante, {len(resultado['padres'])} notif. padres",
            "notificaciones_estudiante": resultado["estudiante"],
            "notificaciones_padres": resultado["padres"],
            "evaluacion_valor": resultado["evaluacion_valor"],
            "umbral_usado": resultado["umbral_usado"],
            "notificacion_padre_activada": resultado["notificacion_padre_activada"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error en notificación dual para evaluación {evaluacion_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/docente/notificar-solo-estudiante")
def crear_notificacion_solo_estudiante(
    estudiante_id: int,
    titulo: str,
    mensaje: str,
    tipo: str = Query("general", description="Tipo de notificación"),
    evaluacion_id: Optional[int] = Query(
        None, description="ID de evaluación relacionada"
    ),
    payload: dict = Depends(docente_o_admin_required),
    db: Session = Depends(get_db),
):
    """👨‍🏫 Crear notificación SOLO para el estudiante (no para padres)"""
    try:
        notificacion_id = NotificationService.crear_notificacion_solo_estudiante(
            db, estudiante_id, titulo, mensaje, tipo, evaluacion_id
        )

        if not notificacion_id:
            raise HTTPException(status_code=400, detail="Error creando la notificación")

        return {
            "success": True,
            "mensaje": "Notificación creada solo para el estudiante",
            "notificacion_id": notificacion_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando notificación solo-estudiante: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/docente/notificar-solo-padres")
def crear_notificacion_solo_padres(
    estudiante_id: int,
    titulo: str,
    mensaje: str,
    tipo: str = Query("general", description="Tipo de notificación"),
    evaluacion_id: Optional[int] = Query(
        None, description="ID de evaluación relacionada"
    ),
    payload: dict = Depends(docente_o_admin_required),
    db: Session = Depends(get_db),
):
    """👨‍🏫 Crear notificación SOLO para los padres (no para estudiante)"""
    try:
        notificaciones_ids = NotificationService.crear_notificacion_solo_padres(
            db, estudiante_id, titulo, mensaje, tipo, evaluacion_id
        )

        if not notificaciones_ids:
            raise HTTPException(
                status_code=400,
                detail="Error creando notificaciones o estudiante sin padres",
            )

        return {
            "success": True,
            "mensaje": f"Notificaciones creadas solo para {len(notificaciones_ids)} padres",
            "notificaciones_ids": notificaciones_ids,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando notificaciones solo-padres: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ========== ENDPOINTS ADMINISTRATIVOS ==========


@router.post("/admin/migrar-sistema-dual")
def migrar_a_sistema_dual(
    limite_dias: int = Query(
        30, ge=1, le=365, description="Días hacia atrás para migrar"
    ),
    umbral_padres: float = Query(
        50.0, ge=0, le=100, description="Umbral para notificaciones de padres"
    ),
    payload: dict = Depends(admin_required),
    db: Session = Depends(get_db),
):
    """👑 Migrar evaluaciones existentes al sistema dual (Solo Administradores)"""
    try:
        resultado = NotificationService.migrar_evaluaciones_existentes(
            db, limite_dias, umbral_padres
        )

        if "error" in resultado:
            raise HTTPException(status_code=500, detail=resultado["error"])

        return {
            "success": True,
            "mensaje": "Migración al sistema dual completada",
            "evaluaciones_procesadas": resultado["evaluaciones_procesadas"],
            "notificaciones_estudiante": resultado["notificaciones_estudiante"],
            "notificaciones_padres": resultado["notificaciones_padres"],
            "dias_migrados": resultado["dias_migrados"],
            "umbral_usado": resultado["umbral_usado"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en migración al sistema dual: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Mantener endpoints administrativos existentes para compatibilidad...
# (los demás endpoints administrativos del código original)
