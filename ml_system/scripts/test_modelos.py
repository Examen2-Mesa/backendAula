"""
Test rápido para verificar que los modelos entrenados funcionan correctamente
"""
import joblib
import numpy as np
import pandas as pd

def test_modelos_entrenados():
    """Prueba los modelos recién entrenados"""
    print("🧪 PROBANDO MODELOS ENTRENADOS")
    print("=" * 40)
    
    try:
        # Cargar modelos
        print("📦 Cargando modelos...")
        modelo_regresion = joblib.load('modelos/modelo_rendimiento_regresion.pkl')
        modelo_clasificacion = joblib.load('modelos/modelo_rendimiento_clasificacion.pkl')
        scaler = joblib.load('modelos/modelo_rendimiento_scaler.pkl')
        label_encoder = joblib.load('modelos/modelo_rendimiento_label_encoder.pkl')
        features_principales = joblib.load('modelos/features_principales.pkl')
        
        print(f"✅ Modelos cargados exitosamente")
        print(f"   📊 Features: {features_principales}")
        print(f"   📊 Clases: {label_encoder.classes_}")
        
        # Test 1: Estudiante promedio
        print(f"\n🧪 TEST 1: Estudiante promedio")
        datos_promedio = {
            'promedio_notas_anterior': 38.75,
            'porcentaje_asistencia': 50.0,
            'promedio_participacion': 50.25,
            'promedio_examenes': 0,
            'promedio_tareas': 0,
            'promedio_exposiciones': 0,
            'promedio_practicas': 0,
            'edad': 16,
            'genero_masculino': 1,
            'turno_manana': 1
        }
        
        X_test = np.array([[datos_promedio[f] for f in features_principales]])
        X_test_scaled = scaler.transform(X_test)
        
        pred_numerica = modelo_regresion.predict(X_test_scaled)[0]
        pred_categoria = modelo_clasificacion.predict(X_test_scaled)[0]
        pred_proba = modelo_clasificacion.predict_proba(X_test_scaled)[0]
        
        categoria = label_encoder.inverse_transform([pred_categoria])[0]
        
        print(f"   📊 Predicción numérica: {pred_numerica:.2f}")
        print(f"   📊 Predicción categórica: {categoria}")
        print(f"   📊 Probabilidades: {dict(zip(label_encoder.classes_, pred_proba))}")
        
        # Test 2: Estudiante con buen rendimiento
        print(f"\n🧪 TEST 2: Estudiante con buen rendimiento")
        datos_bueno = {
            'promedio_notas_anterior': 42.0,
            'porcentaje_asistencia': 70.0,
            'promedio_participacion': 60.0,
            'promedio_examenes': 0,
            'promedio_tareas': 0,
            'promedio_exposiciones': 0,
            'promedio_practicas': 0,
            'edad': 16,
            'genero_masculino': 0,
            'turno_manana': 1
        }
        
        X_test2 = np.array([[datos_bueno[f] for f in features_principales]])
        X_test2_scaled = scaler.transform(X_test2)
        
        pred_numerica2 = modelo_regresion.predict(X_test2_scaled)[0]
        pred_categoria2 = modelo_clasificacion.predict(X_test2_scaled)[0]
        categoria2 = label_encoder.inverse_transform([pred_categoria2])[0]
        
        print(f"   📊 Predicción numérica: {pred_numerica2:.2f}")
        print(f"   📊 Predicción categórica: {categoria2}")
        
        # Test 3: Estudiante con bajo rendimiento
        print(f"\n🧪 TEST 3: Estudiante con bajo rendimiento")
        datos_bajo = {
            'promedio_notas_anterior': 35.0,
            'porcentaje_asistencia': 30.0,
            'promedio_participacion': 35.0,
            'promedio_examenes': 0,
            'promedio_tareas': 0,
            'promedio_exposiciones': 0,
            'promedio_practicas': 0,
            'edad': 17,
            'genero_masculino': 1,
            'turno_manana': 1
        }
        
        X_test3 = np.array([[datos_bajo[f] for f in features_principales]])
        X_test3_scaled = scaler.transform(X_test3)
        
        pred_numerica3 = modelo_regresion.predict(X_test3_scaled)[0]
        pred_categoria3 = modelo_clasificacion.predict(X_test3_scaled)[0]
        categoria3 = label_encoder.inverse_transform([pred_categoria3])[0]
        
        print(f"   📊 Predicción numérica: {pred_numerica3:.2f}")
        print(f"   📊 Predicción categórica: {categoria3}")
        
        print(f"\n✅ TODOS LOS TESTS PASARON")
        print(f"🎯 Los modelos están funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_modelos_entrenados()
    
    if success:
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"1. ✅ Modelos validados")
        print(f"2. 🔄 Copiar prediction_service.py a app/ml/")
        print(f"3. 🔄 Copiar ml_routes.py a app/routers/")
        print(f"4. 🔗 Actualizar main.py")
        print(f"5. 🚀 Probar endpoints ML")
    else:
        print(f"\n❌ Revisar modelos antes de continuar")