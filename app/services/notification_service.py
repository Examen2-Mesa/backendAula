# app/services/notification_service.py - SERVICIO ACTUALIZADO

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.schemas.notificacion import NotificacionCreate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def notificar_evaluacion_completa(
        db: Session, evaluacion_id: int, umbral_padres: float = 50.0
    ) -> dict:
        """
        Notificación completa:
        - SIEMPRE notifica al estudiante (sin umbral)
        - Solo notifica a padres si está debajo del umbral
        """
        try:
            from app.models.evaluacion import Evaluacion
            from app.models.padre_estudiante import PadreEstudiante
            from app.crud import notificacion as crud_notificacion

            # Obtener la evaluación
            evaluacion = (
                db.query(Evaluacion)
                .options(
                    joinedload(Evaluacion.estudiante),
                    joinedload(Evaluacion.materia),
                    joinedload(Evaluacion.tipo_evaluacion),
                )
                .filter(Evaluacion.id == evaluacion_id)
                .first()
            )

            if not evaluacion:
                logger.error(f"Evaluación {evaluacion_id} no encontrada")
                return {
                    "estudiante": [],
                    "padres": [],
                    "error": "Evaluación no encontrada",
                }

            notificaciones_estudiante = []
            notificaciones_padres = []

            # 1. SIEMPRE crear notificación para el estudiante
            titulo_estudiante = f"📝 Nueva Calificación - {evaluacion.materia.nombre}"
            mensaje_estudiante = (
                f"Tu calificación en {evaluacion.descripcion} "
                f"de la materia {evaluacion.materia.nombre} es: {evaluacion.valor} puntos. "
                f"Fecha de evaluación: {evaluacion.fecha.strftime('%d/%m/%Y')}"
            )

            # Verificar si ya existe notificación para el estudiante
            notificacion_estudiante_existente = (
                db.query(crud_notificacion.Notificacion)
                .filter(
                    crud_notificacion.Notificacion.estudiante_id
                    == evaluacion.estudiante_id,
                    crud_notificacion.Notificacion.evaluacion_id == evaluacion_id,
                    crud_notificacion.Notificacion.para_estudiante == True,
                )
                .first()
            )

            if not notificacion_estudiante_existente:
                notificacion_data_estudiante = NotificacionCreate(
                    titulo=titulo_estudiante,
                    mensaje=mensaje_estudiante,
                    tipo="evaluacion",
                    padre_id=None,  # No tiene padre_id porque es para el estudiante
                    estudiante_id=evaluacion.estudiante_id,
                    evaluacion_id=evaluacion.id,
                    para_estudiante=True,
                )

                try:
                    notificacion_estudiante = crud_notificacion.crear_notificacion(
                        db, notificacion_data_estudiante
                    )
                    notificaciones_estudiante.append(notificacion_estudiante.id)
                    logger.info(
                        f"Notificación creada para estudiante {evaluacion.estudiante_id} sobre evaluación {evaluacion_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error creando notificación para estudiante: {str(e)}"
                    )

            # 2. Solo crear notificación para padres si está debajo del umbral
            if evaluacion.valor < umbral_padres:
                # Obtener los padres del estudiante
                padres = (
                    db.query(PadreEstudiante)
                    .filter(PadreEstudiante.estudiante_id == evaluacion.estudiante_id)
                    .all()
                )

                titulo_padre = f"⚠️ Calificación Baja - {evaluacion.estudiante.nombre}"
                mensaje_padre = (
                    f"Su hijo(a) {evaluacion.estudiante.nombre} {evaluacion.estudiante.apellido} "
                    f"obtuvo {evaluacion.valor} puntos en {evaluacion.descripcion} "
                    f"de la materia {evaluacion.materia.nombre}. "
                    f"Le recomendamos estar atento al rendimiento académico."
                )

                for padre_relacion in padres:
                    padre_id = padre_relacion.padre_id

                    # Verificar si ya existe notificación para este padre
                    notificacion_padre_existente = (
                        db.query(crud_notificacion.Notificacion)
                        .filter(
                            crud_notificacion.Notificacion.padre_id == padre_id,
                            crud_notificacion.Notificacion.evaluacion_id
                            == evaluacion_id,
                            crud_notificacion.Notificacion.tipo == "calificacion_baja",
                        )
                        .first()
                    )

                    if not notificacion_padre_existente:
                        notificacion_data_padre = NotificacionCreate(
                            titulo=titulo_padre,
                            mensaje=mensaje_padre,
                            tipo="calificacion_baja",
                            padre_id=padre_id,
                            estudiante_id=evaluacion.estudiante_id,
                            evaluacion_id=evaluacion.id,
                            para_estudiante=False,
                        )

                        try:
                            notificacion_padre = crud_notificacion.crear_notificacion(
                                db, notificacion_data_padre
                            )
                            notificaciones_padres.append(notificacion_padre.id)
                            logger.info(
                                f"Notificación creada para padre {padre_id} sobre calificación baja {evaluacion_id}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error creando notificación para padre {padre_id}: {str(e)}"
                            )

            return {
                "estudiante": notificaciones_estudiante,
                "padres": notificaciones_padres,
                "evaluacion_valor": evaluacion.valor,
                "umbral_usado": umbral_padres,
                "notificacion_padre_activada": evaluacion.valor < umbral_padres,
            }

        except Exception as e:
            logger.error(f"Error en notificar_evaluacion_completa: {str(e)}")
            return {"estudiante": [], "padres": [], "error": str(e)}

    @staticmethod
    def crear_notificacion_solo_estudiante(
        db: Session,
        estudiante_id: int,
        titulo: str,
        mensaje: str,
        tipo: str = "general",
        evaluacion_id: Optional[int] = None,
    ) -> Optional[int]:
        """Crear notificación que solo va al estudiante"""
        try:
            from app.crud import notificacion as crud_notificacion

            notificacion_data = NotificacionCreate(
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                padre_id=None,
                estudiante_id=estudiante_id,
                evaluacion_id=evaluacion_id,
                para_estudiante=True,
            )

            notificacion = crud_notificacion.crear_notificacion(db, notificacion_data)
            logger.info(f"Notificación solo-estudiante creada: {notificacion.id}")
            return notificacion.id

        except Exception as e:
            logger.error(f"Error creando notificación solo-estudiante: {str(e)}")
            return None

    @staticmethod
    def crear_notificacion_solo_padres(
        db: Session,
        estudiante_id: int,
        titulo: str,
        mensaje: str,
        tipo: str = "general",
        evaluacion_id: Optional[int] = None,
    ) -> List[int]:
        """Crear notificación que solo va a los padres"""
        try:
            from app.models.padre_estudiante import PadreEstudiante
            from app.crud import notificacion as crud_notificacion

            # Obtener todos los padres del estudiante
            padres = (
                db.query(PadreEstudiante)
                .filter(PadreEstudiante.estudiante_id == estudiante_id)
                .all()
            )

            notificaciones_creadas = []

            for padre_relacion in padres:
                padre_id = padre_relacion.padre_id

                notificacion_data = NotificacionCreate(
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo=tipo,
                    padre_id=padre_id,
                    estudiante_id=estudiante_id,
                    evaluacion_id=evaluacion_id,
                    para_estudiante=False,
                )

                try:
                    notificacion = crud_notificacion.crear_notificacion(
                        db, notificacion_data
                    )
                    notificaciones_creadas.append(notificacion.id)
                except Exception as e:
                    logger.error(
                        f"Error creando notificación para padre {padre_id}: {str(e)}"
                    )

            return notificaciones_creadas

        except Exception as e:
            logger.error(f"Error en crear_notificacion_solo_padres: {str(e)}")
            return []

    @staticmethod
    def migrar_evaluaciones_existentes(
        db: Session, limite_dias: int = 30, umbral_padres: float = 50.0
    ) -> dict:
        """Migrar evaluaciones existentes para crear notificaciones de estudiantes"""
        try:
            from app.models.evaluacion import Evaluacion
            from datetime import datetime, timedelta

            fecha_limite = datetime.now().date() - timedelta(days=limite_dias)

            # Obtener evaluaciones sin notificaciones para estudiantes
            evaluaciones = (
                db.query(Evaluacion).filter(Evaluacion.fecha >= fecha_limite).all()
            )

            total_procesadas = 0
            total_estudiante = 0
            total_padres = 0

            for evaluacion in evaluaciones:
                resultado = NotificationService.notificar_evaluacion_completa(
                    db, evaluacion.id, umbral_padres
                )

                if "error" not in resultado:
                    total_procesadas += 1
                    total_estudiante += len(resultado["estudiante"])
                    total_padres += len(resultado["padres"])

            return {
                "evaluaciones_procesadas": total_procesadas,
                "notificaciones_estudiante": total_estudiante,
                "notificaciones_padres": total_padres,
                "dias_migrados": limite_dias,
                "umbral_usado": umbral_padres,
            }

        except Exception as e:
            logger.error(f"Error en migración: {str(e)}")
            return {"error": str(e)}

    # Mantener funciones existentes para compatibilidad
    @staticmethod
    def verificar_y_notificar_calificacion_baja(
        db: Session, evaluacion_id: int, umbral: float = 50.0
    ) -> List[int]:
        """Función de compatibilidad - ahora usa el sistema dual"""
        resultado = NotificationService.notificar_evaluacion_completa(
            db, evaluacion_id, umbral
        )
        # Retorna solo las notificaciones de padres para mantener compatibilidad
        return resultado.get("padres", [])

    @staticmethod
    def notificar_evaluacion_registrada(
        db: Session,
        evaluacion_id: int,
        solo_calificaciones_bajas: bool = True,
        umbral: float = 50.0,
    ) -> List[int]:
        """Función de compatibilidad - ahora usa el sistema dual"""
        if solo_calificaciones_bajas:
            resultado = NotificationService.notificar_evaluacion_completa(
                db, evaluacion_id, umbral
            )
            # Retorna notificaciones de padres y estudiantes
            notificaciones = resultado.get("padres", []) + resultado.get(
                "estudiante", []
            )
            return notificaciones
        else:
            # Forzar notificación (establecer umbral muy alto)
            resultado = NotificationService.notificar_evaluacion_completa(
                db, evaluacion_id, 100.0
            )
            notificaciones = resultado.get("padres", []) + resultado.get(
                "estudiante", []
            )
            return notificaciones
