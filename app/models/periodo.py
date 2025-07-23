from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Date,
    ForeignKey,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Periodo(Base):
    __tablename__ = "periodos"
    __table_args__ = (
        UniqueConstraint("nombre", "gestion_id", name="uq_nombre_gestion"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    gestion_id = Column(
        Integer, ForeignKey("gestiones.id", ondelete="CASCADE"), nullable=False
    )

    gestion = relationship("Gestion", backref="periodos")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
