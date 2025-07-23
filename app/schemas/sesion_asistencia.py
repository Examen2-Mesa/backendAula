from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoSesion(str, Enum):
    ACTIVA = "activa"
    CERRADA = "cerrada"
    CANCELADA = "cancelada"


class MetodoMarcado(str, Enum):
    GPS = "gps"
    MANUAL = "manual"
    QR_CODE = "qr_code"


class EstadoAsistenciaEnum(str, Enum):
    PRESENTE = "presente"
    AUSENTE = "ausente"
    TARDANZA = "tardanza"
    JUSTIFICADO = "justificado"


# ================ SCHEMAS BASE ================


class SesionAsistenciaBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    curso_id: int
    materia_id: int
    periodo_id: Optional[int] = None
    duracion_minutos: int = Field(default=60, ge=10, le=300)  # Entre 10 min y 300 min
    radio_permitido_metros: int = Field(default=100, ge=10, le=100)  # Entre 10m y 100m
    permite_asistencia_tardia: bool = True
    minutos_tolerancia: int = Field(default=15, ge=0, le=60)


class AsistenciaEstudianteBase(BaseModel):
    presente: bool = False
    observaciones: Optional[str] = None
    justificado: bool = False
    motivo_justificacion: Optional[str] = None


# ================ SCHEMAS PARA CREAR ================


class SesionAsistenciaCreate(SesionAsistenciaBase):
    latitud_docente: float = Field(..., ge=-90, le=90)
    longitud_docente: float = Field(..., ge=-180, le=180)
    direccion_referencia: Optional[str] = None
    fecha_inicio: Optional[datetime] = None  # ← AÑADIR ESTE CAMPO

    @validator("titulo")
    def titulo_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El título no puede estar vacío")
        return v.strip()

    @validator("fecha_inicio", pre=True, always=True)
    def set_fecha_inicio_default(cls, v):
        """Si no se proporciona fecha_inicio, usar la fecha actual"""
        if v is None:
            return datetime.now()
        return v

    @validator("periodo_id")
    def validar_periodo_opcional(cls, v, values):
        """
        Si se proporciona periodo_id, debe ser válido.
        Si no se proporciona, se detectará automáticamente.
        """
        if v is not None and v <= 0:
            raise ValueError("El periodo_id debe ser un número positivo")
        return v


class MarcarAsistenciaRequest(BaseModel):
    """Request para que un estudiante marque su asistencia"""

    latitud_estudiante: float = Field(..., ge=-90, le=90)
    longitud_estudiante: float = Field(..., ge=-180, le=180)
    observaciones: Optional[str] = None

    @validator("latitud_estudiante", "longitud_estudiante")
    def coordenadas_validas(cls, v):
        if v == 0:
            raise ValueError("Las coordenadas no pueden ser 0,0")
        return v


class JustificarAusenciaRequest(BaseModel):
    """Request para justificar una ausencia"""

    motivo_justificacion: str = Field(..., min_length=10, max_length=500)
    observaciones: Optional[str] = None


# ================ SCHEMAS PARA ACTUALIZAR ================


class SesionAsistenciaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    duracion_minutos: Optional[int] = None
    radio_permitido_metros: Optional[int] = None
    permite_asistencia_tardia: Optional[bool] = None
    minutos_tolerancia: Optional[int] = None
    estado: Optional[EstadoSesion] = None


class AsistenciaEstudianteUpdate(AsistenciaEstudianteBase):
    presente: Optional[bool] = None
    es_tardanza: Optional[bool] = None
    justificado: Optional[bool] = None
    metodo_marcado: Optional[MetodoMarcado] = None


# ================ SCHEMAS DE RESPUESTA ================


class AsistenciaEstudianteOut(BaseModel):
    id: int
    sesion_id: int
    estudiante_id: int
    presente: bool
    fecha_marcado: Optional[datetime]
    latitud_estudiante: Optional[float]
    longitud_estudiante: Optional[float]
    distancia_metros: Optional[float]
    metodo_marcado: str
    observaciones: Optional[str]
    es_tardanza: bool
    justificado: bool
    motivo_justificacion: Optional[str]
    estado_asistencia: str
    dentro_del_rango: Optional[bool]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class SesionAsistenciaOut(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    docente_id: int
    curso_id: int
    materia_id: int
    periodo_id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    duracion_minutos: int
    latitud_docente: float
    longitud_docente: float
    direccion_referencia: Optional[str]
    radio_permitido_metros: int
    permite_asistencia_tardia: bool
    minutos_tolerancia: int
    estado: str
    estudiantes_presentes: int
    total_estudiantes_esperados: int
    esta_activa: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class SesionAsistenciaDetalle(SesionAsistenciaOut):
    """Sesión con lista de asistencias de estudiantes"""

    asistencias: List[AsistenciaEstudianteOut] = []

    class Config:
        from_attributes = True


# ================ SCHEMAS ESPECIALIZADOS ================


class EstudianteAsistencia(BaseModel):
    """Información básica del estudiante para mostrar en listas de asistencia"""

    id: int
    nombre: str
    apellido: str
    codigo: Optional[str] = None
    presente: bool = False
    es_tardanza: bool = False
    justificado: bool = False
    fecha_marcado: Optional[datetime] = None
    distancia_metros: Optional[float] = None
    estado_asistencia: str = "ausente"

    class Config:
        from_attributes = True


class ResumenAsistencia(BaseModel):
    """Resumen estadístico de una sesión de asistencia"""

    sesion_id: int
    titulo_sesion: str
    fecha_sesion: datetime
    total_estudiantes: int
    presentes: int
    ausentes: int
    tardanzas: int
    justificados: int
    porcentaje_asistencia: float
    estado_sesion: str

    class Config:
        from_attributes = True


class UbicacionDocente(BaseModel):
    """Información de ubicación del docente para estudiantes"""

    latitud: float
    longitud: float
    direccion_referencia: Optional[str]
    radio_permitido: int
    mensaje: str = "Ubicación del aula"

    class Config:
        from_attributes = True


# ================ RESPONSES COMPLEJAS ================


class SesionAsistenciaResponse(BaseModel):
    """Response estándar para operaciones de sesión"""

    success: bool
    message: str
    data: Optional[SesionAsistenciaOut] = None
    errors: Optional[List[str]] = None

    class Config:
        from_attributes = True


class MarcarAsistenciaResponse(BaseModel):
    """Response para marcar asistencia"""

    success: bool
    message: str
    asistencia_registrada: bool
    es_tardanza: bool
    distancia_metros: float
    dentro_del_rango: bool
    data: Optional[AsistenciaEstudianteOut] = None

    class Config:
        from_attributes = True


class ListaSesionesResponse(BaseModel):
    """Response para listar sesiones"""

    success: bool
    sesiones: List[SesionAsistenciaOut]
    total: int
    activas: int
    cerradas: int

    class Config:
        from_attributes = True


class ValidacionUbicacionResponse(BaseModel):
    """Response para validar si un estudiante puede marcar asistencia"""

    puede_marcar: bool
    distancia_metros: float
    dentro_del_rango: bool
    sesion_activa: bool
    mensaje: str
    tiempo_restante_minutos: Optional[int] = None

    class Config:
        from_attributes = True


from app.schemas.estudiante_info_academica import DocenteBasico, MateriaBasica


class SesionAsistenciaEstudianteOut(BaseModel):
    """Sesión de asistencia con información de materia y docente para estudiantes"""

    id: int
    titulo: str
    descripcion: Optional[str]
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    duracion_minutos: int
    radio_permitido_metros: int
    permite_asistencia_tardia: bool
    minutos_tolerancia: int
    estado: str
    esta_activa: bool
    fecha_creacion: datetime

    # Información adicional para estudiantes
    materia: Optional[MateriaBasica] = None
    docente: Optional[DocenteBasico] = None

    # Status de asistencia del estudiante
    mi_asistencia: Optional[AsistenciaEstudianteOut] = None

    # No usar from_attributes para este esquema
    class Config:
        # Removido from_attributes para evitar problemas con objetos dinámicos
        pass
