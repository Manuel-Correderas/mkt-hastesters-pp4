##backend/app/crud/order_crud.py
from sqlalchemy.orm import Session
from ..models.models import Cart, CartItem, Order, OrderItem, Payment

def checkout(db: Session, user_id: str) -> Order:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        raise ValueError("Carrito vacío")
    total = sum(ci.qty * ci.price for ci in cart.items)

    order = Order(user_id=user_id, total=total, status="CREADA")
    db.add(order); db.flush()

    for ci in cart.items:
        db.add(OrderItem(order_id=order.id, product_id=ci.product_id,
                         name=ci.name, price=ci.price, qty=ci.qty))
    for ci in list(cart.items):
        db.delete(ci)

    db.commit(); db.refresh(order)
    return order
