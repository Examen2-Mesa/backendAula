from sqlalchemy.orm import Session
from app.models import (
    Estudiante,
    Curso,
    CursoMateria,
    Inscripcion,
    TipoEvaluacion,
    Evaluacion,
)
from datetime import timedelta
import random


def seed_evaluaciones(db: Session, periodo_id: int):
    from app.models.periodo import Periodo

    periodo = db.query(Periodo).filter_by(id=periodo_id).first()
    if not periodo:
        print(f"❌ No se encontró el periodo con id {periodo_id}")
        return

    print(f"🟡 Generando evaluaciones para el periodo: {periodo.nombre}")

    estudiantes = db.query(Estudiante).all()
    inscripciones = db.query(Inscripcion).filter_by(gestion_id=periodo.gestion_id).all()
    cursomaterias = db.query(CursoMateria).all()
    tipos = db.query(TipoEvaluacion).all()

    tipo_dict = {t.nombre.lower(): t.id for t in tipos}

    dias = (periodo.fecha_fin - periodo.fecha_inicio).days + 1
    fechas = [
        periodo.fecha_inicio + timedelta(days=i)
        for i in range(0, dias, max(dias // 30, 1))
    ]

    cantidad_por_tipo = {
        "asistencia": 10,
        "participaciones": 5,
        "tareas": 5,
        "prácticas": 5,
        "exposiciones": 2,
        "ensayos": 2,
        "cuestionarios": 5,
        "trabajo grupal": 1,
        "exámenes": 3,
        "proyecto final": 1,
    }

    evaluaciones_batch = []
    contador = 0

    for insc in inscripciones:
        curso_id = insc.curso_id
        estudiante_id = insc.estudiante_id
        materias_ids = [
            cm.materia_id for cm in cursomaterias if cm.curso_id == curso_id
        ]
        estudiante = db.query(Estudiante).get(estudiante_id)

        for materia_id in materias_ids:
            fechas_disponibles = fechas.copy()
            random.shuffle(fechas_disponibles)

            for tipo_nombre, max_cantidad in cantidad_por_tipo.items():
                fechas_usadas = fechas_disponibles[:max_cantidad]
                for f in fechas_usadas:
                    evaluaciones_batch.append(
                        Evaluacion(
                            fecha=f,
                            descripcion=tipo_nombre.capitalize(),
                            valor=(
                                round(random.uniform(50, 100), 2)
                                if tipo_nombre != "asistencia"
                                else random.choice([0, 50, 100])
                            ),
                            estudiante_id=estudiante_id,
                            materia_id=materia_id,
                            tipo_evaluacion_id=tipo_dict[tipo_nombre],
                            periodo_id=periodo.id,
                        )
                    )
                    contador += 1

                    if contador % 500 == 0:
                        db.add_all(evaluaciones_batch)
                        db.commit()
                        print(f"💾 Guardadas {contador} evaluaciones...")
                        evaluaciones_batch.clear()

    if evaluaciones_batch:
        db.add_all(evaluaciones_batch)
        db.commit()
        print(f"✅ Guardadas las últimas {len(evaluaciones_batch)} evaluaciones.")

    print(f"🎉 Evaluaciones completadas para el periodo: {periodo.nombre}")


from app.models.periodo import Periodo
from app.models.gestion import Gestion


def seed_evaluaciones_multiple_periodos(db: Session, anio: str):
    gestion = db.query(Gestion).filter_by(anio=anio).first()
    if not gestion:
        print(f"❌ Gestión {anio} no encontrada.")
        return

    periodos = db.query(Periodo).filter_by(gestion_id=gestion.id).all()
    for periodo in periodos:
        print(f"🟡 Generando evaluaciones para: {anio} - {periodo.nombre}")
        seed_evaluaciones(db, periodo.id)
