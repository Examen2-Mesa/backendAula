from sqlalchemy.orm import Session
from app.models.tipo_evaluacion import TipoEvaluacion


def seed_tipo_evaluacion(db: Session):
    tipos = [
        "Asistencia",
        "Participaciones",
        "Tareas",
        "Prácticas",
        "Exposiciones",
        "Ensayos",
        "Cuestionarios",
        "Trabajo grupal",
        "Exámenes",
        "Proyecto final",
    ]

    for nombre in tipos:
        existe = db.query(TipoEvaluacion).filter_by(nombre=nombre).first()
        if not existe:
            db.add(TipoEvaluacion(nombre=nombre))

    db.commit()
    print("✅ Tipos de evaluación registrados.")
