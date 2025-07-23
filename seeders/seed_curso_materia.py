from sqlalchemy.orm import Session
from app.models.curso import Curso
from app.models.materia import Materia
from app.models.curso_materia import CursoMateria


def seed_curso_materia(db: Session):
    cursos = db.query(Curso).filter(Curso.nivel == "Secundaria").all()
    materias = db.query(Materia).all()
    materias_map = {m.nombre: m.id for m in materias}

    total = 0
    for curso in cursos:
        for materia in materias:
            existe = (
                db.query(CursoMateria)
                .filter_by(curso_id=curso.id, materia_id=materia.id)
                .first()
            )
            if not existe:
                db.add(CursoMateria(curso_id=curso.id, materia_id=materia.id))
                total += 1

    db.commit()
    print(f"✅ Asignadas {total} relaciones curso-materia.")
