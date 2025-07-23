from sqlalchemy.orm import Session
from app.models.docente import Docente
from app.models.estudiante import Estudiante
from app.models.padre import Padre
from app.seguridad import verificar_contrasena
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def authenticate_user(
        db: Session, correo: str, contrasena: str, tipo_usuario: Optional[str] = None
    ) -> Optional[Tuple[Any, str]]:
        """
        Autentica un usuario según su tipo y retorna el usuario y su tipo
        Si tipo_usuario es None, detecta automáticamente el tipo
        """
        logger.info(f"🔐 Intentando autenticar: {correo}")
        if tipo_usuario:
            logger.info(f"   🎭 Tipo especificado: {tipo_usuario}")
        else:
            logger.info(f"   🔍 Auto-detectando tipo de usuario...")

        # Si se especifica tipo_usuario, usar el método anterior (compatibilidad)
        if tipo_usuario:
            return AuthService._authenticate_specific_type(
                db, correo, contrasena, tipo_usuario
            )

        # Auto-detección: buscar en todas las tablas
        return AuthService._authenticate_auto_detect(db, correo, contrasena)

    @staticmethod
    def _authenticate_specific_type(
        db: Session, correo: str, contrasena: str, tipo_usuario: str
    ) -> Optional[Tuple[Any, str]]:
        """Autenticación con tipo específico (método anterior)"""
        if tipo_usuario == "docente":
            return AuthService._try_docente(db, correo, contrasena)
        elif tipo_usuario == "estudiante":
            return AuthService._try_estudiante(db, correo, contrasena)
        elif tipo_usuario == "padre":
            return AuthService._try_padre(db, correo, contrasena)
        else:
            logger.error(f"   ❌ Tipo de usuario no válido: {tipo_usuario}")
            return None

    @staticmethod
    def _authenticate_auto_detect(
        db: Session, correo: str, contrasena: str
    ) -> Optional[Tuple[Any, str]]:
        """Auto-detección del tipo de usuario"""

        # Estrategia 1: Detectar por dominio del email (más eficiente)
        if AuthService._is_admin_or_docente_email(correo):
            logger.info(f"   🎯 Email de docente/admin detectado por dominio")
            result = AuthService._try_docente(db, correo, contrasena)
            if result:
                return result

        elif AuthService._is_estudiante_email(correo):
            logger.info(f"   🎯 Email de estudiante detectado por dominio")
            result = AuthService._try_estudiante(db, correo, contrasena)
            if result:
                return result

        elif AuthService._is_padre_email(correo):
            logger.info(f"   🎯 Email de padre detectado por dominio")
            result = AuthService._try_padre(db, correo, contrasena)
            if result:
                return result

        # Estrategia 2: Si no se detecta por dominio, buscar en todas las tablas
        logger.info(f"   🔍 Dominio no reconocido, buscando en todas las tablas...")

        # Intentar como docente/admin
        result = AuthService._try_docente(db, correo, contrasena)
        if result:
            return result

        # Intentar como estudiante
        result = AuthService._try_estudiante(db, correo, contrasena)
        if result:
            return result

        # Intentar como padre
        result = AuthService._try_padre(db, correo, contrasena)
        if result:
            return result

        logger.warning(f"🚫 No se encontró usuario con ese correo en ninguna tabla")
        return None

    @staticmethod
    def _is_admin_or_docente_email(correo: str) -> bool:
        """Detectar si el email es de admin o docente por dominio"""
        dominios_docente = [
            "@colegio.edu.bo",
            "@sistema.edu",
            "@admin.edu",
            "@docente.edu",
        ]
        return any(correo.endswith(dominio) for dominio in dominios_docente)

    @staticmethod
    def _is_estudiante_email(correo: str) -> bool:
        """Detectar si el email es de estudiante por dominio"""
        dominios_estudiante = ["@estudiante.edu.bo", "@student.edu", "@alumno.edu"]
        return any(correo.endswith(dominio) for dominio in dominios_estudiante)

    @staticmethod
    def _is_padre_email(correo: str) -> bool:
        """Detectar si el email es de padre por dominio"""
        dominios_padre = ["@padre.com", "@madre.com", "@family.com", "@padres.edu"]
        return any(correo.endswith(dominio) for dominio in dominios_padre)

    @staticmethod
    def _try_docente(
        db: Session, correo: str, contrasena: str
    ) -> Optional[Tuple[Any, str]]:
        """Intentar autenticar como docente/admin"""
        user = db.query(Docente).filter(Docente.correo == correo).first()
        logger.info(f"   👨‍🏫 Docente encontrado: {user is not None}")

        if user and verificar_contrasena(contrasena, user.contrasena):
            user_type = "admin" if not user.is_doc else "docente"
            logger.info(f"   ✅ Autenticación exitosa como {user_type}")
            return user, user_type
        elif user:
            logger.warning(f"   ❌ Contraseña incorrecta para docente")

        return None

    @staticmethod
    def _try_estudiante(
        db: Session, correo: str, contrasena: str
    ) -> Optional[Tuple[Any, str]]:
        """Intentar autenticar como estudiante"""
        user = db.query(Estudiante).filter(Estudiante.correo == correo).first()
        logger.info(f"   🎓 Estudiante encontrado: {user is not None}")

        if (
            user
            and user.contrasena
            and verificar_contrasena(contrasena, user.contrasena)
        ):
            user_type = "estudiante"
            logger.info(f"   ✅ Autenticación exitosa como {user_type}")
            return user, user_type
        elif user and not user.contrasena:
            logger.warning(f"   ❌ Estudiante sin contraseña configurada")
        elif user:
            logger.warning(f"   ❌ Contraseña incorrecta para estudiante")

        return None

    @staticmethod
    def _try_padre(
        db: Session, correo: str, contrasena: str
    ) -> Optional[Tuple[Any, str]]:
        """Intentar autenticar como padre"""
        user = db.query(Padre).filter(Padre.correo == correo).first()
        logger.info(f"   👨‍👩‍👧‍👦 Padre encontrado: {user is not None}")

        if (
            user
            and user.contrasena
            and verificar_contrasena(contrasena, user.contrasena)
        ):
            user_type = "padre"
            logger.info(f"   ✅ Autenticación exitosa como {user_type}")
            return user, user_type
        elif user and not user.contrasena:
            logger.warning(f"   ❌ Padre sin contraseña configurada")
        elif user:
            logger.warning(f"   ❌ Contraseña incorrecta para padre")

        return None

    @staticmethod
    def get_user_profile(db: Session, user_id: int, user_type: str) -> Optional[Dict]:
        """
        Obtiene el perfil del usuario según su tipo
        """
        if user_type in ["docente", "admin"]:
            user = db.query(Docente).filter(Docente.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "nombre": user.nombre,
                    "apellido": user.apellido,
                    "correo": user.correo,
                    "genero": user.genero,
                    "telefono": user.telefono,
                    "user_type": "admin" if not user.is_doc else "docente",
                    "is_doc": user.is_doc,
                }

        elif user_type == "estudiante":
            user = db.query(Estudiante).filter(Estudiante.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "nombre": user.nombre,
                    "apellido": user.apellido,
                    "correo": user.correo,
                    "genero": user.genero,
                    "telefono": user.telefono_tutor,
                    "url_imagen": user.url_imagen,
                    "user_type": "estudiante",
                }

        elif user_type == "padre":
            user = db.query(Padre).filter(Padre.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "nombre": user.nombre,
                    "apellido": user.apellido,
                    "correo": user.correo,
                    "genero": user.genero,
                    "telefono": user.telefono,
                    "user_type": "padre",
                }

        return None
