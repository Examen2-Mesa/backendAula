from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime, timedelta


class SesionAsistencia(Base):
    """
    Modelo para sesiones de asistencia creadas por el docente
    El docente establece su ubicación y los estudiantes deben estar cerca para marcar asistencia
    """

    __tablename__ = "sesiones_asistencia"

    id = Column(Integer, primary_key=True, index=True)

    # Información básica de la sesión
    titulo = Column(String(200), nullable=False)  # Ej: "Matemáticas - Clase 1"
    descripcion = Column(Text, nullable=True)  # Descripción opcional

    # Relaciones con otras tablas
    docente_id = Column(Integer, ForeignKey("docentes.id"), nullable=False)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    materia_id = Column(Integer, ForeignKey("materias.id"), nullable=False)
    periodo_id = Column(Integer, ForeignKey("periodos.id"), nullable=False)

    # Fechas y tiempos
    fecha_inicio = Column(DateTime, nullable=False, default=func.now())
    fecha_fin = Column(DateTime, nullable=True)  # Cuando el docente cierra la sesión
    duracion_minutos = Column(Integer, default=60)  # Duración estimada en minutos

    # Geolocalización del docente
    latitud_docente = Column(Float, nullable=False)  # Ubicación del docente
    longitud_docente = Column(Float, nullable=False)  # Ubicación del docente
    direccion_referencia = Column(String(500), nullable=True)  # Dirección de referencia

    # Configuración de la sesión
    radio_permitido_metros = Column(
        Integer, default=100
    )  # Radio en metros (100m por defecto)
    permite_asistencia_tardia = Column(
        Boolean, default=True
    )  # Si permite marcar después de inicio
    minutos_tolerancia = Column(
        Integer, default=15
    )  # Minutos de tolerancia para llegada tardía

    # Estado de la sesión
    estado = Column(String(20), default="activa")  # activa, cerrada, cancelada

    # Metadata
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    docente = relationship("Docente", back_populates="sesiones_asistencia")
    curso = relationship("Curso")
    materia = relationship("Materia")
    periodo = relationship("Periodo")
    asistencias = relationship("AsistenciaEstudiante", back_populates="sesion")

    def __repr__(self):
        return f"<SesionAsistencia(id={self.id}, titulo='{self.titulo}', estado='{self.estado}')>"

    @property
    def esta_activa(self):
        """Verifica si la sesión está activa y dentro del tiempo permitido"""
        if self.estado != "activa":
            return False

        now = datetime.now()

        # Verificar si no ha pasado el tiempo límite
        if self.fecha_fin and now > self.fecha_fin:
            return False

        # Verificar tolerancia para asistencia tardía
        if not self.permite_asistencia_tardia:
            return now <= self.fecha_inicio

        # ✅ Usar timedelta en lugar de modificar el minuto directamente

        tiempo_limite = self.fecha_inicio + timedelta(minutes=self.minutos_tolerancia)
        return now <= tiempo_limite

    @property
    def estudiantes_presentes(self):
        """Cuenta cuántos estudiantes han marcado asistencia"""
        return len([a for a in self.asistencias if a.presente])

    @property
    def total_estudiantes_esperados(self):
        """Total de estudiantes esperados (calculado desde inscripciones)"""
        # Este valor debería calcularse basado en las inscripciones del curso
        return len(self.asistencias)


class AsistenciaEstudiante(Base):
    """
    Modelo para registrar la asistencia de cada estudiante a una sesión específica
    """

    __tablename__ = "asistencias_estudiantes"

    id = Column(Integer, primary_key=True, index=True)

    # Relaciones
    sesion_id = Column(Integer, ForeignKey("sesiones_asistencia.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)

    # Estado de asistencia
    presente = Column(Boolean, default=False)
    fecha_marcado = Column(DateTime, nullable=True)  # Cuando marcó asistencia

    # Ubicación del estudiante al marcar
    latitud_estudiante = Column(Float, nullable=True)
    longitud_estudiante = Column(Float, nullable=True)
    distancia_metros = Column(Float, nullable=True)  # Distancia calculada al docente

    # Detalles adicionales
    metodo_marcado = Column(String(20), default="gps")  # gps, manual, qr_code (futuro)
    observaciones = Column(Text, nullable=True)  # Notas adicionales

    # Estados especiales
    es_tardanza = Column(Boolean, default=False)  # Si llegó tarde
    justificado = Column(Boolean, default=False)  # Si la ausencia está justificada
    motivo_justificacion = Column(String(500), nullable=True)

    # Metadata
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    sesion = relationship("SesionAsistencia", back_populates="asistencias")
    estudiante = relationship("Estudiante")

    def __repr__(self):
        return f"<AsistenciaEstudiante(id={self.id}, estudiante_id={self.estudiante_id}, presente={self.presente})>"

    @property
    def estado_asistencia(self):
        """Retorna el estado de asistencia como string"""
        if not self.presente:
            return "justificado" if self.justificado else "ausente"
        return "tardanza" if self.es_tardanza else "presente"

    @property
    def dentro_del_rango(self):
        """Verifica si el estudiante estaba dentro del rango permitido"""
        if not self.distancia_metros:
            return None
        return self.distancia_metros <= self.sesion.radio_permitido_metros
