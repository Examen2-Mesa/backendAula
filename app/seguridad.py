from passlib.hash import bcrypt

def hash_contrasena(contrasena: str) -> str:
    return bcrypt.hash(contrasena)

def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return bcrypt.verify(contrasena_plana, contrasena_hash)