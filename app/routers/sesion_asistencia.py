from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.sesion_asistencia import (
    SesionAsistenciaCreate,
    SesionAsistenciaEstudianteOut,
    SesionAsistenciaUpdate,
    SesionAsistenciaOut,
    SesionAsistenciaDetalle,
    SesionAsistenciaResponse,
    MarcarAsistenciaRequest,
    MarcarAsistenciaResponse,
    JustificarAusenciaRequest,
    AsistenciaEstudianteOut,
    ListaSesionesResponse,
    ValidacionUbicacionResponse,
    UbicacionDocente,
    ResumenAsistencia,
    EstudianteAsistencia,
)
from app.crud import sesion_asistencia as crud
from app.auth.roles import (
    docente_required,
    estudiante_required,
    docente_o_admin_required,
)
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/asistencia", tags=["📍 Asistencia por Geolocalización"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def obtener_docente_id(payload: dict) -> int:
    """Helper para obtener el ID del docente desde el payload"""
    user_id = payload.get("user_id")
    user_type = payload.get("user_type")

    if user_type != "docente" and not payload.get("is_doc"):
        raise HTTPException(
            status_code=403, detail="Solo docentes pueden realizar esta acción"
        )

    return user_id


def obtener_estudiante_id(payload: dict) -> int:
    """Helper para obtener el ID del estudiante desde el payload"""
    user_id = payload.get("user_id")
    user_type = payload.get("user_type")

    if user_type != "estudiante":
        raise HTTPException(
            status_code=403, detail="Solo estudiantes pueden realizar esta acción"
        )

    return user_id


# ================ ENDPOINTS PARA DOCENTES ================


@router.post("/sesiones", response_model=SesionAsistenciaResponse)
def crear_sesion_asistencia(
    datos: SesionAsistenciaCreate,
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    📍 **Crear una nueva sesión de asistencia (DOCENTE)**

    El docente establece su ubicación GPS y crea una sesión donde los estudiantes
    podrán marcar asistencia solo si están dentro del radio permitido.

    **Funcionalidad automática:**
    - Si no se proporciona `periodo_id`, se detecta automáticamente basado en `fecha_inicio`
    - El sistema busca el periodo activo que contenga la fecha de la sesión

    **Parámetros importantes:**
    - `latitud_docente`, `longitud_docente`: Ubicación GPS del aula/docente
    - `radio_permitido_metros`: Radio en metros (por defecto 100m)
    - `permite_asistencia_tardia`: Si permite marcar después del inicio
    - `minutos_tolerancia`: Minutos extra para llegar tarde
    - `periodo_id`: OPCIONAL - Si no se proporciona, se detecta automáticamente
    """
    try:
        docente_id = obtener_docente_id(payload)

        sesion = crud.crear_sesion_asistencia(db, datos, docente_id)

        # Obtener información del periodo para mostrar en la respuesta
        periodo_info = ""
        if sesion.periodo_id:
            from app.models.periodo import Periodo

            periodo = db.query(Periodo).filter(Periodo.id == sesion.periodo_id).first()
            if periodo:
                periodo_info = f" (Periodo: {periodo.nombre})"

        return SesionAsistenciaResponse(
            success=True,
            message=(
                f"Sesión '{sesion.titulo}' creada exitosamente{periodo_info}. "
                f"{sesion.total_estudiantes_esperados} estudiantes pueden marcar asistencia."
            ),
            data=SesionAsistenciaOut.from_orm(sesion),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/sesiones/mis-sesiones", response_model=ListaSesionesResponse)
def listar_mis_sesiones(
    estado: Optional[str] = Query(
        None, description="Filtrar por estado: activa, cerrada, cancelada"
    ),
    curso_id: Optional[int] = Query(None, description="Filtrar por curso"),
    materia_id: Optional[int] = Query(None, description="Filtrar por materia"),
    limite: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    📋 **Listar mis sesiones de asistencia (DOCENTE)**

    Obtiene todas las sesiones de asistencia creadas por el docente autenticado.
    """
    try:
        docente_id = obtener_docente_id(payload)

        sesiones = crud.obtener_sesiones_docente(
            db, docente_id, estado, curso_id, materia_id, limite
        )

        sesiones_out = [SesionAsistenciaOut.from_orm(s) for s in sesiones]

        # Contar por estado
        activas = len([s for s in sesiones if s.estado == "activa"])
        cerradas = len([s for s in sesiones if s.estado == "cerrada"])

        return ListaSesionesResponse(
            success=True,
            sesiones=sesiones_out,
            total=len(sesiones_out),
            activas=activas,
            cerradas=cerradas,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/sesiones/{sesion_id}", response_model=SesionAsistenciaDetalle)
def obtener_detalle_sesion(
    sesion_id: int,
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    🔍 **Obtener detalle completo de una sesión (DOCENTE)**

    Incluye la lista completa de estudiantes y su estado de asistencia.
    """
    try:
        docente_id = obtener_docente_id(payload)

        sesion = crud.obtener_sesion_por_id(db, sesion_id, incluir_asistencias=True)

        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        if sesion.docente_id != docente_id:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a esta sesión"
            )

        return SesionAsistenciaDetalle.from_orm(sesion)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/sesiones/{sesion_id}", response_model=SesionAsistenciaResponse)
def actualizar_sesion(
    sesion_id: int,
    datos: SesionAsistenciaUpdate,
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    ✏️ **Actualizar configuración de sesión (DOCENTE)**

    Permite modificar parámetros como radio permitido, tolerancia, etc.
    """
    try:
        docente_id = obtener_docente_id(payload)

        # Verificar propiedad
        sesion_existente = crud.obtener_sesion_por_id(db, sesion_id)
        if not sesion_existente:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        if sesion_existente.docente_id != docente_id:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a esta sesión"
            )

        sesion_actualizada = crud.actualizar_sesion_asistencia(db, sesion_id, datos)

        return SesionAsistenciaResponse(
            success=True,
            message="Sesión actualizada exitosamente",
            data=SesionAsistenciaOut.from_orm(sesion_actualizada),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/sesiones/{sesion_id}/cerrar", response_model=SesionAsistenciaResponse)
def cerrar_sesion(
    sesion_id: int,
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    🔒 **Cerrar sesión de asistencia (DOCENTE)**

    Cierra la sesión y sincroniza los datos con el sistema de evaluaciones.
    Los estudiantes ya no podrán marcar asistencia.
    """
    try:
        docente_id = obtener_docente_id(payload)

        # Verificar propiedad
        sesion_existente = crud.obtener_sesion_por_id(db, sesion_id)
        if not sesion_existente:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        if sesion_existente.docente_id != docente_id:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a esta sesión"
            )

        sesion_cerrada = crud.cerrar_sesion_asistencia(db, sesion_id)

        # Obtener estadísticas finales
        stats = crud.obtener_estadisticas_sesion(db, sesion_id)

        mensaje = (
            f"Sesión cerrada exitosamente. "
            f"Asistieron {stats['presentes']}/{stats['total_estudiantes']} estudiantes "
            f"({stats['porcentaje_asistencia']:.1f}%)"
        )

        return SesionAsistenciaResponse(
            success=True,
            message=mensaje,
            data=SesionAsistenciaOut.from_orm(sesion_cerrada),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/sesiones/{sesion_id}/estadisticas", response_model=dict)
def obtener_estadisticas_sesion(
    sesion_id: int,
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    📊 **Obtener estadísticas de una sesión (DOCENTE)**

    Estadísticas detalladas de asistencia, tardanzas, ausencias, etc.
    """
    try:
        docente_id = obtener_docente_id(payload)

        # Verificar propiedad
        sesion = crud.obtener_sesion_por_id(db, sesion_id)
        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        if sesion.docente_id != docente_id:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a esta sesión"
            )

        stats = crud.obtener_estadisticas_sesion(db, sesion_id)

        return {
            "success": True,
            "sesion_id": sesion_id,
            "titulo": sesion.titulo,
            "estado": sesion.estado,
            "fecha_inicio": sesion.fecha_inicio,
            "estadisticas": stats,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/sesiones/{sesion_id}/estudiantes/{estudiante_id}/justificar")
def justificar_ausencia_estudiante(
    sesion_id: int,
    estudiante_id: int,
    datos: JustificarAusenciaRequest,
    payload: dict = Depends(docente_required),
    db: Session = Depends(get_db),
):
    """
    📝 **Justificar ausencia de estudiante (DOCENTE)**

    Permite al docente justificar la ausencia de un estudiante.
    """
    try:
        docente_id = obtener_docente_id(payload)

        # Verificar propiedad de la sesión
        sesion = crud.obtener_sesion_por_id(db, sesion_id)
        if not sesion or sesion.docente_id != docente_id:
            raise HTTPException(
                status_code=404, detail="Sesión no encontrada o sin acceso"
            )

        asistencia = crud.justificar_ausencia(db, sesion_id, estudiante_id, datos)

        return {
            "success": True,
            "message": "Ausencia justificada exitosamente",
            "data": AsistenciaEstudianteOut.from_orm(asistencia),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ================ ENDPOINTS PARA ESTUDIANTES ================


@router.get(
    "/estudiante/sesiones-activas", response_model=List[SesionAsistenciaEstudianteOut]
)
def obtener_mis_sesiones_activas(
    payload: dict = Depends(estudiante_required), db: Session = Depends(get_db)
):
    """
    🎓 **Obtener sesiones activas donde puedo marcar asistencia (ESTUDIANTE)**

    Lista las sesiones de asistencia activas en los cursos donde está inscrito el estudiante.
    Incluye información de la materia, docente y estado de asistencia del estudiante.
    """
    try:
        estudiante_id = obtener_estudiante_id(payload)

        # Usar la función existente de CRUD
        sesiones = crud.obtener_sesiones_activas_estudiante(db, estudiante_id)

        # Construir manualmente los objetos del esquema con información adicional
        sesiones_enriquecidas = []

        for sesion in sesiones:
            # Obtener información de la materia
            from app.models.materia import Materia

            materia = db.query(Materia).filter(Materia.id == sesion.materia_id).first()

            # Obtener información del docente
            from app.models.docente_materia import DocenteMateria
            from app.models.docente import Docente

            docente_materia = (
                db.query(DocenteMateria)
                .join(Docente, Docente.id == DocenteMateria.docente_id)
                .filter(DocenteMateria.materia_id == sesion.materia_id)
                .first()
            )

            # Obtener la asistencia del estudiante para esta sesión
            from app.models.sesion_asistencia import AsistenciaEstudiante

            mi_asistencia = (
                db.query(AsistenciaEstudiante)
                .filter(
                    crud.and_(
                        AsistenciaEstudiante.sesion_id == sesion.id,
                        AsistenciaEstudiante.estudiante_id == estudiante_id,
                    )
                )
                .first()
            )

            # Construir los objetos manualmente
            materia_info = None
            if materia:
                from app.schemas.estudiante_info_academica import MateriaBasica

                materia_info = MateriaBasica(
                    id=materia.id,
                    nombre=materia.nombre,
                    descripcion=materia.descripcion,
                    sigla=getattr(materia, "sigla", None),
                )

            docente_info = None
            if docente_materia and docente_materia.docente:
                from app.schemas.estudiante_info_academica import DocenteBasico

                docente_info = DocenteBasico(
                    id=docente_materia.docente.id,
                    nombre=docente_materia.docente.nombre,
                    apellido=docente_materia.docente.apellido,
                    correo=docente_materia.docente.correo,
                    telefono=docente_materia.docente.telefono,
                )

            asistencia_info = None
            if mi_asistencia:
                asistencia_info = AsistenciaEstudianteOut.from_orm(mi_asistencia)

            # Crear el objeto del esquema manualmente
            sesion_enriquecida = SesionAsistenciaEstudianteOut(
                id=sesion.id,
                titulo=sesion.titulo,
                descripcion=sesion.descripcion,
                fecha_inicio=sesion.fecha_inicio,
                fecha_fin=sesion.fecha_fin,
                duracion_minutos=sesion.duracion_minutos,
                radio_permitido_metros=sesion.radio_permitido_metros,
                permite_asistencia_tardia=sesion.permite_asistencia_tardia,
                minutos_tolerancia=sesion.minutos_tolerancia,
                estado=sesion.estado,
                esta_activa=sesion.esta_activa,
                fecha_creacion=sesion.fecha_creacion,
                materia=materia_info,
                docente=docente_info,
                mi_asistencia=asistencia_info,
            )

            sesiones_enriquecidas.append(sesion_enriquecida)

        return sesiones_enriquecidas

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/estudiante/sesiones/{sesion_id}/ubicacion", response_model=UbicacionDocente
)
def obtener_ubicacion_aula(
    sesion_id: int,
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    📍 **Obtener ubicación del aula/docente (ESTUDIANTE)**

    Obtiene la ubicación de referencia donde debe estar el estudiante para marcar asistencia.
    """
    try:
        estudiante_id = obtener_estudiante_id(payload)

        sesion = crud.obtener_sesion_por_id(db, sesion_id)

        if not sesion:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        if not sesion.esta_activa:
            raise HTTPException(status_code=400, detail="La sesión no está activa")

        # Verificar que el estudiante pertenece a esta sesión
        asistencia = (
            db.query(crud.AsistenciaEstudiante)
            .filter(
                crud.and_(
                    crud.AsistenciaEstudiante.sesion_id == sesion_id,
                    crud.AsistenciaEstudiante.estudiante_id == estudiante_id,
                )
            )
            .first()
        )

        if not asistencia:
            raise HTTPException(
                status_code=403, detail="No tienes acceso a esta sesión"
            )

        return UbicacionDocente(
            latitud=sesion.latitud_docente,
            longitud=sesion.longitud_docente,
            direccion_referencia=sesion.direccion_referencia or "Ubicación del aula",
            radio_permitido=sesion.radio_permitido_metros,
            mensaje=f"Debes estar dentro de {sesion.radio_permitido_metros}m del aula",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post(
    "/estudiante/sesiones/{sesion_id}/validar-ubicacion",
    response_model=ValidacionUbicacionResponse,
)
def validar_mi_ubicacion(
    sesion_id: int,
    latitud: float = Query(..., ge=-90, le=90),
    longitud: float = Query(..., ge=-180, le=180),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    ✅ **Validar si puedo marcar asistencia desde mi ubicación (ESTUDIANTE)**

    Verifica si el estudiante está dentro del rango permitido SIN marcar asistencia.
    Útil para mostrar feedback en tiempo real en la app.
    """
    try:
        estudiante_id = obtener_estudiante_id(payload)

        resultado = crud.validar_puede_marcar_asistencia(
            db, sesion_id, estudiante_id, latitud, longitud
        )

        return ValidacionUbicacionResponse(**resultado)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post(
    "/estudiante/sesiones/{sesion_id}/marcar", response_model=MarcarAsistenciaResponse
)
def marcar_mi_asistencia(
    sesion_id: int,
    datos: MarcarAsistenciaRequest,
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    ✋ **Marcar mi asistencia (ESTUDIANTE)**

    Registra la asistencia del estudiante verificando que esté dentro del rango GPS permitido.
    """
    try:
        estudiante_id = obtener_estudiante_id(payload)

        asistencia, resultado = crud.marcar_asistencia_estudiante(
            db, sesion_id, estudiante_id, datos
        )

        return MarcarAsistenciaResponse(
            success=resultado["success"],
            message=resultado["message"],
            asistencia_registrada=True,
            es_tardanza=resultado["es_tardanza"],
            distancia_metros=resultado["distancia_metros"],
            dentro_del_rango=resultado["dentro_del_rango"],
            data=AsistenciaEstudianteOut.from_orm(asistencia),
        )

    except ValueError as e:
        # Errores controlados (fuera de rango, ya marcó, etc.)
        return MarcarAsistenciaResponse(
            success=False,
            message=str(e),
            asistencia_registrada=False,
            es_tardanza=False,
            distancia_metros=0.0,
            dentro_del_rango=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/estudiante/mis-asistencias", response_model=List[AsistenciaEstudianteOut])
def obtener_mis_asistencias(
    curso_id: Optional[int] = Query(None, description="Filtrar por curso"),
    materia_id: Optional[int] = Query(None, description="Filtrar por materia"),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    📋 **Ver mi historial de asistencias (ESTUDIANTE)**

    Muestra todas las asistencias registradas del estudiante autenticado.
    """
    try:
        estudiante_id = obtener_estudiante_id(payload)

        asistencias = crud.obtener_asistencias_estudiante(
            db, estudiante_id, curso_id, materia_id
        )

        return [AsistenciaEstudianteOut.from_orm(a) for a in asistencias]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ================ ENDPOINTS ADMINISTRATIVOS ================


@router.get("/admin/sesiones", response_model=List[SesionAsistenciaOut])
def listar_todas_las_sesiones(
    estado: Optional[str] = Query(None),
    docente_id: Optional[int] = Query(None),
    curso_id: Optional[int] = Query(None),
    materia_id: Optional[int] = Query(None),
    limite: int = Query(100, ge=1, le=500),
    payload: dict = Depends(docente_o_admin_required),
    db: Session = Depends(get_db),
):
    """
    👑 **Listar todas las sesiones (ADMIN)**

    Vista administrativa de todas las sesiones de asistencia del sistema.
    """
    try:
        # Verificar que es admin
        if payload.get("user_type") != "admin" and payload.get("is_doc") != False:
            raise HTTPException(status_code=403, detail="Solo administradores")

        # Implementar lógica para obtener todas las sesiones con filtros
        # (Esta función debería agregarse al CRUD)

        query = db.query(crud.SesionAsistencia)

        if estado:
            query = query.filter(crud.SesionAsistencia.estado == estado)
        if docente_id:
            query = query.filter(crud.SesionAsistencia.docente_id == docente_id)
        if curso_id:
            query = query.filter(crud.SesionAsistencia.curso_id == curso_id)
        if materia_id:
            query = query.filter(crud.SesionAsistencia.materia_id == materia_id)

        sesiones = (
            query.order_by(crud.desc(crud.SesionAsistencia.fecha_inicio))
            .limit(limite)
            .all()
        )

        return [SesionAsistenciaOut.from_orm(s) for s in sesiones]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/admin/estadisticas-generales", response_model=dict)
def obtener_estadisticas_generales(
    payload: dict = Depends(docente_o_admin_required), db: Session = Depends(get_db)
):
    """
    📊 **Estadísticas generales del sistema (ADMIN)**

    Métricas globales de uso del sistema de asistencia.
    """
    try:
        # Verificar que es admin
        if payload.get("user_type") != "admin" and payload.get("is_doc") != False:
            raise HTTPException(status_code=403, detail="Solo administradores")

        # Contar sesiones por estado
        total_sesiones = db.query(crud.SesionAsistencia).count()
        sesiones_activas = (
            db.query(crud.SesionAsistencia)
            .filter(crud.SesionAsistencia.estado == "activa")
            .count()
        )
        sesiones_cerradas = (
            db.query(crud.SesionAsistencia)
            .filter(crud.SesionAsistencia.estado == "cerrada")
            .count()
        )

        # Contar asistencias totales
        total_asistencias = db.query(crud.AsistenciaEstudiante).count()
        asistencias_marcadas = (
            db.query(crud.AsistenciaEstudiante)
            .filter(crud.AsistenciaEstudiante.presente == True)
            .count()
        )

        porcentaje_asistencia_global = (
            (asistencias_marcadas / total_asistencias * 100)
            if total_asistencias > 0
            else 0
        )

        return {
            "success": True,
            "estadisticas": {
                "total_sesiones": total_sesiones,
                "sesiones_activas": sesiones_activas,
                "sesiones_cerradas": sesiones_cerradas,
                "total_registros_asistencia": total_asistencias,
                "asistencias_marcadas": asistencias_marcadas,
                "porcentaje_asistencia_global": round(porcentaje_asistencia_global, 2),
            },
            "fecha_consulta": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
