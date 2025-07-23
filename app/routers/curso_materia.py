from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.curso_materia import (
    CursoMateriaCreate,
    CursoMateriaUpdate,
    CursoMateriaOut,
    CursoMateriaDetalle,
    MateriaConCurso,
)
from app.crud import curso_materia as crud
from app.auth.roles import admin_required, docente_o_admin_required

router = APIRouter(prefix="/curso-materia", tags=["CursoMateria"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=CursoMateriaOut)
def asignar(
    datos: CursoMateriaCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.crear_asignacion(db, datos)


@router.get("/", response_model=list[CursoMateriaOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(admin_required)):
    return crud.listar_asignaciones(db)


@router.get("/{asignacion_id}", response_model=CursoMateriaOut)
def obtener(
    asignacion_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    asig = crud.obtener_por_id(db, asignacion_id)
    if not asig:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asig


@router.put("/{asignacion_id}", response_model=CursoMateriaOut)
def actualizar(
    asignacion_id: int,
    datos: CursoMateriaUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    asig = crud.actualizar_asignacion(db, asignacion_id, datos)
    if not asig:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asig


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


@router.get("/materias-por-curso/{curso_id}", response_model=list[CursoMateriaDetalle])
def materias_por_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.listar_materias_por_curso(db, curso_id)


@router.get(
    "/cursos-por-materia/{materia_id}", response_model=list[CursoMateriaDetalle]
)
def cursos_por_materia(
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.listar_cursos_por_materia(db, materia_id)


@router.get("/materias-docente/{docente_id}", response_model=list[MateriaConCurso])
def materias_con_curso_por_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.listar_materias_con_curso_por_docente(db, docente_id)
