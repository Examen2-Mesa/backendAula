from fastapi import Depends, HTTPException
from app.auth.auth_bearer import JWTBearer
from jose import jwt, JWTError  # type: ignore
from app.config import settings


def admin_required(payload: dict = Depends(JWTBearer())):
    if payload.get("is_doc") != False:
        raise HTTPException(status_code=403, detail="Solo administradores")
    return payload


def docente_required(payload: dict = Depends(JWTBearer())):
    if payload.get("is_doc") != True:
        raise HTTPException(status_code=403, detail="Solo docentes")
    return payload


# NUEVO: permite docentes y admin
def docente_o_admin_required(payload: dict = Depends(JWTBearer())):
    if payload.get("is_doc") not in [True, False]:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    return payload


def docente_o_admin_required(payload: dict = Depends(JWTBearer())):
    """Docentes o administradores"""
    user_type = payload.get("user_type")
    is_doc = payload.get("is_doc")

    # Compatibilidad: si no hay user_type, usar is_doc
    if user_type is None:
        if is_doc is not None:
            return payload  # Token legacy de docente
        else:
            raise HTTPException(
                status_code=403, detail="Solo docentes o administradores"
            )

    if user_type not in ["docente", "admin"]:
        raise HTTPException(status_code=403, detail="Solo docentes o administradores")
    return payload


def estudiante_required(payload: dict = Depends(JWTBearer())):
    """Solo estudiantes"""
    if payload.get("user_type") != "estudiante":
        raise HTTPException(status_code=403, detail="Solo estudiantes")
    return payload


def padre_required(payload: dict = Depends(JWTBearer())):
    """Solo padres"""
    if payload.get("user_type") != "padre":
        raise HTTPException(status_code=403, detail="Solo padres")
    return payload


def padre_o_admin_required(payload: dict = Depends(JWTBearer())):
    """Padres o administradores"""
    user_type = payload.get("user_type")
    if user_type not in ["padre", "admin"]:
        raise HTTPException(status_code=403, detail="Solo padres o administradores")
    return payload


def estudiante_o_admin_required(payload: dict = Depends(JWTBearer())):
    """Estudiantes o administradores"""
    user_type = payload.get("user_type")
    if user_type not in ["estudiante", "admin"]:
        raise HTTPException(
            status_code=403, detail="Solo estudiantes o administradores"
        )
    return payload


def usuario_autenticado(payload: dict = Depends(JWTBearer())):
    """Cualquier usuario autenticado - PARA PADRES Y ESTUDIANTES"""
    if not payload:
        raise HTTPException(status_code=401, detail="Token requerido")
    return payload


def propietario_o_admin(payload: dict = Depends(JWTBearer())):
    """
    Verificar que el usuario es el propietario de los datos o es admin
    Nota: La verificación específica se hace en el endpoint
    """
    return payload
