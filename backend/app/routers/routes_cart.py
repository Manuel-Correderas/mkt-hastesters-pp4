# backend/app/routers/routes_cart.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models.models import Cart, CartItem, Product, User
from ..schemas.cart_schemas import CartOut, CartUpdateQty
from ..crud import cart_crud

router = APIRouter(prefix="/cart", tags=["cart"])


class AddItemPayload(BaseModel):
    product_id: str
    qty: int = 1


def _get_or_create_cart(db: Session, user_id: str) -> Cart:
    """
    Devuelve el carrito del usuario. Si no existe, lo crea.
    """
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .order_by(Cart.created_at.desc())
        .first()
    )
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_item(
    payload: AddItemPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Agrega un producto al carrito del usuario actual y descuenta stock.
    """
    if payload.qty <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")

    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if product.stock < payload.qty:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # Descontar stock
    product.stock -= payload.qty

    cart = _get_or_create_cart(db, user.id)

    # Ver si ya existe item en el carrito
    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
        .first()
    )

    if item:
        item.qty += payload.qty
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            name=product.name,
            price=product.price,
            qty=payload.qty,
            image=product.image_url or "",
            seller=str(product.seller_id) if product.seller_id else None,
            stock_snapshot=product.stock,
        )
        db.add(item)

    db.commit()
    db.refresh(cart)
    db.refresh(product)

    return cart_crud.get_cart_for_user(db, user.id)


@router.get("", response_model=CartOut)
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Devuelve el carrito del usuario actual.
    """
    return cart_crud.get_cart_for_user(db, user.id)


@router.patch("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_item_qty(
    item_id: str,
    payload: CartUpdateQty,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Actualiza la cantidad (botones + y - en el frontend).
    """
    ok = cart_crud.update_cart_item_qty(db, user.id, item_id, payload.qty)
    if not ok:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return  # 204 sin body


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Elimina un ítem del carrito (botón 🗑 Quitar).
    """
    ok = cart_crud.remove_cart_item(db, user.id, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return  # 204 sin body
