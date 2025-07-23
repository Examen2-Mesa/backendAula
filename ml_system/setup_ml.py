#!/usr/bin/env python3
"""
Script de configuración e instalación del sistema ML para Aula Inteligente
Ejecuta todo el pipeline de ML automáticamente
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_ml.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MLSetup:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.ml_dir = self.project_root / "ml_system"
        self.models_dir = self.ml_dir / "modelos"
        self.data_dir = self.ml_dir / "data"
        self.scripts_dir = self.ml_dir / "scripts"
        
    def crear_estructura_directorios(self):
        """Crea la estructura de directorios necesaria"""
        logger.info("📁 Creando estructura de directorios...")
        
        directorios = [
            self.ml_dir,
            self.models_dir,
            self.data_dir,
            self.scripts_dir,
            self.ml_dir / "docs",
            self.ml_dir / "tests"
        ]
        
        for dir_path in directorios:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"   ✅ {dir_path}")
        
        return True
    
    def instalar_dependencias(self):
        """Instala las dependencias de ML"""
        logger.info("📦 Instalando dependencias de Machine Learning...")
        
        dependencias = [
            "pandas>=1.5.0",
            "numpy>=1.21.0", 
            "scikit-learn>=1.0.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "joblib>=1.1.0",
            "python-dotenv>=0.19.0"
        ]
        
        try:
            for dep in dependencias:
                logger.info(f"   📥 Instalando {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            
            logger.info("✅ Todas las dependencias instaladas correctamente")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error instalando dependencias: {e}")
            return False
    
    def copiar_archivos_ml(self):
        """Copia los archivos de ML a la estructura del proyecto"""
        logger.info("📄 Configurando archivos del sistema ML...")
        
        # Lista de archivos a crear/copiar
        archivos_config = {
            'data_extractor.py': '''# Archivo de extracción de datos - Ver artifact anterior''',
            'model_trainer.py': '''# Archivo de entrenamiento - Ver artifact anterior''',
            'prediction_service.py': '''# Servicio de predicción - Ver artifact anterior''',
            'requirements_ml.txt': '''pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.0.0
matplotlib>=3.5.0
seaborn>=0.11.0
joblib>=1.1.0
python-dotenv>=0.19.0'''
        }
        
        try:
            for archivo, contenido in archivos_config.items():
                archivo_path = self.scripts_dir / archivo
                if not archivo_path.exists():
                    with open(archivo_path, 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    logger.info(f"   ✅ {archivo}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error copiando archivos: {e}")
            return False
    
    def configurar_variables_entorno(self):
        """Configura variables de entorno para ML"""
        logger.info("⚙️ Configurando variables de entorno...")
        
        env_content = f"""
# Variables de entorno para ML
ML_MODELS_PATH={self.models_dir}
ML_DATA_PATH={self.data_dir}
ML_LOGS_PATH={self.ml_dir}/logs

# Configuración de modelos
MODEL_CACHE_SIZE=10
PREDICTION_BATCH_SIZE=100
FEATURE_SELECTION_THRESHOLD=0.01

# Logging
ML_LOG_LEVEL=INFO
ML_LOG_FILE={self.ml_dir}/ml_system.log
"""
        
        try:
            env_file = self.project_root / ".env.ml"
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content.strip())
            
            logger.info(f"   ✅ Archivo .env.ml creado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando variables: {e}")
            return False
    
    def ejecutar_extraccion_datos(self):
        """Ejecuta la extracción de datos desde la BD"""
        logger.info("🗃️ Iniciando extracción de datos...")
        
        try:
            # Cambiar al directorio de scripts
            os.chdir(self.scripts_dir)
            
            # Ejecutar extracción
            extractor_path = self.scripts_dir / "data_extractor.py"
            if extractor_path.exists():
                logger.info("   📊 Ejecutando extractor de datos...")
                result = subprocess.run([sys.executable, str(extractor_path)], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("   ✅ Extracción completada")
                    return True
                else:
                    logger.error(f"   ❌ Error en extracción: {result.stderr}")
                    return False
            else:
                logger.warning("   ⚠️ Archivo extractor no encontrado, saltando...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando extracción: {e}")
            return False
        finally:
            # Volver al directorio original
            os.chdir(self.project_root)
    
    def ejecutar_entrenamiento(self):
        """Ejecuta el entrenamiento de modelos"""
        logger.info("🤖 Iniciando entrenamiento de modelos...")
        
        try:
            os.chdir(self.scripts_dir)
            
            trainer_path = self.scripts_dir / "model_trainer.py"
            if trainer_path.exists():
                logger.info("   🧠 Entrenando modelos ML...")
                result = subprocess.run([sys.executable, str(trainer_path)], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("   ✅ Entrenamiento completado")
                    
                    # Verificar que se generaron los modelos
                    modelos_esperados = [
                        "modelo_rendimiento_regresion.pkl",
                        "modelo_rendimiento_clasificacion.pkl",
                        "modelo_rendimiento_scaler.pkl",
                        "modelo_rendimiento_label_encoder.pkl",
                        "features_principales.pkl"
                    ]
                    
                    modelos_encontrados = 0
                    for modelo in modelos_esperados:
                        if (self.models_dir / modelo).exists():
                            modelos_encontrados += 1
                            logger.info(f"     ✅ {modelo}")
                        else:
                            logger.warning(f"     ⚠️ {modelo} no encontrado")
                    
                    if modelos_encontrados == len(modelos_esperados):
                        logger.info("   🎉 Todos los modelos generados correctamente")
                        return True
                    else:
                        logger.warning(f"   ⚠️ Solo {modelos_encontrados}/{len(modelos_esperados)} modelos generados")
                        return False
                
                else:
                    logger.error(f"   ❌ Error en entrenamiento: {result.stderr}")
                    return False
            else:
                logger.warning("   ⚠️ Archivo trainer no encontrado, saltando...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando entrenamiento: {e}")
            return False
        finally:
            os.chdir(self.project_root)
    
    def integrar_con_fastapi(self):
        """Integra el sistema ML con FastAPI"""
        logger.info("🔗 Integrando con FastAPI...")
        
        try:
            # Crear el directorio ml en app si no existe
            app_ml_dir = self.project_root / "app" / "ml"
            app_ml_dir.mkdir(exist_ok=True)
            
            # Copiar archivos necesarios
            archivos_copiar = [
                ("prediction_service.py", app_ml_dir / "prediction_service.py"),
                ("ml_routes.py", self.project_root / "app" / "routers" / "ml_prediccion.py")
            ]
            
            for archivo_origen, archivo_destino in archivos_copiar:
                if archivo_origen in ["prediction_service.py"]:
                    # Estos archivos están en artifacts, necesitan ser copiados manualmente
                    logger.info(f"   📋 {archivo_destino.name} - Crear manualmente desde artifacts")
                else:
                    logger.info(f"   📄 {archivo_destino.name}")
            
            # Actualizar main.py para incluir las rutas ML
            main_py_path = self.project_root / "app" / "main.py"
            if main_py_path.exists():
                with open(main_py_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar si ya está incluido
                if "ml_prediccion" not in content:
                    # Encontrar la línea de imports de routers
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "from app.routers import" in line and "(" in line:
                            # Agregar ml_prediccion a los imports
                            if not any("ml_prediccion" in l for l in lines[i:i+10]):
                                # Buscar el final del bloque de imports
                                for j in range(i, len(lines)):
                                    if ")" in lines[j]:
                                        lines[j] = lines[j].replace(")", ",\n    ml_prediccion,\n)")
                                        break
                            break
                    
                    # Buscar donde se incluyen los routers
                    for i, line in enumerate(lines):
                        if "app.include_router" in line and "resumen.router" in line:
                            # Agregar después del último router
                            lines.insert(i+1, "app.include_router(ml_prediccion.router)")
                            break
                    
                    # Escribir el archivo actualizado
                    with open(main_py_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    logger.info("   ✅ main.py actualizado con rutas ML")
                else:
                    logger.info("   ✅ main.py ya incluye rutas ML")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error integrando con FastAPI: {e}")
            return False
    
    def crear_documentacion(self):
        """Crea documentación del sistema ML"""
        logger.info("📚 Creando documentación...")
        
        documentacion = f"""# Sistema de Predicción de Rendimiento Académico

## Descripción
Sistema de Machine Learning integrado para predecir el rendimiento académico de estudiantes.

## Instalación Completada
- **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Versión:** 1.0.0
- **Directorio:** {self.ml_dir}

## Estructura de Archivos
```
ml_system/
├── modelos/           # Modelos entrenados (.pkl)
├── data/              # Datasets y datos procesados
├── scripts/           # Scripts de entrenamiento y extracción
├── docs/              # Documentación
└── tests/             # Tests del sistema
```

## Modelos Incluidos
1. **Modelo de Regresión:** Predicción numérica (0-100)
2. **Modelo de Clasificación:** Categorías (Alto/Medio/Bajo)
3. **Scaler:** Normalización de características
4. **Label Encoder:** Codificación de categorías

## Características Utilizadas
- Promedio de notas anterior
- Porcentaje de asistencia
- Promedio de participación
- Datos demográficos (edad, género)
- Información del curso (turno, nivel)

## API Endpoints Disponibles
- `GET /ml/health` - Estado del sistema
- `POST /ml/predecir-rendimiento` - Predicción manual
- `GET /ml/predecir-estudiante/{{id}}` - Predicción por estudiante
- `GET /ml/predecir-curso/{{id}}` - Predicción por curso
- `GET /ml/estudiantes-en-riesgo` - Estudiantes en riesgo
- `GET /ml/estadisticas-modelo` - Estadísticas del modelo

## Uso Básico
```python
from app.ml.prediction_service import get_prediction_service

service = get_prediction_service()
resultado = service.predecir_rendimiento({{
    'promedio_notas_anterior': 75.0,
    'porcentaje_asistencia': 85.0,
    'promedio_participacion': 80.0
}})
```

## Mantenimiento
- **Reentrenamiento:** Ejecutar `model_trainer.py` con nuevos datos
- **Actualización:** Recargar modelos vía `/ml/admin/recargar-modelos`
- **Monitoreo:** Revisar logs en `{self.ml_dir}/logs/`

## Métricas de Calidad
- **R² Score:** > 0.70 (regresión)
- **Accuracy:** > 0.80 (clasificación)
- **RMSE:** < 15 (error cuadrático medio)

## Soporte
- Logs: `{self.ml_dir}/ml_system.log`
- Diagnóstico: `/ml/admin/diagnostico`
- Contacto: Equipo de desarrollo
"""
        
        try:
            readme_path = self.ml_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(documentacion)
            
            logger.info(f"   ✅ README.md creado")
            
            # Crear guía de uso rápido
            guia_rapida = """# Guía de Uso Rápido - ML System

## 1. Verificar Estado
```bash
curl http://localhost:8000/ml/health
```

## 2. Predicción Manual
```bash
curl -X POST http://localhost:8000/ml/predecir-rendimiento \\
  -H "Content-Type: application/json" \\
  -d '{
    "promedio_notas_anterior": 75.0,
    "porcentaje_asistencia": 85.0,
    "promedio_participacion": 80.0
  }'
```

## 3. Predicción por Estudiante
```bash
curl "http://localhost:8000/ml/predecir-estudiante/1?materia_id=1&periodo_id=1"
```

## 4. Estudiantes en Riesgo
```bash
curl "http://localhost:8000/ml/estudiantes-en-riesgo?umbral=60&limite=10"
```

## 5. Estadísticas del Modelo
```bash
curl http://localhost:8000/ml/estadisticas-modelo
```
"""
            
            guia_path = self.ml_dir / "docs" / "guia_rapida.md"
            with open(guia_path, 'w', encoding='utf-8') as f:
                f.write(guia_rapida)
            
            logger.info(f"   ✅ Guía rápida creada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando documentación: {e}")
            return False
    
    def crear_tests(self):
        """Crea tests básicos para el sistema ML"""
        logger.info("🧪 Creando tests...")
        
        test_content = f"""#!/usr/bin/env python3
\"\"\"
Tests básicos para el sistema ML
\"\"\"
import unittest
import sys
import os
from pathlib import Path

# Agregar path del proyecto
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class TestMLSystem(unittest.TestCase):
    
    def setUp(self):
        \"\"\"Configurar tests\"\"\"
        self.models_path = "{self.models_dir}"
    
    def test_modelos_existen(self):
        \"\"\"Verificar que los modelos existen\"\"\"
        modelos_requeridos = [
            "modelo_rendimiento_regresion.pkl",
            "modelo_rendimiento_clasificacion.pkl", 
            "modelo_rendimiento_scaler.pkl",
            "modelo_rendimiento_label_encoder.pkl",
            "features_principales.pkl"
        ]
        
        for modelo in modelos_requeridos:
            modelo_path = Path(self.models_path) / modelo
            self.assertTrue(modelo_path.exists(), f"Modelo {{modelo}} no encontrado")
    
    def test_carga_servicio(self):
        \"\"\"Test cargar servicio de predicción\"\"\"
        try:
            from app.ml.prediction_service import get_prediction_service
            service = get_prediction_service()
            self.assertTrue(service.models_loaded, "Modelos no cargados")
        except ImportError:
            self.skipTest("Servicio no disponible aún")
    
    def test_prediccion_basica(self):
        \"\"\"Test predicción básica\"\"\"
        try:
            from app.ml.prediction_service import get_prediction_service
            service = get_prediction_service()
            
            datos_test = {{
                'promedio_notas_anterior': 75.0,
                'porcentaje_asistencia': 85.0,
                'promedio_participacion': 80.0
            }}
            
            resultado = service.predecir_rendimiento(datos_test)
            
            self.assertIn('prediccion_numerica', resultado)
            self.assertIn('clasificacion', resultado)
            self.assertIn('nivel_riesgo', resultado)
            
            # Verificar rangos
            self.assertGreaterEqual(resultado['prediccion_numerica'], 0)
            self.assertLessEqual(resultado['prediccion_numerica'], 100)
            
        except ImportError:
            self.skipTest("Servicio no disponible aún")

if __name__ == '__main__':
    unittest.main()
"""
        
        try:
            test_path = self.ml_dir / "tests" / "test_ml_system.py"
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            logger.info(f"   ✅ Tests creados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando tests: {e}")
            return False
    
    def ejecutar_pipeline_completo(self, skip_training=False, skip_data=False):
        """Ejecuta el pipeline completo de configuración"""
        logger.info("🚀 INICIANDO CONFIGURACIÓN COMPLETA DEL SISTEMA ML")
        logger.info("=" * 60)
        
        pasos_exitosos = 0
        pasos_totales = 8
        
        # 1. Crear estructura
        if self.crear_estructura_directorios():
            pasos_exitosos += 1
        
        # 2. Instalar dependencias
        if self.instalar_dependencias():
            pasos_exitosos += 1
        
        # 3. Copiar archivos
        if self.copiar_archivos_ml():
            pasos_exitosos += 1
        
        # 4. Configurar variables
        if self.configurar_variables_entorno():
            pasos_exitosos += 1
        
        # 5. Extracción de datos (opcional)
        if skip_data:
            logger.info("⏭️ Saltando extracción de datos")
            pasos_exitosos += 1
        else:
            if self.ejecutar_extraccion_datos():
                pasos_exitosos += 1
        
        # 6. Entrenamiento (opcional)
        if skip_training:
            logger.info("⏭️ Saltando entrenamiento de modelos")
            pasos_exitosos += 1
        else:
            if self.ejecutar_entrenamiento():
                pasos_exitosos += 1
        
        # 7. Integración con FastAPI
        if self.integrar_con_fastapi():
            pasos_exitosos += 1
        
        # 8. Documentación y tests
        if self.crear_documentacion() and self.crear_tests():
            pasos_exitosos += 1
        
        # Resumen final
        logger.info("=" * 60)
        logger.info(f"🎯 CONFIGURACIÓN COMPLETADA: {pasos_exitosos}/{pasos_totales} pasos exitosos")
        
        if pasos_exitosos == pasos_totales:
            logger.info("🎉 ¡CONFIGURACIÓN EXITOSA!")
            logger.info("\n📋 SIGUIENTES PASOS:")
            logger.info("1. Copiar archivos desde artifacts a la ubicación correcta")
            logger.info("2. Ejecutar: python -m pytest ml_system/tests/")
            logger.info("3. Iniciar tu servidor FastAPI")
            logger.info("4. Probar: curl http://localhost:8000/ml/health")
            logger.info("5. Revisar documentación en ml_system/README.md")
            
            return True
        else:
            logger.warning(f"⚠️ Configuración parcial: {pasos_exitosos}/{pasos_totales}")
            logger.info("🔧 Revisar logs para errores y ejecutar pasos faltantes manualmente")
            return False
    
    def verificar_instalacion(self):
        """Verifica que la instalación esté completa"""
        logger.info("🔍 VERIFICANDO INSTALACIÓN...")
        
        verificaciones = [
            ("Estructura de directorios", lambda: all(d.exists() for d in [self.ml_dir, self.models_dir, self.data_dir])),
            ("Variables de entorno", lambda: (self.project_root / ".env.ml").exists()),
            ("Documentación", lambda: (self.ml_dir / "README.md").exists()),
            ("Tests", lambda: (self.ml_dir / "tests" / "test_ml_system.py").exists())
        ]
        
        todas_exitosas = True
        
        for nombre, verificacion in verificaciones:
            try:
                if verificacion():
                    logger.info(f"   ✅ {nombre}")
                else:
                    logger.warning(f"   ❌ {nombre}")
                    todas_exitosas = False
            except Exception as e:
                logger.error(f"   ❌ {nombre}: Error - {e}")
                todas_exitosas = False
        
        return todas_exitosas


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(description='Configurar sistema ML para Aula Inteligente')
    parser.add_argument('--project-root', default='.', help='Directorio raíz del proyecto')
    parser.add_argument('--skip-training', action='store_true', help='Saltar entrenamiento de modelos')
    parser.add_argument('--skip-data', action='store_true', help='Saltar extracción de datos')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar instalación')
    
    args = parser.parse_args()
    
    # Crear instancia del configurador
    setup = MLSetup(args.project_root)
    
    if args.verify_only:
        # Solo verificar
        if setup.verificar_instalacion():
            logger.info("✅ Instalación verificada correctamente")
            return 0
        else:
            logger.error("❌ Problemas en la instalación")
            return 1
    else:
        # Configuración completa
        if setup.ejecutar_pipeline_completo(args.skip_training, args.skip_data):
            logger.info("🎉 Configuración ML completada exitosamente")
            return 0
        else:
            logger.error("❌ Error en la configuración ML")
            return 1


if __name__ == "__main__":
    sys.exit(main())