from sqlalchemy import Column, DateTime, Integer, String, func
from app.database import Base


class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    nivel = Column(String, nullable=False)  # Ejemplo: Primaria, Secundaria
    paralelo = Column(String, nullable=False)  # Ejemplo: A, B, C
    turno = Column(String, nullable=False)  # Ejemplo: Mañana, Tarde
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())