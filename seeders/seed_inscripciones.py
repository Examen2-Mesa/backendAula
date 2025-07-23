from sqlalchemy.orm import Session
from app.models.estudiante import Estudiante
from app.models.curso import Curso
from app.models.gestion import Gestion
from app.models.inscripcion import Inscripcion
from datetime import date


def seed_inscripciones(db: Session):
    estudiantes = db.query(Estudiante).order_by(Estudiante.id).all()
    cursos = (
        db.query(Curso).filter(Curso.nivel == "Secundaria").order_by(Curso.id).all()
    )
    gestiones = db.query(Gestion).filter(Gestion.anio.in_(["2024", "2025"])).all()

    if len(gestiones) != 2:
        raise Exception("❌ Asegúrate de tener creadas las gestiones 2024 y 2025.")

    total_esperado = len(cursos) * 15
    if len(estudiantes) < total_esperado:
        raise Exception(
            f"❌ Se esperaban al menos {total_esperado} estudiantes para inscribirlos."
        )

    inscripciones = []
    idx = 0

    for gestion in gestiones:
        idx = 0
        for curso in cursos:
            for _ in range(15):
                estudiante = estudiantes[idx]
                inscripciones.append(
                    Inscripcion(
                        descripcion=f"Inscripción automática {gestion.anio}",
                        fecha=date.today(),
                        estudiante_id=estudiante.id,
                        curso_id=curso.id,
                        gestion_id=gestion.id,
                    )
                )
                idx += 1

    db.bulk_save_objects(inscripciones)
    db.commit()
    print(
        f"✅ Se generaron {len(inscripciones)} inscripciones para gestiones 2024 y 2025."
    )
