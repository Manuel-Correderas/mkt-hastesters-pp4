# backend/app/routers/users.py
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from ..deps import get_db, get_current_user, current_admin_or_self
from ..schemas.user_schemas import UserCreate, UserOut
from ..crud.user_crud import create_user_full, update_user_full, get_user_by_id, seed_roles, delete_user_full
from ..crud.kyc_crud import save_kyc_files

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=201)
def post_user(payload: UserCreate, db=Depends(get_db)):
    u = create_user_full(db, payload)
    # devolvemos un UserOut “manual” para no depender del ORM directo
    return {
        "id": u.id,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "email": u.email,
        "roles": [ur.role.code for ur in u.roles],
        "creado_en": u.creado_en,
    }


@router.put("/{user_id}", response_model=UserOut)
def put_user(
    user_id: str,
    payload: UserCreate,
    db=Depends(get_db),
    _=Depends(current_admin_or_self),
):
    u = update_user_full(db, user_id, payload)
    return {
        "id": u.id,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "email": u.email,
        "roles": [ur.role.code for ur in u.roles],
        "creado_en": u.creado_en,
    }


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    db=Depends(get_db),
    _=Depends(current_admin_or_self),
):
    u = get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": u.id,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "email": u.email,
        "roles": [ur.role.code for ur in u.roles],
        "creado_en": u.creado_en,
    }


@router.post("/{user_id}/kyc")
def upload_kyc(
    user_id: str,
    files: List[UploadFile] = File(...),
    db=Depends(get_db),
    _=Depends(current_admin_or_self),
):
    return save_kyc_files(db, user_id, files)


@router.post("/seed-roles", tags=["admin"])
def seed_roles_endpoint(db=Depends(get_db)):
    seed_roles(db)
    return {"ok": True}

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    db=Depends(get_db),
    _=Depends(current_admin_or_self),
):
    """
    Elimina un usuario.
    Solo puede hacerlo:
    - el admin, o
    - el propio usuario (current_admin_or_self)
    """
    ok = delete_user_full(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # 204 no retorna body
    return
