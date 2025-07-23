from sqlalchemy import Column, DateTime, Integer, Float, String, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    descripcion = Column(String, nullable=False)
    valor = Column(Float, nullable=False)

    estudiante_id = Column(
        Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False
    )
    materia_id = Column(
        Integer, ForeignKey("materias.id", ondelete="CASCADE"), nullable=False
    )
    tipo_evaluacion_id = Column(
        Integer, ForeignKey("tipoevaluaciones.id", ondelete="CASCADE"), nullable=False
    )
    periodo_id = Column(
        Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False
    )

    estudiante = relationship("Estudiante", backref="evaluaciones")
    materia = relationship("Materia", backref="evaluaciones")
    tipo_evaluacion = relationship("TipoEvaluacion", backref="evaluaciones")
    periodo = relationship("Periodo", backref="evaluaciones")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    notificaciones = relationship("Notificacion", back_populates="evaluacion")

