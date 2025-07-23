from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.schemas.estudiante import EstudianteOut, EstudianteUpdate
from app.database import SessionLocal
from app.crud import estudiante as crud
from app.auth.roles import (
    admin_required,
    docente_o_admin_required,
    propietario_o_admin,
    usuario_autenticado,
)
from app.cloudinary import subir_imagen_a_cloudinary
from datetime import datetime

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


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


# ========== RUTAS ESPECÍFICAS PRIMERO ==========


@router.get("/mi-perfil", response_model=EstudianteOut)
def obtener_mi_perfil_estudiante(
    payload: dict = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """👤 Obtener mi perfil como estudiante"""
    # Verificar que el usuario es estudiante
    if payload.get("user_type") != "estudiante":
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")

    estudiante_id = payload.get("user_id")
    estudiante = crud.obtener_estudiante(db, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante


@router.get("/mi-curso-actual", response_model=dict)
def obtener_mi_curso_actual(
    payload: dict = Depends(usuario_autenticado), db: Session = Depends(get_db)
):
    """🏫 Obtener mi curso actual (versión simplificada)"""
    # Verificar que el usuario es estudiante
    if payload.get("user_type") != "estudiante":
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")

    estudiante_id = payload.get("user_id")
    estudiante = crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    from app.crud import estudiante_info_academica as info_crud

    curso = info_crud.obtener_curso_estudiante(db, estudiante.id)

    if not curso:
        return {
            "success": False,
            "mensaje": "No tienes curso asignado en la gestión actual",
        }

    return {"success": True, "curso": curso, "mensaje": "Curso obtenido exitosamente"}


@router.get("/mis-materias-docentes", response_model=dict)
def obtener_mis_materias_con_docentes(
    payload: dict = Depends(usuario_autenticado), db: Session = Depends(get_db)
):
    """📚 Obtener mis materias con sus docentes (versión simplificada)"""
    # Verificar que el usuario es estudiante
    if payload.get("user_type") != "estudiante":
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")

    estudiante_id = payload.get("user_id")
    estudiante = crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    from app.crud import estudiante_info_academica as info_crud

    materias = info_crud.obtener_materias_estudiante(db, estudiante.id)

    return {
        "success": True,
        "materias": materias,
        "total": len(materias),
        "mensaje": f"Se encontraron {len(materias)} materias",
    }


@router.get("/dashboard-academico", response_model=dict)
def obtener_dashboard_academico(
    payload: dict = Depends(usuario_autenticado), db: Session = Depends(get_db)
):
    """📊 Dashboard académico completo del estudiante"""
    # Verificar que el usuario es estudiante
    if payload.get("user_type") != "estudiante":
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")

    estudiante_id = payload.get("user_id")
    estudiante = crud.obtener_estudiante(db, estudiante_id)

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    from app.crud import estudiante_info_academica as info_crud

    # Obtener toda la información
    info_completa = info_crud.obtener_info_academica_estudiante(db, estudiante.id)

    if "error" in info_completa:
        return {"success": False, "mensaje": info_completa["error"]}

    # Estadísticas adicionales
    materias = info_completa["materias"]
    docentes_unicos = set()
    materias_con_docente = 0

    for materia in materias:
        if materia["docente"]:
            materias_con_docente += 1
            docentes_unicos.add(materia["docente"]["id"])

    dashboard = {
        "success": True,
        "estudiante": info_completa["estudiante"],
        "curso": info_completa["curso"],
        "gestion": info_completa["gestion"],
        "estadisticas": {
            "total_materias": len(materias),
            "materias_con_docente": materias_con_docente,
            "materias_sin_docente": len(materias) - materias_con_docente,
            "total_docentes": len(docentes_unicos),
        },
        "materias": materias,
        "mensaje": "Dashboard académico obtenido exitosamente",
    }

    return dashboard


# ========== RUTAS SIN PARÁMETROS ==========


@router.post("/", response_model=EstudianteOut)
def crear(
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    nombre_tutor: str = Form(...),
    telefono_tutor: str = Form(...),
    direccion_casa: str = Form(...),
    correo: str = Form(None),  # 🆕 Opcional para login
    contrasena: str = Form(None),  # 🆕 Opcional para login
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    # Validar campos vacíos
    nombre = validar_campo("nombre", nombre)
    apellido = validar_campo("apellido", apellido)
    genero = validar_campo("genero", genero)
    nombre_tutor = validar_campo("nombre_tutor", nombre_tutor)
    telefono_tutor = validar_campo("telefono_tutor", telefono_tutor)
    direccion_casa = validar_campo("direccion_casa", direccion_casa)

    url_imagen = subir_imagen_a_cloudinary(imagen, f"{nombre}_{apellido}")

    nuevo = crud.crear_estudiante(
        db,
        EstudianteUpdate(
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=datetime.fromisoformat(fecha_nacimiento),
            genero=genero,
            url_imagen=url_imagen,
            nombre_tutor=nombre_tutor,
            telefono_tutor=telefono_tutor,
            direccion_casa=direccion_casa,
            correo=correo if correo else None,
            contrasena=contrasena if contrasena else None,
        ),
    )
    return nuevo


@router.get("/", response_model=list[EstudianteOut])
def listar(
    db: Session = Depends(get_db), payload: dict = Depends(docente_o_admin_required)
):
    return crud.obtener_estudiantes(db)


# ========== RUTAS CON PARÁMETROS AL FINAL ==========


@router.get("/{estudiante_id}", response_model=EstudianteOut)
def obtener_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(usuario_autenticado),
):
    """👤 Obtener datos de un estudiante"""
    # Verificar permisos: debe ser el mismo estudiante, padre del estudiante, o admin
    user_type = payload.get("user_type")
    user_id = payload.get("user_id")

    if user_type == "admin":
        # Admin puede ver cualquier estudiante
        pass
    elif user_type == "docente":
        # Docente puede ver estudiantes (verificar asignación si es necesario)
        pass
    elif user_type == "estudiante" and user_id == estudiante_id:
        # El mismo estudiante puede ver su perfil
        pass
    elif user_type == "padre":
        # Verificar que es padre del estudiante
        from app.crud.padre import es_padre_del_estudiante

        if not es_padre_del_estudiante(db, user_id, estudiante_id):
            raise HTTPException(status_code=403, detail="No autorizado")
    else:
        raise HTTPException(status_code=403, detail="No autorizado")

    estudiante = crud.obtener_estudiante(db, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante


@router.put("/{estudiante_id}", response_model=EstudianteOut)
def actualizar(
    estudiante_id: int,
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nacimiento: str = Form(...),
    genero: str = Form(...),
    nombre_tutor: str = Form(...),
    telefono_tutor: str = Form(...),
    direccion_casa: str = Form(...),
    correo: str = Form(None),  # 🆕 Opcional
    contrasena: str = Form(None),  # 🆕 Opcional
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    # Validar campos vacíos
    nombre = validar_campo("nombre", nombre)
    apellido = validar_campo("apellido", apellido)
    genero = validar_campo("genero", genero)
    nombre_tutor = validar_campo("nombre_tutor", nombre_tutor)
    telefono_tutor = validar_campo("telefono_tutor", telefono_tutor)
    direccion_casa = validar_campo("direccion_casa", direccion_casa)

    url_imagen = None
    if imagen:
        url_imagen = subir_imagen_a_cloudinary(imagen, f"{nombre}_{apellido}")

    datos = EstudianteUpdate(
        nombre=nombre,
        apellido=apellido,
        fecha_nacimiento=datetime.fromisoformat(fecha_nacimiento),
        genero=genero,
        url_imagen=url_imagen,
        nombre_tutor=nombre_tutor,
        telefono_tutor=telefono_tutor,
        direccion_casa=direccion_casa,
        correo=correo if correo else None,
        contrasena=contrasena if contrasena else None,
    )
    return crud.actualizar_estudiante(db, estudiante_id, datos)


@router.delete("/{estudiante_id}")
def eliminar(
    estudiante_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(admin_required),
):
    est = crud.eliminar_estudiante(db, estudiante_id)
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"mensaje": "Estudiante eliminado"}
