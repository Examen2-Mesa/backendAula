from app.models.rendimiento_final import RendimientoFinal
from sqlalchemy.orm import Session

def crear_rendimiento(db: Session, datos):
    rf = RendimientoFinal(**datos.dict())
    db.add(rf)
    db.commit()
    db.refresh(rf)
    return rf


def actualizar_rendimiento(db: Session, id: int, datos):
    rf = db.query(RendimientoFinal).get(id)
    if rf:
        rf.nota_final = datos.nota_final
        db.commit()
        db.refresh(rf)
    return rf


def eliminar_rendimiento(db: Session, id: int):
    rf = db.query(RendimientoFinal).get(id)
    if rf:
        db.delete(rf)
        db.commit()
    return rf


def listar_por_estudiante_periodo(db: Session, estudiante_id: int, periodo_id: int):
    return (
        db.query(RendimientoFinal)
        .filter_by(estudiante_id=estudiante_id, periodo_id=periodo_id)
        .all()
    )


def obtener_por_id(db: Session, id: int):
    return db.query(RendimientoFinal).get(id)
