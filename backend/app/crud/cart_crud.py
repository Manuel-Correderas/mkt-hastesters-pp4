# backend/app/crud/cart_crud.py
from typing import Optional
from sqlalchemy.orm import Session

from ..models.models import Cart, CartItem
from ..schemas.cart_schemas import CartOut, CartItemOut


def _get_or_create_cart(db: Session, user_id: str) -> Cart:
    """
    Devuelve el carrito del usuario.
    Si no existe, lo crea vacío.
    """
    cart: Optional[Cart] = (
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


def get_cart_for_user(db: Session, user_id: str) -> CartOut:
    """
    Devuelve el carrito del usuario como CartOut,
    calculando el total a partir de los items.
    """
    cart = _get_or_create_cart(db, user_id)

    items_out = [
        CartItemOut.model_validate(item)  # usa from_attributes=True
        for item in cart.items
    ]

    total = sum(i.price * i.qty for i in cart.items)

    return CartOut(
        id=cart.id,
        user_id=cart.user_id,
        items=items_out,
        total=total,
    )


def update_cart_item_qty(db: Session, user_id: str, item_id: str, qty: int) -> bool:
    """
    Cambia la cantidad de un ítem del carrito del usuario.
    """
    ci: Optional[CartItem] = (
        db.query(CartItem)
        .join(Cart, CartItem.cart_id == Cart.id)
        .filter(CartItem.id == item_id, Cart.user_id == user_id)
        .one_or_none()
    )

    if not ci:
        return False

    ci.qty = qty
    db.commit()
    return True


def remove_cart_item(db: Session, user_id: str, item_id: str) -> bool:
    """
    Elimina un ítem del carrito del usuario.
    """
    ci: Optional[CartItem] = (
        db.query(CartItem)
        .join(Cart, CartItem.cart_id == Cart.id)
        .filter(CartItem.id == item_id, Cart.user_id == user_id)
        .one_or_none()
    )

    if not ci:
        return False

    db.delete(ci)
    db.commit()
    return True
