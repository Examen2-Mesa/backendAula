from sqlalchemy.orm import Session
from app.models.gestion import Gestion
from app.schemas.gestion import GestionCreate, GestionUpdate


def crear_gestion(db: Session, datos: GestionCreate):
    nueva = Gestion(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def listar_gestiones(db: Session):
    return db.query(Gestion).all()


def obtener_gestion_por_id(db: Session, gestion_id: int):
    return db.query(Gestion).filter(Gestion.id == gestion_id).first()


def actualizar_gestion(db: Session, gestion_id: int, datos: GestionUpdate):
    g = db.query(Gestion).filter(Gestion.id == gestion_id).first()
    if g:
        for key, value in datos.dict().items():
            setattr(g, key, value)
        db.commit()
        db.refresh(g)
    return g


def eliminar_gestion(db: Session, gestion_id: int):
    g = db.query(Gestion).filter(Gestion.id == gestion_id).first()
    if g:
        db.delete(g)
        db.commit()
    return g
