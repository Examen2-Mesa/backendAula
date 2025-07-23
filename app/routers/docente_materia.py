from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.docente_materia import AsignacionCreate, AsignacionOut
from app.crud import docente_materia as crud
from app.auth.roles import admin_required, docente_o_admin_required
from app.schemas.docente_materia import MateriaAsignada, DocenteAsignado

router = APIRouter(prefix="/asignaciones", tags=["Asignaciones Docente-Materia"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AsignacionOut)
def asignar(
    datos: AsignacionCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.asignar_docente_materia(db, datos)


@router.get("/", response_model=list[AsignacionOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)):
    return crud.obtener_asignaciones(db)


@router.delete("/{asignacion_id}")
def eliminar(
    asignacion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    asig = crud.eliminar_asignacion(db, asignacion_id)
    if not asig:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {"mensaje": "Asignación eliminada"}


@router.get("/materias-por-docente/{docente_id}", response_model=list[MateriaAsignada])
def materias_por_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    asignaciones = crud.obtener_materias_por_docente(db, docente_id)
    return asignaciones


@router.get("/docentes-por-materia/{materia_id}", response_model=list[DocenteAsignado])
def docentes_por_materia(
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    asignaciones = crud.obtener_docentes_por_materia(db, materia_id)
    return asignaciones
