from sqlalchemy.orm import Session
from app.models.gestion import Gestion
from app.models.periodo import Periodo
from datetime import date


def seed_gestion(db: Session):
    gestiones = [
        {"anio": "2024", "descripcion": "Gestión académica del año 2024"},
        {"anio": "2025", "descripcion": "Gestión académica del año 2025"},
    ]

    for g in gestiones:
        gestion = db.query(Gestion).filter_by(anio=g["anio"]).first()
        if not gestion:
            nueva = Gestion(anio=g["anio"], descripcion=g["descripcion"])
            db.add(nueva)
            db.commit()
            gestion = nueva
            print(f"✅ Gestión {g['anio']} creada.")
        else:
            print(f"ℹ️ Gestión {g['anio']} ya existe.")

        # Periodos por gestión con nombres incluyendo el año
        periodos = [
            (
                "Primer Trimestre",
                date(int(g["anio"]), 2, 1),
                date(int(g["anio"]), 4, 30),
            ),
            (
                "Segundo Trimestre",
                date(int(g["anio"]), 5, 1),
                date(int(g["anio"]), 8, 10),
            ),
            (
                "Tercer Trimestre",
                date(int(g["anio"]), 8, 20),
                date(int(g["anio"]), 11, 30),
            ),
        ]

        for nombre, ini, fin in periodos:
            nombre_completo = f"{nombre} {g['anio']}"
            ya_existe = (
                db.query(Periodo)
                .filter_by(nombre=nombre_completo, gestion_id=gestion.id)
                .first()
            )
            if not ya_existe:
                db.add(
                    Periodo(
                        nombre=nombre_completo,
                        fecha_inicio=ini,
                        fecha_fin=fin,
                        gestion_id=gestion.id,
                    )
                )

    db.commit()
    print("📘 Periodos insertados correctamente por gestión.")
