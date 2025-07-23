from sqlalchemy.orm import Session
from app.models.padre import Padre
from app.models.estudiante import Estudiante
from app.models.padre_estudiante import PadreEstudiante


def seed_padre_estudiante(db: Session):
    padres = db.query(Padre).all()
    estudiantes = db.query(Estudiante).all()

    relaciones = []
    for i, estudiante in enumerate(estudiantes):
        padre = padres[i % len(padres)]
        relaciones.append(
            PadreEstudiante(padre_id=padre.id, estudiante_id=estudiante.id)
        )

    db.bulk_save_objects(relaciones)
    db.commit()
    print(f"👨‍👧 Relaciones padre-estudiante creadas: {len(relaciones)}")
