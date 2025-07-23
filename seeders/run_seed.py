from app.database import SessionLocal

# Estructura académica
from seeders.seed_gestion import seed_gestion
from seeders.seed_materias import seed_materias
from seeders.seed_cursos import seed_cursos
from seeders.seed_curso_materia import seed_curso_materia

# Usuarios y relaciones
from seeders.seed_docentes import seed_docentes
from seeders.seed_docente_materia import seed_docente_materia
from seeders.seed_estudiantes import seed_estudiantes
from seeders.seed_padres import seed_padres
from seeders.seed_padre_estudiante import seed_padre_estudiante

# Evaluaciones y reglas
from seeders.seed_tipo_evaluacion import seed_tipo_evaluacion
from seeders.seed_peso_tipo_evaluacion import seed_peso_tipo_evaluacion
from seeders.seed_inscripciones import seed_inscripciones
from seeders.seed_evaluaciones_completo import seed_evaluaciones_multiple_periodos


def run():
    db = SessionLocal()

    # 1. Crear estructura académica
    seed_gestion(db)  # 2024 y 2025 con periodos
    seed_materias(db)  # Materias de secundaria
    seed_cursos(db)  # Cursos secundaria
    seed_curso_materia(db)  # Asignar materias a cursos

    # 2. Crear docentes, estudiantes y padres
    seed_docentes(db)  # Incluye admin
    seed_docente_materia(db)  # Vinculación docente-materia
    seed_estudiantes(db)  # 20 por curso secundaria
    seed_padres(db)
    seed_padre_estudiante(db)

    # 3. Evaluaciones y reglas de calificación
    seed_tipo_evaluacion(db)  # 10 tipos (asistencia, tareas, etc.)
    seed_peso_tipo_evaluacion(db)  # Para ambas gestiones

    # 4. Inscripciones y generación de evaluaciones para 2024 y 2025
    seed_inscripciones(db)
    seed_evaluaciones_multiple_periodos(db, "2024")
    seed_evaluaciones_multiple_periodos(db, "2025")

    db.close()
    print("🎓 Base de datos poblada con toda la información académica y de evaluación.")


if __name__ == "__main__":
    run()
