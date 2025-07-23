from sqlalchemy import Column, DateTime, Integer, Float, ForeignKey, func
from app.database import Base
from sqlalchemy.orm import relationship


class PesoTipoEvaluacion(Base):
    __tablename__ = "peso_tipo_evaluacion"

    id = Column(Integer, primary_key=True, index=True)
    porcentaje = Column(Float, nullable=False)

    docente_id = Column(
        Integer, ForeignKey("docentes.id", ondelete="CASCADE"), nullable=False
    )
    materia_id = Column(
        Integer, ForeignKey("materias.id", ondelete="CASCADE"), nullable=False
    )
    gestion_id = Column(
        Integer, ForeignKey("gestiones.id", ondelete="CASCADE"), nullable=False
    )
    tipo_evaluacion_id = Column(
        Integer, ForeignKey("tipoevaluaciones.id", ondelete="CASCADE"), nullable=False
    )

    docente = relationship("Docente", backref="pesos_tipo_evaluacion")
    materia = relationship("Materia", backref="pesos_tipo_evaluacion")
    gestion = relationship("Gestion", backref="pesos_tipo_evaluacion")
    tipo_evaluacion = relationship("TipoEvaluacion", backref="pesos_tipo_evaluacion")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
