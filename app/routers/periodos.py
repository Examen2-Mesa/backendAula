from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.periodo import PeriodoCreate, PeriodoUpdate, PeriodoOut
from app.crud import periodo as crud
from app.auth.roles import admin_required, docente_o_admin_required

router = APIRouter(prefix="/periodos", tags=["Periodos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=PeriodoOut)
def crear(
    datos: PeriodoCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.crear_periodo(db, datos)


@router.get("/", response_model=list[PeriodoOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)):
    return crud.listar_periodos(db)


@router.get("/{periodo_id}", response_model=PeriodoOut)
def obtener(
    periodo_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    p = crud.obtener_por_id(db, periodo_id)
    if not p:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    return p


@router.put("/{periodo_id}", response_model=PeriodoOut)
def actualizar(
    periodo_id: int,
    datos: PeriodoUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    p = crud.actualizar_periodo(db, periodo_id, datos)
    if not p:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    return p


@router.delete("/{periodo_id}")
def eliminar(
    periodo_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    p = crud.eliminar_periodo(db, periodo_id)
    if not p:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    return {"mensaje": "Periodo eliminado"}


@router.get("/por-gestion/{gestion_id}", response_model=list[PeriodoOut])
def listar_por_gestion(
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_gestion(db, gestion_id)


@router.get("/buscar-por-nombre/", response_model=list[PeriodoOut])
def buscar(
    nombre: str, db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)
):
    return crud.buscar_por_nombre(db, nombre)
