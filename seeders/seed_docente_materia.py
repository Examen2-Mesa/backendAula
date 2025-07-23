from sqlalchemy.orm import Session
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.docente_materia import DocenteMateria


def seed_docente_materia(db: Session):
    docentes = db.query(Docente).filter(Docente.is_doc == True).all()
    materias = db.query(Materia).all()

    asignaciones = []
    for i in range(min(len(docentes), len(materias))):
        docente = docentes[i]
        materia = materias[i]

        ya_existe = (
            db.query(DocenteMateria)
            .filter_by(docente_id=docente.id, materia_id=materia.id)
            .first()
        )
        if not ya_existe:
            asignaciones.append(
                DocenteMateria(docente_id=docente.id, materia_id=materia.id)
            )

    db.bulk_save_objects(asignaciones)
    db.commit()
    print(f"✅ Asignadas {len(asignaciones)} materias a docentes.")
