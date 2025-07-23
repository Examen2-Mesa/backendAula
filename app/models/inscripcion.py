from sqlalchemy import Column, DateTime, Integer, ForeignKey, Date, String, func
from app.database import Base
from sqlalchemy.orm import relationship


class Inscripcion(Base):
    __tablename__ = "inscripciones"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)

    estudiante_id = Column(
        Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False
    )
    curso_id = Column(
        Integer, ForeignKey("cursos.id", ondelete="CASCADE"), nullable=False
    )
    gestion_id = Column(
        Integer, ForeignKey("gestiones.id", ondelete="CASCADE"), nullable=False
    )

    estudiante = relationship("Estudiante", backref="inscripciones")
    curso = relationship("Curso", backref="inscripciones")
    gestion = relationship("Gestion", backref="inscripciones")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
