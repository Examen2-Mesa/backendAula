from sqlalchemy.orm import Session
from app.models.padre import Padre
from app.seguridad import hash_contrasena
import random

nombres_masculinos = [
    "Carlos",
    "Juan",
    "Luis",
    "Marco",
    "Pedro",
    "José",
    "Hugo",
    "Edgar",
    "Jorge",
    "Mauricio",
    "Diego",
    "Sebastián",
    "Ramiro",
    "Raúl",
    "Nicolás",
    "Alberto",
    "Fernando",
    "Iván",
    "Gonzalo",
    "Ricardo",
]

nombres_femeninos = [
    "Ana",
    "María",
    "Paola",
    "Lucía",
    "Gabriela",
    "Daniela",
    "Valeria",
    "Roxana",
    "Sandra",
    "Camila",
    "Verónica",
    "Patricia",
    "Karen",
    "Mariela",
    "Julieta",
    "Estefanía",
    "Lorena",
    "Carla",
    "Bianca",
    "Mónica",
]

apellidos = [
    "Quispe",
    "Mamani",
    "Condori",
    "Choque",
    "Rojas",
    "Guzmán",
    "Salvatierra",
    "Rivera",
    "Alarcón",
    "Vargas",
    "Sánchez",
    "Flores",
    "Paredes",
    "Céspedes",
    "Ortíz",
    "Castro",
    "Navarro",
    "Cabrera",
    "Medina",
    "Aguilera",
]


def seed_padres(db: Session):
    padres = []
    usados = set()
    for i in range(120):  # 120 padres para cubrir a todos
        nombre = random.choice(nombres_masculinos + nombres_femeninos)
        apellido = random.choice(apellidos)
        correo = f"{nombre.lower()}.{apellido.lower()}{i}@gmail.com"
        while correo in usados:
            correo = (
                f"{nombre.lower()}.{apellido.lower()}{i+random.randint(1,99)}@gmail.com"
            )
        usados.add(correo)

        padre = Padre(
            nombre=nombre,
            apellido=apellido,
            telefono=f"7{random.randint(1000000,9999999)}",
            correo=correo,
            genero=random.choice(["Masculino", "Femenino"]),
            contrasena=hash_contrasena(nombre.lower()),
        )
        padres.append(padre)
    db.bulk_save_objects(padres)
    db.commit()
    print(f"👨‍👩‍👧‍👦 Se insertaron {len(padres)} padres.")
