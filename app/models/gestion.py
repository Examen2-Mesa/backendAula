from sqlalchemy import Column, DateTime, Integer, String, func
from app.database import Base


class Gestion(Base):
    __tablename__ = "gestiones"

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(String, unique=True, nullable=False)  # Ej: "2024"
    descripcion = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
