from sqlalchemy import Column, DateTime, Integer, String, func
from app.database import Base
from sqlalchemy.orm import relationship


class Padre(Base):
    __tablename__ = "padres"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    genero = Column(String, nullable=False)
    contrasena = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación para acceder a hijos
    @property
    def hijos(self):
        return [rel.estudiante for rel in self.hijos_relacion]

    notificaciones_recibidas = relationship("Notificacion", back_populates="padre")
