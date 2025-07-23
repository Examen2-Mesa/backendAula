from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException
from app.auth.auth_handler import verificar_token


class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            payload = verificar_token(credentials.credentials)
            if payload is None:
                raise HTTPException(status_code=403, detail="Token inválido o expirado")
            return payload
        else:
            raise HTTPException(status_code=403, detail="Token requerido")
