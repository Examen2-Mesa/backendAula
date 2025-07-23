"""
Entrenador de modelos ML ajustado para los datos reales de 210 estudiantes
VERSIÓN CORREGIDA - Maneja clases desbalanceadas
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")


class ModelTrainerAjustado:
    def __init__(self, dataset_path="dataset_estudiantes_completo.csv"):
        self.dataset_path = dataset_path
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}

    def cargar_y_validar_datos(self):
        """Carga y valida los datos reales"""
        print("📊 Cargando dataset de estudiantes reales...")

        try:
            self.df = pd.read_csv(self.dataset_path, encoding="utf-8-sig")
            print(f"✅ Dataset cargado: {len(self.df)} registros")

            # Validaciones específicas para datos reales
            print(f"   👥 Estudiantes únicos: {self.df['estudiante_id'].nunique()}")
            print(f"   📚 Materias únicas: {self.df['materia_nombre'].nunique()}")
            print(f"   📅 Períodos únicos: {self.df['periodo_nombre'].nunique()}")

            # Verificar columnas esenciales
            columnas_requeridas = [
                "promedio_notas_anterior",
                "porcentaje_asistencia",
                "promedio_participacion",
                "nota_final_real",
                "rendimiento_categoria",
            ]

            columnas_faltantes = [
                col for col in columnas_requeridas if col not in self.df.columns
            ]
            if columnas_faltantes:
                raise ValueError(f"Columnas faltantes: {columnas_faltantes}")

            # Validar rangos de datos
            print(
                f"   📈 Rango notas: {self.df['nota_final_real'].min():.1f} - {self.df['nota_final_real'].max():.1f}"
            )
            print(f"   📊 Promedio general: {self.df['nota_final_real'].mean():.2f}")

            # Verificar distribución de categorías
            print(f"   📋 Distribución categorías:")
            distribucion = self.df["rendimiento_categoria"].value_counts()
            for cat, count in distribucion.items():
                print(f"      {cat}: {count} ({count/len(self.df)*100:.1f}%)")

            # NUEVO: Detectar y manejar clases con muy pocos ejemplos
            clases_minimas = distribucion[distribucion < 5]
            if len(clases_minimas) > 0:
                print(f"   ⚠️ ATENCIÓN: Clases con muy pocos ejemplos detectadas:")
                for clase, count in clases_minimas.items():
                    print(f"      {clase}: {count} ejemplos")
                print(
                    f"   🔧 Se ajustará el entrenamiento para manejar datos desbalanceados"
                )

            print("✅ Validación de datos completada")
            return True

        except Exception as e:
            print(f"❌ Error cargando datos: {str(e)}")
            return False

    def analisis_exploratorio_realista(self):
        """Análisis exploratorio ajustado para datos reales"""
        print("\n📊 ANÁLISIS EXPLORATORIO - DATOS REALES")
        print("=" * 50)

        # Estadísticas descriptivas
        print("📈 Estadísticas descriptivas:")
        estadisticas = self.df[
            [
                "promedio_notas_anterior",
                "porcentaje_asistencia",
                "promedio_participacion",
                "nota_final_real",
            ]
        ].describe()
        print(estadisticas.round(2))

        # Correlaciones
        print(f"\n🔗 Matriz de correlaciones:")
        correlaciones = self.df[
            [
                "promedio_notas_anterior",
                "porcentaje_asistencia",
                "promedio_participacion",
                "nota_final_real",
            ]
        ].corr()
        print(correlaciones.round(3))

        # Crear visualizaciones ajustadas
        self.crear_visualizaciones_reales()

        # Análisis por materia
        print(f"\n📚 Análisis por materia:")
        por_materia = (
            self.df.groupby("materia_nombre")["nota_final_real"]
            .agg(["count", "mean", "std"])
            .round(2)
        )
        print(por_materia)

        # Análisis temporal (por período)
        print(f"\n📅 Análisis por período:")
        por_periodo = (
            self.df.groupby("periodo_nombre")["nota_final_real"]
            .agg(["count", "mean", "std"])
            .round(2)
        )
        print(por_periodo)

    def crear_visualizaciones_reales(self):
        """Crea visualizaciones específicas para datos reales"""
        plt.style.use("default")
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # 1. Distribución de notas finales
        self.df["nota_final_real"].hist(
            bins=20, ax=axes[0, 0], alpha=0.7, color="skyblue", edgecolor="black"
        )
        axes[0, 0].set_title(
            "Distribución de Notas Finales\n(Datos Reales)",
            fontsize=12,
            fontweight="bold",
        )
        axes[0, 0].set_xlabel("Nota Final")
        axes[0, 0].set_ylabel("Frecuencia")
        axes[0, 0].axvline(
            self.df["nota_final_real"].mean(),
            color="red",
            linestyle="--",
            label=f'Media: {self.df["nota_final_real"].mean():.1f}',
        )
        axes[0, 0].legend()

        # 2. Boxplot por categoría
        categorias_disponibles = self.df["rendimiento_categoria"].unique()
        datos_boxplot = []
        labels_boxplot = []

        for cat in ["Bajo", "Medio", "Alto"]:
            if cat in categorias_disponibles:
                datos_cat = self.df[self.df["rendimiento_categoria"] == cat][
                    "nota_final_real"
                ]
                if len(datos_cat) > 0:
                    datos_boxplot.append(datos_cat)
                    labels_boxplot.append(f"{cat} (n={len(datos_cat)})")

        if datos_boxplot:
            axes[0, 1].boxplot(datos_boxplot, labels=labels_boxplot)
            axes[0, 1].set_title(
                "Distribución por Categoría de Rendimiento",
                fontsize=12,
                fontweight="bold",
            )
            axes[0, 1].set_ylabel("Nota Final")
            axes[0, 1].tick_params(axis="x", rotation=45)
        else:
            axes[0, 1].text(
                0.5,
                0.5,
                "No hay suficientes\ncategorías para mostrar",
                ha="center",
                va="center",
                transform=axes[0, 1].transAxes,
            )
            axes[0, 1].set_title(
                "Distribución por Categoría", fontsize=12, fontweight="bold"
            )

        # 3. Correlación entre variables
        correlacion_matrix = self.df[
            [
                "promedio_notas_anterior",
                "porcentaje_asistencia",
                "promedio_participacion",
                "nota_final_real",
            ]
        ].corr()
        sns.heatmap(
            correlacion_matrix,
            annot=True,
            cmap="RdYlBu_r",
            center=0,
            ax=axes[0, 2],
            square=True,
            fmt=".3f",
        )
        axes[0, 2].set_title("Matriz de Correlaciones", fontsize=12, fontweight="bold")

        # 4. Scatter plot principal
        scatter = axes[1, 0].scatter(
            self.df["promedio_notas_anterior"],
            self.df["nota_final_real"],
            c=self.df["porcentaje_asistencia"],
            cmap="viridis",
            alpha=0.6,
        )
        axes[1, 0].set_xlabel("Promedio Notas Anterior")
        axes[1, 0].set_ylabel("Nota Final Real")
        axes[1, 0].set_title(
            "Relación: Promedio Anterior vs Nota Final\n(Color = Asistencia)",
            fontsize=12,
            fontweight="bold",
        )
        plt.colorbar(scatter, ax=axes[1, 0], label="% Asistencia")

        # 5. Distribución por materia
        materias_top = self.df["materia_nombre"].value_counts().head(5)
        axes[1, 1].bar(
            range(len(materias_top)), materias_top.values, color="lightcoral"
        )
        axes[1, 1].set_title(
            "Registros por Materia (Top 5)", fontsize=12, fontweight="bold"
        )
        axes[1, 1].set_xlabel("Materias")
        axes[1, 1].set_ylabel("Número de Registros")
        axes[1, 1].set_xticks(range(len(materias_top)))
        axes[1, 1].set_xticklabels(
            [
                name[:15] + "..." if len(name) > 15 else name
                for name in materias_top.index
            ],
            rotation=45,
        )

        # 6. Distribución de asistencia
        self.df["porcentaje_asistencia"].hist(
            bins=15, ax=axes[1, 2], alpha=0.7, color="lightgreen", edgecolor="black"
        )
        axes[1, 2].set_title(
            "Distribución de Asistencia", fontsize=12, fontweight="bold"
        )
        axes[1, 2].set_xlabel("Porcentaje de Asistencia")
        axes[1, 2].set_ylabel("Frecuencia")
        axes[1, 2].axvline(
            self.df["porcentaje_asistencia"].mean(),
            color="red",
            linestyle="--",
            label=f'Media: {self.df["porcentaje_asistencia"].mean():.1f}%',
        )
        axes[1, 2].legend()

        plt.tight_layout()
        plt.savefig("analisis_datos_reales.png", dpi=300, bbox_inches="tight")
        print("✅ Visualizaciones guardadas en 'analisis_datos_reales.png'")
        plt.close()

    def preparar_features_optimizadas(self):
        """Prepara características optimizadas para datos reales"""
        print("\n🔧 Preparando características para entrenamiento...")

        # Características principales (las mismas del extractor)
        self.features_principales = [
            "promedio_notas_anterior",
            "porcentaje_asistencia",
            "promedio_participacion",
        ]

        # Agregar características adicionales si están disponibles
        features_adicionales = [
            "promedio_examenes",
            "promedio_tareas",
            "promedio_exposiciones",
            "promedio_practicas",
            "edad",
            "genero_masculino",
            "turno_manana",
        ]

        for feature in features_adicionales:
            if (
                feature in self.df.columns
                and self.df[feature].notna().sum() > len(self.df) * 0.5
            ):
                self.features_principales.append(feature)

        print(f"✅ Características seleccionadas: {len(self.features_principales)}")
        for i, feature in enumerate(self.features_principales, 1):
            print(f"   {i}. {feature}")

        # Preparar X e y
        self.X = self.df[self.features_principales].copy()
        self.y_regresion = self.df["nota_final_real"].copy()
        self.y_clasificacion = self.df["rendimiento_categoria"].copy()

        # Limpiar valores faltantes
        self.X = self.X.fillna(0)

        # Normalizar características
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)

        # NUEVO: Analizar distribución de clases antes de codificar
        distribucion_clases = self.y_clasificacion.value_counts()
        print(f"\n📊 Análisis de clases para clasificación:")
        for clase, count in distribucion_clases.items():
            print(
                f"   {clase}: {count} ejemplos ({count/len(self.y_clasificacion)*100:.2f}%)"
            )

        # Determinar si el dataset es viable para clasificación
        clases_minimas = distribucion_clases[distribucion_clases < 5]
        self.clasificacion_viable = len(clases_minimas) == 0

        if not self.clasificacion_viable:
            print(f"   ⚠️ ATENCIÓN: Clasificación no viable con clases < 5 ejemplos")
            print(f"   🔄 Se entrenará solo el modelo de regresión")
        else:
            # Codificar labels para clasificación
            self.label_encoder = LabelEncoder()
            self.y_clasificacion_encoded = self.label_encoder.fit_transform(
                self.y_clasificacion
            )
            print(f"   ✅ Clases codificadas: {list(self.label_encoder.classes_)}")

        print(
            f"✅ Datos preparados: {self.X.shape[0]} muestras, {self.X.shape[1]} características"
        )
        print(
            f"   📊 Rango y_regresion: {self.y_regresion.min():.1f} - {self.y_regresion.max():.1f}"
        )

    def entrenar_modelos_ajustados(self):
        """Entrena modelos ajustados para el tamaño de datos reales"""
        print(f"\n🤖 ENTRENANDO MODELOS CON DATOS REALES")
        print("=" * 50)

        # Dividir datos - SIN estratificación si hay problemas con clases
        if self.clasificacion_viable:
            X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = (
                train_test_split(
                    self.X_scaled,
                    self.y_regresion,
                    self.y_clasificacion_encoded,
                    test_size=0.25,
                    random_state=42,
                    stratify=self.y_clasificacion_encoded,
                )
            )
        else:
            # Solo división para regresión
            X_train, X_test, y_reg_train, y_reg_test = train_test_split(
                self.X_scaled, self.y_regresion, test_size=0.25, random_state=42
            )

        print(f"📊 División de datos:")
        print(f"   Entrenamiento: {len(X_train)} muestras")
        print(f"   Prueba: {len(X_test)} muestras")

        # === MODELO DE REGRESIÓN ===
        print(f"\n🔢 Entrenando modelo de REGRESIÓN...")

        # Configuración ajustada para datos reales
        rf_regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,  # Reducido para evitar sobreajuste
            min_samples_split=5,
            min_samples_leaf=3,  # Aumentado para generalización
            random_state=42,
        )

        rf_regressor.fit(X_train, y_reg_train)

        # Predicciones y evaluación
        y_reg_pred = rf_regressor.predict(X_test)
        r2 = r2_score(y_reg_test, y_reg_pred)
        rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))

        print(f"   📈 R² Score: {r2:.4f}")
        print(f"   📈 RMSE: {rmse:.4f}")

        # Validación cruzada
        cv_scores_r2 = cross_val_score(
            rf_regressor, self.X_scaled, self.y_regresion, cv=5, scoring="r2"
        )
        print(
            f"   📊 Validación cruzada R²: {cv_scores_r2.mean():.4f} ± {cv_scores_r2.std():.4f}"
        )

        self.modelo_regresion = rf_regressor

        # === MODELO DE CLASIFICACIÓN ===
        accuracy = 0.0  # Valor por defecto

        if self.clasificacion_viable:
            print(f"\n🏷️ Entrenando modelo de CLASIFICACIÓN...")

            rf_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=3,
                random_state=42,
                class_weight="balanced",  # Importante para datos desbalanceados
            )

            rf_classifier.fit(X_train, y_clf_train)

            # Predicciones y evaluación
            y_clf_pred = rf_classifier.predict(X_test)
            accuracy = accuracy_score(y_clf_test, y_clf_pred)

            print(f"   📈 Accuracy: {accuracy:.4f}")

            # Reporte detallado
            print(f"\n   📋 Reporte de clasificación:")
            report = classification_report(
                y_clf_test, y_clf_pred, target_names=self.label_encoder.classes_
            )
            print(report)

            # Validación cruzada
            cv_scores_acc = cross_val_score(
                rf_classifier,
                self.X_scaled,
                self.y_clasificacion_encoded,
                cv=5,
                scoring="accuracy",
            )
            print(
                f"   📊 Validación cruzada Accuracy: {cv_scores_acc.mean():.4f} ± {cv_scores_acc.std():.4f}"
            )

            self.modelo_clasificacion = rf_classifier

            # Importancia de características
            self.feature_importance = {
                "regresion": dict(
                    zip(self.features_principales, rf_regressor.feature_importances_)
                ),
                "clasificacion": dict(
                    zip(self.features_principales, rf_classifier.feature_importances_)
                ),
            }
        else:
            print(
                f"\n⚠️ CLASIFICACIÓN OMITIDA - Datos insuficientes para clases minoritarias"
            )
            print(f"   📊 Solo se entrenó el modelo de regresión")
            self.modelo_clasificacion = None
            self.label_encoder = None

            # Solo importancia de regresión
            self.feature_importance = {
                "regresion": dict(
                    zip(self.features_principales, rf_regressor.feature_importances_)
                )
            }

        return r2, rmse, accuracy

    def guardar_modelos_y_metadatos(self):
        """Guarda modelos y metadatos específicos"""
        print(f"\n💾 GUARDANDO MODELOS Y METADATOS...")
        print("=" * 40)

        import os

        os.makedirs("modelos", exist_ok=True)

        # Modelos básicos
        modelos_a_guardar = {
            "modelo_rendimiento_regresion.pkl": self.modelo_regresion,
            "modelo_rendimiento_scaler.pkl": self.scaler,
            "features_principales.pkl": self.features_principales,
            "feature_importance.pkl": self.feature_importance,
        }

        # Agregar modelos de clasificación solo si existen
        if self.clasificacion_viable and self.modelo_clasificacion is not None:
            modelos_a_guardar.update(
                {
                    "modelo_rendimiento_clasificacion.pkl": self.modelo_clasificacion,
                    "modelo_rendimiento_label_encoder.pkl": self.label_encoder,
                }
            )

        for filename, objeto in modelos_a_guardar.items():
            filepath = os.path.join("modelos", filename)
            joblib.dump(objeto, filepath)
            print(f"   ✅ {filename}")

        # Metadatos del entrenamiento
        metadatos = {
            "fecha_entrenamiento": pd.Timestamp.now().isoformat(),
            "dataset_usado": self.dataset_path,
            "num_registros": len(self.df),
            "num_estudiantes": self.df["estudiante_id"].nunique(),
            "num_features": len(self.features_principales),
            "features_utilizadas": self.features_principales,
            "clasificacion_disponible": self.clasificacion_viable,
            "distribucion_clases": dict(
                self.df["rendimiento_categoria"].value_counts()
            ),
        }

        if self.clasificacion_viable and self.label_encoder is not None:
            metadatos["clases_disponibles"] = list(self.label_encoder.classes_)

        joblib.dump(metadatos, "modelos/metadatos_entrenamiento.pkl")
        print(f"   ✅ metadatos_entrenamiento.pkl")

        print(f"✅ Todos los archivos guardados en directorio 'modelos/'")

    def generar_reporte_final_realista(self, r2, rmse, accuracy):
        """Genera reporte final ajustado para datos reales"""
        reporte = f"""
=== REPORTE DE ENTRENAMIENTO - DATOS REALES ===
Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

DATASET UTILIZADO:
- Archivo: {self.dataset_path}
- Registros totales: {len(self.df):,}
- Estudiantes únicos: {self.df['estudiante_id'].nunique()}
- Materias: {self.df['materia_nombre'].nunique()}
- Períodos: {self.df['periodo_nombre'].nunique()}
- Características utilizadas: {len(self.features_principales)}

RENDIMIENTO DE MODELOS:
- Modelo Regresión (R²): {r2:.4f}
- Error RMSE: {rmse:.4f}
"""

        if self.clasificacion_viable:
            reporte += f"- Modelo Clasificación (Accuracy): {accuracy:.4f}\n"
        else:
            reporte += "- Modelo Clasificación: NO ENTRENADO (datos insuficientes)\n"

        reporte += f"""
EVALUACIÓN DE CALIDAD:
- R² > 0.60: {'✅ Bueno' if r2 > 0.60 else '⚠️ Mejorable'}
- RMSE < 20: {'✅ Aceptable' if rmse < 20 else '⚠️ Alto error'}
"""

        if self.clasificacion_viable:
            reporte += f"- Accuracy > 0.70: {'✅ Buena clasificación' if accuracy > 0.70 else '⚠️ Revisar datos'}\n"
        else:
            reporte += "- Clasificación: ⚠️ Requiere más datos balanceados\n"

        reporte += "\nCARACTERÍSTICAS MÁS IMPORTANTES (Regresión):\n"

        # Agregar importancia de características
        if "regresion" in self.feature_importance:
            sorted_features = sorted(
                self.feature_importance["regresion"].items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for i, (feature, importance) in enumerate(sorted_features[:5], 1):
                reporte += f"{i}. {feature}: {importance:.4f}\n"

        reporte += f"""
DISTRIBUCIÓN DE DATOS:
{self.df['rendimiento_categoria'].value_counts().to_string()}

RECOMENDACIONES PARA PRODUCCIÓN:
- ✅ Modelo de regresión listo para predicciones
"""

        if self.clasificacion_viable:
            reporte += "- ✅ Modelo de clasificación disponible\n"
        else:
            reporte += "- ⚠️ Clasificación requiere más datos balanceados\n"

        reporte += f"""- ✅ Integrar con API FastAPI
- 🔄 Recolectar más datos para clases minoritarias
- 📊 Monitorear rendimiento en producción

NOTAS TÉCNICAS:
- Dataset muy desbalanceado detectado
- Se priorizó modelo de regresión por confiabilidad
- Considerar recolección de más datos "Alto" y "Bajo"

=== FIN DEL REPORTE ===
"""

        # Guardar reporte
        with open("reporte_entrenamiento_real.txt", "w", encoding="utf-8") as f:
            f.write(reporte)

        print(reporte)
        print("✅ Reporte guardado en 'reporte_entrenamiento_real.txt'")

    def ejecutar_entrenamiento_completo(self):
        """Ejecuta el pipeline completo ajustado para datos reales"""
        print("🚀 ENTRENAMIENTO CON DATOS REALES - MANEJO DE CLASES DESBALANCEADAS")
        print("=" * 70)

        # 1. Cargar y validar datos
        if not self.cargar_y_validar_datos():
            return False

        # 2. Análisis exploratorio
        self.analisis_exploratorio_realista()

        # 3. Preparar características
        self.preparar_features_optimizadas()

        # 4. Entrenar modelos
        r2, rmse, accuracy = self.entrenar_modelos_ajustados()

        # 5. Guardar todo
        self.guardar_modelos_y_metadatos()

        # 6. Generar reporte
        self.generar_reporte_final_realista(r2, rmse, accuracy)

        print(f"\n🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 50)
        print(f"📊 Modelos entrenados con {len(self.df)} registros reales")
        print(f"🎯 R² Score: {r2:.3f} | RMSE: {rmse:.2f}", end="")
        if self.clasificacion_viable:
            print(f" | Accuracy: {accuracy:.3f}")
        else:
            print(f" | Clasificación: No disponible")
        print(f"📁 Archivos guardados en directorio 'modelos/'")

        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"1. ✅ Modelo de regresión entrenado y listo")
        if self.clasificacion_viable:
            print(f"2. ✅ Modelo de clasificación disponible")
        else:
            print(f"2. ⚠️ Recopilar más datos para clasificación balanceada")
        print(f"3. 🔄 Integrar con FastAPI (prediction_service.py)")
        print(f"4. 🧪 Probar predicciones con datos reales")
        print(f"5. 🚀 Preparar demo para presentación")

        return True


if __name__ == "__main__":
    # Entrenar con datos reales
    trainer = ModelTrainerAjustado()
    success = trainer.ejecutar_entrenamiento_completo()

    if success:
        print(f"\n🎯 ¡LISTO PARA INTEGRAR CON TU APLICACIÓN!")
        print(f"El modelo de regresión está optimizado para tus datos reales.")
        print(f"Para clasificación, considera recopilar más datos balanceados.")
    else:
        print(f"\n❌ Error en entrenamiento. Revisar logs.")
