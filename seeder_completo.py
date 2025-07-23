"""
🌱 Seeder completo para probar el sistema unificado
Crea admin, docentes, estudiantes, padres y sus relaciones
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.docente import Docente
from app.models.estudiante import Estudiante
from app.models.padre import Padre
from app.models.padre_estudiante import PadreEstudiante
from app.seguridad import hash_contrasena
from datetime import date, datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def crear_admin(db: Session):
    """Crear usuario administrador"""
    logger.info("👑 Creando administrador...")
    
    admin_email = "admin@colegio.edu.bo"
    admin_existente = db.query(Docente).filter(Docente.correo == admin_email).first()
    
    if not admin_existente:
        admin = Docente(
            nombre="Administrador",
            apellido="Sistema",
            telefono="70000001",
            correo=admin_email,
            genero="Masculino",
            contrasena=hash_contrasena("admin123"),
            is_doc=False  # False = Admin
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"✅ Admin creado: {admin_email} / admin123")
        return admin
    else:
        logger.info(f"ℹ️ Admin ya existe: {admin_email}")
        return admin_existente


def crear_docentes(db: Session):
    """Crear docentes de ejemplo"""
    logger.info("👨‍🏫 Creando docentes...")
    
    docentes_data = [
        {
            "nombre": "Carlos",
            "apellido": "Rodríguez", 
            "telefono": "70123456",
            "correo": "carlos.rodriguez@colegio.edu.bo",
            "genero": "Masculino",
            "contrasena": "docente123"
        },
        {
            "nombre": "María",
            "apellido": "González",
            "telefono": "70234567", 
            "correo": "maria.gonzalez@colegio.edu.bo",
            "genero": "Femenino",
            "contrasena": "docente456"
        },
        {
            "nombre": "Luis",
            "apellido": "Mamani",
            "telefono": "70345678",
            "correo": "luis.mamani@colegio.edu.bo", 
            "genero": "Masculino",
            "contrasena": "docente789"
        }
    ]
    
    docentes_creados = []
    
    for data in docentes_data:
        existente = db.query(Docente).filter(Docente.correo == data["correo"]).first()
        
        if not existente:
            docente = Docente(
                nombre=data["nombre"],
                apellido=data["apellido"],
                telefono=data["telefono"],
                correo=data["correo"],
                genero=data["genero"],
                contrasena=hash_contrasena(data["contrasena"]),
                is_doc=True  # True = Docente
            )
            db.add(docente)
            db.commit()
            db.refresh(docente)
            docentes_creados.append(docente)
            logger.info(f"✅ Docente creado: {data['correo']} / {data['contrasena']}")
        else:
            docentes_creados.append(existente)
            logger.info(f"ℹ️ Docente ya existe: {data['correo']}")
    
    return docentes_creados


def crear_estudiantes(db: Session):
    """Crear estudiantes de ejemplo"""
    logger.info("🎓 Creando estudiantes...")
    
    estudiantes_data = [
        {
            "nombre": "Ana María",
            "apellido": "Pérez Quispe",
            "fecha_nacimiento": date(2010, 3, 15),
            "genero": "Femenino",
            "nombre_tutor": "Juan Pérez",
            "telefono_tutor": "70111111",
            "direccion_casa": "Av. 6 de Agosto 1234, La Paz",
            "correo": "ana.perez@estudiante.edu.bo",
            "contrasena": "estudiante123"
        },
        {
            "nombre": "Carlos Andrés", 
            "apellido": "González López",
            "fecha_nacimiento": date(2011, 7, 22),
            "genero": "Masculino",
            "nombre_tutor": "María González",
            "telefono_tutor": "70222222",
            "direccion_casa": "Calle Murillo 567, La Paz",
            "correo": "carlos.gonzalez@estudiante.edu.bo",
            "contrasena": "estudiante456"
        },
        {
            "nombre": "Sofía",
            "apellido": "Mamani Choque",
            "fecha_nacimiento": date(2009, 11, 8),
            "genero": "Femenino", 
            "nombre_tutor": "Rosa Choque",
            "telefono_tutor": "70333333",
            "direccion_casa": "Zona Sur, Calle 21 de Calacoto 890",
            "correo": "sofia.mamani@estudiante.edu.bo",
            "contrasena": "estudiante789"
        },
        {
            "nombre": "Diego",
            "apellido": "Vargas Rojas",
            "fecha_nacimiento": date(2012, 4, 12),
            "genero": "Masculino",
            "nombre_tutor": "Roberto Vargas",
            "telefono_tutor": "70444444", 
            "direccion_casa": "El Alto, Villa Dolores 345",
            "correo": "diego.vargas@estudiante.edu.bo",
            "contrasena": "estudiante321"
        },
        {
            "nombre": "Valeria",
            "apellido": "Condori Silva",
            "fecha_nacimiento": date(2010, 9, 30),
            "genero": "Femenino",
            "nombre_tutor": "Carmen Silva",
            "telefono_tutor": "70555555",
            "direccion_casa": "Sopocachi, Calle Rosendo Gutiérrez 123",
            "correo": "valeria.condori@estudiante.edu.bo", 
            "contrasena": "estudiante654"
        }
    ]
    
    estudiantes_creados = []
    
    for data in estudiantes_data:
        existente = db.query(Estudiante).filter(Estudiante.correo == data["correo"]).first()
        
        if not existente:
            estudiante = Estudiante(
                nombre=data["nombre"],
                apellido=data["apellido"],
                fecha_nacimiento=data["fecha_nacimiento"],
                genero=data["genero"],
                nombre_tutor=data["nombre_tutor"],
                telefono_tutor=data["telefono_tutor"],
                direccion_casa=data["direccion_casa"],
                correo=data["correo"],
                contrasena=hash_contrasena(data["contrasena"])
            )
            db.add(estudiante)
            db.commit()
            db.refresh(estudiante)
            estudiantes_creados.append(estudiante)
            logger.info(f"✅ Estudiante creado: {data['correo']} / {data['contrasena']}")
        else:
            estudiantes_creados.append(existente)
            logger.info(f"ℹ️ Estudiante ya existe: {data['correo']}")
    
    return estudiantes_creados


def crear_padres(db: Session):
    """Crear padres de ejemplo"""
    logger.info("👨‍👩‍👧‍👦 Creando padres...")
    
    padres_data = [
        {
            "nombre": "Juan Carlos",
            "apellido": "Pérez Mendoza", 
            "telefono": "70111111",
            "correo": "juan.perez@padre.com",
            "genero": "Masculino",
            "contrasena": "padre123"
        },
        {
            "nombre": "María Elena",
            "apellido": "González Quispe",
            "telefono": "70222222",
            "correo": "maria.gonzalez@madre.com", 
            "genero": "Femenino",
            "contrasena": "madre123"
        },
        {
            "nombre": "Rosa Carmen",
            "apellido": "Choque Mamani",
            "telefono": "70333333",
            "correo": "rosa.choque@madre.com",
            "genero": "Femenino", 
            "contrasena": "madre456"
        },
        {
            "nombre": "Roberto",
            "apellido": "Vargas López",
            "telefono": "70444444",
            "correo": "roberto.vargas@padre.com",
            "genero": "Masculino",
            "contrasena": "padre456"
        },
        {
            "nombre": "Carmen Lucía",
            "apellido": "Silva Condori",
            "telefono": "70555555", 
            "correo": "carmen.silva@madre.com",
            "genero": "Femenino",
            "contrasena": "madre789"
        }
    ]
    
    padres_creados = []
    
    for data in padres_data:
        existente = db.query(Padre).filter(Padre.correo == data["correo"]).first()
        
        if not existente:
            padre = Padre(
                nombre=data["nombre"],
                apellido=data["apellido"],
                telefono=data["telefono"],
                correo=data["correo"],
                genero=data["genero"],
                contrasena=hash_contrasena(data["contrasena"])
            )
            db.add(padre)
            db.commit()
            db.refresh(padre)
            padres_creados.append(padre)
            logger.info(f"✅ Padre creado: {data['correo']} / {data['contrasena']}")
        else:
            padres_creados.append(existente)
            logger.info(f"ℹ️ Padre ya existe: {data['correo']}")
    
    return padres_creados


def crear_relaciones_padre_hijo(db: Session, padres: list, estudiantes: list):
    """Crear relaciones entre padres e hijos"""
    logger.info("🔗 Creando relaciones padre-hijo...")
    
    # Definir relaciones familiares realistas
    relaciones = [
        # Familia Pérez - Ana María tiene papá y mamá
        {"padre_correo": "juan.perez@padre.com", "estudiante_correo": "ana.perez@estudiante.edu.bo"},
        {"padre_correo": "maria.gonzalez@madre.com", "estudiante_correo": "ana.perez@estudiante.edu.bo"},
        
        # Familia González - Carlos Andrés tiene solo mamá
        {"padre_correo": "maria.gonzalez@madre.com", "estudiante_correo": "carlos.gonzalez@estudiante.edu.bo"},
        
        # Familia Mamani - Sofía tiene solo mamá
        {"padre_correo": "rosa.choque@madre.com", "estudiante_correo": "sofia.mamani@estudiante.edu.bo"},
        
        # Familia Vargas - Diego tiene papá
        {"padre_correo": "roberto.vargas@padre.com", "estudiante_correo": "diego.vargas@estudiante.edu.bo"},
        
        # Familia Condori - Valeria tiene mamá  
        {"padre_correo": "carmen.silva@madre.com", "estudiante_correo": "valeria.condori@estudiante.edu.bo"},
        
        # Relaciones adicionales - María González tiene dos hijos
        {"padre_correo": "maria.gonzalez@madre.com", "estudiante_correo": "valeria.condori@estudiante.edu.bo"},
    ]
    
    relaciones_creadas = 0
    
    for relacion in relaciones:
        # Buscar padre
        padre = next((p for p in padres if p.correo == relacion["padre_correo"]), None)
        # Buscar estudiante  
        estudiante = next((e for e in estudiantes if e.correo == relacion["estudiante_correo"]), None)
        
        if padre and estudiante:
            # Verificar si ya existe la relación
            relacion_existente = db.query(PadreEstudiante).filter(
                PadreEstudiante.padre_id == padre.id,
                PadreEstudiante.estudiante_id == estudiante.id
            ).first()
            
            if not relacion_existente:
                nueva_relacion = PadreEstudiante(
                    padre_id=padre.id,
                    estudiante_id=estudiante.id
                )
                db.add(nueva_relacion)
                relaciones_creadas += 1
                logger.info(f"✅ Relación creada: {padre.nombre} {padre.apellido} -> {estudiante.nombre} {estudiante.apellido}")
            else:
                logger.info(f"ℹ️ Relación ya existe: {padre.nombre} -> {estudiante.nombre}")
        else:
            logger.warning(f"⚠️ No se pudo crear relación: padre o estudiante no encontrado")
    
    db.commit()
    logger.info(f"✅ Total relaciones padre-hijo creadas: {relaciones_creadas}")


def mostrar_resumen(db: Session):
    """Mostrar resumen de datos creados"""
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMEN DE DATOS CREADOS")
    logger.info("="*60)
    
    # Contar registros
    total_docentes = db.query(Docente).count()
    total_estudiantes = db.query(Estudiante).count() 
    total_padres = db.query(Padre).count()
    total_relaciones = db.query(PadreEstudiante).count()
    
    logger.info(f"👨‍🏫 Docentes (incluye admin): {total_docentes}")
    logger.info(f"🎓 Estudiantes: {total_estudiantes}")
    logger.info(f"👨‍👩‍👧‍👦 Padres: {total_padres}")
    logger.info(f"🔗 Relaciones padre-hijo: {total_relaciones}")
    
    logger.info("\n🔑 CREDENCIALES DE PRUEBA:")
    logger.info("-" * 40)
    logger.info("🔐 ADMIN:")
    logger.info("   Email: admin@colegio.edu.bo")
    logger.info("   Pass:  admin123")
    logger.info("   Tipo:  docente (is_doc=false)")
    
    logger.info("\n👨‍🏫 DOCENTES:")
    logger.info("   Email: carlos.rodriguez@colegio.edu.bo | Pass: docente123")
    logger.info("   Email: maria.gonzalez@colegio.edu.bo  | Pass: docente456") 
    logger.info("   Email: luis.mamani@colegio.edu.bo     | Pass: docente789")
    logger.info("   Tipo:  docente (is_doc=true)")
    
    logger.info("\n🎓 ESTUDIANTES:")
    logger.info("   Email: ana.perez@estudiante.edu.bo      | Pass: estudiante123")
    logger.info("   Email: carlos.gonzalez@estudiante.edu.bo| Pass: estudiante456")
    logger.info("   Email: sofia.mamani@estudiante.edu.bo   | Pass: estudiante789")
    logger.info("   Email: diego.vargas@estudiante.edu.bo   | Pass: estudiante321")
    logger.info("   Email: valeria.condori@estudiante.edu.bo| Pass: estudiante654")
    logger.info("   Tipo:  estudiante")
    
    logger.info("\n👨‍👩‍👧‍👦 PADRES:")
    logger.info("   Email: juan.perez@padre.com      | Pass: padre123")
    logger.info("   Email: maria.gonzalez@madre.com  | Pass: madre123") 
    logger.info("   Email: rosa.choque@madre.com     | Pass: madre456")
    logger.info("   Email: roberto.vargas@padre.com  | Pass: padre456")
    logger.info("   Email: carmen.silva@madre.com    | Pass: madre789")
    logger.info("   Tipo:  padre")
    
    logger.info("\n👪 RELACIONES FAMILIARES:")
    logger.info("   • Ana María Pérez: Juan Pérez (papá) + María González (mamá)")
    logger.info("   • Carlos González: María González (mamá)")
    logger.info("   • Sofía Mamani: Rosa Choque (mamá)")
    logger.info("   • Diego Vargas: Roberto Vargas (papá)")
    logger.info("   • Valeria Condori: Carmen Silva (mamá) + María González (madrina)")
    
    logger.info("\n🚀 ENDPOINTS PARA PROBAR:")
    logger.info("   POST /auth/login - Login unificado")
    logger.info("   GET  /auth/profile - Perfil del usuario")
    logger.info("   GET  /padres/mis-hijos - Hijos del padre")
    logger.info("   GET  /estudiantes/mi-perfil - Perfil del estudiante")
    logger.info("   GET  /docs - Documentación interactiva")


def seed_sistema_completo():
    """Función principal para crear todos los datos de prueba"""
    db = SessionLocal()
    try:
        logger.info("🌱 INICIANDO SEEDER COMPLETO DEL SISTEMA")
        logger.info("="*60)
        
        # Crear datos paso a paso
        admin = crear_admin(db)
        docentes = crear_docentes(db)
        estudiantes = crear_estudiantes(db)
        padres = crear_padres(db)
        
        # Crear relaciones familiares
        crear_relaciones_padre_hijo(db, padres, estudiantes)
        
        # Mostrar resumen
        mostrar_resumen(db)
        
        logger.info("\n✅ SEEDER COMPLETADO EXITOSAMENTE")
        logger.info("🎯 Ejecuta 'python examples/test_login_unificado.py' para probar")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando seeder: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_sistema_completo()