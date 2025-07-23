from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.padre import PadreCreate, PadreOut, PadreUpdate, PadreConHijos
from app.schemas.estudiante import EstudianteOut
from app.schemas.sesion_asistencia import AsistenciaEstudianteOut
from app.crud import padre as crud
from app.crud import sesion_asistencia as asistencia_crud
from app.auth.roles import admin_required, usuario_autenticado, propietario_o_admin
from typing import List, Optional
from app.schemas.estudiante_info_academica import (
    MateriaConDocente,
    CursoBasico,
    DocenteConMaterias,
    InfoAcademicaCompleta,
)

router = APIRouter(prefix="/padres", tags=["👨‍👩‍👧‍👦 Padres"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== RUTAS ESPECÍFICAS (DEBEN IR PRIMERO) ==========

# ========== ENDPOINT PARA VER INFORMACIÓN ACADÉMICA DE TODOS LOS HIJOS ==========


@router.get("/info-academica-todos-hijos", response_model=dict)
def obtener_info_academica_todos_hijos(
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📋 Ver información académica de todos mis hijos (curso, materias, docentes)"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Obtener todos los hijos del padre
    hijos = crud.obtener_hijos_del_padre(db, padre_id)

    if not hijos:
        return {"success": False, "mensaje": "No tienes hijos registrados", "data": []}

    # Obtener información académica para cada hijo
    info_hijos = []

    for hijo in hijos:
        # Obtener información académica del hijo
        from app.crud import estudiante_info_academica as info_crud

        info_academica = info_crud.obtener_info_academica_estudiante(
            db, hijo.id, gestion_id
        )

        # Si hay error, incluirlo en el resultado
        if "error" in info_academica:
            info_hijos.append(
                {
                    "estudiante": {
                        "id": hijo.id,
                        "nombre": hijo.nombre,
                        "apellido": hijo.apellido,
                        "codigo": f"EST{hijo.id:03d}",
                    },
                    "info_academica": None,
                    "error": info_academica["error"],
                    "estadisticas": {
                        "total_materias": 0,
                        "materias_con_docente": 0,
                        "materias_sin_docente": 0,
                        "total_docentes_unicos": 0,
                    },
                }
            )
            continue

        # Calcular estadísticas
        materias = info_academica.get("materias", [])
        materias_con_docente = sum(1 for m in materias if m.get("docente") is not None)
        materias_sin_docente = len(materias) - materias_con_docente

        # Contar docentes únicos
        docentes_unicos = set()
        for materia in materias:
            if materia.get("docente"):
                docentes_unicos.add(materia["docente"]["id"])

        info_hijos.append(
            {
                "estudiante": {
                    "id": hijo.id,
                    "nombre": hijo.nombre,
                    "apellido": hijo.apellido,
                    "codigo": f"EST{hijo.id:03d}",
                },
                "info_academica": info_academica,
                "estadisticas": {
                    "total_materias": len(materias),
                    "materias_con_docente": materias_con_docente,
                    "materias_sin_docente": materias_sin_docente,
                    "total_docentes_unicos": len(docentes_unicos),
                },
            }
        )

    return {
        "success": True,
        "data": info_hijos,
        "total_hijos": len(hijos),
        "mensaje": f"Información académica obtenida para {len(hijos)} hijo(s)",
    }


@router.get("/", response_model=List[PadreOut])
def listar_padres(
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    """📋 Listar todos los padres (Solo administradores)"""
    return crud.obtener_padres(db)


@router.get("/mi-perfil", response_model=PadreOut)
def obtener_mi_perfil(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """👤 Obtener mi perfil como padre"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")
    padre = crud.obtener_padre_por_id(db, padre_id)
    if not padre:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    return padre


@router.get("/mis-hijos", response_model=List[EstudianteOut])
def obtener_mis_hijos(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """👶 Obtener mis hijos"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")
    return crud.obtener_hijos_del_padre(db, padre_id)


# ========== NUEVOS ENDPOINTS DE ASISTENCIA (RUTAS ESPECÍFICAS) ==========


@router.get("/asistencias-todos-hijos", response_model=dict)
def obtener_asistencias_todos_hijos(
    curso_id: Optional[int] = Query(None, description="Filtrar por curso"),
    materia_id: Optional[int] = Query(None, description="Filtrar por materia"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📋 Ver asistencias de todos mis hijos organizadas por hijo"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Obtener todos los hijos del padre
    hijos = crud.obtener_hijos_del_padre(db, padre_id)

    if not hijos:
        return {"success": False, "mensaje": "No tienes hijos registrados", "data": []}

    # Obtener asistencias para cada hijo
    resultado = []
    for hijo in hijos:
        asistencias = asistencia_crud.obtener_asistencias_estudiante(
            db, hijo.id, curso_id, materia_id
        )

        resultado.append(
            {
                "estudiante": {
                    "id": hijo.id,
                    "nombre": hijo.nombre,
                    "apellido": hijo.apellido,
                    "codigo": f"EST{hijo.id:03d}",
                },
                "asistencias": [
                    AsistenciaEstudianteOut.from_orm(a) for a in asistencias
                ],
                "total_asistencias": len(asistencias),
            }
        )

    return {
        "success": True,
        "data": resultado,
        "total_hijos": len(hijos),
        "mensaje": f"Asistencias obtenidas para {len(hijos)} hijo(s)",
    }


@router.get("/resumen-asistencia-todos-hijos", response_model=dict)
def obtener_resumen_asistencia_todos_hijos(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📊 Resumen de asistencia de todos los hijos por materia"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Obtener todos los hijos del padre
    hijos = crud.obtener_hijos_del_padre(db, padre_id)

    if not hijos:
        return {"success": False, "mensaje": "No tienes hijos registrados", "data": []}

    # Obtener resumen para cada hijo
    resumenes_hijos = []

    for hijo in hijos:
        # Obtener materias del hijo
        from app.crud import estudiante_info_academica as info_crud

        materias = info_crud.obtener_materias_estudiante(db, hijo.id)

        # Calcular resumen por materia para este hijo
        resumen_materias = []
        total_sesiones_hijo = 0
        total_presentes_hijo = 0

        for materia_info in materias:
            materia_id = materia_info["materia"]["id"]
            materia_nombre = materia_info["materia"]["nombre"]

            # Obtener asistencias para esta materia
            asistencias = asistencia_crud.obtener_asistencias_estudiante(
                db, hijo.id, None, materia_id
            )

            # Calcular estadísticas
            total_sesiones = len(asistencias)
            presentes = sum(1 for a in asistencias if a.presente)
            tardanzas = sum(1 for a in asistencias if a.es_tardanza)

            total_sesiones_hijo += total_sesiones
            total_presentes_hijo += presentes

            porcentaje_asistencia = (
                (presentes / total_sesiones * 100) if total_sesiones > 0 else 0
            )

            resumen_materias.append(
                {
                    "materia_nombre": materia_nombre,
                    "total_sesiones": total_sesiones,
                    "presentes": presentes,
                    "tardanzas": tardanzas,
                    "porcentaje_asistencia": round(porcentaje_asistencia, 2),
                }
            )

        porcentaje_general_hijo = (
            (total_presentes_hijo / total_sesiones_hijo * 100)
            if total_sesiones_hijo > 0
            else 0
        )

        resumenes_hijos.append(
            {
                "estudiante": {
                    "id": hijo.id,
                    "nombre": hijo.nombre,
                    "apellido": hijo.apellido,
                    "codigo": f"EST{hijo.id:03d}",
                },
                "resumen_general": {
                    "total_sesiones": total_sesiones_hijo,
                    "total_presentes": total_presentes_hijo,
                    "porcentaje_asistencia": round(porcentaje_general_hijo, 2),
                },
                "materias": resumen_materias,
            }
        )

    return {
        "success": True,
        "data": resumenes_hijos,
        "total_hijos": len(hijos),
        "mensaje": f"Resumen generado para {len(hijos)} hijo(s)",
    }


# ========== RUTAS CON PARÁMETROS (DEBEN IR AL FINAL) ==========


@router.post("/", response_model=PadreOut)
def crear_padre(
    padre: PadreCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    """👤 Crear un nuevo padre (Solo administradores)"""
    return crud.crear_padre(db, padre)


@router.get(
    "/hijo/{estudiante_id}/asistencias", response_model=List[AsistenciaEstudianteOut]
)
def obtener_asistencias_de_hijo(
    estudiante_id: int,
    curso_id: Optional[int] = Query(None, description="Filtrar por curso"),
    materia_id: Optional[int] = Query(None, description="Filtrar por materia"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📋 Ver asistencias de mi hijo (filtrable por materia)"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener asistencias del hijo usando la lógica existente
    asistencias = asistencia_crud.obtener_asistencias_estudiante(
        db, estudiante_id, curso_id, materia_id
    )

    return [AsistenciaEstudianteOut.from_orm(a) for a in asistencias]


@router.get("/hijo/{estudiante_id}/resumen-asistencia-por-materia", response_model=dict)
def obtener_resumen_asistencia_por_materia(
    estudiante_id: int,
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📊 Resumen estadístico de asistencia por materia para un hijo"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener información del estudiante
    from app.crud import estudiante as estudiante_crud

    estudiante = estudiante_crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener materias del estudiante
    from app.crud import estudiante_info_academica as info_crud

    materias = info_crud.obtener_materias_estudiante(db, estudiante_id)

    # Calcular resumen por materia
    resumen_materias = []

    for materia_info in materias:
        materia_id = materia_info["materia"]["id"]
        materia_nombre = materia_info["materia"]["nombre"]

        # Obtener asistencias para esta materia
        asistencias = asistencia_crud.obtener_asistencias_estudiante(
            db, estudiante_id, None, materia_id
        )

        # Calcular estadísticas
        total_sesiones = len(asistencias)
        presentes = sum(1 for a in asistencias if a.presente)
        ausentes = total_sesiones - presentes
        tardanzas = sum(1 for a in asistencias if a.es_tardanza)
        justificados = sum(1 for a in asistencias if a.justificado)

        porcentaje_asistencia = (
            (presentes / total_sesiones * 100) if total_sesiones > 0 else 0
        )

        resumen_materias.append(
            {
                "materia": {"id": materia_id, "nombre": materia_nombre},
                "docente": materia_info.get("docente"),
                "estadisticas": {
                    "total_sesiones": total_sesiones,
                    "presentes": presentes,
                    "ausentes": ausentes,
                    "tardanzas": tardanzas,
                    "justificados": justificados,
                    "porcentaje_asistencia": round(porcentaje_asistencia, 2),
                },
            }
        )

    # Calcular estadísticas generales
    total_sesiones_general = sum(
        m["estadisticas"]["total_sesiones"] for m in resumen_materias
    )
    total_presentes_general = sum(
        m["estadisticas"]["presentes"] for m in resumen_materias
    )
    porcentaje_general = (
        (total_presentes_general / total_sesiones_general * 100)
        if total_sesiones_general > 0
        else 0
    )

    return {
        "success": True,
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "codigo": f"EST{estudiante.id:03d}",
        },
        "resumen_general": {
            "total_sesiones": total_sesiones_general,
            "total_presentes": total_presentes_general,
            "porcentaje_asistencia_general": round(porcentaje_general, 2),
        },
        "resumen_por_materia": resumen_materias,
        "total_materias": len(resumen_materias),
        "mensaje": f"Resumen de asistencia generado para {len(resumen_materias)} materia(s)",
    }


@router.post("/{padre_id}/hijos/{estudiante_id}")
def asignar_hijo(
    padre_id: int,
    estudiante_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    """👶 Asignar hijo a padre (Solo administradores)"""
    resultado = crud.asignar_hijo_a_padre(db, padre_id, estudiante_id)
    if not resultado:
        raise HTTPException(status_code=400, detail="No se pudo asignar hijo al padre")
    return {"mensaje": "Hijo asignado correctamente"}


@router.delete("/{padre_id}/hijos/{estudiante_id}")
def desasignar_hijo(
    padre_id: int,
    estudiante_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    """❌ Desasignar hijo de padre (Solo administradores)"""
    resultado = crud.desasignar_hijo_de_padre(db, padre_id, estudiante_id)
    if not resultado:
        raise HTTPException(
            status_code=400, detail="No se pudo desasignar hijo del padre"
        )
    return {"mensaje": "Hijo desasignado correctamente"}


@router.get("/{padre_id}/hijos")
def obtener_hijos_del_padre(
    padre_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(propietario_o_admin),
):
    """👶 Obtener hijos de un padre específico"""
    # Verificar permisos: debe ser el mismo padre o admin
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type != "admin" and (user_type != "padre" or user_id != padre_id):
        raise HTTPException(status_code=403, detail="No autorizado")

    return crud.obtener_hijos_del_padre(db, padre_id)


@router.put("/{padre_id}", response_model=PadreOut)
def actualizar_padre(
    padre_id: int,
    datos: PadreUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    """✏️ Actualizar datos del padre (Solo administradores)"""
    padre = crud.actualizar_padre(db, padre_id, datos)
    if not padre:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    return padre


@router.delete("/{padre_id}")
def eliminar_padre(
    padre_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    """🗑️ Eliminar padre (Solo administradores)"""
    padre = crud.eliminar_padre(db, padre_id)
    if not padre:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    return {"mensaje": "Padre eliminado correctamente"}


# ESTA RUTA DEBE IR AL FINAL DE TODO
@router.get("/{padre_id}", response_model=PadreOut)
def obtener_padre(
    padre_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(propietario_o_admin),
):
    """👤 Obtener datos de un padre"""
    # Verificar permisos: debe ser el mismo padre o admin
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type != "admin" and (user_type != "padre" or user_id != padre_id):
        raise HTTPException(status_code=403, detail="No autorizado")

    padre = crud.obtener_padre_por_id(db, padre_id)
    if not padre:
        raise HTTPException(status_code=404, detail="Padre no encontrado")
    return padre


@router.get("/hijo/{estudiante_id}/materias", response_model=dict)
def obtener_materias_de_hijo(
    estudiante_id: int,
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📚 Ver las materias de mi hijo con sus docentes"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener información del estudiante
    from app.crud import estudiante as estudiante_crud

    estudiante = estudiante_crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener materias del estudiante
    from app.crud import estudiante_info_academica as info_crud

    materias = info_crud.obtener_materias_estudiante(db, estudiante_id, gestion_id)

    if not materias:
        return {
            "success": False,
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "codigo": f"EST{estudiante.id:03d}",
            },
            "materias": [],
            "total": 0,
            "mensaje": "El estudiante no tiene materias asignadas en esta gestión",
        }

    return {
        "success": True,
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "codigo": f"EST{estudiante.id:03d}",
        },
        "materias": materias,
        "total": len(materias),
        "mensaje": f"Se encontraron {len(materias)} materia(s) para el estudiante",
    }


@router.get("/hijo/{estudiante_id}/curso", response_model=dict)
def obtener_curso_de_hijo(
    estudiante_id: int,
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """🏫 Ver el curso actual de mi hijo"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener información del estudiante
    from app.crud import estudiante as estudiante_crud

    estudiante = estudiante_crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener curso del estudiante
    from app.crud import estudiante_info_academica as info_crud

    curso = info_crud.obtener_curso_estudiante(db, estudiante_id, gestion_id)

    if not curso:
        return {
            "success": False,
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "codigo": f"EST{estudiante.id:03d}",
            },
            "curso": None,
            "mensaje": "El estudiante no tiene curso asignado en esta gestión",
        }

    return {
        "success": True,
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "codigo": f"EST{estudiante.id:03d}",
        },
        "curso": curso,
        "mensaje": "Curso obtenido exitosamente",
    }


@router.get("/hijo/{estudiante_id}/docentes", response_model=dict)
def obtener_docentes_de_hijo(
    estudiante_id: int,
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """👨‍🏫 Ver todos los docentes que enseñan a mi hijo"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener información del estudiante
    from app.crud import estudiante as estudiante_crud

    estudiante = estudiante_crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener docentes del estudiante
    from app.crud import estudiante_info_academica as info_crud

    docentes = info_crud.obtener_docentes_estudiante(db, estudiante_id, gestion_id)

    if not docentes:
        return {
            "success": False,
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "codigo": f"EST{estudiante.id:03d}",
            },
            "docentes": [],
            "total": 0,
            "mensaje": "El estudiante no tiene docentes asignados en esta gestión",
        }

    return {
        "success": True,
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "codigo": f"EST{estudiante.id:03d}",
        },
        "docentes": docentes,
        "total": len(docentes),
        "mensaje": f"Se encontraron {len(docentes)} docente(s) para el estudiante",
    }


@router.get("/hijo/{estudiante_id}/info-academica-completa", response_model=dict)
def obtener_info_academica_completa_hijo(
    estudiante_id: int,
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """📋 Ver toda la información académica completa de mi hijo"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener información académica completa
    from app.crud import estudiante_info_academica as info_crud

    info_academica = info_crud.obtener_info_academica_estudiante(
        db, estudiante_id, gestion_id
    )

    # Verificar si hay error en la respuesta
    if "error" in info_academica:
        return {"success": False, "mensaje": info_academica["error"]}

    # Calcular estadísticas adicionales
    materias = info_academica.get("materias", [])
    materias_con_docente = sum(1 for m in materias if m.get("docente") is not None)
    materias_sin_docente = len(materias) - materias_con_docente

    # Contar docentes únicos
    docentes_unicos = set()
    for materia in materias:
        if materia.get("docente"):
            docentes_unicos.add(materia["docente"]["id"])

    return {
        "success": True,
        "info_academica": info_academica,
        "estadisticas": {
            "total_materias": len(materias),
            "materias_con_docente": materias_con_docente,
            "materias_sin_docente": materias_sin_docente,
            "total_docentes_unicos": len(docentes_unicos),
        },
        "mensaje": f"Información académica completa obtenida para la gestión {info_academica.get('gestion', {}).get('anio', 'N/A')}",
    }


@router.get("/hijo/{estudiante_id}/materia/{materia_id}/docente", response_model=dict)
def obtener_docente_de_materia_hijo(
    estudiante_id: int,
    materia_id: int,
    gestion_id: Optional[int] = Query(None, description="ID de la gestión (opcional)"),
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """👨‍🏫 Ver el docente de una materia específica de mi hijo"""
    # Verificar que el usuario es padre
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres pueden acceder")

    padre_id = payload.get("user_id")

    # Verificar que es padre del estudiante
    if not crud.es_padre_del_estudiante(db, padre_id, estudiante_id):
        raise HTTPException(
            status_code=403, detail="No autorizado para ver este estudiante"
        )

    # Obtener información del estudiante
    from app.crud import estudiante as estudiante_crud

    estudiante = estudiante_crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener materias del estudiante
    from app.crud import estudiante_info_academica as info_crud

    materias = info_crud.obtener_materias_estudiante(db, estudiante_id, gestion_id)

    # Buscar la materia específica
    materia_encontrada = None
    for materia in materias:
        if materia["materia"]["id"] == materia_id:
            materia_encontrada = materia
            break

    if not materia_encontrada:
        return {
            "success": False,
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "codigo": f"EST{estudiante.id:03d}",
            },
            "mensaje": "El estudiante no está inscrito en esta materia o la materia no existe",
        }

    if not materia_encontrada["docente"]:
        return {
            "success": False,
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "codigo": f"EST{estudiante.id:03d}",
            },
            "materia": materia_encontrada["materia"],
            "docente": None,
            "mensaje": "Esta materia no tiene docente asignado",
        }

    return {
        "success": True,
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "codigo": f"EST{estudiante.id:03d}",
        },
        "materia": materia_encontrada["materia"],
        "docente": materia_encontrada["docente"],
        "mensaje": "Docente encontrado exitosamente",
    }
