from sqlalchemy.orm import Session
from app.models.materia import Materia

def seed_materias(db: Session):
    materias = [
        # Materias para secundaria
        {"nombre": "Matemática Avanzada", "descripcion": "Álgebra, geometría, estadística y lógica."},
        {"nombre": "Lengua Castellana", "descripcion": "Expresión oral y escrita en lengua oficial."},
        {"nombre": "Física", "descripcion": "Leyes del movimiento, energía y materia."},
        {"nombre": "Química", "descripcion": "Propiedades y transformación de la materia."},
        {"nombre": "Biología", "descripcion": "Seres vivos, anatomía y medio ambiente."},
        {"nombre": "Inglés", "descripcion": "Lengua extranjera, comprensión y comunicación."},
        {"nombre": "Filosofía y Sociología", "descripcion": "Pensamiento crítico, sociedad y ética."},
        {"nombre": "Tecnología", "descripcion": "Herramientas digitales y técnicas prácticas."},
        {"nombre": "Educación Física", "descripcion": "Actividad física y salud integral."},
        {"nombre": "Artes Plásticas", "descripcion": "Creatividad, pintura, dibujo y expresión visual."},
    ]

    for mat in materias:
        existe = db.query(Materia).filter_by(nombre=mat["nombre"]).first()
        if not existe:
            db.add(Materia(**mat))

    db.commit()
    print("✅ Materias para secundaria insertadas.")
