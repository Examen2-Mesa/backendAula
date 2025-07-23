from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.peso_tipo_evaluacion import (
    PesoTipoEvaluacionCreate,
    PesoTipoEvaluacionUpdate,
    PesoTipoEvaluacionOut,
)
from app.crud import peso_tipo_evaluacion as crud
from app.auth.roles import docente_o_admin_required

router = APIRouter(prefix="/pesos-evaluacion", tags=["PesoTipoEvaluacion"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=PesoTipoEvaluacionOut)
def crear(
    datos: PesoTipoEvaluacionCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.crear_peso(db, datos)


@router.get("/", response_model=list[PesoTipoEvaluacionOut])
def listar(
    db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)
):
    return crud.listar_pesos(db)


@router.get("/{peso_id}", response_model=PesoTipoEvaluacionOut)
def obtener(
    peso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    p = crud.obtener_por_id(db, peso_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peso no encontrado")
    return p


@router.put("/{peso_id}", response_model=PesoTipoEvaluacionOut)
def actualizar(
    peso_id: int,
    datos: PesoTipoEvaluacionUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    p = crud.actualizar_peso(db, peso_id, datos)
    if not p:
        raise HTTPException(status_code=404, detail="Peso no encontrado")
    return p


@router.delete("/{peso_id}")
def eliminar(
    peso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    p = crud.eliminar_peso(db, peso_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peso no encontrado")
    return {"mensaje": "Peso de tipo de evaluación eliminado"}


@router.get("/por-asignacion/")
def listar_por_asignacion(
    materia_id: int,
    docente_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_materia_docente_gestion(
        db, materia_id, docente_id, gestion_id
    )


@router.get("/por-docente-materia/")
def listar_por_docente_materia(
    docente_id: int,
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_docente_materia(db, docente_id, materia_id)


@router.get("/por-materia-gestion/")
def listar_por_materia_gestion(
    materia_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_materia_gestion(db, materia_id, gestion_id)


@router.get("/por-docente-gestion/")
def listar_por_docente_gestion(
    docente_id: int,
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_docente_gestion(db, docente_id, gestion_id)


@router.get("/por-docente/{docente_id}", response_model=list[PesoTipoEvaluacionOut])
def listar_pesos_por_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_por_docente(db, docente_id)
