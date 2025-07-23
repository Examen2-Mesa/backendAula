from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.prediccion_rendimiento import (
    PrediccionRendimientoCreate,
    PrediccionRendimientoOut,
)
from app.crud import prediccion_rendimiento as crud

router = APIRouter(prefix="/predicciones", tags=["Predicción de Rendimiento"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=PrediccionRendimientoOut)
def crear_prediccion(
    payload: PrediccionRendimientoCreate, db: Session = Depends(get_db)
):
    return crud.crear_prediccion(db, payload)


@router.get(
    "/estudiante/{estudiante_id}", response_model=list[PrediccionRendimientoOut]
)
def predicciones_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    return crud.obtener_predicciones_por_estudiante(db, estudiante_id)


@router.get("/materia/{materia_id}", response_model=list[PrediccionRendimientoOut])
def predicciones_materia(materia_id: int, db: Session = Depends(get_db)):
    return crud.obtener_predicciones_por_materia(db, materia_id)


@router.get("/periodo/{periodo_id}", response_model=list[PrediccionRendimientoOut])
def predicciones_periodo(periodo_id: int, db: Session = Depends(get_db)):
    return crud.obtener_predicciones_por_periodo(db, periodo_id)
