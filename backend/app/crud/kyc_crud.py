## backend/app/crud/kyc_crud.py
# backend/app/crud/kyc_crud.py
import os, secrets
from typing import List
from sqlalchemy.orm import Session
from fastapi import UploadFile
from ..models.models import KYCDocument

def save_kyc_files(db: Session, user_id: str, files: List[UploadFile]):
    base = os.path.join(".", "secure", "kyc", user_id)
    os.makedirs(base, exist_ok=True)
    saved = []
    for f in files:
        rand = secrets.token_hex(8)
        _, ext = os.path.splitext(f.filename or "")
        disk_name = f"{rand}{ext or ''}"
        path = os.path.join(base, disk_name)
        with open(path, "wb") as out:
            out.write(f.file.read())
        doc = KYCDocument(
            user_id=user_id,
            tipo="OTRO",
            filename=f.filename or disk_name,
            mime=f.content_type or "",
            size_bytes=os.path.getsize(path),
            storage_path=path
        )
        db.add(doc); saved.append(disk_name)
    db.commit()
    return {"archivos_guardados": saved}
