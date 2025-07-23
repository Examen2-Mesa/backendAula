from sqlalchemy import Column, DateTime, Integer, ForeignKey, func
from app.database import Base
from sqlalchemy.orm import relationship


class PadreEstudiante(Base):
    __tablename__ = "padre_estudiante"

    id = Column(Integer, primary_key=True, index=True)
    padre_id = Column(
        Integer, ForeignKey("padres.id", ondelete="CASCADE"), nullable=False
    )
    estudiante_id = Column(
        Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False
    )

    padre = relationship("Padre", backref="hijos_relacion")
    estudiante = relationship("Estudiante", backref="padres_relacion")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
