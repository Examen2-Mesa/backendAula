from sqlalchemy import Column, DateTime, Integer, String, Boolean, func
from app.database import Base
from sqlalchemy.orm import relationship


class Docente(Base):
    __tablename__ = "docentes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    genero = Column(String, nullable=False)
    contrasena = Column(String, nullable=False)
    is_doc = Column(Boolean, default=True)  # True = docente, False = admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sesiones_asistencia = relationship("SesionAsistencia", back_populates="docente")
