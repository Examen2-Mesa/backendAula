from sqlalchemy import Column, DateTime, Integer, String, func
from app.database import Base


class TipoEvaluacion(Base):
    __tablename__ = "tipoevaluaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
