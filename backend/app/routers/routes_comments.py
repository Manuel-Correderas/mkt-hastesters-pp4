# app/routers/routes_comments.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..deps import get_db, get_current_user  # <-- asegurate que exista
from ..models.models import Comment, Product, Order, OrderItem, User  # <-- Order/OrderItem existen en tu init_db
from ..schemas.comment_schemas import CommentCreate, CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("", response_model=list[CommentOut])
def list_comments(
    db: Session = Depends(get_db),
    product_id: Optional[str] = Query(None)
):
    q = db.query(Comment)
    if product_id:
        q = q.filter(Comment.product_id == product_id)
    rows = q.order_by(Comment.created_at.desc()).all()
    return rows


def user_received_product(db: Session, user_id: str, product_id: str) -> bool:
    """
    True si existe al menos una OrderItem del producto
    en una Order del user con status 'Entregado'.
    """
    row = (
        db.query(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            # validamos status case-insensitive
            Order.status.ilike("entregado")
        )
        .first()
    )
    return row is not None


@router.post("", response_model=CommentOut, status_code=201)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # <-- login obligatorio
):
    # Validar producto existente
    p = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.is_active == True)
        .first()
    )
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    # Validar que el usuario lo haya comprado y recibido
    if not user_received_product(db, current_user.id, payload.product_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo podés comentar productos que compraste y recibiste (estado Entregado)."
        )

    c = Comment(
        product_id=payload.product_id,
        user_name=f"{current_user.nombre} {current_user.apellido}".strip() or current_user.email,
        rating=payload.rating,
        criteria=payload.criteria or {},
        comment=payload.comment or ""
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{comment_id}", status_code=204)
@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ---- helper interno: detectar admin en varios formatos ----
    def _is_admin(u: User) -> bool:
        # caso 1: campo directo "role"
        r = getattr(u, "role", None)
        if r and str(r).upper() == "ADMIN":
            return True

        # caso 2: lista/relación "roles"
        roles_attr = getattr(u, "roles", None)
        if roles_attr:
            # puede ser lista de strings o lista de UserRole con .role/.name
            for item in roles_attr:
                if isinstance(item, str) and item.upper() == "ADMIN":
                    return True
                # UserRole -> Role (o similar)
                role_obj = getattr(item, "role", None) or getattr(item, "name", None)
                if role_obj and str(role_obj).upper() == "ADMIN":
                    return True

        return False

    # ---- solo ADMIN puede borrar ----
    if not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede eliminar comentarios."
        )

    c = db.query(Comment).filter(Comment.id == comment_id).first()
    if not c:
        return
    db.delete(c)
    db.commit()
