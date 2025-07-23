from sqlalchemy import Column, DateTime, Integer, String, Date, func
from app.database import Base
from sqlalchemy.orm import relationship


class Estudiante(Base):
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String, nullable=False)
    url_imagen = Column(String)
    nombre_tutor = Column(String, nullable=True)
    telefono_tutor = Column(String, nullable=True)
    direccion_casa = Column(String, nullable=True)
    # 🆕 NUEVOS: Campos para login unificado
    correo = Column(String, unique=True, nullable=True)  # Opcional para estudiantes
    contrasena = Column(String, nullable=True)  # Opcional para estudiantes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 🆕 Relación para acceder a padres
    @property
    def padres(self):
        return [rel.padre for rel in self.padres_relacion]

    notificaciones_generadas = relationship("Notificacion", back_populates="estudiante")
