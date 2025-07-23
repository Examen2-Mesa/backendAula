from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.inscripcion import (
    InscripcionCreate,
    InscripcionUpdate,
    InscripcionOut,
    InscripcionDetalle,
)
from app.crud import inscripcion as crud
from app.auth.roles import admin_required

router = APIRouter(prefix="/inscripciones", tags=["Inscripciones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=InscripcionOut)
def crear(
    datos: InscripcionCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.descripcion = datos.descripcion.strip()
    return crud.crear_inscripcion(db, datos)


@router.get("/", response_model=list[InscripcionOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(admin_required)):
    return crud.listar_inscripciones(db)


@router.get("/{inscripcion_id}", response_model=InscripcionOut)
def obtener(
    inscripcion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    insc = crud.obtener_por_id(db, inscripcion_id)
    if not insc:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return insc


@router.put("/{inscripcion_id}", response_model=InscripcionOut)
def actualizar(
    inscripcion_id: int,
    datos: InscripcionUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.descripcion = datos.descripcion.strip()
    return crud.actualizar_inscripcion(db, inscripcion_id, datos)


@router.delete("/{inscripcion_id}")
def eliminar(
    inscripcion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    insc = crud.eliminar_inscripcion(db, inscripcion_id)
    if not insc:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return {"mensaje": "Inscripción eliminada"}


@router.get("/por-estudiante/{estudiante_id}", response_model=list[InscripcionDetalle])
def inscripciones_por_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.listar_por_estudiante(db, estudiante_id)


@router.get("/por-curso/{curso_id}", response_model=list[InscripcionDetalle])
def inscripciones_por_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.listar_por_curso(db, curso_id)


@router.get("/por-gestion/{gestion_id}", response_model=list[InscripcionDetalle])
def inscripciones_por_gestion(
    gestion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.listar_por_gestion(db, gestion_id)
