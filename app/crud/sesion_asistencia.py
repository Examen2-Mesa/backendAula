from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from app.models.sesion_asistencia import SesionAsistencia, AsistenciaEstudiante
from app.models.inscripcion import Inscripcion
from app.models.estudiante import Estudiante
from app.models.evaluacion import Evaluacion
from app.models.tipo_evaluacion import TipoEvaluacion
from app.schemas.sesion_asistencia import (
    SesionAsistenciaCreate,
    SesionAsistenciaUpdate,
    MarcarAsistenciaRequest,
    JustificarAusenciaRequest,
)
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import math


# ================ UTILIDADES GEOGRÁFICAS ================


def calcular_distancia_haversine(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula Haversine
    Retorna la distancia en metros
    """
    # Radio de la Tierra en metros
    R = 6371000

    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Fórmula Haversine
    a = math.sin(delta_lat / 2) * math.sin(delta_lat / 2) + math.cos(
        lat1_rad
    ) * math.cos(lat2_rad) * math.sin(delta_lon / 2) * math.sin(delta_lon / 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distancia = R * c

    return round(distancia, 2)


def validar_ubicacion_estudiante(
    lat_docente: float,
    lon_docente: float,
    lat_estudiante: float,
    lon_estudiante: float,
    radio_permitido: int,
) -> Tuple[float, bool]:
    """
    Valida si un estudiante está dentro del rango permitido
    Retorna (distancia_metros, dentro_del_rango)
    """
    distancia = calcular_distancia_haversine(
        lat_docente, lon_docente, lat_estudiante, lon_estudiante
    )
    dentro_del_rango = distancia <= radio_permitido
    return distancia, dentro_del_rango


# ================ CRUD SESIONES DE ASISTENCIA ================


def crear_sesion_asistencia(
    db: Session, datos: SesionAsistenciaCreate, docente_id: int
) -> SesionAsistencia:
    """Crear una nueva sesión de asistencia con detección automática de periodo"""

    # Convertir los datos a dict para poder modificarlos
    datos_dict = datos.dict()

    # Si no se proporciona periodo_id, detectarlo automáticamente
    if not datos_dict.get("periodo_id"):
        try:
            periodo_id, gestion_id = obtener_periodo_y_gestion_por_fecha(
                db, datos.fecha_inicio or datetime.now()
            )
            datos_dict["periodo_id"] = periodo_id

            print(
                f"🔍 Periodo detectado automáticamente: {periodo_id} (Gestión: {gestion_id})"
            )

        except ValueError as e:
            raise ValueError(f"Error al detectar periodo automáticamente: {str(e)}")

    # Verificar que no haya otra sesión activa para la misma materia y curso
    sesion_existente = (
        db.query(SesionAsistencia)
        .filter(
            and_(
                SesionAsistencia.docente_id == docente_id,
                SesionAsistencia.curso_id == datos_dict["curso_id"],
                SesionAsistencia.materia_id == datos_dict["materia_id"],
                SesionAsistencia.estado == "activa",
            )
        )
        .first()
    )

    if sesion_existente:
        raise ValueError("Ya existe una sesión activa para esta materia y curso")

    # Crear la sesión con el periodo detectado
    sesion = SesionAsistencia(**datos_dict, docente_id=docente_id)

    db.add(sesion)
    db.commit()
    db.refresh(sesion)

    # Crear registros de asistencia para todos los estudiantes inscritos
    crear_registros_asistencia_estudiantes(db, sesion)

    return sesion


def crear_registros_asistencia_estudiantes(db: Session, sesion: SesionAsistencia):
    """Crear registros de asistencia para todos los estudiantes del curso"""

    # Obtener estudiantes inscritos en el curso
    inscripciones = (
        db.query(Inscripcion).filter(Inscripcion.curso_id == sesion.curso_id).all()
    )

    for inscripcion in inscripciones:
        asistencia = AsistenciaEstudiante(
            sesion_id=sesion.id, estudiante_id=inscripcion.estudiante_id, presente=False
        )
        db.add(asistencia)

    db.commit()


def obtener_sesiones_docente(
    db: Session,
    docente_id: int,
    estado: Optional[str] = None,
    curso_id: Optional[int] = None,
    materia_id: Optional[int] = None,
    limite: int = 50,
) -> List[SesionAsistencia]:
    """Obtener sesiones de asistencia de un docente"""

    query = db.query(SesionAsistencia).filter(SesionAsistencia.docente_id == docente_id)

    if estado:
        query = query.filter(SesionAsistencia.estado == estado)

    if curso_id:
        query = query.filter(SesionAsistencia.curso_id == curso_id)

    if materia_id:
        query = query.filter(SesionAsistencia.materia_id == materia_id)

    return query.order_by(desc(SesionAsistencia.fecha_inicio)).limit(limite).all()


def obtener_sesion_por_id(
    db: Session, sesion_id: int, incluir_asistencias: bool = False
) -> Optional[SesionAsistencia]:
    """Obtener una sesión específica por ID"""

    query = db.query(SesionAsistencia)

    if incluir_asistencias:
        query = query.options(
            joinedload(SesionAsistencia.asistencias).joinedload(
                AsistenciaEstudiante.estudiante
            )
        )

    return query.filter(SesionAsistencia.id == sesion_id).first()


def actualizar_sesion_asistencia(
    db: Session, sesion_id: int, datos: SesionAsistenciaUpdate
) -> Optional[SesionAsistencia]:
    """Actualizar una sesión de asistencia"""

    sesion = db.query(SesionAsistencia).filter(SesionAsistencia.id == sesion_id).first()

    if not sesion:
        return None

    # Actualizar solo los campos proporcionados
    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(sesion, campo, valor)

    sesion.fecha_actualizacion = datetime.now()

    db.commit()
    db.refresh(sesion)

    return sesion


def cerrar_sesion_asistencia(db: Session, sesion_id: int) -> Optional[SesionAsistencia]:
    """Cerrar una sesión de asistencia y sincronizar con el sistema de evaluaciones"""

    sesion = obtener_sesion_por_id(db, sesion_id, incluir_asistencias=True)

    if not sesion:
        return None

    if sesion.estado != "activa":
        raise ValueError("La sesión no está activa")

    # Cerrar la sesión
    sesion.estado = "cerrada"
    sesion.fecha_fin = datetime.now()
    sesion.fecha_actualizacion = datetime.now()

    # Sincronizar con el sistema de evaluaciones existente
    sincronizar_con_evaluaciones(db, sesion)

    db.commit()
    db.refresh(sesion)

    return sesion


def sincronizar_con_evaluaciones(db: Session, sesion: SesionAsistencia):
    """Sincronizar la sesión de asistencia con el sistema de evaluaciones existente"""

    # Obtener el tipo de evaluación "Asistencia"
    tipo_asistencia = (
        db.query(TipoEvaluacion)
        .filter(TipoEvaluacion.nombre.ilike("Asistencia"))
        .first()
    )

    if not tipo_asistencia:
        raise ValueError("Tipo de evaluación 'Asistencia' no encontrado")

    # Crear evaluaciones para cada estudiante
    for asistencia in sesion.asistencias:
        # Verificar si ya existe una evaluación para esta fecha y estudiante
        evaluacion_existente = (
            db.query(Evaluacion)
            .filter(
                and_(
                    Evaluacion.estudiante_id == asistencia.estudiante_id,
                    Evaluacion.materia_id == sesion.materia_id,
                    Evaluacion.periodo_id == sesion.periodo_id,
                    Evaluacion.tipo_evaluacion_id == tipo_asistencia.id,
                    func.date(Evaluacion.fecha) == func.date(sesion.fecha_inicio),
                )
            )
            .first()
        )

        if evaluacion_existente:
            # Actualizar evaluación existente
            evaluacion_existente.valor = calcular_valor_asistencia(asistencia)
            evaluacion_existente.descripcion = f"Asistencia - {sesion.titulo}"
        else:
            # Crear nueva evaluación
            evaluacion = Evaluacion(
                estudiante_id=asistencia.estudiante_id,
                materia_id=sesion.materia_id,
                periodo_id=sesion.periodo_id,
                tipo_evaluacion_id=tipo_asistencia.id,
                fecha=sesion.fecha_inicio.date(),
                valor=calcular_valor_asistencia(asistencia),
                descripcion=f"Asistencia - {sesion.titulo}",
            )
            db.add(evaluacion)


def calcular_valor_asistencia(asistencia: AsistenciaEstudiante) -> float:
    """Calcular el valor numérico de la asistencia según el estado"""
    if asistencia.presente:
        return (
            50.0 if asistencia.es_tardanza else 100.0
        )  # Tardanza = 50, Presente = 100
    elif asistencia.justificado:
        return 75.0  # Justificado = 75
    else:
        return 0.0  # Ausente = 0


# ================ CRUD ASISTENCIA DE ESTUDIANTES ================


def marcar_asistencia_estudiante(
    db: Session, sesion_id: int, estudiante_id: int, datos: MarcarAsistenciaRequest
) -> Tuple[AsistenciaEstudiante, Dict]:
    """Marcar asistencia de un estudiante con validación de ubicación"""

    # Obtener la sesión
    sesion = obtener_sesion_por_id(db, sesion_id)
    if not sesion:
        raise ValueError("Sesión no encontrada")

    if not sesion.esta_activa:
        raise ValueError("La sesión no está activa o ha expirado")

    # Obtener el registro de asistencia del estudiante
    asistencia = (
        db.query(AsistenciaEstudiante)
        .filter(
            and_(
                AsistenciaEstudiante.sesion_id == sesion_id,
                AsistenciaEstudiante.estudiante_id == estudiante_id,
            )
        )
        .first()
    )

    if not asistencia:
        raise ValueError("Estudiante no encontrado en esta sesión")

    if asistencia.presente:
        raise ValueError("El estudiante ya ha marcado asistencia")

    # Validar ubicación
    distancia, dentro_del_rango = validar_ubicacion_estudiante(
        sesion.latitud_docente,
        sesion.longitud_docente,
        datos.latitud_estudiante,
        datos.longitud_estudiante,
        sesion.radio_permitido_metros,
    )

    if not dentro_del_rango:
        raise ValueError(
            f"Estudiante fuera del rango permitido. Distancia: {distancia}m"
        )

    # Verificar si es tardanza
    now = datetime.now()
    es_tardanza = now > sesion.fecha_inicio

    # Marcar asistencia
    asistencia.presente = True
    asistencia.fecha_marcado = now
    asistencia.latitud_estudiante = datos.latitud_estudiante
    asistencia.longitud_estudiante = datos.longitud_estudiante
    asistencia.distancia_metros = distancia
    asistencia.es_tardanza = es_tardanza
    asistencia.observaciones = datos.observaciones
    asistencia.fecha_actualizacion = now

    db.commit()
    db.refresh(asistencia)

    resultado = {
        "success": True,
        "message": "Asistencia marcada exitosamente",
        "es_tardanza": es_tardanza,
        "distancia_metros": distancia,
        "dentro_del_rango": dentro_del_rango,
    }

    return asistencia, resultado


def justificar_ausencia(
    db: Session, sesion_id: int, estudiante_id: int, datos: JustificarAusenciaRequest
) -> AsistenciaEstudiante:
    """Justificar la ausencia de un estudiante"""

    asistencia = (
        db.query(AsistenciaEstudiante)
        .filter(
            and_(
                AsistenciaEstudiante.sesion_id == sesion_id,
                AsistenciaEstudiante.estudiante_id == estudiante_id,
            )
        )
        .first()
    )

    if not asistencia:
        raise ValueError("Registro de asistencia no encontrado")

    asistencia.justificado = True
    asistencia.motivo_justificacion = datos.motivo_justificacion
    if datos.observaciones:
        asistencia.observaciones = datos.observaciones
    asistencia.fecha_actualizacion = datetime.now()

    db.commit()
    db.refresh(asistencia)

    return asistencia


def obtener_asistencias_sesion(
    db: Session, sesion_id: int
) -> List[AsistenciaEstudiante]:
    """Obtener todas las asistencias de una sesión con información de estudiantes"""

    return (
        db.query(AsistenciaEstudiante)
        .options(joinedload(AsistenciaEstudiante.estudiante))
        .filter(AsistenciaEstudiante.sesion_id == sesion_id)
        .all()
    )


def obtener_asistencias_estudiante(
    db: Session,
    estudiante_id: int,
    curso_id: Optional[int] = None,
    materia_id: Optional[int] = None,
) -> List[AsistenciaEstudiante]:
    """Obtener todas las asistencias de un estudiante"""

    query = (
        db.query(AsistenciaEstudiante)
        .options(joinedload(AsistenciaEstudiante.sesion))
        .filter(AsistenciaEstudiante.estudiante_id == estudiante_id)
    )

    if curso_id or materia_id:
        query = query.join(SesionAsistencia)
        if curso_id:
            query = query.filter(SesionAsistencia.curso_id == curso_id)
        if materia_id:
            query = query.filter(SesionAsistencia.materia_id == materia_id)

    return query.order_by(desc(AsistenciaEstudiante.fecha_creacion)).all()


# ================ FUNCIONES DE CONSULTA Y ESTADÍSTICAS ================


def obtener_sesiones_activas_estudiante(
    db: Session, estudiante_id: int
) -> List[SesionAsistencia]:
    """Obtener sesiones activas donde el estudiante puede marcar asistencia"""

    # Obtener cursos del estudiante
    inscripciones = (
        db.query(Inscripcion).filter(Inscripcion.estudiante_id == estudiante_id).all()
    )

    curso_ids = [insc.curso_id for insc in inscripciones]

    if not curso_ids:
        return []

    # Buscar sesiones activas en los cursos del estudiante
    sesiones = (
        db.query(SesionAsistencia)
        .filter(
            and_(
                SesionAsistencia.curso_id.in_(curso_ids),
                SesionAsistencia.estado == "activa",
            )
        )
        .all()
    )

    # Filtrar sesiones que realmente están activas
    sesiones_activas = [s for s in sesiones if s.esta_activa]

    return sesiones_activas


def validar_puede_marcar_asistencia(
    db: Session,
    sesion_id: int,
    estudiante_id: int,
    lat_estudiante: float,
    lon_estudiante: float,
) -> Dict:
    """Validar si un estudiante puede marcar asistencia sin registrarla"""

    sesion = obtener_sesion_por_id(db, sesion_id)

    if not sesion:
        return {
            "puede_marcar": False,
            "mensaje": "Sesión no encontrada",
            "sesion_activa": False,
        }

    if not sesion.esta_activa:
        return {
            "puede_marcar": False,
            "mensaje": "La sesión no está activa o ha expirado",
            "sesion_activa": False,
        }

    # Verificar si ya marcó asistencia
    asistencia = (
        db.query(AsistenciaEstudiante)
        .filter(
            and_(
                AsistenciaEstudiante.sesion_id == sesion_id,
                AsistenciaEstudiante.estudiante_id == estudiante_id,
            )
        )
        .first()
    )

    if not asistencia:
        return {
            "puede_marcar": False,
            "mensaje": "Estudiante no encontrado en esta sesión",
            "sesion_activa": True,
        }

    if asistencia.presente:
        return {
            "puede_marcar": False,
            "mensaje": "Ya has marcado asistencia",
            "sesion_activa": True,
        }

    # Validar ubicación
    distancia, dentro_del_rango = validar_ubicacion_estudiante(
        sesion.latitud_docente,
        sesion.longitud_docente,
        lat_estudiante,
        lon_estudiante,
        sesion.radio_permitido_metros,
    )

    if not dentro_del_rango:
        return {
            "puede_marcar": False,
            "mensaje": f"Estás fuera del rango permitido ({sesion.radio_permitido_metros}m). Tu distancia: {distancia}m",
            "sesion_activa": True,
            "distancia_metros": distancia,
            "dentro_del_rango": False,
        }

    # Calcular tiempo restante
    now = datetime.now()
    tiempo_limite = sesion.fecha_inicio + timedelta(minutes=sesion.minutos_tolerancia)
    tiempo_restante = (tiempo_limite - now).total_seconds() / 60

    return {
        "puede_marcar": True,
        "mensaje": "Puedes marcar asistencia",
        "sesion_activa": True,
        "distancia_metros": distancia,
        "dentro_del_rango": True,
        "tiempo_restante_minutos": max(0, int(tiempo_restante)),
    }


def obtener_estadisticas_sesion(db: Session, sesion_id: int) -> Dict:
    """Obtener estadísticas de una sesión de asistencia"""

    asistencias = obtener_asistencias_sesion(db, sesion_id)

    total = len(asistencias)
    presentes = len([a for a in asistencias if a.presente])
    ausentes = total - presentes
    tardanzas = len([a for a in asistencias if a.presente and a.es_tardanza])
    justificados = len([a for a in asistencias if a.justificado])

    porcentaje_asistencia = (presentes / total * 100) if total > 0 else 0

    return {
        "total_estudiantes": total,
        "presentes": presentes,
        "ausentes": ausentes,
        "tardanzas": tardanzas,
        "justificados": justificados,
        "porcentaje_asistencia": round(porcentaje_asistencia, 2),
    }


def obtener_periodo_y_gestion_por_fecha(db: Session, fecha):
    """
    Obtiene el periodo y gestión correspondiente a una fecha específica
    """
    from app.models.periodo import Periodo

    # Si fecha es datetime, convertir a date
    if hasattr(fecha, "date"):
        fecha = fecha.date()

    periodo = (
        db.query(Periodo)
        .filter(Periodo.fecha_inicio <= fecha, Periodo.fecha_fin >= fecha)
        .first()
    )

    if not periodo:
        raise ValueError(
            f"La fecha {fecha} no coincide con ningún periodo activo. "
            f"Verifique que exista un periodo configurado que incluya esta fecha."
        )

    return periodo.id, periodo.gestion_id


def obtener_sesiones_activas_estudiante_con_info(
    db: Session, estudiante_id: int
) -> List[SesionAsistencia]:
    """
    Obtener sesiones activas del estudiante con información de materia y docente
    """
    from app.models.inscripcion import Inscripcion
    from app.models.materia import Materia
    from app.models.docente_materia import DocenteMateria
    from app.models.docente import Docente

    # Query base con todas las relaciones necesarias
    query = (
        db.query(SesionAsistencia)
        .join(Inscripcion, Inscripcion.curso_id == SesionAsistencia.curso_id)
        .join(Materia, Materia.id == SesionAsistencia.materia_id)
        .outerjoin(DocenteMateria, DocenteMateria.materia_id == Materia.id)
        .outerjoin(Docente, Docente.id == DocenteMateria.docente_id)
        .options(
            # Cargar las relaciones
            joinedload(
                SesionAsistencia.asistencias.and_(
                    AsistenciaEstudiante.estudiante_id == estudiante_id
                )
            ),
        )
        .filter(
            and_(
                Inscripcion.estudiante_id == estudiante_id,
                SesionAsistencia.estado == "activa",
                # Asegurar que el estudiante tenga un registro de asistencia
                AsistenciaEstudiante.sesion_id == SesionAsistencia.id,
                AsistenciaEstudiante.estudiante_id == estudiante_id,
            )
        )
        .order_by(SesionAsistencia.fecha_inicio.desc())
    )

    sesiones = query.all()

    # Enriquecer cada sesión con información adicional
    sesiones_enriquecidas = []
    for sesion in sesiones:
        # Obtener información de la materia
        materia = db.query(Materia).filter(Materia.id == sesion.materia_id).first()

        # Obtener información del docente
        docente_materia = (
            db.query(DocenteMateria)
            .options(joinedload(DocenteMateria.docente))
            .filter(DocenteMateria.materia_id == sesion.materia_id)
            .first()
        )

        # Obtener la asistencia del estudiante para esta sesión
        mi_asistencia = (
            db.query(AsistenciaEstudiante)
            .filter(
                and_(
                    AsistenciaEstudiante.sesion_id == sesion.id,
                    AsistenciaEstudiante.estudiante_id == estudiante_id,
                )
            )
            .first()
        )

        # Agregar atributos dinámicos a la sesión
        if materia:
            sesion.materia = {
                "id": materia.id,
                "nombre": materia.nombre,
                "descripcion": materia.descripcion,
                "sigla": getattr(materia, "sigla", None),
            }
        else:
            sesion.materia = None

        if docente_materia and docente_materia.docente:
            sesion.docente = {
                "id": docente_materia.docente.id,
                "nombre": docente_materia.docente.nombre,
                "apellido": docente_materia.docente.apellido,
                "correo": docente_materia.docente.correo,
                "telefono": docente_materia.docente.telefono,
            }
        else:
            sesion.docente = None

        sesion.mi_asistencia = mi_asistencia

        sesiones_enriquecidas.append(sesion)

    return sesiones_enriquecidas
