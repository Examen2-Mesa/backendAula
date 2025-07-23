"""
Servicio de predicción de rendimiento académico usando Machine Learning
"""

import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
import logging

from sqlalchemy import func
from app.models.prediccion_rendimiento import PrediccionRendimiento

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(
        self,  # models_path: str = "ml_system\scripts\modelos"
        models_path: str = os.path.join("ml_system", "scripts", "modelos"),
    ):
        """
        Inicializa el servicio de predicción

        Args:
            models_path: Ruta donde están los modelos entrenados
        """
        self.models_path = models_path
        self.models_loaded = False
        self.modelo_regresion = None
        self.modelo_clasificacion = None
        self.scaler = None
        self.label_encoder = None
        self.features_principales = None
        self.feature_importance = None

        # Cargar modelos al inicializar
        self.cargar_modelos()

    def cargar_modelos(self) -> bool:
        """Carga todos los modelos y artefactos necesarios"""
        try:
            logger.info("Cargando modelos de ML...")

            # Verificar que existen los archivos
            archivos_requeridos = [
                "modelo_rendimiento_regresion.pkl",
                "modelo_rendimiento_clasificacion.pkl",
                "modelo_rendimiento_scaler.pkl",
                "modelo_rendimiento_label_encoder.pkl",
                "features_principales.pkl",
            ]

            for archivo in archivos_requeridos:
                ruta_completa = os.path.join(self.models_path, archivo)
                if not os.path.exists(ruta_completa):
                    logger.error(f"Archivo no encontrado: {ruta_completa}")
                    return False

            # Cargar modelos
            self.modelo_regresion = joblib.load(
                os.path.join(self.models_path, "modelo_rendimiento_regresion.pkl")
            )
            self.modelo_clasificacion = joblib.load(
                os.path.join(self.models_path, "modelo_rendimiento_clasificacion.pkl")
            )
            self.scaler = joblib.load(
                os.path.join(self.models_path, "modelo_rendimiento_scaler.pkl")
            )
            self.label_encoder = joblib.load(
                os.path.join(self.models_path, "modelo_rendimiento_label_encoder.pkl")
            )
            self.features_principales = joblib.load(
                os.path.join(self.models_path, "features_principales.pkl")
            )

            # Cargar importancia de características (opcional)
            ruta_importance = os.path.join(self.models_path, "feature_importance.pkl")
            if os.path.exists(ruta_importance):
                self.feature_importance = joblib.load(ruta_importance)

            self.models_loaded = True
            logger.info("✅ Modelos cargados exitosamente")
            logger.info(f"Características: {self.features_principales}")

            return True

        except Exception as e:
            logger.error(f"Error cargando modelos: {str(e)}")
            return False

    def validar_entrada(self, datos: Dict) -> Tuple[bool, str]:
        """
        Valida que los datos de entrada sean correctos

        Args:
            datos: Diccionario con los datos del estudiante

        Returns:
            Tuple (es_valido, mensaje_error)
        """
        if not self.models_loaded:
            return False, "Modelos no cargados"

        # Características mínimas requeridas
        caracteristicas_minimas = [
            "promedio_notas_anterior",
            "porcentaje_asistencia",
            "promedio_participacion",
        ]

        # Verificar que existen las características mínimas
        for feature in caracteristicas_minimas:
            if feature not in datos:
                return False, f"Característica requerida faltante: {feature}"

        # Validar rangos
        validaciones = [
            ("promedio_notas_anterior", 0, 100),
            ("porcentaje_asistencia", 0, 100),
            ("promedio_participacion", 0, 100),
        ]

        for feature, min_val, max_val in validaciones:
            if feature in datos:
                valor = datos[feature]
                if not isinstance(valor, (int, float)):
                    return False, f"{feature} debe ser un número"
                if not (min_val <= valor <= max_val):
                    return False, f"{feature} debe estar entre {min_val} y {max_val}"

        return True, "Datos válidos"

    def preparar_features(self, datos: Dict) -> np.ndarray:
        """
        Prepara las características para predicción

        Args:
            datos: Diccionario con los datos del estudiante

        Returns:
            Array numpy con las características preparadas
        """
        # Crear diccionario con todas las características
        features_dict = {}

        # Llenar características principales
        for feature in self.features_principales:
            if feature in datos:
                features_dict[feature] = datos[feature]
            else:
                # Valor por defecto para características faltantes
                features_dict[feature] = 0.0

        # Crear array en el orden correcto
        X = np.array([[features_dict[f] for f in self.features_principales]])

        # Escalar características
        X_scaled = self.scaler.transform(X)

        return X_scaled

    def predecir_rendimiento(self, datos: Dict) -> Dict:
        """
        Realiza predicción completa de rendimiento

        Args:
            datos: Diccionario con datos del estudiante

        Returns:
            Diccionario con las predicciones y metadatos
        """
        # Validar entrada
        es_valido, mensaje = self.validar_entrada(datos)
        if not es_valido:
            raise ValueError(mensaje)

        # Preparar características
        X_scaled = self.preparar_features(datos)

        # Predicción numérica (regresión)
        prediccion_numerica = self.modelo_regresion.predict(X_scaled)[0]
        prediccion_numerica = np.clip(
            prediccion_numerica, 0, 100
        )  # Asegurar rango válido

        # Predicción categórica (clasificación)
        prediccion_categoria_encoded = self.modelo_clasificacion.predict(X_scaled)[0]
        prediccion_categoria = self.label_encoder.inverse_transform(
            [prediccion_categoria_encoded]
        )[0]

        # Probabilidades por clase
        probabilidades = self.modelo_clasificacion.predict_proba(X_scaled)[0]
        probabilidades_dict = dict(
            zip(self.label_encoder.classes_, [float(p) for p in probabilidades])
        )

        # Nivel de confianza (probabilidad máxima)
        confianza = float(max(probabilidades))

        # Generar recomendaciones
        recomendaciones = self.generar_recomendaciones(
            datos, prediccion_numerica, prediccion_categoria
        )

        # Determinar nivel de riesgo
        nivel_riesgo = self.evaluar_riesgo(prediccion_numerica, datos)

        resultado = {
            "prediccion_numerica": round(float(prediccion_numerica), 2),
            "clasificacion": prediccion_categoria,
            "probabilidades": probabilidades_dict,
            "confianza": round(confianza, 4),
            "nivel_riesgo": nivel_riesgo,
            "recomendaciones": recomendaciones,
            "datos_entrada": datos,
            "timestamp": datetime.now().isoformat(),
            "metadatos": {
                "modelo_regresion": type(self.modelo_regresion).__name__,
                "modelo_clasificacion": type(self.modelo_clasificacion).__name__,
                "features_utilizadas": self.features_principales,
            },
        }

        return resultado

    def generar_recomendaciones(
        self, datos: Dict, prediccion: float, categoria: str
    ) -> List[str]:
        """
        Genera recomendaciones personalizadas basadas en la predicción

        Args:
            datos: Datos de entrada del estudiante
            prediccion: Predicción numérica del rendimiento
            categoria: Categoría de rendimiento predicha

        Returns:
            Lista de recomendaciones
        """
        recomendaciones = []

        # Recomendaciones basadas en la predicción general
        if prediccion < 50:
            recomendaciones.append("🚨 Requiere atención inmediata y apoyo académico")
            recomendaciones.append("📚 Programar sesiones de tutoría urgentes")
        elif prediccion < 70:
            recomendaciones.append("⚠️ Necesita refuerzo en algunas áreas")
            recomendaciones.append(
                "📖 Considerar apoyo adicional en materias específicas"
            )
        else:
            recomendaciones.append("✅ Mantener el buen rendimiento actual")
            recomendaciones.append("🎯 Considerar desafíos académicos adicionales")

        # Recomendaciones específicas por área
        promedio_anterior = datos.get("promedio_notas_anterior", 0)
        asistencia = datos.get("porcentaje_asistencia", 0)
        participacion = datos.get("promedio_participacion", 0)

        if promedio_anterior < 60:
            recomendaciones.append("📝 Reforzar técnicas de estudio y comprensión")
            recomendaciones.append("🔍 Revisar metodología de evaluación")

        if asistencia < 80:
            recomendaciones.append(
                "🏫 Mejorar asistencia a clases (actual: {:.1f}%)".format(asistencia)
            )
            recomendaciones.append("📞 Contactar con padres/tutores sobre asistencia")

        if participacion < 60:
            recomendaciones.append("🗣️ Fomentar mayor participación en clase")
            recomendaciones.append("🤝 Crear ambiente más participativo y confianza")

        # Recomendaciones por categoría
        if categoria == "Alto":
            recomendaciones.append("🌟 Considerar actividades de liderazgo estudiantil")
            recomendaciones.append("🏆 Oportunidades de reconocimiento académico")
        elif categoria == "Bajo":
            recomendaciones.append("💪 Plan de mejora académica personalizado")
            recomendaciones.append("👨‍👩‍👧‍👦 Involucrar más a la familia en el proceso")

        return recomendaciones[:6]  # Limitar a 6 recomendaciones

    def evaluar_riesgo(self, prediccion: float, datos: Dict) -> str:
        """
        Evalúa el nivel de riesgo académico

        Args:
            prediccion: Predicción numérica
            datos: Datos del estudiante

        Returns:
            Nivel de riesgo ('bajo', 'medio', 'alto', 'critico')
        """
        asistencia = datos.get("porcentaje_asistencia", 100)
        promedio_anterior = datos.get("promedio_notas_anterior", 100)

        # Factores de riesgo
        factores_riesgo = 0

        if prediccion < 40:
            factores_riesgo += 3
        elif prediccion < 60:
            factores_riesgo += 2
        elif prediccion < 70:
            factores_riesgo += 1

        if asistencia < 70:
            factores_riesgo += 2
        elif asistencia < 85:
            factores_riesgo += 1

        if promedio_anterior < 50:
            factores_riesgo += 2
        elif promedio_anterior < 70:
            factores_riesgo += 1

        # Determinar nivel de riesgo
        if factores_riesgo >= 5:
            return "critico"
        elif factores_riesgo >= 3:
            return "alto"
        elif factores_riesgo >= 1:
            return "medio"
        else:
            return "bajo"

    def predecir_estudiante_por_bd1(
        self, db, estudiante_id: int, materia_id: int, periodo_id: int
    ) -> Dict:
        """
        Predice rendimiento para un estudiante usando datos de la BD

        Args:
            db: Sesión de base de datos
            estudiante_id: ID del estudiante
            materia_id: ID de la materia
            periodo_id: ID del periodo

        Returns:
            Diccionario con la predicción
        """
        try:
            from sqlalchemy import text

            # Query para obtener datos del estudiante
            query = """
            WITH evaluaciones_estudiante AS (
                SELECT 
                    ev.estudiante_id,
                    te.nombre as tipo_evaluacion,
                    AVG(ev.valor) as promedio_tipo,
                    CASE 
                        WHEN te.nombre = 'Asistencia' THEN 
                            ROUND((COUNT(CASE WHEN ev.valor >= 1 THEN 1 END) * 100.0 / COUNT(*)), 2)
                        ELSE AVG(ev.valor)
                    END as valor_calculado
                FROM evaluaciones ev
                JOIN tipoevaluaciones te ON ev.tipo_evaluacion_id = te.id
                WHERE ev.estudiante_id = :estudiante_id 
                    AND ev.materia_id = :materia_id 
                    AND ev.periodo_id = :periodo_id
                GROUP BY ev.estudiante_id, te.id, te.nombre
            ),
            periodo_anterior AS (
                SELECT 
                    rf.estudiante_id,
                    AVG(rf.nota_final) as promedio_anterior
                FROM rendimiento_final rf
                JOIN periodos p ON rf.periodo_id = p.id
                WHERE rf.estudiante_id = :estudiante_id 
                    AND rf.materia_id = :materia_id
                    AND p.id < :periodo_id
                GROUP BY rf.estudiante_id
            ),
            datos_estudiante AS (
                SELECT 
                    e.id,
                    e.nombre,
                    e.apellido,
                    e.genero,
                    EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM e.fecha_nacimiento) as edad
                FROM estudiantes e
                WHERE e.id = :estudiante_id
            )
            SELECT 
                de.id as estudiante_id,
                de.nombre,
                de.apellido,
                de.genero,
                de.edad,
                COALESCE(pa.promedio_anterior, 50) as promedio_notas_anterior,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Asistencia' THEN ee.valor_calculado END), 85) as porcentaje_asistencia,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Participaciones' THEN ee.valor_calculado END), 70) as promedio_participacion,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Exámenes' THEN ee.valor_calculado END), 0) as promedio_examenes,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Tareas' THEN ee.valor_calculado END), 0) as promedio_tareas,
                CASE WHEN de.genero = 'Masculino' THEN 1 ELSE 0 END as genero_masculino
            FROM datos_estudiante de
            LEFT JOIN evaluaciones_estudiante ee ON de.id = ee.estudiante_id
            LEFT JOIN periodo_anterior pa ON de.id = pa.estudiante_id
            GROUP BY de.id, de.nombre, de.apellido, de.genero, de.edad, pa.promedio_anterior
            """

            result = db.execute(
                text(query),
                {
                    "estudiante_id": estudiante_id,
                    "materia_id": materia_id,
                    "periodo_id": periodo_id,
                },
            ).fetchone()

            if not result:
                raise ValueError(
                    f"No se encontraron datos para estudiante {estudiante_id}"
                )

            # Convertir resultado a diccionario
            datos = {
                "promedio_notas_anterior": float(result.promedio_notas_anterior),
                "porcentaje_asistencia": float(result.porcentaje_asistencia),
                "promedio_participacion": float(result.promedio_participacion),
                "promedio_examenes": float(result.promedio_examenes or 0),
                "promedio_tareas": float(result.promedio_tareas or 0),
                "edad": int(result.edad or 18),
                "genero_masculino": int(result.genero_masculino or 0),
                "turno_manana": 1,  # Valor por defecto
            }

            # Realizar predicción
            prediccion = self.predecir_rendimiento(datos)

            # Agregar información del estudiante
            prediccion["estudiante_info"] = {
                "id": estudiante_id,
                "nombre": result.nombre,
                "apellido": result.apellido,
                "genero": result.genero,
                "edad": result.edad,
            }

            return prediccion

        except Exception as e:
            logger.error(f"Error prediciendo para estudiante {estudiante_id}: {str(e)}")
            raise

    def predecir_estudiante_por_bd2(
        self, db, estudiante_id: int, materia_id: int, periodo_id: int
    ) -> Dict:
        """
        Predice el rendimiento de un estudiante a partir de la base de datos
        y guarda el resultado en la tabla prediccion_rendimiento
        """
        try:
            from sqlalchemy import text

            # Query para obtener datos necesarios del estudiante
            query = """
            WITH evaluaciones_estudiante AS (
                SELECT 
                    ev.estudiante_id,
                    te.nombre as tipo_evaluacion,
                    AVG(ev.valor) as promedio_tipo,
                    CASE 
                        WHEN te.nombre = 'Asistencia' THEN 
                            ROUND((COUNT(CASE WHEN ev.valor >= 1 THEN 1 END) * 100.0 / COUNT(*)), 2)
                        ELSE AVG(ev.valor)
                    END as valor_calculado
                FROM evaluaciones ev
                JOIN tipoevaluaciones te ON ev.tipo_evaluacion_id = te.id
                WHERE ev.estudiante_id = :estudiante_id 
                    AND ev.materia_id = :materia_id 
                    AND ev.periodo_id = :periodo_id
                GROUP BY ev.estudiante_id, te.id, te.nombre
            ),
            periodo_anterior AS (
                SELECT 
                    rf.estudiante_id,
                    AVG(rf.nota_final) as promedio_anterior
                FROM rendimiento_final rf
                JOIN periodos p ON rf.periodo_id = p.id
                WHERE rf.estudiante_id = :estudiante_id 
                    AND rf.materia_id = :materia_id
                    AND p.id < :periodo_id
                GROUP BY rf.estudiante_id
            ),
            datos_estudiante AS (
                SELECT 
                    e.id,
                    e.nombre,
                    e.apellido,
                    e.genero,
                    EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM e.fecha_nacimiento) as edad
                FROM estudiantes e
                WHERE e.id = :estudiante_id
            )
            SELECT 
                de.id as estudiante_id,
                de.nombre,
                de.apellido,
                de.genero,
                de.edad,
                COALESCE(pa.promedio_anterior, 50) as promedio_notas_anterior,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Asistencia' THEN ee.valor_calculado END), 85) as porcentaje_asistencia,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Participaciones' THEN ee.valor_calculado END), 70) as promedio_participacion,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Exámenes' THEN ee.valor_calculado END), 0) as promedio_examenes,
                COALESCE(MAX(CASE WHEN ee.tipo_evaluacion = 'Tareas' THEN ee.valor_calculado END), 0) as promedio_tareas,
                CASE WHEN de.genero = 'Masculino' THEN 1 ELSE 0 END as genero_masculino
            FROM datos_estudiante de
            LEFT JOIN evaluaciones_estudiante ee ON de.id = ee.estudiante_id
            LEFT JOIN periodo_anterior pa ON de.id = pa.estudiante_id
            GROUP BY de.id, de.nombre, de.apellido, de.genero, de.edad, pa.promedio_anterior
            """

            result = db.execute(
                text(query),
                {
                    "estudiante_id": estudiante_id,
                    "materia_id": materia_id,
                    "periodo_id": periodo_id,
                },
            ).fetchone()

            if not result:
                raise ValueError(
                    f"No se encontraron datos para estudiante {estudiante_id}"
                )

            # Construir diccionario para predicción
            datos = {
                "promedio_notas_anterior": float(result.promedio_notas_anterior),
                "porcentaje_asistencia": float(result.porcentaje_asistencia),
                "promedio_participacion": float(result.promedio_participacion),
                "promedio_examenes": float(result.promedio_examenes or 0),
                "promedio_tareas": float(result.promedio_tareas or 0),
                "edad": int(result.edad or 18),
                "genero_masculino": int(result.genero_masculino or 0),
                "turno_manana": 1,
            }

            # Ejecutar predicción
            prediccion = self.predecir_rendimiento(datos)

            # Verificar si ya existe una predicción previa para este estudiante-materia-periodo
            existente = (
                db.query(PrediccionRendimiento)
                .filter_by(
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                )
                .first()
            )

            if existente:
                # Actualizar valores
                existente.promedio_notas = datos["promedio_notas_anterior"]
                existente.porcentaje_asistencia = datos["porcentaje_asistencia"]
                existente.promedio_participacion = datos["promedio_participacion"]
                existente.resultado_numerico = prediccion["prediccion_numerica"]
                existente.clasificacion = prediccion["clasificacion"]
                existente.updated_at = datetime.utcnow()
                db.commit()
                prediccion["registro_id"] = existente.id
            else:
                # Crear nuevo registro
                nueva_pred = PrediccionRendimiento(
                    promedio_notas=datos["promedio_notas_anterior"],
                    porcentaje_asistencia=datos["porcentaje_asistencia"],
                    promedio_participacion=datos["promedio_participacion"],
                    resultado_numerico=prediccion["prediccion_numerica"],
                    clasificacion=prediccion["clasificacion"],
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                )
                db.add(nueva_pred)
                db.commit()
                db.refresh(nueva_pred)
                prediccion["registro_id"] = nueva_pred.id

            # Añadir info básica del estudiante
            prediccion["estudiante_info"] = {
                "id": estudiante_id,
                "nombre": result.nombre,
                "apellido": result.apellido,
                "genero": result.genero,
                "edad": result.edad,
            }

            return prediccion

        except Exception as e:
            logger.error(f"Error prediciendo para estudiante {estudiante_id}: {str(e)}")
            raise

    def predecir_estudiante_por_bd(
        self, db, estudiante_id: int, materia_id: int, periodo_id: int
    ) -> Dict:
        """
        Predice el rendimiento de un estudiante usando promedio ponderado real por tipo de evaluación.
        Guarda la predicción y actualiza también la tabla RendimientoFinal.
        """
        try:
            from app.models import (
                Evaluacion,
                TipoEvaluacion,
                PesoTipoEvaluacion,
                DocenteMateria,
                RendimientoFinal,
                Estudiante,
                Periodo,
            )

            estudiante = db.query(Estudiante).filter_by(id=estudiante_id).first()
            if not estudiante:
                raise ValueError("Estudiante no encontrado")

            edad = datetime.now().year - estudiante.fecha_nacimiento.year
            genero_masculino = 1 if estudiante.genero.lower() == "masculino" else 0

            # Obtener gestión del periodo
            periodo = db.query(Periodo).filter_by(id=periodo_id).first()
            if not periodo:
                raise ValueError("Periodo no válido")
            gestion_id = periodo.gestion_id

            # Docente asignado a la materia
            docente_materia = (
                db.query(DocenteMateria).filter_by(materia_id=materia_id).first()
            )
            if not docente_materia:
                raise ValueError("Docente no asignado a la materia")
            docente_id = docente_materia.docente_id

            tipos = db.query(TipoEvaluacion).all()

            nota_final = 0.0
            porcentaje_asistencia = 85.0
            promedio_participacion = 70.0
            detalle = []

            for tipo in tipos:
                # Buscar peso definido por el docente para este tipo
                peso = (
                    db.query(PesoTipoEvaluacion)
                    .filter_by(
                        docente_id=docente_id,
                        materia_id=materia_id,
                        gestion_id=gestion_id,
                        tipo_evaluacion_id=tipo.id,
                    )
                    .first()
                )
                if not peso:
                    continue

                # Obtener todas las evaluaciones del tipo
                evaluaciones = (
                    db.query(Evaluacion)
                    .filter_by(
                        estudiante_id=estudiante_id,
                        materia_id=materia_id,
                        periodo_id=periodo_id,
                        tipo_evaluacion_id=tipo.id,
                    )
                    .all()
                )
                if not evaluaciones:
                    continue

                promedio = sum(e.valor for e in evaluaciones) / len(evaluaciones)
                aporte = (promedio * peso.porcentaje) / 100
                nota_final += aporte

                if tipo.nombre.lower() == "asistencia":
                    porcentaje_asistencia = round(promedio, 2)
                elif tipo.nombre.lower() == "participaciones":
                    promedio_participacion = round(promedio, 2)

                detalle.append(
                    {
                        "tipo": tipo.nombre,
                        "promedio": round(promedio, 2),
                        "peso": peso.porcentaje,
                        "aporte": round(aporte, 2),
                    }
                )

            promedio_notas_anterior = round(nota_final, 2)

            # Preparar datos para la predicción
            datos = {
                "promedio_notas_anterior": promedio_notas_anterior,
                "porcentaje_asistencia": porcentaje_asistencia,
                "promedio_participacion": promedio_participacion,
                "edad": edad,
                "genero_masculino": genero_masculino,
                "turno_manana": 1,
            }

            # Realizar predicción ML
            prediccion = self.predecir_rendimiento(datos)

            # Guardar o actualizar en PrediccionRendimiento
            existente = (
                db.query(PrediccionRendimiento)
                .filter_by(
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                )
                .first()
            )

            if existente:
                existente.promedio_notas = promedio_notas_anterior
                existente.porcentaje_asistencia = porcentaje_asistencia
                existente.promedio_participacion = promedio_participacion
                existente.resultado_numerico = prediccion["prediccion_numerica"]
                existente.clasificacion = prediccion["clasificacion"]
                existente.updated_at = datetime.utcnow()
                db.commit()
                prediccion["registro_id"] = existente.id
            else:
                nueva = PrediccionRendimiento(
                    promedio_notas=promedio_notas_anterior,
                    porcentaje_asistencia=porcentaje_asistencia,
                    promedio_participacion=promedio_participacion,
                    resultado_numerico=prediccion["prediccion_numerica"],
                    clasificacion=prediccion["clasificacion"],
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                )
                db.add(nueva)
                db.commit()
                db.refresh(nueva)
                prediccion["registro_id"] = nueva.id

            # Actualizar también en RendimientoFinal
            rf = (
                db.query(RendimientoFinal)
                .filter_by(
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                )
                .first()
            )
            if rf:
                rf.nota_final = promedio_notas_anterior
                rf.fecha_calculo = func.now()
                db.commit()
            else:
                nuevo_rf = RendimientoFinal(
                    estudiante_id=estudiante_id,
                    materia_id=materia_id,
                    periodo_id=periodo_id,
                    nota_final=promedio_notas_anterior,
                )
                db.add(nuevo_rf)
                db.commit()

            # Retornar predicción y detalle
            prediccion["detalle_evaluacion"] = detalle
            prediccion["estudiante_info"] = {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "genero": estudiante.genero,
                "edad": edad,
            }

            return prediccion

        except Exception as e:
            logger.error(f"Error prediciendo estudiante {estudiante_id}: {str(e)}")
            raise

    def predecir_lote_estudiantes(
        self, db, curso_id: int, materia_id: int, periodo_id: int
    ) -> List[Dict]:
        """
        Predice rendimiento para todos los estudiantes de un curso

        Args:
            db: Sesión de base de datos
            curso_id: ID del curso
            materia_id: ID de la materia
            periodo_id: ID del periodo

        Returns:
            Lista de predicciones para cada estudiante
        """
        try:
            from sqlalchemy import text

            # Obtener estudiantes del curso
            query_estudiantes = """
            SELECT DISTINCT i.estudiante_id 
            FROM inscripciones i 
            WHERE i.curso_id = :curso_id
            """

            estudiantes = db.execute(
                text(query_estudiantes), {"curso_id": curso_id}
            ).fetchall()

            predicciones = []

            for estudiante_row in estudiantes:
                try:
                    prediccion = self.predecir_estudiante_por_bd(
                        db, estudiante_row.estudiante_id, materia_id, periodo_id
                    )
                    predicciones.append(prediccion)
                except Exception as e:
                    logger.warning(
                        f"Error prediciendo estudiante {estudiante_row.estudiante_id}: {str(e)}"
                    )
                    continue

            return predicciones

        except Exception as e:
            logger.error(f"Error en predicción por lotes: {str(e)}")
            raise

    def obtener_estadisticas_modelo(self) -> Dict:
        """
        Retorna estadísticas y metadatos de los modelos cargados

        Returns:
            Diccionario con estadísticas del modelo
        """
        if not self.models_loaded:
            return {"error": "Modelos no cargados"}

        estadisticas = {
            "modelos_cargados": True,
            "fecha_carga": datetime.now().isoformat(),
            "modelo_regresion": {
                "tipo": type(self.modelo_regresion).__name__,
                "n_features": len(self.features_principales),
            },
            "modelo_clasificacion": {
                "tipo": type(self.modelo_clasificacion).__name__,
                "clases": self.label_encoder.classes_.tolist(),
                "n_clases": len(self.label_encoder.classes_),
            },
            "features_utilizadas": self.features_principales,
            "ruta_modelos": self.models_path,
        }

        # Agregar importancia de características si está disponible
        if self.feature_importance:
            estadisticas["importancia_features"] = self.feature_importance

        return estadisticas

    def obtener_estudiantes_en_riesgo(
        self, db, umbral_riesgo: float = 60.0, limite: int = 20
    ) -> List[Dict]:
        """
        Identifica estudiantes en riesgo académico

        Args:
            db: Sesión de base de datos
            umbral_riesgo: Umbral por debajo del cual se considera riesgo
            limite: Número máximo de estudiantes a retornar

        Returns:
            Lista de estudiantes en riesgo con sus predicciones
        """
        try:
            from sqlalchemy import text

            # Query para obtener estudiantes activos
            query = """
            SELECT DISTINCT 
                e.id as estudiante_id,
                e.nombre,
                e.apellido,
                i.curso_id,
                p.id as periodo_actual
            FROM estudiantes e
            JOIN inscripciones i ON e.id = i.estudiante_id
            JOIN periodos p ON p.gestion_id = i.gestion_id
            WHERE p.fecha_inicio <= CURRENT_DATE 
                AND p.fecha_fin >= CURRENT_DATE
            LIMIT :limite
            """

            estudiantes = db.execute(text(query), {"limite": limite * 2}).fetchall()

            estudiantes_riesgo = []

            for estudiante in estudiantes:
                try:
                    # Obtener materias del curso (simplificado - tomar primera materia)
                    query_materia = """
                    SELECT cm.materia_id 
                    FROM curso_materia cm 
                    WHERE cm.curso_id = :curso_id 
                    LIMIT 1
                    """

                    materia_result = db.execute(
                        text(query_materia), {"curso_id": estudiante.curso_id}
                    ).fetchone()

                    if not materia_result:
                        continue

                    prediccion = self.predecir_estudiante_por_bd(
                        db,
                        estudiante.estudiante_id,
                        materia_result.materia_id,
                        estudiante.periodo_actual,
                    )

                    # Verificar si está en riesgo
                    if prediccion["prediccion_numerica"] < umbral_riesgo or prediccion[
                        "nivel_riesgo"
                    ] in ["alto", "critico"]:

                        estudiantes_riesgo.append(
                            {
                                "estudiante_id": estudiante.estudiante_id,
                                "nombre": estudiante.nombre,
                                "apellido": estudiante.apellido,
                                "prediccion_numerica": prediccion[
                                    "prediccion_numerica"
                                ],
                                "clasificacion": prediccion["clasificacion"],
                                "nivel_riesgo": prediccion["nivel_riesgo"],
                                "confianza": prediccion["confianza"],
                                "recomendaciones": prediccion["recomendaciones"][
                                    :3
                                ],  # Solo primeras 3
                            }
                        )

                    if len(estudiantes_riesgo) >= limite:
                        break

                except Exception as e:
                    logger.warning(
                        f"Error evaluando riesgo para estudiante {estudiante.estudiante_id}: {str(e)}"
                    )
                    continue

            # Ordenar por nivel de riesgo y predicción
            orden_riesgo = {"critico": 4, "alto": 3, "medio": 2, "bajo": 1}
            estudiantes_riesgo.sort(
                key=lambda x: (
                    orden_riesgo.get(x["nivel_riesgo"], 0),
                    -x["prediccion_numerica"],
                )
            )

            return estudiantes_riesgo

        except Exception as e:
            logger.error(f"Error obteniendo estudiantes en riesgo: {str(e)}")
            return []


# Instancia global del servicio
prediction_service = PredictionService()


def get_prediction_service() -> PredictionService:
    """
    Función para obtener la instancia del servicio de predicción
    Útil para dependency injection en FastAPI
    """
    if not prediction_service.models_loaded:
        # Intentar recargar modelos
        prediction_service.cargar_modelos()

    return prediction_service


# Funciones de utilidad para FastAPI
def validar_servicio_disponible():
    """Decorator para validar que el servicio esté disponible"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            service = get_prediction_service()
            if not service.models_loaded:
                raise RuntimeError(
                    "Servicio de predicción no disponible. Modelos no cargados."
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Clase para respuestas de la API
class PredictionResponse:
    """Clase para estructurar respuestas de predicción"""

    def __init__(self, success: bool = True, data: Dict = None, error: str = None):
        self.success = success
        self.data = data or {}
        self.error = error
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convierte la respuesta a diccionario"""
        response = {"success": self.success, "timestamp": self.timestamp}

        if self.success:
            response["data"] = self.data
        else:
            response["error"] = self.error

        return response


# Funciones específicas para endpoints
def crear_prediccion_response(prediccion: Dict) -> Dict:
    """
    Crea una respuesta estructurada para predicciones

    Args:
        prediccion: Resultado de la predicción

    Returns:
        Respuesta estructurada
    """
    return PredictionResponse(
        success=True,
        data={
            "prediccion": prediccion,
            "interpretacion": {
                "nivel": (
                    "Excelente"
                    if prediccion["prediccion_numerica"] >= 80
                    else (
                        "Bueno"
                        if prediccion["prediccion_numerica"] >= 70
                        else (
                            "Regular"
                            if prediccion["prediccion_numerica"] >= 60
                            else "Necesita Mejora"
                        )
                    )
                ),
                "color": (
                    "success"
                    if prediccion["prediccion_numerica"] >= 70
                    else (
                        "warning"
                        if prediccion["prediccion_numerica"] >= 60
                        else "danger"
                    )
                ),
                "icono": (
                    "🟢"
                    if prediccion["prediccion_numerica"] >= 70
                    else "🟡" if prediccion["prediccion_numerica"] >= 60 else "🔴"
                ),
            },
        },
    ).to_dict()


def crear_error_response(error_msg: str) -> Dict:
    """
    Crea una respuesta de error estructurada

    Args:
        error_msg: Mensaje de error

    Returns:
        Respuesta de error estructurada
    """
    return PredictionResponse(success=False, error=error_msg).to_dict()


# Ejemplo de uso y testing
if __name__ == "__main__":
    # Ejemplo de uso del servicio
    print("🧪 Probando servicio de predicción...")

    service = PredictionService()

    if service.models_loaded:
        # Datos de prueba
        datos_prueba = {
            "promedio_notas_anterior": 75.0,
            "porcentaje_asistencia": 85.0,
            "promedio_participacion": 80.0,
            "edad": 16,
            "genero_masculino": 1,
        }

        try:
            resultado = service.predecir_rendimiento(datos_prueba)
            print("✅ Predicción exitosa:")
            print(f"  - Predicción numérica: {resultado['prediccion_numerica']}")
            print(f"  - Clasificación: {resultado['clasificacion']}")
            print(f"  - Nivel de riesgo: {resultado['nivel_riesgo']}")
            print(f"  - Confianza: {resultado['confianza']}")

            # Mostrar estadísticas
            stats = service.obtener_estadisticas_modelo()
            print(f"\n📊 Estadísticas del modelo:")
            print(f"  - Características: {len(stats['features_utilizadas'])}")
            print(f"  - Clases: {stats['modelo_clasificacion']['clases']}")

        except Exception as e:
            print(f"❌ Error en predicción: {str(e)}")

    else:
        print("❌ Modelos no cargados. Asegúrate de haber ejecutado el entrenamiento.")
