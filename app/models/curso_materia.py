from sqlalchemy import Column, DateTime, Integer, ForeignKey, func
from app.database import Base
from sqlalchemy.orm import relationship


class CursoMateria(Base):
    __tablename__ = "curso_materia"

    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(
        Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False
    )
    materia_id = Column(
        Integer, ForeignKey("materias.id", ondelete="CASCADE"), nullable=False
    )

    curso = relationship("Curso", backref="materias_asignadas")
    materia = relationship("Materia", backref="cursos_asignados")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
