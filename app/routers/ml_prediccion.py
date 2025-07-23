"""
Rutas de FastAPI para el sistema de predicción de rendimiento académico
"""

from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, validator
from app.database import SessionLocal
from app.auth.roles import docente_o_admin_required, usuario_autenticado
import logging

from app.models.curso_materia import CursoMateria
from app.models.estudiante import Estudiante
from app.models.inscripcion import Inscripcion
from app.models.materia import Materia
from app.models.periodo import Periodo
from app.models.prediccion_rendimiento import PrediccionRendimiento
from app.schemas.prediccion_rendimiento import PrediccionRendimientoOut

# Importar el servicio de predicción
try:
    from app.ml.prediction_service import (
        get_prediction_service,
        PredictionService,
        crear_prediccion_response,
        crear_error_response,
    )
except ImportError:
    # Si no se puede importar, crear imports relativos
    import sys
    import os

    sys.path.append(os.path.dirname(__file__))
    from app.ml.prediction_service import (
        get_prediction_service,
        PredictionService,
        crear_prediccion_response,
        crear_error_response,
    )

# Configurar logging
logger = logging.getLogger(__name__)

# Router para las rutas de ML
router = APIRouter(prefix="/ml", tags=["Machine Learning - Predicción de Rendimiento"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================ MODELOS PYDANTIC ================


class PredictionRequest(BaseModel):
    """Modelo para solicitud de predicción manual"""

    promedio_notas_anterior: float
    porcentaje_asistencia: float
    promedio_participacion: float
    promedio_examenes: Optional[float] = 0.0
    promedio_tareas: Optional[float] = 0.0
    promedio_exposiciones: Optional[float] = 0.0
    promedio_practicas: Optional[float] = 0.0
    edad: Optional[int] = 16
    genero_masculino: Optional[int] = 0
    turno_manana: Optional[int] = 1

    @validator(
        "promedio_notas_anterior", "porcentaje_asistencia", "promedio_participacion"
    )
    def validar_rangos_principales(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Los valores deben estar entre 0 y 100")
        return v

    @validator("edad")
    def validar_edad(cls, v):
        if v and not 10 <= v <= 30:
            raise ValueError("La edad debe estar entre 10 y 30 años")
        return v


class EstudiantePrediccionResponse(BaseModel):
    """Modelo para respuesta de predicción de estudiante"""

    estudiante_id: int
    nombre: str
    apellido: str
    prediccion_numerica: float
    clasificacion: str
    nivel_riesgo: str
    confianza: float
    recomendaciones: List[str]


class ModelStatsResponse(BaseModel):
    """Modelo para estadísticas del modelo"""

    modelos_cargados: bool
    modelo_regresion: dict
    modelo_clasificacion: dict
    features_utilizadas: List[str]
    fecha_carga: str


# ================ ENDPOINTS PRINCIPALES ================


@router.get("/health")
def health_check():
    """Verificar estado del servicio de ML"""
    try:
        service = get_prediction_service()
        if service.models_loaded:
            return {
                "status": "healthy",
                "modelos_cargados": True,
                "mensaje": "Servicio de ML funcionando correctamente",
            }
        else:
            return {
                "status": "unhealthy",
                "modelos_cargados": False,
                "mensaje": "Modelos no cargados",
            }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servicio ML")


@router.post("/predecir-rendimiento")
def predecir_rendimiento_manual(
    datos: PredictionRequest, payload: dict = Depends(docente_o_admin_required)
):
    """
    Realizar predicción manual de rendimiento académico

    Permite a los docentes hacer predicciones introduciendo datos manualmente
    """
    try:
        service = get_prediction_service()

        # Convertir a diccionario
        datos_dict = datos.dict()

        # Realizar predicción
        resultado = service.predecir_rendimiento(datos_dict)

        return crear_prediccion_response(resultado)

    except ValueError as e:
        logger.warning(f"Error de validación en predicción manual: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en predicción manual: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno en predicción")


@router.get("/predecir-estudiante/{estudiante_id}")
def predecir_estudiante(
    estudiante_id: int,
    materia_id: int = Query(..., description="ID de la materia"),
    periodo_id: int = Query(..., description="ID del periodo"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Predecir rendimiento para un estudiante específico usando datos de la BD
    """
    try:
        service = get_prediction_service()

        # Realizar predicción usando datos de la BD
        resultado = service.predecir_estudiante_por_bd(
            db, estudiante_id, materia_id, periodo_id
        )

        return crear_prediccion_response(resultado)

    except ValueError as e:
        logger.warning(f"Estudiante no encontrado: {estudiante_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error prediciendo estudiante {estudiante_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno en predicción")


@router.get("/predecir-curso/{curso_id}")
def predecir_curso_completo(
    curso_id: int,
    materia_id: int = Query(..., description="ID de la materia"),
    periodo_id: int = Query(..., description="ID del periodo"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Predecir rendimiento para todos los estudiantes de un curso
    """
    try:
        service = get_prediction_service()

        # Realizar predicciones para todo el curso
        predicciones = service.predecir_lote_estudiantes(
            db, curso_id, materia_id, periodo_id
        )

        if not predicciones:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron estudiantes para predecir en este curso",
            )

        # Calcular estadísticas del curso
        promedio_curso = sum(p["prediccion_numerica"] for p in predicciones) / len(
            predicciones
        )

        # Contar por categorías
        categorias = {}
        riesgos = {}

        for pred in predicciones:
            cat = pred["clasificacion"]
            riesgo = pred["nivel_riesgo"]

            categorias[cat] = categorias.get(cat, 0) + 1
            riesgos[riesgo] = riesgos.get(riesgo, 0) + 1

        return {
            "success": True,
            "data": {
                "curso_id": curso_id,
                "materia_id": materia_id,
                "periodo_id": periodo_id,
                "total_estudiantes": len(predicciones),
                "promedio_curso": round(promedio_curso, 2),
                "distribucion_categorias": categorias,
                "distribucion_riesgos": riesgos,
                "predicciones": predicciones,
            },
        }

    except Exception as e:
        logger.error(f"Error prediciendo curso {curso_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error interno en predicción del curso"
        )


@router.get("/estudiantes-en-riesgo")
def obtener_estudiantes_riesgo(
    umbral: float = Query(60.0, description="Umbral de riesgo (0-100)"),
    limite: int = Query(20, description="Número máximo de estudiantes"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Obtener lista de estudiantes en riesgo académico
    """
    try:
        service = get_prediction_service()

        estudiantes_riesgo = service.obtener_estudiantes_en_riesgo(
            db, umbral_riesgo=umbral, limite=limite
        )

        return {
            "success": True,
            "data": {
                "umbral_utilizado": umbral,
                "total_encontrados": len(estudiantes_riesgo),
                "estudiantes": estudiantes_riesgo,
            },
        }

    except Exception as e:
        logger.error(f"Error obteniendo estudiantes en riesgo: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error obteniendo estudiantes en riesgo"
        )


@router.get("/estadisticas-modelo")
def obtener_estadisticas_modelo(payload: dict = Depends(docente_o_admin_required)):
    """
    Obtener estadísticas y metadatos de los modelos ML
    """
    try:
        service = get_prediction_service()
        estadisticas = service.obtener_estadisticas_modelo()

        return {"success": True, "data": estadisticas}

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error obteniendo estadísticas del modelo"
        )


# ================ ENDPOINTS PARA DASHBOARD ================


@router.get("/dashboard/resumen-ml")
def dashboard_ml_resumen(
    db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)
):
    """
    Resumen para dashboard de ML con métricas generales
    """
    try:
        service = get_prediction_service()

        # Obtener estadísticas básicas
        stats = service.obtener_estadisticas_modelo()

        # Obtener estudiantes en riesgo (muestra pequeña)
        estudiantes_riesgo = service.obtener_estudiantes_en_riesgo(db, limite=5)

        return {
            "success": True,
            "data": {
                "modelo_activo": stats.get("modelos_cargados", False),
                "total_features": len(stats.get("features_utilizadas", [])),
                "estudiantes_riesgo_detectados": len(estudiantes_riesgo),
                "modelo_info": {
                    "regresion": stats.get("modelo_regresion", {}).get("tipo", "N/A"),
                    "clasificacion": stats.get("modelo_clasificacion", {}).get(
                        "tipo", "N/A"
                    ),
                },
                "estudiantes_riesgo_muestra": estudiantes_riesgo[:3],  # Solo primeros 3
                "ultima_actualizacion": stats.get("fecha_carga", "N/A"),
            },
        }

    except Exception as e:
        logger.error(f"Error en dashboard ML: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generando resumen ML")


@router.get("/dashboard/predicciones-recientes")
def predicciones_recientes(
    limite: int = Query(10, description="Número de predicciones"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Obtener predicciones recientes para mostrar en dashboard
    """
    try:
        # Obtener estudiantes recientes de la BD
        from sqlalchemy import text

        query = """
        SELECT DISTINCT 
            e.id as estudiante_id,
            e.nombre,
            e.apellido,
            i.curso_id,
            p.id as periodo_id,
            cm.materia_id
        FROM estudiantes e
        JOIN inscripciones i ON e.id = i.estudiante_id
        JOIN periodos p ON p.gestion_id = i.gestion_id
        JOIN curso_materia cm ON cm.curso_id = i.curso_id
        WHERE p.fecha_inicio <= CURRENT_DATE 
            AND p.fecha_fin >= CURRENT_DATE
        ORDER BY e.id DESC
        LIMIT :limite
        """

        resultados = db.execute(text(query), {"limite": limite}).fetchall()

        service = get_prediction_service()
        predicciones_recientes = []

        for row in resultados[:5]:  # Limitar para evitar sobrecarga
            try:
                prediccion = service.predecir_estudiante_por_bd(
                    db, row.estudiante_id, row.materia_id, row.periodo_id
                )

                predicciones_recientes.append(
                    {
                        "estudiante_id": row.estudiante_id,
                        "nombre_completo": f"{row.nombre} {row.apellido}",
                        "prediccion_numerica": prediccion["prediccion_numerica"],
                        "clasificacion": prediccion["clasificacion"],
                        "nivel_riesgo": prediccion["nivel_riesgo"],
                        "timestamp": prediccion["timestamp"],
                    }
                )

            except Exception as e:
                logger.warning(
                    f"Error prediciendo estudiante {row.estudiante_id}: {str(e)}"
                )
                continue

        return {
            "success": True,
            "data": {
                "predicciones": predicciones_recientes,
                "total": len(predicciones_recientes),
            },
        }

    except Exception as e:
        logger.error(f"Error obteniendo predicciones recientes: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error obteniendo predicciones recientes"
        )


# ================ ENDPOINTS PARA RECOMENDACIONES ================


@router.get("/recomendaciones/{estudiante_id}")
def obtener_recomendaciones_estudiante(
    estudiante_id: int,
    materia_id: int = Query(..., description="ID de la materia"),
    periodo_id: int = Query(..., description="ID del periodo"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Obtener recomendaciones específicas para un estudiante
    """
    try:
        service = get_prediction_service()

        # Realizar predicción completa
        resultado = service.predecir_estudiante_por_bd(
            db, estudiante_id, materia_id, periodo_id
        )

        return {
            "success": True,
            "data": {
                "estudiante_id": estudiante_id,
                "prediccion_numerica": resultado["prediccion_numerica"],
                "nivel_riesgo": resultado["nivel_riesgo"],
                "recomendaciones": resultado["recomendaciones"],
                "acciones_sugeridas": {
                    "inmediatas": [
                        rec
                        for rec in resultado["recomendaciones"]
                        if "🚨" in rec or "⚠️" in rec
                    ],
                    "seguimiento": [
                        rec
                        for rec in resultado["recomendaciones"]
                        if "📚" in rec or "📖" in rec
                    ],
                    "motivacion": [
                        rec
                        for rec in resultado["recomendaciones"]
                        if "✅" in rec or "🌟" in rec
                    ],
                },
            },
        }

    except Exception as e:
        logger.error(
            f"Error obteniendo recomendaciones para estudiante {estudiante_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error obteniendo recomendaciones")


# ================ ENDPOINTS DE ADMINISTRACIÓN ================


@router.post("/admin/recargar-modelos")
def recargar_modelos(payload: dict = Depends(docente_o_admin_required)):
    """
    Recargar modelos ML (solo para administradores)
    """
    try:
        # Verificar que es admin
        if payload.get("is_doc") != False:
            raise HTTPException(status_code=403, detail="Solo administradores")

        service = get_prediction_service()
        exito = service.cargar_modelos()

        if exito:
            return {"success": True, "mensaje": "Modelos recargados exitosamente"}
        else:
            raise HTTPException(status_code=500, detail="Error recargando modelos")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recargando modelos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno recargando modelos")


@router.get("/admin/diagnostico")
def diagnostico_sistema(payload: dict = Depends(docente_o_admin_required)):
    """
    Diagnóstico completo del sistema ML
    """
    try:
        # Verificar que es admin
        if payload.get("is_doc") != False:
            raise HTTPException(status_code=403, detail="Solo administradores")

        service = get_prediction_service()

        # Ejecutar diagnósticos
        diagnostico = {
            "modelos_cargados": service.models_loaded,
            "ruta_modelos": service.models_path,
            "archivos_modelo": [],
        }

        # Verificar archivos
        import os

        if os.path.exists(service.models_path):
            archivos = os.listdir(service.models_path)
            diagnostico["archivos_modelo"] = archivos

        # Probar predicción simple
        try:
            datos_prueba = {
                "promedio_notas_anterior": 75.0,
                "porcentaje_asistencia": 85.0,
                "promedio_participacion": 80.0,
            }
            resultado_prueba = service.predecir_rendimiento(datos_prueba)
            diagnostico["test_prediccion"] = "EXITOSO"
            diagnostico["resultado_prueba"] = resultado_prueba["prediccion_numerica"]
        except Exception as e:
            diagnostico["test_prediccion"] = f"ERROR: {str(e)}"

        return {"success": True, "data": diagnostico}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en diagnóstico: {str(e)}")
        raise HTTPException(status_code=500, detail="Error en diagnóstico del sistema")


# ================ ENDPOINTS ESPECÍFICOS PARA TU APLICACIÓN ================


@router.get("/docente/{docente_id}/predicciones-materias")
def predicciones_materias_docente(
    docente_id: int,
    gestion_id: int = Query(..., description="ID de la gestión"),
    periodo_id: int = Query(..., description="ID del periodo"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Obtener predicciones para todas las materias de un docente
    """
    try:
        from sqlalchemy import text

        # Obtener materias del docente
        query_materias = """
        SELECT DISTINCT dm.materia_id, m.nombre as materia_nombre
        FROM docente_materia dm
        JOIN materias m ON dm.materia_id = m.id
        WHERE dm.docente_id = :docente_id
        """

        materias = db.execute(
            text(query_materias), {"docente_id": docente_id}
        ).fetchall()

        if not materias:
            raise HTTPException(
                status_code=404, detail="No se encontraron materias para este docente"
            )

        service = get_prediction_service()
        resultados_por_materia = []

        for materia in materias:
            try:
                # Obtener cursos que tienen esta materia
                query_cursos = """
                SELECT DISTINCT cm.curso_id, c.nombre as curso_nombre
                FROM curso_materia cm
                JOIN cursos c ON cm.curso_id = c.id
                WHERE cm.materia_id = :materia_id
                """

                cursos = db.execute(
                    text(query_cursos), {"materia_id": materia.materia_id}
                ).fetchall()

                predicciones_materia = []

                for curso in cursos:
                    try:
                        predicciones_curso = service.predecir_lote_estudiantes(
                            db, curso.curso_id, materia.materia_id, periodo_id
                        )

                        if predicciones_curso:
                            # Calcular estadísticas del curso
                            promedio_curso = sum(
                                p["prediccion_numerica"] for p in predicciones_curso
                            ) / len(predicciones_curso)
                            estudiantes_riesgo = [
                                p
                                for p in predicciones_curso
                                if p["nivel_riesgo"] in ["alto", "critico"]
                            ]

                            predicciones_materia.append(
                                {
                                    "curso_id": curso.curso_id,
                                    "curso_nombre": curso.curso_nombre,
                                    "total_estudiantes": len(predicciones_curso),
                                    "promedio_curso": round(promedio_curso, 2),
                                    "estudiantes_riesgo": len(estudiantes_riesgo),
                                    "predicciones": predicciones_curso[
                                        :5
                                    ],  # Solo primeros 5 para resumen
                                }
                            )

                    except Exception as e:
                        logger.warning(
                            f"Error prediciendo curso {curso.curso_id}: {str(e)}"
                        )
                        continue

                if predicciones_materia:
                    # Calcular estadísticas generales de la materia
                    total_estudiantes = sum(
                        p["total_estudiantes"] for p in predicciones_materia
                    )
                    promedio_general = (
                        sum(
                            p["promedio_curso"] * p["total_estudiantes"]
                            for p in predicciones_materia
                        )
                        / total_estudiantes
                        if total_estudiantes > 0
                        else 0
                    )
                    total_riesgo = sum(
                        p["estudiantes_riesgo"] for p in predicciones_materia
                    )

                    resultados_por_materia.append(
                        {
                            "materia_id": materia.materia_id,
                            "materia_nombre": materia.materia_nombre,
                            "total_estudiantes": total_estudiantes,
                            "promedio_general": round(promedio_general, 2),
                            "total_estudiantes_riesgo": total_riesgo,
                            "porcentaje_riesgo": (
                                round((total_riesgo / total_estudiantes) * 100, 1)
                                if total_estudiantes > 0
                                else 0
                            ),
                            "cursos": predicciones_materia,
                        }
                    )

            except Exception as e:
                logger.warning(
                    f"Error procesando materia {materia.materia_id}: {str(e)}"
                )
                continue

        return {
            "success": True,
            "data": {
                "docente_id": docente_id,
                "gestion_id": gestion_id,
                "periodo_id": periodo_id,
                "total_materias": len(resultados_por_materia),
                "materias": resultados_por_materia,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error obteniendo predicciones para docente {docente_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Error obteniendo predicciones del docente"
        )


@router.get("/curso/{curso_id}/materia/{materia_id}/analisis-completo")
def analisis_completo_curso_materia(
    curso_id: int,
    materia_id: int,
    periodo_id: int = Query(..., description="ID del periodo"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Análisis completo de un curso en una materia específica con ML
    """
    try:
        service = get_prediction_service()

        # Obtener predicciones para todos los estudiantes
        predicciones = service.predecir_lote_estudiantes(
            db, curso_id, materia_id, periodo_id
        )

        if not predicciones:
            raise HTTPException(
                status_code=404, detail="No se encontraron estudiantes para analizar"
            )

        # Análisis estadístico detallado
        notas_predichas = [p["prediccion_numerica"] for p in predicciones]

        estadisticas = {
            "promedio": round(sum(notas_predichas) / len(notas_predichas), 2),
            "mediana": round(sorted(notas_predichas)[len(notas_predichas) // 2], 2),
            "nota_maxima": round(max(notas_predichas), 2),
            "nota_minima": round(min(notas_predichas), 2),
            "desviacion_estandar": round(
                (
                    sum(
                        (x - sum(notas_predichas) / len(notas_predichas)) ** 2
                        for x in notas_predichas
                    )
                    / len(notas_predichas)
                )
                ** 0.5,
                2,
            ),
        }

        # Distribución por categorías
        distribucion_categorias = {}
        distribucion_riesgo = {}

        for pred in predicciones:
            cat = pred["clasificacion"]
            riesgo = pred["nivel_riesgo"]

            distribucion_categorias[cat] = distribucion_categorias.get(cat, 0) + 1
            distribucion_riesgo[riesgo] = distribucion_riesgo.get(riesgo, 0) + 1

        # Estudiantes que necesitan atención inmediata
        atencion_inmediata = [
            p
            for p in predicciones
            if p["nivel_riesgo"] in ["critico", "alto"] or p["prediccion_numerica"] < 60
        ]

        # Estudiantes con mejor rendimiento
        alto_rendimiento = [
            p
            for p in predicciones
            if p["prediccion_numerica"] >= 80 and p["clasificacion"] == "Alto"
        ]

        # Recomendaciones para el curso completo
        recomendaciones_curso = []

        if len(atencion_inmediata) > len(predicciones) * 0.3:  # Más del 30% en riesgo
            recomendaciones_curso.append(
                "🚨 Alto porcentaje de estudiantes en riesgo - Revisar metodología"
            )
            recomendaciones_curso.append(
                "📚 Implementar programa de refuerzo académico grupal"
            )

        if estadisticas["promedio"] < 65:
            recomendaciones_curso.append(
                "📈 Promedio curso bajo - Evaluar dificultad del contenido"
            )
            recomendaciones_curso.append("🔄 Considerar ajustes en plan de estudios")

        if estadisticas["desviacion_estandar"] > 20:
            recomendaciones_curso.append(
                "📊 Alta dispersión en rendimiento - Atención individualizada"
            )

        if len(alto_rendimiento) > 0:
            recomendaciones_curso.append(
                f"🌟 {len(alto_rendimiento)} estudiantes destacados - Oportunidades avanzadas"
            )

        return {
            "success": True,
            "data": {
                "curso_id": curso_id,
                "materia_id": materia_id,
                "periodo_id": periodo_id,
                "total_estudiantes": len(predicciones),
                "estadisticas": estadisticas,
                "distribucion_categorias": distribucion_categorias,
                "distribucion_riesgo": distribucion_riesgo,
                "estudiantes_atencion_inmediata": {
                    "total": len(atencion_inmediata),
                    "porcentaje": round(
                        (len(atencion_inmediata) / len(predicciones)) * 100, 1
                    ),
                    "estudiantes": atencion_inmediata,
                },
                "estudiantes_alto_rendimiento": {
                    "total": len(alto_rendimiento),
                    "porcentaje": round(
                        (len(alto_rendimiento) / len(predicciones)) * 100, 1
                    ),
                    "estudiantes": alto_rendimiento,
                },
                "recomendaciones_curso": recomendaciones_curso,
                "todas_predicciones": predicciones,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error en análisis completo curso {curso_id} materia {materia_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error en análisis completo")


# ================ ENDPOINTS PARA REPORTES ================


@router.get("/reportes/resumen-institucional")
def reporte_resumen_institucional(
    gestion_id: int = Query(..., description="ID de la gestión"),
    periodo_id: int = Query(..., description="ID del periodo"),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Reporte de resumen institucional con predicciones ML
    """
    try:
        # Verificar que es admin para reportes institucionales
        if payload.get("is_doc") != False:
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden ver reportes institucionales",
            )

        from sqlalchemy import text

        service = get_prediction_service()

        # Obtener muestra representativa de estudiantes
        query_muestra = """
        SELECT DISTINCT 
            e.id as estudiante_id,
            i.curso_id,
            cm.materia_id,
            c.nivel,
            c.paralelo
        FROM estudiantes e
        JOIN inscripciones i ON e.id = i.estudiante_id
        JOIN curso_materia cm ON cm.curso_id = i.curso_id
        JOIN cursos c ON c.id = i.curso_id
        WHERE i.gestion_id = :gestion_id
        ORDER BY RANDOM()
        LIMIT 100
        """

        muestra = db.execute(text(query_muestra), {"gestion_id": gestion_id}).fetchall()

        predicciones_muestra = []

        for row in muestra:
            try:
                pred = service.predecir_estudiante_por_bd(
                    db, row.estudiante_id, row.materia_id, periodo_id
                )
                predicciones_muestra.append(
                    {**pred, "nivel": row.nivel, "paralelo": row.paralelo}
                )
            except Exception:
                continue

        if not predicciones_muestra:
            raise HTTPException(
                status_code=404,
                detail="No se pudieron generar predicciones para el reporte",
            )

        # Calcular métricas institucionales
        total_muestra = len(predicciones_muestra)
        promedio_institucional = (
            sum(p["prediccion_numerica"] for p in predicciones_muestra) / total_muestra
        )

        # Distribución por nivel educativo
        por_nivel = {}
        for pred in predicciones_muestra:
            nivel = pred["nivel"]
            if nivel not in por_nivel:
                por_nivel[nivel] = {"total": 0, "promedio": 0, "riesgo": 0}

            por_nivel[nivel]["total"] += 1
            por_nivel[nivel]["promedio"] += pred["prediccion_numerica"]
            if pred["nivel_riesgo"] in ["alto", "critico"]:
                por_nivel[nivel]["riesgo"] += 1

        # Calcular promedios finales por nivel
        for nivel in por_nivel:
            if por_nivel[nivel]["total"] > 0:
                por_nivel[nivel]["promedio"] = round(
                    por_nivel[nivel]["promedio"] / por_nivel[nivel]["total"], 2
                )
                por_nivel[nivel]["porcentaje_riesgo"] = round(
                    (por_nivel[nivel]["riesgo"] / por_nivel[nivel]["total"]) * 100, 1
                )

        # Alertas institucionales
        alertas = []

        if promedio_institucional < 65:
            alertas.append("⚠️ Promedio institucional por debajo del estándar esperado")

        estudiantes_riesgo_total = len(
            [
                p
                for p in predicciones_muestra
                if p["nivel_riesgo"] in ["alto", "critico"]
            ]
        )
        porcentaje_riesgo = (estudiantes_riesgo_total / total_muestra) * 100

        if porcentaje_riesgo > 25:
            alertas.append(
                f"🚨 {porcentaje_riesgo:.1f}% de estudiantes en riesgo académico"
            )

        return {
            "success": True,
            "data": {
                "gestion_id": gestion_id,
                "periodo_id": periodo_id,
                "fecha_reporte": pd.Timestamp.now().isoformat(),
                "muestra_analizada": total_muestra,
                "promedio_institucional": round(promedio_institucional, 2),
                "distribucion_por_nivel": por_nivel,
                "estudiantes_en_riesgo": {
                    "total": estudiantes_riesgo_total,
                    "porcentaje": round(porcentaje_riesgo, 1),
                },
                "alertas_institucionales": alertas,
                "recomendaciones": [
                    "📊 Monitorear tendencias de rendimiento mensualmente",
                    "🎯 Implementar programas de apoyo focalizados",
                    "📈 Usar predicciones para intervención temprana",
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando reporte institucional: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error generando reporte institucional"
        )


# ================ FUNCIONES DE UTILIDAD ================


def importar_pandas():
    """Importar pandas solo cuando sea necesario"""
    try:
        import pandas as pd

        return pd
    except ImportError:
        logger.warning("Pandas no disponible para algunas funcionalidades avanzadas")
        return None


# Agregar pandas para el reporte
try:
    import pandas as pd
except ImportError:
    # Crear una clase mock para evitar errores si pandas no está disponible
    class MockPandas:
        class Timestamp:
            @staticmethod
            def now():
                return type(
                    "MockTimestamp",
                    (),
                    {"isoformat": lambda: datetime.now().isoformat()},
                )()

    pd = MockPandas()

# ================ DOCUMENTACIÓN ADICIONAL ================

# Metadatos adicionales para la documentación de la API
router_metadata = {
    "name": "Machine Learning - Predicción de Rendimiento",
    "description": """
    Sistema de predicción de rendimiento académico usando Machine Learning.
    
    **Características principales:**
    - Predicción numérica de notas (0-100)
    - Clasificación categórica (Alto/Medio/Bajo)
    - Evaluación de riesgo académico
    - Recomendaciones personalizadas
    - Análisis por curso y materia
    - Reportes institucionales
    
    **Modelos utilizados:**
    - Random Forest para regresión y clasificación
    - Características: promedio anterior, asistencia, participación
    - Validación cruzada y optimización de hiperparámetros
    """,
    "version": "1.0.0",
}
from fastapi import Query


@router.get("/predicciones-guardadas")
def obtener_prediccion_guardada(
    estudiante_id: int = Query(...),
    materia_id: int = Query(...),
    periodo_id: int = Query(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    pred = (
        db.query(PrediccionRendimiento)
        .filter_by(
            estudiante_id=estudiante_id,
            materia_id=materia_id,
            periodo_id=periodo_id,
        )
        .first()
    )

    if not pred:
        raise HTTPException(status_code=404, detail="Predicción no encontrada")

    return {
        "success": True,
        "data": {
            "id": pred.id,
            "estudiante_id": pred.estudiante_id,
            "materia_id": pred.materia_id,
            "periodo_id": pred.periodo_id,
            "promedio_notas": pred.promedio_notas,
            "porcentaje_asistencia": pred.porcentaje_asistencia,
            "promedio_participacion": pred.promedio_participacion,
            "resultado_numerico": pred.resultado_numerico,
            "clasificacion": pred.clasificacion,
            "fecha_generada": pred.fecha_generada.isoformat(),
        },
    }


@router.post("/generar-prediccion")
def generar_prediccion_y_guardar(
    estudiante_id: int = Body(...),
    materia_id: int = Body(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    try:
        # Obtener el último periodo activo
        periodo = (
            db.query(Periodo)
            .filter(Periodo.fecha_inicio <= func.current_date())
            .order_by(Periodo.fecha_inicio.desc())
            .first()
        )

        if not periodo:
            raise HTTPException(status_code=404, detail="No hay periodo activo")

        # Generar y guardar la predicción
        service = get_prediction_service()
        _ = service.predecir_estudiante_por_bd(
            db, estudiante_id, materia_id, periodo.id
        )

        # Consultar predicción guardada
        pred = (
            db.query(PrediccionRendimiento)
            .filter_by(
                estudiante_id=estudiante_id,
                materia_id=materia_id,
                periodo_id=periodo.id,
            )
            .first()
        )

        if not pred:
            raise HTTPException(
                status_code=500,
                detail="La predicción no se guardó correctamente en la base de datos",
            )

        return {
            "success": True,
            "mensaje": "Predicción generada y almacenada exitosamente",
            "data": {
                "id": pred.id,
                "estudiante_id": pred.estudiante_id,
                "materia_id": pred.materia_id,
                "periodo_id": pred.periodo_id,
                "promedio_notas": pred.promedio_notas,
                "porcentaje_asistencia": pred.porcentaje_asistencia,
                "promedio_participacion": pred.promedio_participacion,
                "resultado_numerico": pred.resultado_numerico,
                "clasificacion": pred.clasificacion,
                "fecha_generada": pred.fecha_generada.isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Error generando predicción: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error interno al generar predicción"
        )


@router.post("/generar-predicciones-gestion")
def generar_predicciones_por_gestion(
    estudiante_id: int = Body(...),
    materia_id: int = Body(...),
    gestion_id: int = Body(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    """
    Genera y guarda predicciones de un estudiante para todos los periodos de una gestión
    """
    try:
        # Buscar los periodos de la gestión
        periodos = (
            db.query(Periodo)
            .filter(Periodo.gestion_id == gestion_id)
            .order_by(Periodo.fecha_inicio)
            .all()
        )

        if not periodos:
            raise HTTPException(
                status_code=404, detail="No hay periodos en esta gestión"
            )

        service = get_prediction_service()
        predicciones = []

        for periodo in periodos:
            try:
                service.predecir_estudiante_por_bd(
                    db, estudiante_id, materia_id, periodo.id
                )

                pred = (
                    db.query(PrediccionRendimiento)
                    .filter_by(
                        estudiante_id=estudiante_id,
                        materia_id=materia_id,
                        periodo_id=periodo.id,
                    )
                    .first()
                )

                if pred:
                    predicciones.append(
                        {
                            "id": pred.id,
                            "estudiante_id": pred.estudiante_id,
                            "materia_id": pred.materia_id,
                            "periodo_id": pred.periodo_id,
                            "promedio_notas": pred.promedio_notas,
                            "porcentaje_asistencia": pred.porcentaje_asistencia,
                            "promedio_participacion": pred.promedio_participacion,
                            "resultado_numerico": pred.resultado_numerico,
                            "clasificacion": pred.clasificacion,
                            "fecha_generada": pred.fecha_generada.isoformat(),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error prediciendo para periodo {periodo.id}: {str(e)}")
                continue

        return {
            "success": True,
            "mensaje": f"{len(predicciones)} predicciones generadas y guardadas",
            "data": predicciones,
        }

    except Exception as e:
        logger.error(
            f"Error generando predicciones para gestión {gestion_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail="Error generando predicciones por gestión"
        )


@router.get("/predicciones-estudiante-gestion")
def obtener_predicciones_estudiante_gestion(
    estudiante_id: int = Query(...),
    gestion_id: int = Query(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    """
    Obtiene todas las predicciones de un estudiante en todas sus materias
    para los periodos pertenecientes a una gestión.
    """
    try:
        from sqlalchemy import text

        # 1. Obtener los periodos de la gestión
        periodos = (
            db.query(Periodo)
            .filter(Periodo.gestion_id == gestion_id)
            .order_by(Periodo.fecha_inicio)
            .all()
        )

        if not periodos:
            raise HTTPException(status_code=404, detail="No se encontraron periodos")

        periodos_ids = [p.id for p in periodos]

        # 2. Obtener materias del estudiante por curso y gestion
        query = """
        SELECT DISTINCT cm.materia_id
        FROM inscripciones i
        JOIN curso_materia cm ON i.curso_id = cm.curso_id
        WHERE i.estudiante_id = :estudiante_id
        AND i.gestion_id = :gestion_id
        """

        materias = db.execute(
            text(query), {"estudiante_id": estudiante_id, "gestion_id": gestion_id}
        ).fetchall()

        if not materias:
            raise HTTPException(
                status_code=404, detail="El estudiante no tiene materias asignadas"
            )

        materia_ids = [m.materia_id for m in materias]

        # 3. Buscar predicciones
        predicciones = (
            db.query(PrediccionRendimiento)
            .filter(
                PrediccionRendimiento.estudiante_id == estudiante_id,
                PrediccionRendimiento.materia_id.in_(materia_ids),
                PrediccionRendimiento.periodo_id.in_(periodos_ids),
            )
            .order_by(PrediccionRendimiento.periodo_id)
            .all()
        )

        resultado = []
        for pred in predicciones:
            resultado.append(
                {
                    "id": pred.id,
                    "periodo_id": pred.periodo_id,
                    "materia_id": pred.materia_id,
                    "estudiante_id": pred.estudiante_id,
                    "promedio_notas": pred.promedio_notas,
                    "porcentaje_asistencia": pred.porcentaje_asistencia,
                    "promedio_participacion": pred.promedio_participacion,
                    "resultado_numerico": pred.resultado_numerico,
                    "clasificacion": pred.clasificacion,
                    "fecha_generada": pred.fecha_generada.isoformat(),
                }
            )

        return {
            "success": True,
            "mensaje": f"Se encontraron {len(resultado)} predicciones",
            "data": resultado,
        }

    except Exception as e:
        logger.error(f"Error obteniendo predicciones del estudiante: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo predicciones")


@router.get(
    "/estudiante/{estudiante_id}/gestion/{gestion_id}", response_model=list[dict]
)
def obtener_predicciones_estudiante_gestion(
    estudiante_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    # Verificar que el estudiante existe
    estudiante = db.query(Estudiante).filter_by(id=estudiante_id).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener todos los periodos de esa gestión
    periodos = db.query(Periodo).filter_by(gestion_id=gestion_id).all()
    if not periodos:
        raise HTTPException(status_code=404, detail="No hay periodos en esta gestión")

    periodo_ids = [p.id for p in periodos]

    # Obtener inscripciones en la gestión
    inscripciones = (
        db.query(Inscripcion)
        .filter_by(estudiante_id=estudiante_id, gestion_id=gestion_id)
        .all()
    )
    if not inscripciones:
        raise HTTPException(
            status_code=404,
            detail="El estudiante no tiene inscripciones en esta gestión",
        )

    resultados = []

    for ins in inscripciones:
        curso_id = ins.curso_id
        curso_materias = db.query(CursoMateria).filter_by(curso_id=curso_id).all()
        for cm in curso_materias:
            materia = db.query(Materia).filter_by(id=cm.materia_id).first()
            if not materia:
                continue

            # Buscar predicciones por cada periodo para esta materia
            predicciones = (
                db.query(PrediccionRendimiento)
                .filter(
                    PrediccionRendimiento.estudiante_id == estudiante_id,
                    PrediccionRendimiento.materia_id == materia.id,
                    PrediccionRendimiento.periodo_id.in_(periodo_ids),
                )
                .all()
            )

            for pred in predicciones:
                periodo = db.query(Periodo).filter_by(id=pred.periodo_id).first()

                resultados.append(
                    {
                        "materia_id": materia.id,
                        "materia_nombre": materia.nombre,
                        "periodo_id": periodo.id,
                        "periodo_nombre": periodo.nombre,
                        "promedio_notas": pred.promedio_notas,
                        "porcentaje_asistencia": pred.porcentaje_asistencia,
                        "promedio_participacion": pred.promedio_participacion,
                        "resultado_numerico": pred.resultado_numerico,
                        "clasificacion": pred.clasificacion,
                        "fecha_generada": pred.fecha_generada,
                    }
                )

    return resultados


@router.get("/predicciones-completas")
def obtener_o_generar_predicciones_completas(
    estudiante_id: int = Query(...),
    materia_id: int = Query(...),
    gestion_id: int = Query(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    """
    Retorna predicciones completas para una materia en una gestión.
    Si no existen, las genera automáticamente.
    """
    try:
        # Obtener todos los periodos de la gestión
        periodos = (
            db.query(Periodo)
            .filter(Periodo.gestion_id == gestion_id)
            .order_by(Periodo.fecha_inicio)
            .all()
        )

        if not periodos:
            raise HTTPException(
                status_code=404, detail="No hay periodos en esta gestión"
            )

        periodo_ids = [p.id for p in periodos]

        # Verificar si ya existen predicciones guardadas
        predicciones = (
            db.query(PrediccionRendimiento)
            .filter(
                PrediccionRendimiento.estudiante_id == estudiante_id,
                PrediccionRendimiento.materia_id == materia_id,
                PrediccionRendimiento.periodo_id.in_(periodo_ids),
            )
            .all()
        )

        service = get_prediction_service()

        # Si no hay ninguna, las generamos
        if not predicciones:
            for periodo in periodos:
                try:
                    service.predecir_estudiante_por_bd(
                        db, estudiante_id, materia_id, periodo.id
                    )
                except Exception as e:
                    logger.warning(
                        f"Error generando predicción para periodo {periodo.id}: {str(e)}"
                    )

            # Buscar nuevamente
            predicciones = (
                db.query(PrediccionRendimiento)
                .filter(
                    PrediccionRendimiento.estudiante_id == estudiante_id,
                    PrediccionRendimiento.materia_id == materia_id,
                    PrediccionRendimiento.periodo_id.in_(periodo_ids),
                )
                .all()
            )

        if not predicciones:
            raise HTTPException(
                status_code=500, detail="No se pudieron generar las predicciones"
            )

        resultado = [
            {
                "id": p.id,
                "estudiante_id": p.estudiante_id,
                "materia_id": p.materia_id,
                "periodo_id": p.periodo_id,
                "promedio_notas": p.promedio_notas,
                "porcentaje_asistencia": p.porcentaje_asistencia,
                "promedio_participacion": p.promedio_participacion,
                "resultado_numerico": p.resultado_numerico,
                "clasificacion": p.clasificacion,
                "fecha_generada": p.fecha_generada.isoformat(),
            }
            for p in predicciones
        ]

        return {
            "success": True,
            "mensaje": f"Se encontraron {len(resultado)} predicciones",
            "data": resultado,
        }

    except Exception as e:
        logger.error(f"Error en predicciones-completas: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud")
