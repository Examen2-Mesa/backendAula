from sqlalchemy.orm import Session
from app.models.docente import Docente
from app.models.materia import Materia
import random
import unicodedata
from app.seguridad import hash_contrasena

nombres_hombre = ["Carlos", "Juan", "Luis", "José", "Andrés", "Mauricio"]
nombres_mujer = ["Ana", "María", "Gabriela", "Valeria", "Daniela", "Roxana"]
apellidos = ["Condori", "Mamani", "Quispe", "Rojas", "Salvatierra", "Rivera"]


def limpiar_texto(texto):
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ASCII", "ignore")
        .decode()
        .lower()
        .replace(" ", "")
    )


def seed_docentes(db: Session):
    existentes = set(doc.correo for doc in db.query(Docente).all())
    nuevos = []

    # Admin general
    if "admin@gmail.com" not in existentes:
        nuevos.append(
            Docente(
                nombre="Admin",
                apellido="General",
                telefono="70000000",
                correo="admin@gmail.com",
                genero="Masculino",
                contrasena=hash_contrasena("admin"),
                is_doc=False,
            )
        )

    materias = db.query(Materia).all()
    usados = set()
    for mat in materias:
        nombre = random.choice(nombres_mujer + nombres_hombre)
        apellido = random.choice(apellidos)
        clave = (nombre, apellido)

        while clave in usados:
            nombre = random.choice(nombres_mujer + nombres_hombre)
            apellido = random.choice(apellidos)
            clave = (nombre, apellido)
        usados.add(clave)

        correo = limpiar_texto(f"{nombre}{apellido}@gmail.com")
        while correo in existentes:
            correo = limpiar_texto(
                f"{nombre}{apellido}{random.randint(1,99)}@gmail.com"
            )
        existentes.add(correo)

        nuevos.append(
            Docente(
                nombre=nombre,
                apellido=apellido,
                telefono=f"7{random.randint(1000000,9999999)}",
                correo=correo,
                genero="Femenino" if nombre in nombres_mujer else "Masculino",
                contrasena=hash_contrasena(nombre.lower()),
                is_doc=True,
            )
        )

    db.bulk_save_objects(nuevos)
    db.commit()
    print(f"✅ Se insertaron {len(nuevos)} docentes (incluye admin).")
