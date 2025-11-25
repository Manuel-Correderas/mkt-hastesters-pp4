# routes_products.py
# backend/app/routers/routes_products.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db, get_current_user
from ..models.models import Product, ProductImage
from ..schemas.product_schemas import ProductCreate, ProductUpdate, ProductOut
from ..security import require_vendor

router = APIRouter(prefix="/products", tags=["products"])

def _product_to_out(p: Product) -> ProductOut:
    out = ProductOut.model_validate(p)
    # seller_name (si tenés nombre/apellido en User)
    try:
        out.seller_name = f"{p.seller.nombre} {p.seller.apellido}".strip() if p.seller else None
    except Exception:
        out.seller_name = None
    # ordenar imágenes
    if p.images:
        out.images = sorted(p.images, key=lambda im: im.sort_order or 0)
    return out

@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate,
                   db: Session = Depends(get_db),
                   user = Depends(get_current_user)):
    require_vendor(user)
    p = Product(
        seller_id=user.id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        condition=payload.condition,
        category_id=payload.category_id,
        subcategory=payload.subcategory,
        image_url=payload.image_url,
        is_active=payload.is_active
    )
    db.add(p)
    db.flush()  # para obtener p.id
    if payload.images:
        for i, url in enumerate(payload.images):
            db.add(ProductImage(product_id=p.id, url=url, sort_order=i))
    db.commit()
    db.refresh(p)
    return _product_to_out(p)

@router.get("", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db),
                  q: Optional[str] = Query(None),
                  category_id: Optional[str] = None,
                  seller_id: Optional[str] = None,
                  limit: int = 20,
                  offset: int = 0):
    query = db.query(Product).filter(Product.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.filter(Product.name.ilike(like))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if seller_id:
        query = query.filter(Product.seller_id == seller_id)

    rows = query.order_by(Product.created_at.desc()).limit(limit).offset(offset).all()
    return [_product_to_out(p) for p in rows]

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return _product_to_out(p)

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: str,
                   payload: ProductUpdate,
                   db: Session = Depends(get_db),
                   user = Depends(get_current_user)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    require_vendor(user)
    if p.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No sos el dueño del producto")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field != "images":
            setattr(p, field, value)

    if payload.images is not None:
        for im in list(p.images or []):
            db.delete(im)
        for i, url in enumerate(payload.images):
            db.add(ProductImage(product_id=p.id, url=url, sort_order=i))

    db.commit()
    db.refresh(p)
    return _product_to_out(p)

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: str,
                   db: Session = Depends(get_db),
                   user = Depends(get_current_user)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return
    require_vendor(user)
    if p.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No sos el dueño del producto")

    p.is_active = False
    db.commit()
