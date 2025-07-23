from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(
        String, nullable=False
    )  # 'calificacion_baja', 'evaluacion', 'general'
    leida = Column(Boolean, default=False)

    # Relaciones
    padre_id = Column(Integer, ForeignKey("padres.id"), nullable=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    evaluacion_id = Column(Integer, ForeignKey("evaluaciones.id"), nullable=True)

    # NUEVO: Campo para indicar si la notificación es para el estudiante directamente
    para_estudiante = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones ORM bidireccionales
    padre = relationship("Padre", back_populates="notificaciones_recibidas")
    estudiante = relationship("Estudiante", back_populates="notificaciones_generadas")
    evaluacion = relationship("Evaluacion", back_populates="notificaciones")

    def __repr__(self):
        return f"<Notificacion(id={self.id}, tipo='{self.tipo}', leida={self.leida})>"
