# app/routers/estudiante_info_academica.py
from datetime import date
from venv import logger
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.estudiante_info_academica import (
    InfoAcademicaResponse,
    InfoAcademicaCompleta,
    CursoEstudianteResponse,
    MateriasEstudianteResponse,
    DocentesEstudianteResponse,
    InfoAcademicaResumen,
    CursoBasico,
    MateriaConDocente,
    DocenteConMaterias,
)
from app.crud import estudiante_info_academica as crud
from app.auth.roles import usuario_autenticado, estudiante_required
from typing import Optional
from sqlalchemy import func

router = APIRouter(
    prefix="/estudiante/mi-info-academica", tags=["Información Académica Estudiante"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def obtener_estudiante_actual(payload: dict, db: Session):
    """Helper para obtener el estudiante autenticado"""
    user_id = payload.get("user_id")
    user_type = payload.get("user_type")

    if not user_id or user_type != "estudiante":
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")

    estudiante = crud.obtener_estudiante_por_id(db, user_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.get("/completa", response_model=InfoAcademicaResponse)
def obtener_info_academica_completa(
    gestion_id: Optional[int] = Query(
        None,
        description="ID de la gestión (opcional, usa la gestión activa por defecto)",
    ),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    📚 Obtener toda la información académica del estudiante autenticado:
    - Su curso actual
    - Las materias del curso
    - Los docentes de cada materia
    """
    estudiante = obtener_estudiante_actual(payload, db)

    info_academica = crud.obtener_info_academica_estudiante(
        db, estudiante.id, gestion_id
    )

    # Verificar si hay error en la respuesta
    if "error" in info_academica:
        return InfoAcademicaResponse(success=False, mensaje=info_academica["error"])

    # Convertir a modelo Pydantic
    data = InfoAcademicaCompleta(**info_academica)

    return InfoAcademicaResponse(
        success=True,
        data=data,
        mensaje=f"Información académica obtenida exitosamente para la gestión {info_academica['gestion']['anio']}",
    )


@router.get("/curso", response_model=CursoEstudianteResponse)
def obtener_mi_curso(
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    🏫 Obtener el curso actual del estudiante autenticado
    """
    estudiante = obtener_estudiante_actual(payload, db)

    curso = crud.obtener_curso_estudiante(db, estudiante.id, gestion_id)

    if not curso:
        return CursoEstudianteResponse(
            success=False, mensaje="No tienes curso asignado en esta gestión"
        )

    return CursoEstudianteResponse(
        success=True, curso=CursoBasico(**curso), mensaje="Curso obtenido exitosamente"
    )


@router.get("/materias", response_model=MateriasEstudianteResponse)
def obtener_mis_materias(
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    📖 Obtener las materias del estudiante autenticado con sus docentes
    """
    estudiante = obtener_estudiante_actual(payload, db)

    materias = crud.obtener_materias_estudiante(db, estudiante.id, gestion_id)

    if not materias:
        return MateriasEstudianteResponse(
            success=False,
            mensaje="No tienes materias asignadas en esta gestión",
            total=0,
        )

    # Convertir a modelos Pydantic
    materias_response = [MateriaConDocente(**materia) for materia in materias]

    return MateriasEstudianteResponse(
        success=True,
        materias=materias_response,
        total=len(materias_response),
        mensaje=f"Se encontraron {len(materias_response)} materias",
    )


@router.get("/docentes", response_model=DocentesEstudianteResponse)
def obtener_mis_docentes(
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    👨‍🏫 Obtener todos los docentes que enseñan al estudiante autenticado
    """
    estudiante = obtener_estudiante_actual(payload, db)

    docentes = crud.obtener_docentes_estudiante(db, estudiante.id, gestion_id)

    if not docentes:
        return DocentesEstudianteResponse(
            success=False,
            mensaje="No tienes docentes asignados en esta gestión",
            total=0,
        )

    # Convertir a modelos Pydantic
    docentes_response = [DocenteConMaterias(**docente) for docente in docentes]

    return DocentesEstudianteResponse(
        success=True,
        docentes=docentes_response,
        total=len(docentes_response),
        mensaje=f"Se encontraron {len(docentes_response)} docentes",
    )


@router.get("/resumen", response_model=dict)
def obtener_resumen_academico(
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    📊 Obtener un resumen de la información académica del estudiante
    """
    estudiante = obtener_estudiante_actual(payload, db)

    info_academica = crud.obtener_info_academica_estudiante(
        db, estudiante.id, gestion_id
    )

    if "error" in info_academica:
        return {"success": False, "mensaje": info_academica["error"]}

    # Crear resumen
    materias_con_docente = sum(
        1 for m in info_academica["materias"] if m["docente"] is not None
    )
    materias_sin_docente = len(info_academica["materias"]) - materias_con_docente

    resumen = {
        "success": True,
        "estudiante": info_academica["estudiante"],
        "curso": info_academica["curso"],
        "gestion": info_academica["gestion"],
        "estadisticas": {
            "total_materias": len(info_academica["materias"]),
            "materias_con_docente": materias_con_docente,
            "materias_sin_docente": materias_sin_docente,
            "total_docentes": len(
                set(
                    m["docente"]["id"]
                    for m in info_academica["materias"]
                    if m["docente"] is not None
                )
            ),
        },
        "mensaje": f"Resumen académico para la gestión {info_academica['gestion']['anio']}",
    }

    return resumen


# ================ ENDPOINTS ADICIONALES PARA FUNCIONALIDADES ESPECÍFICAS ================


@router.get("/materia/{materia_id}/docente", response_model=dict)
def obtener_docente_de_materia(
    materia_id: int,
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(estudiante_required),
    db: Session = Depends(get_db),
):
    """
    👨‍🏫 Obtener el docente de una materia específica del estudiante
    """
    estudiante = obtener_estudiante_actual(payload, db)

    materias = crud.obtener_materias_estudiante(db, estudiante.id, gestion_id)

    # Buscar la materia específica
    materia_encontrada = None
    for materia in materias:
        if materia["materia"]["id"] == materia_id:
            materia_encontrada = materia
            break

    if not materia_encontrada:
        return {
            "success": False,
            "mensaje": "No estás inscrito en esta materia o la materia no existe",
        }

    if not materia_encontrada["docente"]:
        return {"success": False, "mensaje": "Esta materia no tiene docente asignado"}

    return {
        "success": True,
        "materia": materia_encontrada["materia"],
        "docente": materia_encontrada["docente"],
        "mensaje": "Docente encontrado exitosamente",
    }


@router.get("/verificar-inscripcion", response_model=dict)
def verificar_inscripcion_activa(
    payload: dict = Depends(estudiante_required), db: Session = Depends(get_db)
):
    """
    ✅ Verificar si el estudiante tiene una inscripción activa
    """
    estudiante = obtener_estudiante_actual(payload, db)

    curso = crud.obtener_curso_estudiante(db, estudiante.id)

    if curso:
        return {
            "success": True,
            "inscrito": True,
            "curso": curso,
            "mensaje": "Tienes inscripción activa",
        }
    else:
        return {
            "success": True,
            "inscrito": False,
            "mensaje": "No tienes inscripción activa en la gestión actual",
        }


@router.get("/estudiante-completo")
def obtener_rendimientos_y_predicciones_completos(
    estudiante_id: int = Query(..., description="ID del estudiante"),
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    """
    🎯 Obtener rendimientos académicos y predicciones ML completos de un estudiante

    **Acceso por roles:**
    - 🎓 **Estudiante**: Solo puede ver sus propios datos
    - 👨‍👩‍👧‍👦 **Padre**: Puede ver datos de sus hijos registrados
    - 👨‍🏫 **Docente**: Puede ver datos de estudiantes en sus materias
    - 🔧 **Admin**: Puede ver datos de cualquier estudiante

    **Ejemplos de uso:**
    ```
    # Estudiante consultando sus datos
    GET /info-academica/estudiante-completo?estudiante_id=123
    Authorization: Bearer [token_estudiante_123]

    # Padre consultando datos de su hijo
    GET /info-academica/estudiante-completo?estudiante_id=456
    Authorization: Bearer [token_padre_789]

    # Docente consultando estudiante en sus materias
    GET /info-academica/estudiante-completo?estudiante_id=456
    Authorization: Bearer [token_docente_101]

    # Admin consultando cualquier estudiante
    GET /info-academica/estudiante-completo?estudiante_id=456
    Authorization: Bearer [token_admin_202]
    ```

    **Funcionalidades:**
    - Detecta automáticamente la gestión activa actual
    - Calcula rendimientos finales por materia y periodo
    - Genera predicciones ML automáticamente si no existen
    - Incluye información completa de materias y docentes
    - Un solo endpoint para toda la información académica

    **Respuesta incluye:**
    - Rendimientos calculados por tipo de evaluación
    - Predicciones de Machine Learning
    - Información del docente asignado
    - Datos de la materia y periodos
    - Estadísticas y recomendaciones
    """
    from app.models import (
        Inscripcion,
        CursoMateria,
        TipoEvaluacion,
        Evaluacion,
        PesoTipoEvaluacion,
        RendimientoFinal,
        DocenteMateria,
        Periodo,
        Gestion,
        Materia,
        Docente,
        PrediccionRendimiento,
        PadreEstudiante,
        Estudiante,
    )
    from app.ml.prediction_service import get_prediction_service

    try:
        # 🔐 CONTROL DE ACCESO POR ROLES
        user_type = payload.get("user_type")
        user_id = payload.get("user_id")

        # Verificar que el estudiante existe
        estudiante = db.query(Estudiante).filter_by(id=estudiante_id).first()
        if not estudiante:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # VALIDACIÓN POR TIPO DE USUARIO
        if user_type == "estudiante":
            # Estudiantes solo pueden ver sus propios datos
            if user_id != estudiante_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo puedes ver tu propia información académica",
                )

        elif user_type == "padre":
            # Padres solo pueden ver datos de sus hijos
            relacion_padre = (
                db.query(PadreEstudiante)
                .filter_by(padre_id=user_id, estudiante_id=estudiante_id)
                .first()
            )
            if not relacion_padre:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes autorización para ver este estudiante",
                )

        elif user_type == "docente":
            # Docentes pueden ver estudiantes en sus materias
            docente_materias = (
                db.query(DocenteMateria.materia_id).filter_by(docente_id=user_id).all()
            )
            materia_ids_docente = [dm.materia_id for dm in docente_materias]

            if not materia_ids_docente:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes materias asignadas para ver estudiantes",
                )

            # Verificar si el estudiante está en alguna materia del docente
            # (Esta verificación se refinará más adelante con la gestión activa)

        elif user_type == "admin":
            # Administradores pueden ver cualquier estudiante
            pass

        else:
            raise HTTPException(status_code=403, detail="Tipo de usuario no autorizado")

        # 1. DETECTAR GESTIÓN ACTIVA AUTOMÁTICAMENTE
        hoy = date.today()
        gestion_activa = (
            db.query(Gestion)
            .join(Periodo, Periodo.gestion_id == Gestion.id)
            .filter(Periodo.fecha_inicio <= hoy, Periodo.fecha_fin >= hoy)
            .first()
        )

        if not gestion_activa:
            # Si no hay gestión con periodo activo, usar la más reciente
            gestion_activa = db.query(Gestion).order_by(Gestion.id.desc()).first()

        if not gestion_activa:
            raise HTTPException(
                status_code=404, detail="No se encontró ninguna gestión disponible"
            )

        gestion_id = gestion_activa.id

        # 2. VERIFICAR INSCRIPCIÓN DEL ESTUDIANTE
        inscripciones = (
            db.query(Inscripcion)
            .filter_by(estudiante_id=estudiante_id, gestion_id=gestion_id)
            .all()
        )

        if not inscripciones:
            raise HTTPException(
                status_code=404,
                detail=f"El estudiante no está inscrito en la gestión {gestion_activa.anio}",
            )

        # 3. OBTENER PERIODOS DE LA GESTIÓN
        periodos = (
            db.query(Periodo)
            .filter_by(gestion_id=gestion_id)
            .order_by(Periodo.fecha_inicio)
            .all()
        )

        if not periodos:
            raise HTTPException(
                status_code=404, detail="No hay periodos definidos para esta gestión"
            )

        # 5. VALIDACIÓN ADICIONAL PARA DOCENTES
        if user_type == "docente":
            # Verificar que el estudiante esté inscrito en materias del docente
            docente_materias = (
                db.query(DocenteMateria.materia_id).filter_by(docente_id=user_id).all()
            )
            materia_ids_docente = [dm.materia_id for dm in docente_materias]

            # Obtener materias del estudiante en esta gestión
            materias_estudiante = []
            for inscripcion in inscripciones:
                curso_materias = (
                    db.query(CursoMateria)
                    .filter_by(curso_id=inscripcion.curso_id)
                    .all()
                )
                materias_estudiante.extend([cm.materia_id for cm in curso_materias])

            # Verificar si hay intersección entre materias del docente y del estudiante
            materias_comunes = set(materia_ids_docente) & set(materias_estudiante)

            if not materias_comunes:
                raise HTTPException(
                    status_code=403,
                    detail="No tienes materias en común con este estudiante",
                )

            # Filtrar solo las materias que enseña este docente
            materia_ids_permitidas = list(materias_comunes)
        else:
            # Para otros usuarios, permitir todas las materias
            materia_ids_permitidas = None

        # 6. OBTENER TIPOS DE EVALUACIÓN
        tipos = db.query(TipoEvaluacion).all()

        # 7. PROCESAR CADA INSCRIPCIÓN
        resultados = []
        service = get_prediction_service()

        for inscripcion in inscripciones:
            curso_id = inscripcion.curso_id

            # Obtener materias del curso
            curso_materias = db.query(CursoMateria).filter_by(curso_id=curso_id).all()

            for curso_materia in curso_materias:
                materia_id = curso_materia.materia_id

                # Filtrar materias para docentes
                if (
                    materia_ids_permitidas is not None
                    and materia_id not in materia_ids_permitidas
                ):
                    continue

                # Información de la materia
                materia = db.query(Materia).filter_by(id=materia_id).first()
                if not materia:
                    continue

                # Información del docente
                docente_materia = (
                    db.query(DocenteMateria).filter_by(materia_id=materia_id).first()
                )

                docente_info = None
                if docente_materia:
                    docente = (
                        db.query(Docente)
                        .filter_by(id=docente_materia.docente_id)
                        .first()
                    )
                    if docente:
                        docente_info = {
                            "id": docente.id,
                            "nombre": docente.nombre,
                            "apellido": docente.apellido,
                            "correo": docente.correo,
                            "telefono": docente.telefono,
                        }

                # 6. PROCESAR CADA PERIODO
                periodos_data = []

                for periodo in periodos:
                    periodo_id = periodo.id

                    # CALCULAR RENDIMIENTO FINAL
                    nota_final = 0.0
                    detalle_evaluaciones = []

                    if docente_materia:
                        docente_id = docente_materia.docente_id

                        for tipo in tipos:
                            # Peso definido por el docente
                            peso = (
                                db.query(PesoTipoEvaluacion)
                                .filter_by(
                                    docente_id=docente_id,
                                    materia_id=materia_id,
                                    gestion_id=gestion_id,
                                    tipo_evaluacion_id=tipo.id,
                                )
                                .first()
                            )

                            if not peso:
                                continue

                            # Evaluaciones del estudiante
                            evaluaciones = (
                                db.query(Evaluacion)
                                .filter_by(
                                    estudiante_id=estudiante_id,
                                    materia_id=materia_id,
                                    periodo_id=periodo_id,
                                    tipo_evaluacion_id=tipo.id,
                                )
                                .all()
                            )

                            if evaluaciones:
                                promedio = sum(e.valor for e in evaluaciones) / len(
                                    evaluaciones
                                )
                                aporte = (promedio * peso.porcentaje) / 100
                                nota_final += aporte

                                detalle_evaluaciones.append(
                                    {
                                        "tipo_evaluacion_id": tipo.id,
                                        "tipo_nombre": tipo.nombre,
                                        "promedio": round(promedio, 2),
                                        "peso": peso.porcentaje,
                                        "aporte": round(aporte, 2),
                                        "cantidad_evaluaciones": len(evaluaciones),
                                    }
                                )

                    nota_final = round(nota_final, 2)

                    # GUARDAR/ACTUALIZAR RENDIMIENTO FINAL
                    existente_rendimiento = (
                        db.query(RendimientoFinal)
                        .filter_by(
                            estudiante_id=estudiante_id,
                            materia_id=materia_id,
                            periodo_id=periodo_id,
                        )
                        .first()
                    )

                    if existente_rendimiento:
                        existente_rendimiento.nota_final = nota_final
                        existente_rendimiento.fecha_calculo = func.now()
                    else:
                        existente_rendimiento = RendimientoFinal(
                            estudiante_id=estudiante_id,
                            materia_id=materia_id,
                            periodo_id=periodo_id,
                            nota_final=nota_final,
                        )
                        db.add(existente_rendimiento)

                    db.commit()

                    # GENERAR/OBTENER PREDICCIONES ML
                    prediccion_data = None
                    try:
                        # Verificar si ya existe predicción
                        prediccion_existente = (
                            db.query(PrediccionRendimiento)
                            .filter_by(
                                estudiante_id=estudiante_id,
                                materia_id=materia_id,
                                periodo_id=periodo_id,
                            )
                            .first()
                        )

                        if not prediccion_existente:
                            # Generar nueva predicción
                            service.predecir_estudiante_por_bd(
                                db, estudiante_id, materia_id, periodo_id
                            )

                            # Buscar la predicción recién creada
                            prediccion_existente = (
                                db.query(PrediccionRendimiento)
                                .filter_by(
                                    estudiante_id=estudiante_id,
                                    materia_id=materia_id,
                                    periodo_id=periodo_id,
                                )
                                .first()
                            )

                        if prediccion_existente:
                            prediccion_data = {
                                "id": prediccion_existente.id,
                                "promedio_notas": prediccion_existente.promedio_notas,
                                "porcentaje_asistencia": prediccion_existente.porcentaje_asistencia,
                                "promedio_participacion": prediccion_existente.promedio_participacion,
                                "resultado_numerico": prediccion_existente.resultado_numerico,
                                "clasificacion": prediccion_existente.clasificacion,
                                "fecha_generada": prediccion_existente.fecha_generada.isoformat(),
                            }

                    except Exception as e:
                        logger.warning(
                            f"Error generando predicción para estudiante {estudiante_id}, "
                            f"materia {materia_id}, periodo {periodo_id}: {str(e)}"
                        )

                    # Agregar datos del periodo
                    periodos_data.append(
                        {
                            "periodo_id": periodo_id,
                            "periodo_nombre": periodo.nombre,
                            "fecha_inicio": periodo.fecha_inicio.isoformat(),
                            "fecha_fin": periodo.fecha_fin.isoformat(),
                            "rendimiento": {
                                "nota_final": nota_final,
                                "detalle_evaluaciones": detalle_evaluaciones,
                                "fecha_calculo": (
                                    existente_rendimiento.fecha_calculo.isoformat()
                                    if existente_rendimiento.fecha_calculo
                                    else None
                                ),
                            },
                            "prediccion_ml": prediccion_data,
                        }
                    )

                # Calcular estadísticas generales de la materia
                notas_finales = [
                    p["rendimiento"]["nota_final"]
                    for p in periodos_data
                    if p["rendimiento"]["nota_final"] > 0
                ]
                predicciones_numericas = [
                    p["prediccion_ml"]["resultado_numerico"]
                    for p in periodos_data
                    if p["prediccion_ml"] and p["prediccion_ml"]["resultado_numerico"]
                ]

                estadisticas = {
                    "promedio_rendimiento": (
                        round(sum(notas_finales) / len(notas_finales), 2)
                        if notas_finales
                        else 0
                    ),
                    "promedio_prediccion": (
                        round(
                            sum(predicciones_numericas) / len(predicciones_numericas), 2
                        )
                        if predicciones_numericas
                        else 0
                    ),
                    "mejor_periodo": max(notas_finales) if notas_finales else 0,
                    "peor_periodo": min(notas_finales) if notas_finales else 0,
                    "total_periodos_evaluados": len(notas_finales),
                }

                # Agregar resultado de la materia
                resultados.append(
                    {
                        "materia": {
                            "id": materia_id,
                            "nombre": materia.nombre,
                            "descripcion": materia.descripcion,
                        },
                        "docente": docente_info,
                        "curso_id": curso_id,
                        "periodos": periodos_data,
                        "estadisticas": estadisticas,
                    }
                )

        # 8. ESTADÍSTICAS GENERALES DEL ESTUDIANTE
        todas_las_notas = []
        todas_las_predicciones = []

        for resultado in resultados:
            for periodo in resultado["periodos"]:
                if periodo["rendimiento"]["nota_final"] > 0:
                    todas_las_notas.append(periodo["rendimiento"]["nota_final"])
                if (
                    periodo["prediccion_ml"]
                    and periodo["prediccion_ml"]["resultado_numerico"]
                ):
                    todas_las_predicciones.append(
                        periodo["prediccion_ml"]["resultado_numerico"]
                    )

        estadisticas_generales = {
            "promedio_general": (
                round(sum(todas_las_notas) / len(todas_las_notas), 2)
                if todas_las_notas
                else 0
            ),
            "promedio_predicciones": (
                round(sum(todas_las_predicciones) / len(todas_las_predicciones), 2)
                if todas_las_predicciones
                else 0
            ),
            "total_materias": len(resultados),
            "total_evaluaciones": len(todas_las_notas),
            "mejor_materia": (
                max(
                    resultados, key=lambda x: x["estadisticas"]["promedio_rendimiento"]
                )["materia"]["nombre"]
                if resultados
                else None
            ),
        }

        # Mensaje personalizado según el usuario
        mensajes_por_tipo = {
            "estudiante": "Tu información académica completa ha sido obtenida exitosamente",
            "padre": f"Información académica de tu hijo/a {estudiante.nombre} {estudiante.apellido} obtenida exitosamente",
            "docente": f"Información académica del estudiante {estudiante.nombre} {estudiante.apellido} en tus materias",
            "admin": f"Información académica completa del estudiante {estudiante.nombre} {estudiante.apellido}",
        }

        mensaje_personalizado = mensajes_por_tipo.get(
            user_type,
            f"Información académica obtenida para gestión {gestion_activa.anio}",
        )

        return {
            "success": True,
            "mensaje": mensaje_personalizado,
            "gestion": {
                "id": gestion_activa.id,
                "anio": gestion_activa.anio,
                "descripcion": gestion_activa.descripcion,
            },
            "estudiante": {
                "id": estudiante_id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "correo": estudiante.correo,
                "codigo": f"EST{estudiante_id:03d}",
            },
            "usuario_consultante": {
                "id": user_id,
                "tipo": user_type,
                "permisos": {
                    "puede_ver_todas_materias": user_type
                    in ["admin", "estudiante", "padre"],
                    "materias_limitadas": (
                        materia_ids_permitidas if user_type == "docente" else None
                    ),
                },
            },
            "estadisticas_generales": estadisticas_generales,
            "materias": resultados,
            "metadatos": {
                "fecha_consulta": hoy.isoformat(),
                "total_periodos": len(periodos),
                "predicciones_generadas": sum(
                    1
                    for resultado in resultados
                    for periodo in resultado["periodos"]
                    if periodo["prediccion_ml"]
                ),
                "materias_filtradas_por_permisos": materia_ids_permitidas is not None,
            },
        }

    except HTTPException:
        raise
    except PermissionError as e:
        logger.error(f"Error de permisos para usuario {user_id}: {str(e)}")
        raise HTTPException(
            status_code=403, detail="No tienes permisos para acceder a esta información"
        )
    except Exception as e:
        logger.error(
            f"Error en obtener_rendimientos_y_predicciones_completos: {str(e)}"
        )

        # Errores más específicos para mejor debugging
        if "gestión" in str(e).lower():
            raise HTTPException(
                status_code=404, detail="Error relacionado con gestión académica"
            )
        elif "predicción" in str(e).lower():
            raise HTTPException(
                status_code=500, detail="Error en el sistema de predicciones ML"
            )
        else:
            raise HTTPException(
                status_code=500, detail=f"Error interno del servidor: {str(e)}"
            )
