from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import SessionLocal
from app.auth.roles import docente_o_admin_required, admin_required
from app.models import Evaluacion, RendimientoFinal, Inscripcion, Periodo
from app.models.curso import Curso
from app.models.curso_materia import CursoMateria
from app.models.docente import Docente
from app.models.docente_materia import DocenteMateria
from app.models.estudiante import Estudiante
from app.models.gestion import Gestion
from app.models.materia import Materia
from app.models.tipo_evaluacion import TipoEvaluacion

router = APIRouter(prefix="/resumen", tags=["Resumen Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/materia/completo")
def resumen_materia_completo(
    curso_id: int,
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    # Obtener IDs de estudiantes en el curso
    inscripciones = db.query(Inscripcion).filter_by(curso_id=curso_id).all()
    estudiante_ids = [i.estudiante_id for i in inscripciones]
    if not estudiante_ids:
        raise HTTPException(status_code=404, detail="No hay estudiantes en este curso.")

    # Obtener periodos que tienen al menos una evaluación registrada
    periodos_con_datos = (
        db.query(Evaluacion.periodo_id)
        .filter(
            Evaluacion.materia_id == materia_id,
            Evaluacion.estudiante_id.in_(estudiante_ids),
        )
        .distinct()
        .all()
    )
    periodos_ids = [p[0] for p in periodos_con_datos]
    if not periodos_ids:
        raise HTTPException(status_code=404, detail="No hay evaluaciones registradas.")

    resumen_por_periodo = []

    for pid in periodos_ids:
        # Notas finales (rendimiento)
        rendimientos = (
            db.query(RendimientoFinal)
            .filter(
                RendimientoFinal.estudiante_id.in_(estudiante_ids),
                RendimientoFinal.materia_id == materia_id,
                RendimientoFinal.periodo_id == pid,
            )
            .all()
        )
        promedio_notas = (
            sum(r.nota_final for r in rendimientos) / len(rendimientos)
            if rendimientos
            else 0
        )

        # Asistencia
        asistencias = (
            db.query(Evaluacion)
            .filter(
                Evaluacion.estudiante_id.in_(estudiante_ids),
                Evaluacion.materia_id == materia_id,
                Evaluacion.periodo_id == pid,
                Evaluacion.tipo_evaluacion_id == 5,
            )
            .all()
        )
        promedio_asistencia = (
            sum(e.valor for e in asistencias) / len(asistencias) if asistencias else 0
        )

        # Participación
        participaciones = (
            db.query(Evaluacion)
            .filter(
                Evaluacion.estudiante_id.in_(estudiante_ids),
                Evaluacion.materia_id == materia_id,
                Evaluacion.periodo_id == pid,
                Evaluacion.tipo_evaluacion_id == 4,
            )
            .all()
        )
        promedio_participacion = (
            sum(e.valor for e in participaciones) / len(participaciones)
            if participaciones
            else 0
        )

        resumen_por_periodo.append(
            {
                "periodo_id": pid,
                "promedio_notas": round(promedio_notas, 2),
                "promedio_asistencia": round(promedio_asistencia, 2),
                "promedio_participacion": round(promedio_participacion, 2),
            }
        )

    # Promedios generales
    n = len(resumen_por_periodo)
    promedio_general = {
        "notas": round(sum(r["promedio_notas"] for r in resumen_por_periodo) / n, 2),
        "asistencia": round(
            sum(r["promedio_asistencia"] for r in resumen_por_periodo) / n, 2
        ),
        "participacion": round(
            sum(r["promedio_participacion"] for r in resumen_por_periodo) / n, 2
        ),
    }

    return {
        "total_estudiantes": len(estudiante_ids),
        "resumen_por_periodo": resumen_por_periodo,
        "promedio_general": promedio_general,
    }


@router.get("/admin/resumen")
def dashboard_admin(
    db: Session = Depends(get_db), payload: dict = Depends(admin_required)
):
    total_estudiantes = db.query(Estudiante).count()
    total_cursos = db.query(Curso).count()
    total_admins = db.query(Docente).filter_by(is_doc=False).count()
    total_docentes = db.query(Docente).filter_by(is_doc=True).count()
    total_materias = db.query(Materia).count()
    total_gestiones = db.query(Gestion).count()
    total_periodos = db.query(Periodo).count()
    total_tipo_evaluaciones = db.query(TipoEvaluacion).count()
    total_evaluaciones = db.query(Evaluacion).count()
    total_inscripciones = db.query(Inscripcion).count()
    total_rendimientos = db.query(RendimientoFinal).count()

    return {
        "total_estudiantes": total_estudiantes,
        "total_cursos": total_cursos,
        "total_admins": total_admins,
        "total_docentes": total_docentes,
        "total_materias": total_materias,
        "total_gestiones": total_gestiones,
        "total_periodos": total_periodos,
        "total_tipo_evaluaciones": total_tipo_evaluaciones,
        "total_evaluaciones": total_evaluaciones,
        "total_inscripciones": total_inscripciones,
        "total_rendimientos": total_rendimientos,
    }


@router.get("/docente/resumen")
def dashboard_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    hoy = date.today()

    # Buscar la gestión activa (con al menos un periodo que incluya la fecha actual)
    gestion_activa = (
        db.query(Gestion)
        .join(Periodo, Periodo.gestion_id == Gestion.id)
        .filter(Periodo.fecha_inicio <= hoy, Periodo.fecha_fin >= hoy)
        .first()
    )

    if not gestion_activa:
        raise HTTPException(
            status_code=404, detail="No hay gestión activa en la fecha actual."
        )

    # Obtener materias del docente
    materias_ids = (
        db.query(DocenteMateria.materia_id)
        .filter_by(docente_id=docente_id)
        .distinct()
        .all()
    )
    materias_ids = [m[0] for m in materias_ids]

    if not materias_ids:
        raise HTTPException(
            status_code=404, detail="El docente no tiene materias asignadas."
        )

    # Obtener cursos relacionados a las materias
    cursos_ids = (
        db.query(CursoMateria.curso_id)
        .filter(CursoMateria.materia_id.in_(materias_ids))
        .distinct()
        .all()
    )
    cursos_ids = [c[0] for c in cursos_ids]

    # Obtener inscripciones dentro de la gestión activa
    inscripciones = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.curso_id.in_(cursos_ids),
            Inscripcion.gestion_id == gestion_activa.id,
        )
        .all()
    )

    estudiante_ids = list(set(insc.estudiante_id for insc in inscripciones))
    periodos_ids = [p.id for p in gestion_activa.periodos]

    total_materias = len(materias_ids)
    total_cursos = len(cursos_ids)
    total_estudiantes = len(estudiante_ids)
    total_inscripciones = len(inscripciones)
    total_evaluaciones = (
        db.query(Evaluacion)
        .filter(
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo_id.in_(periodos_ids),
        )
        .count()
    )
    total_rendimientos = (
        db.query(RendimientoFinal)
        .filter(
            RendimientoFinal.materia_id.in_(materias_ids),
            RendimientoFinal.periodo_id.in_(periodos_ids),
        )
        .count()
    )
    total_periodos = len(periodos_ids)

    return {
        "gestion_activa": gestion_activa.anio,
        "total_materias": total_materias,
        "total_cursos": total_cursos,
        "total_estudiantes": total_estudiantes,
        "total_inscripciones": total_inscripciones,
        "total_evaluaciones": total_evaluaciones,
        "total_rendimientos": total_rendimientos,
        "total_periodos": total_periodos,
    }


@router.get("/docente")
def dashboard_docente1(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    # Obtener gestión activa
    gestion_activa = db.query(Gestion).order_by(desc(Gestion.id)).first()
    if not gestion_activa:
        raise HTTPException(status_code=404, detail="No hay gestión activa")

    # Materias asignadas
    materias_ids = (
        db.query(DocenteMateria.materia_id)
        .filter(DocenteMateria.docente_id == docente_id)
        .distinct()
        .all()
    )
    materias_ids = [m[0] for m in materias_ids]
    materias = db.query(Materia).filter(Materia.id.in_(materias_ids)).all()

    total_materias = len(materias)
    nombres_materias = [m.nombre for m in materias]

    # Cantidad total de estudiantes distintos
    inscripciones = (
        db.query(Inscripcion).filter(Inscripcion.gestion_id == gestion_activa.id).all()
    )
    estudiantes_ids = list({i.estudiante_id for i in inscripciones})
    total_estudiantes = len(estudiantes_ids)

    # Evaluaciones por tipo
    tipos = db.query(TipoEvaluacion).all()
    evaluaciones_por_tipo = {}
    for tipo in tipos:
        count = (
            db.query(Evaluacion)
            .filter(
                Evaluacion.tipo_evaluacion_id == tipo.id,
                Evaluacion.materia_id.in_(materias_ids),
                Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id),
            )
            .count()
        )
        evaluaciones_por_tipo[tipo.nombre] = count

    # Promedio general por materia
    promedios_materias = {}
    for materia in materias:
        notas = (
            db.query(RendimientoFinal.nota_final)
            .filter(
                RendimientoFinal.materia_id == materia.id,
                RendimientoFinal.periodo.has(Periodo.gestion_id == gestion_activa.id),
            )
            .all()
        )
        if notas:
            promedio = sum(n[0] for n in notas) / len(notas)
            promedios_materias[materia.nombre] = round(promedio, 2)

    # Promedio general asistencia y participación
    asistencias = (
        db.query(Evaluacion.valor)
        .filter(
            Evaluacion.tipo_evaluacion_id == 5,
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id),
        )
        .all()
    )
    participaciones = (
        db.query(Evaluacion.valor)
        .filter(
            Evaluacion.tipo_evaluacion_id == 4,
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id),
        )
        .all()
    )
    promedio_asistencia = (
        round(sum(a[0] for a in asistencias) / len(asistencias), 2)
        if asistencias
        else 0
    )
    promedio_participacion = (
        round(sum(p[0] for p in participaciones) / len(participaciones), 2)
        if participaciones
        else 0
    )

    # Top 3 estudiantes por materia
    top_estudiantes = {}
    for materia in materias:
        top = (
            db.query(
                Estudiante.nombre, Estudiante.apellido, RendimientoFinal.nota_final
            )
            .join(RendimientoFinal, RendimientoFinal.estudiante_id == Estudiante.id)
            .filter(
                RendimientoFinal.materia_id == materia.id,
                RendimientoFinal.periodo.has(Periodo.gestion_id == gestion_activa.id),
            )
            .order_by(desc(RendimientoFinal.nota_final))
            .limit(3)
            .all()
        )
        top_estudiantes[materia.nombre] = [
            {"nombre": t[0], "apellido": t[1], "nota": t[2]} for t in top
        ]

    # Última evaluación registrada
    ultima_eval = (
        db.query(Evaluacion)
        .filter(
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id),
        )
        .order_by(desc(Evaluacion.fecha))
        .first()
    )
    ultima_fecha = ultima_eval.fecha.isoformat() if ultima_eval else None

    # Materias sin evaluaciones aún
    materias_sin_eval = []
    for materia in materias:
        existe = (
            db.query(Evaluacion)
            .filter(
                Evaluacion.materia_id == materia.id,
                Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id),
            )
            .first()
        )
        if not existe:
            materias_sin_eval.append(materia.nombre)

    return {
        "gestion": gestion_activa.anio,
        "materias_asignadas": total_materias,
        "nombres_materias": nombres_materias,
        "total_estudiantes": total_estudiantes,
        "evaluaciones_por_tipo": evaluaciones_por_tipo,
        "promedios_materias": promedios_materias,
        "promedio_asistencia": promedio_asistencia,
        "promedio_participacion": promedio_participacion,
        "top_estudiantes": top_estudiantes,
        "ultima_evaluacion": ultima_fecha,
        "materias_sin_evaluaciones": materias_sin_eval,
    }

@router.get("/docente/dashboard")
def dashboard_docente_completo(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    hoy = date.today()

    # Gestión activa (que contenga el día actual)
    gestion_activa = (
        db.query(Gestion)
        .join(Periodo)
        .filter(Periodo.fecha_inicio <= hoy, Periodo.fecha_fin >= hoy)
        .first()
    )
    if not gestion_activa:
        raise HTTPException(status_code=404, detail="No hay gestión activa")

    periodos_ids = [p.id for p in gestion_activa.periodos]

    # Materias asignadas al docente
    materias_ids = [m[0] for m in db.query(DocenteMateria.materia_id)
                    .filter_by(docente_id=docente_id).distinct()]
    materias = db.query(Materia).filter(Materia.id.in_(materias_ids)).all()
    nombres_materias = [m.nombre for m in materias]

    # Cursos relacionados a las materias
    cursos_ids = [c[0] for c in db.query(CursoMateria.curso_id)
                  .filter(CursoMateria.materia_id.in_(materias_ids)).distinct()]

    # Inscripciones en esa gestión
    inscripciones = db.query(Inscripcion).filter(
        Inscripcion.curso_id.in_(cursos_ids),
        Inscripcion.gestion_id == gestion_activa.id
    ).all()
    estudiante_ids = list({i.estudiante_id for i in inscripciones})

    # Evaluaciones por tipo
    tipos = db.query(TipoEvaluacion).all()
    evaluaciones_por_tipo = {
        tipo.nombre: db.query(Evaluacion).filter(
            Evaluacion.tipo_evaluacion_id == tipo.id,
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id)
        ).count()
        for tipo in tipos
    }

    # Promedios por materia
    promedios_materias = {}
    for materia in materias:
        notas = db.query(RendimientoFinal.nota_final).filter(
            RendimientoFinal.materia_id == materia.id,
            RendimientoFinal.periodo.has(Periodo.gestion_id == gestion_activa.id)
        ).all()
        if notas:
            promedios_materias[materia.nombre] = round(sum(n[0] for n in notas) / len(notas), 2)

    # Asistencia y participación
    def promedio(tipo_id):
        valores = db.query(Evaluacion.valor).filter(
            Evaluacion.tipo_evaluacion_id == tipo_id,
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id)
        ).all()
        return round(sum(v[0] for v in valores) / len(valores), 2) if valores else 0

    promedio_asistencia = promedio(5)
    promedio_participacion = promedio(4)

    # Top estudiantes
    top_estudiantes = {}
    for materia in materias:
        top = db.query(
            Estudiante.nombre, Estudiante.apellido, RendimientoFinal.nota_final
        ).join(RendimientoFinal, RendimientoFinal.estudiante_id == Estudiante.id).filter(
            RendimientoFinal.materia_id == materia.id,
            RendimientoFinal.periodo.has(Periodo.gestion_id == gestion_activa.id)
        ).order_by(RendimientoFinal.nota_final.desc()).limit(3).all()
        top_estudiantes[materia.nombre] = [
            {"nombre": t[0], "apellido": t[1], "nota": t[2]} for t in top
        ]

    # Última evaluación
    ultima_eval = db.query(Evaluacion).filter(
        Evaluacion.materia_id.in_(materias_ids),
        Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id)
    ).order_by(Evaluacion.fecha.desc()).first()
    ultima_fecha = ultima_eval.fecha.isoformat() if ultima_eval else None

    # Materias sin evaluaciones
    materias_sin_eval = []
    for materia in materias:
        existe = db.query(Evaluacion).filter(
            Evaluacion.materia_id == materia.id,
            Evaluacion.periodo.has(Periodo.gestion_id == gestion_activa.id)
        ).first()
        if not existe:
            materias_sin_eval.append(materia.nombre)

    return {
        "gestion": gestion_activa.anio,
        "materias_asignadas": len(materias),
        "nombres_materias": nombres_materias,
        "total_cursos": len(cursos_ids),
        "total_estudiantes": len(estudiante_ids),
        "total_inscripciones": len(inscripciones),
        "total_evaluaciones": db.query(Evaluacion).filter(
            Evaluacion.materia_id.in_(materias_ids),
            Evaluacion.periodo_id.in_(periodos_ids),
        ).count(),
        "total_rendimientos": db.query(RendimientoFinal).filter(
            RendimientoFinal.materia_id.in_(materias_ids),
            RendimientoFinal.periodo_id.in_(periodos_ids),
        ).count(),
        "total_periodos": len(periodos_ids),
        "evaluaciones_por_tipo": evaluaciones_por_tipo,
        "promedios_materias": promedios_materias,
        "promedio_asistencia": promedio_asistencia,
        "promedio_participacion": promedio_participacion,
        "top_estudiantes": top_estudiantes,
        "ultima_evaluacion": ultima_fecha,
        "materias_sin_evaluaciones": materias_sin_eval,
    }
