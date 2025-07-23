from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.auth import LoginRequest, LoginResponse, UserProfileResponse
from app.services.auth_service import AuthService
from app.auth.auth_handler import crear_token
from app.auth.auth_bearer import JWTBearer

router = APIRouter(prefix="/auth", tags=["🔐 Autenticación Unificada"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=LoginResponse)
def login_unificado(datos: LoginRequest, db: Session = Depends(get_db)):
    """
    🚀 Login unificado con auto-detección de tipo de usuario

    **Formas de usar:**

    1️⃣ **Auto-detección (recomendado):**
    ```json
    {
      "correo": "juan.perez@padre.com",
      "contrasena": "padre123"
    }
    ```

    2️⃣ **Especificando tipo (compatible):**
    ```json
    {
      "correo": "juan.perez@padre.com",
      "contrasena": "padre123",
      "tipo_usuario": "padre"
    }
    ```

    **Detección automática por dominio:**
    - `@colegio.edu.bo`, `@sistema.edu` → Docentes/Admin
    - `@estudiante.edu.bo` → Estudiantes
    - `@padre.com`, `@madre.com` → Padres
    - Otros dominios → Busca en todas las tablas
    """
    # Autenticar usuario (con o sin tipo_usuario)
    resultado = AuthService.authenticate_user(
        db, datos.correo, datos.contrasena, datos.tipo_usuario  # Puede ser None
    )

    if not resultado:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    user, user_type = resultado

    # Crear payload del token
    token_payload = {"sub": user.correo, "user_id": user.id, "user_type": user_type}

    # Agregar is_doc solo para docentes/admins (compatibilidad)
    if user_type in ["docente", "admin"]:
        token_payload["is_doc"] = user.is_doc

    # Generar token
    token = crear_token(token_payload)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_type=user_type,
        user_id=user.id,
        is_doc=user.is_doc if hasattr(user, "is_doc") else None,
    )


@router.get("/profile", response_model=UserProfileResponse)
def get_profile_unificado(
    payload: dict = Depends(JWTBearer()), db: Session = Depends(get_db)
):
    """
    👤 Obtener perfil del usuario autenticado (cualquier tipo)
    """
    user_id = payload.get("user_id")
    user_type = payload.get("user_type")

    if not user_id or not user_type:
        raise HTTPException(status_code=401, detail="Token inválido")

    profile = AuthService.get_user_profile(db, user_id, user_type)

    if not profile:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return UserProfileResponse(**profile)
