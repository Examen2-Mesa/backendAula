# app/utils/geolocalizacion.py
import math
from typing import Tuple, Dict, List
from dataclasses import dataclass


@dataclass
class Coordenada:
    """Clase para representar coordenadas geográficas"""

    latitud: float
    longitud: float

    def __post_init__(self):
        if not (-90 <= self.latitud <= 90):
            raise ValueError("Latitud debe estar entre -90 y 90")
        if not (-180 <= self.longitud <= 180):
            raise ValueError("Longitud debe estar entre -180 y 180")


@dataclass
class AreaGeografica:
    """Clase para representar un área geográfica circular"""

    centro: Coordenada
    radio_metros: int
    nombre: str = "Área"


class GeolocalizacionUtils:
    """Utilidades para cálculos geográficos y validaciones"""

    RADIO_TIERRA_METROS = 6371000  # Radio de la Tierra en metros

    @staticmethod
    def calcular_distancia_haversine(coord1: Coordenada, coord2: Coordenada) -> float:
        """
        Calcula la distancia entre dos coordenadas usando la fórmula Haversine
        Retorna la distancia en metros
        """
        lat1_rad = math.radians(coord1.latitud)
        lat2_rad = math.radians(coord2.latitud)
        delta_lat = math.radians(coord2.latitud - coord1.latitud)
        delta_lon = math.radians(coord2.longitud - coord1.longitud)

        a = math.sin(delta_lat / 2) * math.sin(delta_lat / 2) + math.cos(
            lat1_rad
        ) * math.cos(lat2_rad) * math.sin(delta_lon / 2) * math.sin(delta_lon / 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distancia = GeolocalizacionUtils.RADIO_TIERRA_METROS * c

        return round(distancia, 2)

    @staticmethod
    def punto_dentro_del_area(
        punto: Coordenada, area: AreaGeografica
    ) -> Tuple[bool, float]:
        """
        Verifica si un punto está dentro de un área geográfica
        Retorna (dentro_del_area, distancia_al_centro)
        """
        distancia = GeolocalizacionUtils.calcular_distancia_haversine(
            punto, area.centro
        )
        dentro = distancia <= area.radio_metros
        return dentro, distancia

    @staticmethod
    def calcular_area_cobertura(radio_metros: int) -> Dict[str, float]:
        """
        Calcula el área de cobertura en diferentes unidades
        """
        area_m2 = math.pi * (radio_metros**2)
        area_hectareas = area_m2 / 10000

        return {
            "radio_metros": radio_metros,
            "area_metros_cuadrados": round(area_m2, 2),
            "area_hectareas": round(area_hectareas, 4),
            "diametro_metros": radio_metros * 2,
        }

    @staticmethod
    def generar_puntos_circulo(
        centro: Coordenada, radio_metros: int, num_puntos: int = 16
    ) -> List[Coordenada]:
        """
        Genera puntos alrededor de un círculo para visualización
        Útil para mostrar el área de cobertura en mapas
        """
        puntos = []

        for i in range(num_puntos):
            angulo = 2 * math.pi * i / num_puntos

            # Calcular offset en metros
            delta_lat = (
                radio_metros
                * math.cos(angulo)
                / GeolocalizacionUtils.RADIO_TIERRA_METROS
                * 180
                / math.pi
            )
            delta_lon = (
                radio_metros
                * math.sin(angulo)
                / (
                    GeolocalizacionUtils.RADIO_TIERRA_METROS
                    * math.cos(math.radians(centro.latitud))
                )
                * 180
                / math.pi
            )

            nueva_coord = Coordenada(
                latitud=centro.latitud + delta_lat, longitud=centro.longitud + delta_lon
            )
            puntos.append(nueva_coord)

        return puntos

    @staticmethod
    def obtener_distancia_recomendada_por_tipo_lugar(tipo_lugar: str) -> int:
        """
        Retorna el radio recomendado según el tipo de lugar
        """
        radios_recomendados = {
            "aula_pequena": 20,  # Aula pequeña
            "aula_normal": 50,  # Aula estándar
            "aula_magna": 100,  # Aula magna o auditorio
            "laboratorio": 30,  # Laboratorio
            "biblioteca": 75,  # Biblioteca
            "patio": 150,  # Patio o área abierta
            "cancha_deportes": 200,  # Cancha deportiva
            "exterior": 100,  # Área exterior general
        }

        return radios_recomendados.get(tipo_lugar, 100)  # Default 100m

    @staticmethod
    def validar_coordenadas_bolivia(coord: Coordenada) -> bool:
        """
        Valida si las coordenadas están dentro del territorio boliviano (aproximado)
        """
        # Límites aproximados de Bolivia
        lat_min, lat_max = -22.9, -9.7
        lon_min, lon_max = -69.6, -57.5

        return (
            lat_min <= coord.latitud <= lat_max and lon_min <= coord.longitud <= lon_max
        )

    @staticmethod
    def obtener_precision_gps_metros(precision_gps: float) -> str:
        """
        Convierte la precisión GPS en metros a una descripción legible
        """
        if precision_gps <= 3:
            return "Excelente (≤ 3m)"
        elif precision_gps <= 5:
            return "Muy buena (≤ 5m)"
        elif precision_gps <= 10:
            return "Buena (≤ 10m)"
        elif precision_gps <= 20:
            return "Regular (≤ 20m)"
        else:
            return f"Baja ({precision_gps:.0f}m)"


class ValidadorUbicacion:
    """Clase para validar ubicaciones en el contexto educativo"""

    @staticmethod
    def validar_ubicacion_docente(
        coord: Coordenada, nombre_institucion: str = ""
    ) -> Dict:
        """
        Valida la ubicación del docente al crear una sesión
        """
        resultado = {"valida": True, "advertencias": [], "errores": []}

        # Validar que esté en Bolivia
        if not GeolocalizacionUtils.validar_coordenadas_bolivia(coord):
            resultado["advertencias"].append(
                "La ubicación parece estar fuera de Bolivia"
            )

        # Validar coordenadas válidas (no 0,0)
        if coord.latitud == 0 and coord.longitud == 0:
            resultado["valida"] = False
            resultado["errores"].append("Coordenadas inválidas (0,0)")

        # Validar precisión mínima (esto se haría con datos adicionales del GPS)
        # Por ahora solo validamos que las coordenadas sean razonables

        return resultado

    @staticmethod
    def validar_ubicacion_estudiante(
        coord_estudiante: Coordenada,
        coord_docente: Coordenada,
        radio_permitido: int,
        precision_gps: float = None,
    ) -> Dict:
        """
        Valida la ubicación del estudiante al marcar asistencia
        """
        distancia = GeolocalizacionUtils.calcular_distancia_haversine(
            coord_estudiante, coord_docente
        )

        dentro_del_rango = distancia <= radio_permitido

        resultado = {
            "puede_marcar": dentro_del_rango,
            "distancia_metros": distancia,
            "radio_permitido": radio_permitido,
            "diferencia_metros": distancia - radio_permitido,
            "advertencias": [],
            "sugerencias": [],
        }

        if not dentro_del_rango:
            metros_faltantes = distancia - radio_permitido
            resultado["sugerencias"].append(
                f"Acércate {metros_faltantes:.0f}m más al aula"
            )

        # Verificar precisión GPS si está disponible
        if precision_gps and precision_gps > 10:
            resultado["advertencias"].append(
                f"Precisión GPS baja ({precision_gps:.0f}m). Busca mejor señal."
            )

        # Sugerencias adicionales
        if distancia > radio_permitido * 2:
            resultado["sugerencias"].append("Verifica que estés en el lugar correcto")

        return resultado


# ================ CONFIGURACIONES PREDEFINIDAS ================


class ConfiguracionesAsistencia:
    """Configuraciones predefinidas para diferentes escenarios"""

    CONFIGURACIONES_PREDEFINIDAS = {
        "aula_pequena": {
            "radio_metros": 20,
            "minutos_tolerancia": 10,
            "permite_asistencia_tardia": True,
            "descripcion": "Aula pequeña (20-30 estudiantes)",
        },
        "aula_normal": {
            "radio_metros": 50,
            "minutos_tolerancia": 15,
            "permite_asistencia_tardia": True,
            "descripcion": "Aula estándar (30-50 estudiantes)",
        },
        "aula_magna": {
            "radio_metros": 100,
            "minutos_tolerancia": 20,
            "permite_asistencia_tardia": True,
            "descripcion": "Aula magna o auditorio (50+ estudiantes)",
        },
        "laboratorio": {
            "radio_metros": 30,
            "minutos_tolerancia": 5,
            "permite_asistencia_tardia": False,
            "descripcion": "Laboratorio (requiere puntualidad)",
        },
        "campo_abierto": {
            "radio_metros": 200,
            "minutos_tolerancia": 30,
            "permite_asistencia_tardia": True,
            "descripcion": "Área abierta o deportiva",
        },
        "estricto": {
            "radio_metros": 25,
            "minutos_tolerancia": 0,
            "permite_asistencia_tardia": False,
            "descripcion": "Configuración estricta (exámenes, evaluaciones)",
        },
    }

    @classmethod
    def obtener_configuracion(cls, tipo: str) -> Dict:
        """Obtiene una configuración predefinida"""
        return cls.CONFIGURACIONES_PREDEFINIDAS.get(
            tipo, cls.CONFIGURACIONES_PREDEFINIDAS["aula_normal"]
        )

    @classmethod
    def listar_configuraciones(cls) -> Dict:
        """Lista todas las configuraciones disponibles"""
        return cls.CONFIGURACIONES_PREDEFINIDAS


# ================ MIGRACIÓN DE BASE DE DATOS ================

# app/alembic/versions/add_sesion_asistencia_tables.py
"""
Añade las tablas para sesiones de asistencia con geolocalización

Revision ID: sesion_asistencia_001
Revises: [revision_anterior]
Create Date: 2025-01-16 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# Revision identifiers
revision = "sesion_asistencia_001"
down_revision = "[revision_anterior]"  # Reemplazar con la revisión anterior
branch_labels = None
depends_on = None


def upgrade():
    """Crear las tablas para sesiones de asistencia"""

    # Tabla sesiones_asistencia
    op.create_table(
        "sesiones_asistencia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("docente_id", sa.Integer(), nullable=False),
        sa.Column("curso_id", sa.Integer(), nullable=False),
        sa.Column("materia_id", sa.Integer(), nullable=False),
        sa.Column("periodo_id", sa.Integer(), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(), nullable=True),
        sa.Column("duracion_minutos", sa.Integer(), nullable=False, default=60),
        sa.Column("latitud_docente", sa.Float(), nullable=False),
        sa.Column("longitud_docente", sa.Float(), nullable=False),
        sa.Column("direccion_referencia", sa.String(500), nullable=True),
        sa.Column("radio_permitido_metros", sa.Integer(), nullable=False, default=100),
        sa.Column(
            "permite_asistencia_tardia", sa.Boolean(), nullable=False, default=True
        ),
        sa.Column("minutos_tolerancia", sa.Integer(), nullable=False, default=15),
        sa.Column("estado", sa.String(20), nullable=False, default="activa"),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["docente_id"], ["docentes.id"]),
        sa.ForeignKeyConstraint(["curso_id"], ["cursos.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["periodo_id"], ["periodos.id"]),
    )

    # Tabla asistencias_estudiantes
    op.create_table(
        "asistencias_estudiantes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sesion_id", sa.Integer(), nullable=False),
        sa.Column("estudiante_id", sa.Integer(), nullable=False),
        sa.Column("presente", sa.Boolean(), nullable=False, default=False),
        sa.Column("fecha_marcado", sa.DateTime(), nullable=True),
        sa.Column("latitud_estudiante", sa.Float(), nullable=True),
        sa.Column("longitud_estudiante", sa.Float(), nullable=True),
        sa.Column("distancia_metros", sa.Float(), nullable=True),
        sa.Column("metodo_marcado", sa.String(20), nullable=False, default="gps"),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("es_tardanza", sa.Boolean(), nullable=False, default=False),
        sa.Column("justificado", sa.Boolean(), nullable=False, default=False),
        sa.Column("motivo_justificacion", sa.String(500), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["sesion_id"], ["sesiones_asistencia.id"]),
        sa.ForeignKeyConstraint(["estudiante_id"], ["estudiantes.id"]),
    )

    # Índices para optimizar consultas
    op.create_index(
        "idx_sesiones_docente_estado", "sesiones_asistencia", ["docente_id", "estado"]
    )
    op.create_index(
        "idx_sesiones_curso_materia", "sesiones_asistencia", ["curso_id", "materia_id"]
    )
    op.create_index(
        "idx_sesiones_fecha_inicio", "sesiones_asistencia", ["fecha_inicio"]
    )
    op.create_index(
        "idx_asistencias_sesion_estudiante",
        "asistencias_estudiantes",
        ["sesion_id", "estudiante_id"],
    )
    op.create_index("idx_asistencias_presente", "asistencias_estudiantes", ["presente"])


def downgrade():
    """Eliminar las tablas de sesiones de asistencia"""
    op.drop_index("idx_asistencias_presente", table_name="asistencias_estudiantes")
    op.drop_index(
        "idx_asistencias_sesion_estudiante", table_name="asistencias_estudiantes"
    )
    op.drop_index("idx_sesiones_fecha_inicio", table_name="sesiones_asistencia")
    op.drop_index("idx_sesiones_curso_materia", table_name="sesiones_asistencia")
    op.drop_index("idx_sesiones_docente_estado", table_name="sesiones_asistencia")

    op.drop_table("asistencias_estudiantes")
    op.drop_table("sesiones_asistencia")
