# routes_product_comments.py (opcional)
# backend/app/routers/routes_product_comments.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.models import Product, ProductComment
from ..schemas.product_schemas import ProductCommentOut

router = APIRouter(prefix="/products", tags=["product-comments"])


@router.get("/{product_id}/comments", response_model=List[ProductCommentOut])
def list_comments(product_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ProductComment)
        .filter(ProductComment.product_id == product_id)
        .order_by(ProductComment.created_at.desc())
        .all()
    )
    return rows

