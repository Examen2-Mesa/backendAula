from sqlalchemy.orm import Session
from app.models.curso import Curso


def seed_cursos(db: Session):
    grados = [f"{i}° Secundaria" for i in range(1, 7)]
    paralelo = "A"
    turno = "Tarde"

    for grado in grados:
        nombre = f"{grado} {paralelo} - {turno}"
        existe = db.query(Curso).filter_by(nombre=nombre).first()
        if not existe:
            db.add(
                Curso(nombre=nombre, nivel="Secundaria", paralelo=paralelo, turno=turno)
            )

    db.commit()
    print("✅ Cursos nivel secundaria (1 paralelo, turno tarde) creados.")
