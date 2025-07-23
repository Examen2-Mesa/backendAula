"""
🔍 Script para debuggear problemas de login con estudiantes y padres
"""
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.docente import Docente
from app.models.estudiante import Estudiante
from app.models.padre import Padre
from app.seguridad import verificar_contrasena, hash_contrasena
from app.services.auth_service import AuthService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probar_hash_contrasena():
    """Probar que el hash de contraseñas funciona correctamente"""
    logger.info("🔐 PROBANDO HASH DE CONTRASEÑAS")
    logger.info("=" * 50)
    
    # Probar hash y verificación
    contrasena_original = "estudiante123"
    hash_generado = hash_contrasena(contrasena_original)
    verificacion = verificar_contrasena(contrasena_original, hash_generado)
    
    logger.info(f"Contraseña original: {contrasena_original}")
    logger.info(f"Hash generado: {hash_generado}")
    logger.info(f"Verificación exitosa: {verificacion}")
    
    if not verificacion:
        logger.error("❌ ERROR: El hash de contraseñas no funciona correctamente")
        return False
    else:
        logger.info("✅ Hash de contraseñas funciona correctamente")
        return True

def verificar_datos_estudiantes(db: Session):
    """Verificar que los estudiantes existen y tienen contraseñas"""
    logger.info("\n🎓 VERIFICANDO DATOS DE ESTUDIANTES")
    logger.info("=" * 50)
    
    estudiantes = db.query(Estudiante).filter(Estudiante.correo.isnot(None)).all()
    
    if not estudiantes:
        logger.error("❌ ERROR: No hay estudiantes con correo en la base de datos")
        return False
    
    logger.info(f"📊 Estudiantes encontrados: {len(estudiantes)}")
    
    for estudiante in estudiantes:
        logger.info(f"\n👤 Estudiante: {estudiante.nombre} {estudiante.apellido}")
        logger.info(f"   📧 Correo: {estudiante.correo}")
        logger.info(f"   🔐 Tiene contraseña: {'Sí' if estudiante.contrasena else 'NO'}")
        
        if estudiante.contrasena:
            logger.info(f"   🔐 Hash contraseña: {estudiante.contrasena[:50]}...")
            
            # Probar verificación con contraseña conocida
            test_passwords = ["estudiante123", "estudiante456", "estudiante789", "estudiante321", "estudiante654"]
            for test_pass in test_passwords:
                if verificar_contrasena(test_pass, estudiante.contrasena):
                    logger.info(f"   ✅ Contraseña correcta: {test_pass}")
                    break
            else:
                logger.warning(f"   ⚠️ No se pudo verificar la contraseña con ninguna de las de prueba")
        else:
            logger.error(f"   ❌ ERROR: Estudiante sin contraseña")
    
    return True

def verificar_datos_padres(db: Session):
    """Verificar que los padres existen y tienen contraseñas"""
    logger.info("\n👨‍👩‍👧‍👦 VERIFICANDO DATOS DE PADRES")
    logger.info("=" * 50)
    
    padres = db.query(Padre).all()
    
    if not padres:
        logger.error("❌ ERROR: No hay padres en la base de datos")
        return False
    
    logger.info(f"📊 Padres encontrados: {len(padres)}")
    
    for padre in padres:
        logger.info(f"\n👤 Padre: {padre.nombre} {padre.apellido}")
        logger.info(f"   📧 Correo: {padre.correo}")
        logger.info(f"   🔐 Tiene contraseña: {'Sí' if padre.contrasena else 'NO'}")
        
        if padre.contrasena:
            logger.info(f"   🔐 Hash contraseña: {padre.contrasena[:50]}...")
            
            # Probar verificación con contraseña conocida
            test_passwords = ["padre123", "madre123", "padre456", "madre456", "madre789"]
            for test_pass in test_passwords:
                if verificar_contrasena(test_pass, padre.contrasena):
                    logger.info(f"   ✅ Contraseña correcta: {test_pass}")
                    break
            else:
                logger.warning(f"   ⚠️ No se pudo verificar la contraseña con ninguna de las de prueba")
        else:
            logger.error(f"   ❌ ERROR: Padre sin contraseña")
    
    return True

def probar_auth_service(db: Session):
    """Probar el AuthService directamente"""
    logger.info("\n🔧 PROBANDO AUTH SERVICE")
    logger.info("=" * 50)
    
    # Casos de prueba
    casos_prueba = [
        {
            "tipo": "estudiante",
            "correo": "ana.perez@estudiante.edu.bo",
            "contrasena": "estudiante123"
        },
        {
            "tipo": "padre", 
            "correo": "juan.perez@padre.com",
            "contrasena": "padre123"
        },
        {
            "tipo": "docente",
            "correo": "admin@colegio.edu.bo", 
            "contrasena": "admin123"
        }
    ]
    
    resultados = []
    
    for caso in casos_prueba:
        logger.info(f"\n🧪 Probando: {caso['tipo']} - {caso['correo']}")
        
        try:
            resultado = AuthService.authenticate_user(
                db, 
                caso['correo'], 
                caso['contrasena'], 
                caso['tipo']
            )
            
            if resultado:
                user, user_type = resultado
                logger.info(f"   ✅ Login exitoso")
                logger.info(f"   👤 Usuario: {user.nombre} {user.apellido}")
                logger.info(f"   🎭 Tipo: {user_type}")
                resultados.append(True)
            else:
                logger.error(f"   ❌ Login falló - AuthService retornó None")
                resultados.append(False)
                
        except Exception as e:
            logger.error(f"   ❌ Error en AuthService: {e}")
            resultados.append(False)
    
    exitosos = sum(resultados)
    logger.info(f"\n📊 Resultados: {exitosos}/{len(casos_prueba)} exitosos")
    
    return exitosos == len(casos_prueba)

def probar_busqueda_directa(db: Session):
    """Probar búsqueda directa en la base de datos"""
    logger.info("\n🔍 PROBANDO BÚSQUEDA DIRECTA EN BD")
    logger.info("=" * 50)
    
    # Probar buscar estudiante
    correo_estudiante = "ana.perez@estudiante.edu.bo"
    estudiante = db.query(Estudiante).filter(Estudiante.correo == correo_estudiante).first()
    
    logger.info(f"🎓 Buscando estudiante: {correo_estudiante}")
    if estudiante:
        logger.info(f"   ✅ Encontrado: {estudiante.nombre} {estudiante.apellido}")
        logger.info(f"   🔐 Contraseña hash: {estudiante.contrasena[:30]}..." if estudiante.contrasena else "   ❌ Sin contraseña")
        
        if estudiante.contrasena:
            # Probar verificación manual
            if verificar_contrasena("estudiante123", estudiante.contrasena):
                logger.info(f"   ✅ Verificación manual exitosa")
            else:
                logger.error(f"   ❌ Verificación manual falló")
    else:
        logger.error(f"   ❌ Estudiante no encontrado")
    
    # Probar buscar padre
    correo_padre = "juan.perez@padre.com"
    padre = db.query(Padre).filter(Padre.correo == correo_padre).first()
    
    logger.info(f"\n👨‍👩‍👧‍👦 Buscando padre: {correo_padre}")
    if padre:
        logger.info(f"   ✅ Encontrado: {padre.nombre} {padre.apellido}")
        logger.info(f"   🔐 Contraseña hash: {padre.contrasena[:30]}..." if padre.contrasena else "   ❌ Sin contraseña")
        
        if padre.contrasena:
            # Probar verificación manual
            if verificar_contrasena("padre123", padre.contrasena):
                logger.info(f"   ✅ Verificación manual exitosa")
            else:
                logger.error(f"   ❌ Verificación manual falló")
    else:
        logger.error(f"   ❌ Padre no encontrado")

def diagnosticar_problema_especifico(db: Session):
    """Diagnosticar el problema específico paso a paso"""
    logger.info("\n🩺 DIAGNÓSTICO ESPECÍFICO DEL PROBLEMA")
    logger.info("=" * 60)
    
    # Caso específico: estudiante
    correo = "ana.perez@estudiante.edu.bo"
    contrasena = "estudiante123"
    tipo = "estudiante"
    
    logger.info(f"🔍 Diagnosticando caso: {tipo} - {correo}")
    
    # Paso 1: Verificar que existe en BD
    estudiante = db.query(Estudiante).filter(Estudiante.correo == correo).first()
    if not estudiante:
        logger.error(f"❌ PROBLEMA: Estudiante no existe en BD")
        return
    
    logger.info(f"✅ Paso 1: Estudiante existe en BD")
    
    # Paso 2: Verificar que tiene contraseña
    if not estudiante.contrasena:
        logger.error(f"❌ PROBLEMA: Estudiante no tiene contraseña")
        return
    
    logger.info(f"✅ Paso 2: Estudiante tiene contraseña")
    
    # Paso 3: Verificar hash de contraseña
    if not verificar_contrasena(contrasena, estudiante.contrasena):
        logger.error(f"❌ PROBLEMA: Hash de contraseña no coincide")
        logger.info(f"   Hash en BD: {estudiante.contrasena}")
        logger.info(f"   Contraseña probada: {contrasena}")
        
        # Probar regenerar hash
        nuevo_hash = hash_contrasena(contrasena)
        logger.info(f"   Nuevo hash generado: {nuevo_hash}")
        
        if verificar_contrasena(contrasena, nuevo_hash):
            logger.info(f"   ✅ Nuevo hash funciona correctamente")
            logger.info(f"   💡 SOLUCIÓN: Ejecutar seeder nuevamente")
        else:
            logger.error(f"   ❌ Problema con función de hash")
        return
    
    logger.info(f"✅ Paso 3: Hash de contraseña es correcto")
    
    # Paso 4: Probar AuthService
    resultado = AuthService.authenticate_user(db, correo, contrasena, tipo)
    if not resultado:
        logger.error(f"❌ PROBLEMA: AuthService falla")
        
        # Debug AuthService línea por línea
        logger.info(f"🔍 Debuggeando AuthService para tipo '{tipo}':")
        
        if tipo == "estudiante":
            user = db.query(Estudiante).filter(Estudiante.correo == correo).first()
            logger.info(f"   Usuario encontrado: {user is not None}")
            if user and user.contrasena:
                hash_ok = verificar_contrasena(contrasena, user.contrasena)
                logger.info(f"   Hash correcto: {hash_ok}")
                if hash_ok:
                    logger.info(f"   ✅ Debería retornar: ({user}, 'estudiante')")
                else:
                    logger.error(f"   ❌ Hash incorrecto en AuthService")
            else:
                logger.error(f"   ❌ Usuario sin contraseña en AuthService")
        return
    
    user, user_type = resultado
    logger.info(f"✅ Paso 4: AuthService funciona correctamente")
    logger.info(f"   Usuario retornado: {user.nombre} {user.apellido}")
    logger.info(f"   Tipo retornado: {user_type}")
    
    logger.info(f"\n🎉 DIAGNÓSTICO: Login debería funcionar correctamente")

def mostrar_solucion_recomendada():
    """Mostrar la solución recomendada basada en el diagnóstico"""
    logger.info("\n💡 SOLUCIONES RECOMENDADAS")
    logger.info("=" * 50)
    
    logger.info("1️⃣ Si los datos no existen o están mal:")
    logger.info("   python scripts/limpiar_datos_prueba.py")
    logger.info("   python scripts/ejecutar_seeder.py")
    
    logger.info("\n2️⃣ Si hay problema con contraseñas:")
    logger.info("   # Actualizar contraseñas manualmente")
    logger.info("   python scripts/arreglar_contrasenas.py")
    
    logger.info("\n3️⃣ Si AuthService falla:")
    logger.info("   # Revisar el código de app/services/auth_service.py")
    
    logger.info("\n4️⃣ Verificar después de cualquier cambio:")
    logger.info("   python scripts/debug_login.py")
    logger.info("   python examples/test_login_unificado.py")

def main():
    """Función principal de debugging"""
    try:
        logger.info("🔍 DEBUGGING LOGIN DE ESTUDIANTES Y PADRES")
        logger.info("=" * 60)
        
        # Obtener sesión de BD
        db = SessionLocal()
        
        try:
            # Ejecutar diagnósticos
            paso1 = probar_hash_contrasena()
            paso2 = verificar_datos_estudiantes(db)
            paso3 = verificar_datos_padres(db)
            
            probar_busqueda_directa(db)
            paso4 = probar_auth_service(db)
            
            diagnosticar_problema_especifico(db)
            
            # Resumen
            logger.info(f"\n📋 RESUMEN DE DIAGNÓSTICO")
            logger.info("=" * 30)
            logger.info(f"Hash contraseñas: {'✅' if paso1 else '❌'}")
            logger.info(f"Datos estudiantes: {'✅' if paso2 else '❌'}")
            logger.info(f"Datos padres: {'✅' if paso3 else '❌'}")
            logger.info(f"AuthService: {'✅' if paso4 else '❌'}")
            
            if not all([paso1, paso2, paso3, paso4]):
                mostrar_solucion_recomendada()
            else:
                logger.info("\n🎉 Todo parece estar funcionando correctamente")
                logger.info("💡 Si aún tienes problemas, verifica que el servidor esté usando el código actualizado")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error durante debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()