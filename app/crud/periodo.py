from sqlalchemy.orm import Session
from app.models.periodo import Periodo
from app.schemas.periodo import PeriodoCreate, PeriodoUpdate


def crear_periodo(db: Session, datos: PeriodoCreate):
    nuevo = Periodo(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def listar_periodos(db: Session):
    return db.query(Periodo).all()


def obtener_por_id(db: Session, periodo_id: int):
    return db.query(Periodo).filter(Periodo.id == periodo_id).first()


def actualizar_periodo(db: Session, periodo_id: int, datos: PeriodoUpdate):
    p = db.query(Periodo).filter(Periodo.id == periodo_id).first()
    if p:
        for key, value in datos.dict().items():
            setattr(p, key, value)
        db.commit()
        db.refresh(p)
    return p


def eliminar_periodo(db: Session, periodo_id: int):
    p = db.query(Periodo).filter(Periodo.id == periodo_id).first()
    if p:
        db.delete(p)
        db.commit()
    return p


def listar_por_gestion(db: Session, gestion_id: int):
    return db.query(Periodo).filter(Periodo.gestion_id == gestion_id).all()


def buscar_por_nombre(db: Session, nombre: str):
    return db.query(Periodo).filter(Periodo.nombre.ilike(f"%{nombre}%")).all()
