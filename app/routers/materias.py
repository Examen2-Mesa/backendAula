from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.materia import MateriaCreate, MateriaUpdate, MateriaOut
from app.crud import materia as crud
from app.auth.roles import admin_required, docente_o_admin_required

router = APIRouter(prefix="/materias", tags=["Materias"])


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


@router.post("/", response_model=MateriaOut)
def crear(
    datos: MateriaCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.nombre = validar_campo("nombre", datos.nombre)
    datos.descripcion = validar_campo("descripcion", datos.descripcion)
    return crud.crear_materia(db, datos)


@router.get("/", response_model=list[MateriaOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(admin_required)):
    return crud.obtener_materias(db)


@router.get("/{materia_id}", response_model=MateriaOut)
def obtener(
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    materia = crud.obtener_materia_por_id(db, materia_id)
    if not materia:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return materia


@router.put("/{materia_id}", response_model=MateriaOut)
def actualizar(
    materia_id: int,
    datos: MateriaUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.nombre = validar_campo("nombre", datos.nombre)
    datos.descripcion = validar_campo("descripcion", datos.descripcion)
    return crud.actualizar_materia(db, materia_id, datos)


@router.delete("/{materia_id}")
def eliminar(
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    materia = crud.eliminar_materia(db, materia_id)
    if not materia:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return {"mensaje": "Materia eliminada"}
