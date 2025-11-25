from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from deps import get_db, current_admin_or_self
from schemas import UserCreate, UserOut
from crud import create_user, update_user, get_user_out, save_kyc_files

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserOut, status_code=201)
def post_user(payload: UserCreate, db=Depends(get_db)):
    return create_user(db, payload)

@router.put("/{user_id}", response_model=UserOut)
def put_user(user_id: str, payload: UserCreate, db=Depends(get_db), _=Depends(current_admin_or_self)):
    return update_user(db, user_id, payload)

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db=Depends(get_db), _=Depends(current_admin_or_self)):
    return get_user_out(db, user_id)

@router.post("/{user_id}/kyc")
def upload_kyc(user_id: str, files: List[UploadFile] = File(...), db=Depends(get_db), _=Depends(current_admin_or_self)):
    return save_kyc_files(db, user_id, files)
