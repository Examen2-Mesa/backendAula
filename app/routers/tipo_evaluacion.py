from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.tipo_evaluacion import (
    TipoEvaluacionCreate,
    TipoEvaluacionUpdate,
    TipoEvaluacionOut,
)
from app.crud import tipo_evaluacion as crud
from app.auth.roles import admin_required, docente_o_admin_required

router = APIRouter(prefix="/tipo-evaluacion", tags=["TipoEvaluacion"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=TipoEvaluacionOut)
def crear(
    datos: TipoEvaluacionCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.crear_tipo(db, datos)


@router.get("/", response_model=list[TipoEvaluacionOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)):
    return crud.listar_tipos(db)


@router.get("/{tipo_id}", response_model=TipoEvaluacionOut)
def obtener(
    tipo_id: int, db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)
):
    tipo = crud.obtener_por_id(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de evaluación no encontrado")
    return tipo


@router.put("/{tipo_id}", response_model=TipoEvaluacionOut)
def actualizar(
    tipo_id: int,
    datos: TipoEvaluacionUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    tipo = crud.actualizar_tipo(db, tipo_id, datos)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de evaluación no encontrado")
    return tipo


@router.delete("/{tipo_id}")
def eliminar(
    tipo_id: int, db: Session = Depends(get_db), payload: dict = Depends(admin_required)
):
    tipo = crud.eliminar_tipo(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de evaluación no encontrado")
    return {"mensaje": "Tipo de evaluación eliminado"}
