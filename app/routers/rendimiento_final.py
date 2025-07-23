from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.evaluacion import Evaluacion
from app.models.peso_tipo_evaluacion import PesoTipoEvaluacion
from app.models.tipo_evaluacion import TipoEvaluacion
from app.schemas.rendimiento_final import *
from app.auth.roles import docente_o_admin_required, usuario_autenticado
from app.crud import rendimiento_final as crud

router = APIRouter(prefix="/rendimientos", tags=["Rendimiento Final"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=RendimientoFinalOut)
def crear_rendimiento(
    datos: RendimientoFinalCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.crear_rendimiento(db, datos)


@router.put("/{id}", response_model=RendimientoFinalOut)
def actualizar(
    id: int,
    datos: RendimientoFinalUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.actualizar_rendimiento(db, id, datos)


@router.delete("/{id}")
def eliminar(
    id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    rf = crud.eliminar_rendimiento(db, id)
    if not rf:
        raise HTTPException(status_code=404, detail="No encontrado")
    return {"mensaje": "Eliminado"}


@router.get(
    "/estudiante/{estudiante_id}/periodo/{periodo_id}",
    response_model=list[RendimientoFinalOut],
)
def listar_rendimientos(
    estudiante_id: int,
    periodo_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_estudiante_periodo(db, estudiante_id, periodo_id)


@router.post("/calcular", response_model=RendimientoFinalOut)
def calcular_rendimiento_final(
    estudiante_id: int,
    materia_id: int,
    periodo_id: int,
    gestion_id: int,
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    tipos = db.query(TipoEvaluacion).all()
    nota_final = 0.0

    for tipo in tipos:
        # Obtener peso definido por el docente
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

        if not evaluaciones:
            continue

        promedio = sum(e.valor for e in evaluaciones) / len(evaluaciones)
        aporte = (promedio * peso.porcentaje) / 100
        nota_final += aporte

    # Redondear a una cifra clara
    nota_final = round(nota_final, 2)

    # Guardar resultado
    from app.models.rendimiento_final import RendimientoFinal

    existente = (
        db.query(RendimientoFinal)
        .filter_by(
            estudiante_id=estudiante_id, materia_id=materia_id, periodo_id=periodo_id
        )
        .first()
    )

    if existente:
        existente.nota_final = nota_final
        existente.fecha_calculo = func.now()
        db.commit()
        db.refresh(existente)
        return existente
    else:
        nuevo = RendimientoFinal(
            estudiante_id=estudiante_id,
            materia_id=materia_id,
            periodo_id=periodo_id,
            nota_final=nota_final,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo


@router.post("/calcular-todos", response_model=list[dict])
def calcular_todos_los_rendimientos(
    estudiante_id: int,
    periodo_id: int,
    gestion_id: int,
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    from app.models import (
        Inscripcion,
        CursoMateria,
        TipoEvaluacion,
        Evaluacion,
        PesoTipoEvaluacion,
        RendimientoFinal,
    )

    tipos = db.query(TipoEvaluacion).all()

    # Obtener curso del estudiante en esa gestión
    inscripciones = (
        db.query(Inscripcion)
        .filter_by(estudiante_id=estudiante_id, gestion_id=gestion_id)
        .all()
    )

    if not inscripciones:
        raise HTTPException(
            status_code=404, detail="El estudiante no está inscrito en esta gestión"
        )

    resultados = []

    for inscripcion in inscripciones:
        curso_id = inscripcion.curso_id

        # Obtener materias del curso
        curso_materias = db.query(CursoMateria).filter_by(curso_id=curso_id).all()
        materia_ids = [cm.materia_id for cm in curso_materias]

        for materia_id in materia_ids:
            nota_final = 0.0
            detalle = []

            for tipo in tipos:
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
                    promedio = sum(e.valor for e in evaluaciones) / len(evaluaciones)
                    aporte = (promedio * peso.porcentaje) / 100
                    nota_final += aporte
                    detalle.append(
                        {
                            "tipo_evaluacion_id": tipo.id,
                            "promedio": round(promedio, 2),
                            "peso": peso.porcentaje,
                            "aporte": round(aporte, 2),
                        }
                    )

            nota_final = round(nota_final, 2)

            existente = (
                db.query(RendimientoFinal)
                .filter_by(
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                )
                .first()
            )

            if existente:
                existente.nota_final = nota_final
                existente.fecha_calculo = func.now()
                db.commit()
                db.refresh(existente)
            else:
                existente = RendimientoFinal(
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                    nota_final=nota_final,
                )
                db.add(existente)
                db.commit()
                db.refresh(existente)

            resultados.append(
                {
                    "materia_id": materia_id,
                    "estudiante_id": estudiante_id,
                    "periodo_id": periodo_id,
                    "nota_final": nota_final,
                    "detalle": detalle,
                }
            )

    return resultados


@router.post("/calcular-todos-periodos", response_model=list[dict])
def calcular_todos_los_rendimientos_periodos(
    estudiante_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    from app.models import (
        Inscripcion,
        CursoMateria,
        TipoEvaluacion,
        Evaluacion,
        PesoTipoEvaluacion,
        RendimientoFinal,
        DocenteMateria,
        Periodo,
    )

    tipos = db.query(TipoEvaluacion).all()

    # Obtener todos los periodos de la gestión
    periodos = db.query(Periodo).filter_by(gestion_id=gestion_id).all()
    if not periodos:
        raise HTTPException(status_code=404, detail="No hay periodos para esta gestión")

    # Obtener inscripciones del estudiante en la gestión
    inscripciones = (
        db.query(Inscripcion)
        .filter_by(estudiante_id=estudiante_id, gestion_id=gestion_id)
        .all()
    )

    if not inscripciones:
        raise HTTPException(
            status_code=404, detail="El estudiante no está inscrito en esta gestión"
        )

    resultados = []

    for inscripcion in inscripciones:
        curso_id = inscripcion.curso_id

        # Materias del curso
        curso_materias = db.query(CursoMateria).filter_by(curso_id=curso_id).all()
        materia_ids = [cm.materia_id for cm in curso_materias]

        for materia_id in materia_ids:
            # Obtener docente asignado a esa materia
            docente_materia = (
                db.query(DocenteMateria).filter_by(materia_id=materia_id).first()
            )

            if not docente_materia:
                continue  # Saltar si no hay docente asignado

            docente_id = docente_materia.docente_id

            for periodo in periodos:
                periodo_id = periodo.id
                nota_final = 0.0
                detalle = []

                for tipo in tipos:
                    # Peso definido por el docente para ese tipo de evaluación
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

                    # Evaluaciones del estudiante para ese tipo
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
                        detalle.append(
                            {
                                "tipo_evaluacion_id": tipo.id,
                                "promedio": round(promedio, 2),
                                "peso": peso.porcentaje,
                                "aporte": round(aporte, 2),
                            }
                        )

                nota_final = round(nota_final, 2)

                existente = (
                    db.query(RendimientoFinal)
                    .filter_by(
                        estudiante_id=estudiante_id,
                        materia_id=materia_id,
                        periodo_id=periodo_id,
                    )
                    .first()
                )

                if existente:
                    existente.nota_final = nota_final
                    existente.fecha_calculo = func.now()
                    db.commit()
                    db.refresh(existente)
                else:
                    existente = RendimientoFinal(
                        estudiante_id=estudiante_id,
                        materia_id=materia_id,
                        periodo_id=periodo_id,
                        nota_final=nota_final,
                    )
                    db.add(existente)
                    db.commit()
                    db.refresh(existente)

                resultados.append(
                    {
                        "materia_id": materia_id,
                        "estudiante_id": estudiante_id,
                        "periodo_id": periodo_id,
                        "nota_final": nota_final,
                        "detalle": detalle,
                    }
                )

    return resultados


@router.get(
    "/estudiante/{estudiante_id}/gestion/{gestion_id}", response_model=list[dict]
)
def listar_rendimientos_por_gestion(
    estudiante_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    from app.models import Periodo, RendimientoFinal, Materia

    # Obtener todos los periodos de la gestión
    periodos = db.query(Periodo).filter_by(gestion_id=gestion_id).all()
    if not periodos:
        raise HTTPException(status_code=404, detail="No hay periodos en esta gestión")

    periodo_dict = {p.id: p.nombre for p in periodos}
    periodo_ids = list(periodo_dict.keys())

    # Obtener todos los rendimientos del estudiante en los periodos
    rendimientos = (
        db.query(RendimientoFinal)
        .filter(
            RendimientoFinal.estudiante_id == estudiante_id,
            RendimientoFinal.periodo_id.in_(periodo_ids),
        )
        .all()
    )

    resultados = []

    for r in rendimientos:
        materia = db.query(Materia).filter_by(id=r.materia_id).first()

        resultados.append(
            {
                "materia_id": r.materia_id,
                "materia_nombre": materia.nombre if materia else "Desconocida",
                "periodo_id": r.periodo_id,
                "periodo_nombre": periodo_dict.get(r.periodo_id, "Desconocido"),
                "nota_final": r.nota_final,
                "fecha_calculo": r.fecha_calculo,
            }
        )

    return resultados


@router.get("/curso/{curso_id}/gestion/{gestion_id}", response_model=list[dict])
def rendimiento_final_curso_por_gestion(
    curso_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    from app.models import (
        Inscripcion,
        CursoMateria,
        DocenteMateria,
        Evaluacion,
        TipoEvaluacion,
        PesoTipoEvaluacion,
        RendimientoFinal,
        Periodo,
        Estudiante,
        Materia,
    )

    periodos = db.query(Periodo).filter_by(gestion_id=gestion_id).all()
    if not periodos:
        raise HTTPException(status_code=404, detail="No hay periodos en esta gestión")

    periodo_ids = [p.id for p in periodos]
    periodo_dict = {p.id: p.nombre for p in periodos}

    estudiantes = (
        db.query(Estudiante)
        .join(Inscripcion)
        .filter(Inscripcion.curso_id == curso_id, Inscripcion.gestion_id == gestion_id)
        .all()
    )

    if not estudiantes:
        raise HTTPException(
            status_code=404, detail="No hay estudiantes inscritos en este curso"
        )

    curso_materias = db.query(CursoMateria).filter_by(curso_id=curso_id).all()
    materia_ids = [cm.materia_id for cm in curso_materias]
    materias_dict = {
        m.id: m.nombre
        for m in db.query(Materia).filter(Materia.id.in_(materia_ids)).all()
    }

    tipos = db.query(TipoEvaluacion).all()
    resultados = []

    for estudiante in estudiantes:
        for materia_id in materia_ids:
            docente_materia = (
                db.query(DocenteMateria).filter_by(materia_id=materia_id).first()
            )
            if not docente_materia:
                continue
            docente_id = docente_materia.docente_id

            for periodo_id in periodo_ids:
                nota_final = 0.0
                total_peso = 0
                detalle = []

                for tipo in tipos:
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

                    evaluaciones = (
                        db.query(Evaluacion)
                        .filter_by(
                            estudiante_id=estudiante.id,
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
                        total_peso += peso.porcentaje
                        detalle.append(
                            {
                                "tipo_evaluacion_id": tipo.id,
                                "promedio": round(promedio, 2),
                                "peso": peso.porcentaje,
                                "aporte": round(aporte, 2),
                            }
                        )

                nota_final = round(nota_final, 2)

                # ✅ Guardar o actualizar en la tabla rendimiento_final
                existente = (
                    db.query(RendimientoFinal)
                    .filter_by(
                        estudiante_id=estudiante.id,
                        materia_id=materia_id,
                        periodo_id=periodo_id,
                    )
                    .first()
                )

                if existente:
                    existente.nota_final = nota_final
                    existente.fecha_calculo = func.now()
                    db.commit()
                    db.refresh(existente)
                else:
                    nuevo = RendimientoFinal(
                        estudiante_id=estudiante.id,
                        materia_id=materia_id,
                        periodo_id=periodo_id,
                        nota_final=nota_final,
                    )
                    db.add(nuevo)
                    db.commit()
                    db.refresh(nuevo)

                resultados.append(
                    {
                        "estudiante_id": estudiante.id,
                        "estudiante_nombre": f"{estudiante.nombre} {estudiante.apellido}",
                        "materia_id": materia_id,
                        "materia_nombre": materias_dict.get(materia_id, "Desconocida"),
                        "periodo_id": periodo_id,
                        "periodo_nombre": periodo_dict.get(periodo_id, "Desconocido"),
                        "nota_final": nota_final,
                        "detalle": detalle,
                    }
                )

    return resultados
