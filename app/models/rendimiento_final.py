from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class RendimientoFinal(Base):
    __tablename__ = "rendimiento_final"

    id = Column(Integer, primary_key=True, index=True)
    nota_final = Column(Float, nullable=False)
    fecha_calculo = Column(DateTime(timezone=True), server_default=func.now())

    estudiante_id = Column(
        Integer, ForeignKey("estudiantes.id", ondelete="CASCADE"), nullable=False
    )
    materia_id = Column(
        Integer, ForeignKey("materias.id", ondelete="CASCADE"), nullable=False
    )
    periodo_id = Column(
        Integer, ForeignKey("periodos.id", ondelete="CASCADE"), nullable=False
    )

    estudiante = relationship("Estudiante", backref="rendimientos")
    materia = relationship("Materia", backref="rendimientos")
    periodo = relationship("Periodo", backref="rendimientos")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
