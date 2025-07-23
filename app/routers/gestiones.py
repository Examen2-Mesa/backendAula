from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.gestion import GestionCreate, GestionUpdate, GestionOut
from app.crud import gestion as crud
from app.auth.roles import admin_required, docente_o_admin_required

router = APIRouter(prefix="/gestiones", tags=["Gestiones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validar_campo(nombre: str, valor: str):
    if not valor or valor.strip() == "":
        raise HTTPException(
            status_code=400, detail=f"El campo '{nombre}' no puede estar vacío"
        )
    return valor.strip()


@router.post("/", response_model=GestionOut)
def crear(
    datos: GestionCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.anio = validar_campo("anio", datos.anio)
    datos.descripcion = validar_campo("descripcion", datos.descripcion)
    return crud.crear_gestion(db, datos)


@router.get("/", response_model=list[GestionOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)):
    return crud.listar_gestiones(db)


@router.get("/{gestion_id}", response_model=GestionOut)
def obtener(
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    g = crud.obtener_gestion_por_id(db, gestion_id)
    if not g:
        raise HTTPException(status_code=404, detail="Gestión no encontrada")
    return g


@router.put("/{gestion_id}", response_model=GestionOut)
def actualizar(
    gestion_id: int,
    datos: GestionUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.anio = validar_campo("anio", datos.anio)
    datos.descripcion = validar_campo("descripcion", datos.descripcion)
    return crud.actualizar_gestion(db, gestion_id, datos)


@router.delete("/{gestion_id}")
def eliminar(
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    g = crud.eliminar_gestion(db, gestion_id)
    if not g:
        raise HTTPException(status_code=404, detail="Gestión no encontrada")
    return {"mensaje": "Gestión eliminada"}
