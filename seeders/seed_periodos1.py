from sqlalchemy.orm import Session
from datetime import date
from app.models.periodo import Periodo


def seed_periodos(db: Session, gestion_id: int):
    periodos = [
        {
            "nombre": "Primer Trimestre",
            "fecha_inicio": date(2024, 2, 3),
            "fecha_fin": date(2024, 5, 9),
            "gestion_id": 1,
        },
        {
            "nombre": "Segundo Trimestre",
            "fecha_inicio": date(2024, 5, 12),
            "fecha_fin": date(2024, 8, 29),
            "gestion_id": 1,
        },
        {
            "nombre": "Tercer Trimestre",
            "fecha_inicio": date(2024, 9, 1),
            "fecha_fin": date(2024, 12, 2),
            "gestion_id": 1,
        },
    ]
    for p in periodos:
        existe = (
            db.query(Periodo)
            .filter(
                Periodo.nombre == p["nombre"], Periodo.gestion_id == p["gestion_id"]
            )
            .first()
        )

        if not existe:
            nuevo = Periodo(**p)
            db.add(nuevo)

    db.commit()
    print("✔️ Periodos insertados correctamente.")
