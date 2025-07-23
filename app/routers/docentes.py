from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.curso import CursoOut
from app.schemas.docente import DocenteCreate, DocenteLogin, DocenteOut, DocenteUpdate, EstudianteAsignadoDetalle
from app.crud import docente as crud
from app.auth.auth_handler import crear_token
from app.auth.roles import admin_required, docente_o_admin_required
from app.auth.auth_bearer import JWTBearer
from app.schemas.estudiante import EstudianteOut
from app.schemas.materia import MateriaOut

router = APIRouter(prefix="/docentes", tags=["Docentes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=DocenteOut)
def crear(
    docente: DocenteCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    return crud.crear_docente(db, docente)


@router.post("/login")
def login(datos: DocenteLogin, db: Session = Depends(get_db)):
    docente = crud.autenticar_docente(db, datos.correo, datos.contrasena)
    if not docente:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = crear_token({"sub": docente.correo, "is_doc": docente.is_doc})
    return {"access_token": token, "token_type": "bearer", "is_doc": docente.is_doc}


@router.get("/yo", response_model=DocenteOut)
def perfil(payload: dict = Depends(JWTBearer()), db: Session = Depends(get_db)):
    correo = payload.get("sub")
    docente = crud.obtener_por_correo(db, correo)
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return docente


@router.put("/{docente_id}", response_model=DocenteOut)
def actualizar(
    docente_id: int,
    datos: DocenteUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    docente = crud.actualizar_docente(db, docente_id, datos)
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return docente


@router.delete("/{docente_id}")
def eliminar(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    docente = crud.eliminar_docente(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return {"mensaje": "Docente eliminado correctamente"}


@router.get("/solo-docentes", response_model=list[DocenteOut])
def listar_docentes(
    db: Session = Depends(get_db), payload: dict = Depends(admin_required)
):
    return crud.obtener_docentes(db)


@router.get("/solo-admins", response_model=list[DocenteOut])
def listar_admins(
    db: Session = Depends(get_db), payload: dict = Depends(admin_required)
):
    return crud.obtener_admins(db)


@router.get("/{docente_id}", response_model=DocenteOut)
def obtener_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    docente = crud.obtener_docente_por_id(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return docente


@router.get("/materias-docente/{docente_id}", response_model=list[MateriaOut])
def listar_materias_del_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.obtener_materias_del_docente(db, docente_id)


@router.get("/cursos-docente/{docente_id}", response_model=list[CursoOut])
def listar_cursos_del_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.obtener_cursos_del_docente(db, docente_id)


@router.get(
    "/alumnos-docente/{docente_id}/curso/{curso_id}/materia/{materia_id}",
    response_model=list[EstudianteOut],
)
def listar_alumnos_de_materia_y_curso(
    docente_id: int,
    curso_id: int,
    materia_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.obtener_estudiantes_de_materia_curso(
        db, docente_id, curso_id, materia_id
    )


@router.get("/{docente_id}/curso/{curso_id}/materias", response_model=list[MateriaOut])
def materias_docente_en_curso(
    docente_id: int,
    curso_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.obtener_materias_docente_en_curso(db, docente_id, curso_id)


@router.get("/alumnos-asignados/{docente_id}", response_model=list[EstudianteAsignadoDetalle])
def listar_estudiantes_asignados_a_docente(
    docente_id: int,
    curso_id: int = None,
    materia_id: int = None,
    nombre: str = None,
    db: Session = Depends(get_db),
    payload: dict = Depends(docente_o_admin_required),
):
    return crud.obtener_estudiantes_de_docente(
        db, docente_id, curso_id=curso_id, materia_id=materia_id, nombre=nombre
    )
