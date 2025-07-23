from sqlalchemy.orm import Session
from app.models.docente_materia import DocenteMateria
from app.models.tipo_evaluacion import TipoEvaluacion
from app.models.gestion import Gestion
from app.models.peso_tipo_evaluacion import PesoTipoEvaluacion


def seed_peso_tipo_evaluacion(db: Session):
    gestiones = db.query(Gestion).filter(Gestion.anio.in_(["2024", "2025"])).all()
    if len(gestiones) != 2:
        print("❌ Faltan las gestiones 2024 y 2025.")
        return

    tipo_evals = db.query(TipoEvaluacion).all()
    tipos_dict = {t.nombre.lower(): t.id for t in tipo_evals}
    docente_materias = db.query(DocenteMateria).all()

    # Pesos definidos por tipo de evaluación
    pesos = {
        "asistencia": 5,
        "participaciones": 10,
        "tareas": 10,
        "prácticas": 10,
        "exposiciones": 10,
        "ensayos": 5,
        "cuestionarios": 5,
        "trabajo grupal": 5,
        "exámenes": 30,
        "proyecto final": 10,
    }

    total = 0
    for gestion in gestiones:
        for dm in docente_materias:
            for nombre_tipo, peso in pesos.items():
                tipo_id = tipos_dict.get(nombre_tipo)
                if tipo_id:
                    ya_existe = (
                        db.query(PesoTipoEvaluacion)
                        .filter_by(
                            docente_id=dm.docente_id,
                            materia_id=dm.materia_id,
                            gestion_id=gestion.id,
                            tipo_evaluacion_id=tipo_id,
                        )
                        .first()
                    )
                    if not ya_existe:
                        nuevo = PesoTipoEvaluacion(
                            porcentaje=peso,
                            docente_id=dm.docente_id,
                            materia_id=dm.materia_id,
                            gestion_id=gestion.id,
                            tipo_evaluacion_id=tipo_id,
                        )
                        db.add(nuevo)
                        total += 1

    db.commit()
    print(f"🎯 Se asignaron {total} pesos de tipo de evaluación para 2024 y 2025.")
