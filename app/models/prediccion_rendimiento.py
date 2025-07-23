from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, func
from app.database import Base
from sqlalchemy.orm import relationship


class PrediccionRendimiento(Base):
    __tablename__ = "prediccion_rendimiento"

    id = Column(Integer, primary_key=True, index=True)
    promedio_notas = Column(Float, nullable=False)
    porcentaje_asistencia = Column(Float, nullable=False)
    promedio_participacion = Column(Float, nullable=False)
    resultado_numerico = Column(Float, nullable=False)
    clasificacion = Column(String, nullable=False)
    fecha_generada = Column(DateTime(timezone=True), server_default=func.now())

    estudiante_id = Column(
        Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False
    )
    materia_id = Column(
        Integer, ForeignKey("materias.id", ondelete="CASCADE"), nullable=False
    )
    periodo_id = Column(
        Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False
    )

    estudiante = relationship("Estudiante", backref="predicciones")
    materia = relationship("Materia", backref="predicciones")
    periodo = relationship("Periodo", backref="predicciones")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
