from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.curso import CursoCreate, CursoUpdate, CursoOut
from app.crud import curso as crud
from app.auth.roles import admin_required,docente_o_admin_required

router = APIRouter(prefix="/cursos", tags=["Cursos"])


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


@router.post("/", response_model=CursoOut)
def crear(
    datos: CursoCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.nombre = validar_campo("nombre", datos.nombre)
    datos.nivel = validar_campo("nivel", datos.nivel)
    datos.paralelo = validar_campo("paralelo", datos.paralelo)
    datos.turno = validar_campo("turno", datos.turno)

    return crud.crear_curso(db, datos)


@router.get("/", response_model=list[CursoOut])
def listar(db: Session = Depends(get_db), payload: dict = Depends(admin_required)):
    return crud.obtener_cursos(db)


@router.get("/{curso_id}", response_model=CursoOut)
def obtener(
    curso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    curso = crud.obtener_curso_por_id(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso


@router.put("/{curso_id}", response_model=CursoOut)
def actualizar(
    curso_id: int,
    datos: CursoUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    datos.nombre = validar_campo("nombre", datos.nombre)
    datos.nivel = validar_campo("nivel", datos.nivel)
    datos.paralelo = validar_campo("paralelo", datos.paralelo)
    datos.turno = validar_campo("turno", datos.turno)

    return crud.actualizar_curso(db, curso_id, datos)


@router.delete("/{curso_id}")
def eliminar(
    curso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    curso = crud.eliminar_curso(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return {"mensaje": "Curso eliminado"}
