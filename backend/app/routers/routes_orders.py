# backend/app/routers/routes_orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import joinedload

from ..deps import get_db, get_current_user
from ..models.models import Cart, Order, OrderItem, User

router = APIRouter(prefix="/orders", tags=["orders"])


# ============ Schemas ============
class OrderItemOut(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    seller: Optional[str] = None
    company: Optional[str] = None
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    status: str
    created_at: datetime
    total_amount: int
    items: List[OrderItemOut]

    class Config:
        from_attributes = True


# ============ GET /orders (solo comprador dueño) ============
@router.get("", response_model=List[OrderOut])
def list_my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders


# ============ POST /orders/checkout ============
@router.post("/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Genera una orden desde el carrito.
    Queda en pending_admin hasta verificación admin/vendedor.
    """
    try:
        # 1) traer carrito del usuario
        cart = (
            db.query(Cart)
            .filter(Cart.user_id == user.id)
            .order_by(Cart.created_at.desc())
            .first()
        )
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="El carrito está vacío")

        # 2) calcular total según CartItem.price * CartItem.qty
        total_amount = 0
        for ci in cart.items:
            price = getattr(ci, "price", 0) or 0
            qty = getattr(ci, "qty", 0) or 0
            total_amount += int(price) * int(qty)

        if total_amount <= 0:
            raise HTTPException(status_code=400, detail="Total inválido")

        # 3) crear orden
        order = Order(
            user_id=user.id,
            user_name=f"{user.nombre} {user.apellido}",
            total_amount=total_amount,
            status="pending_admin",
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 4) crear items de orden con nombres reales del modelo OrderItem
        for ci in cart.items:
            oi = OrderItem(
                order_id=order.id,
                product_id=ci.product_id,
                product_name=ci.name,          # CartItem.name -> OrderItem.product_name
                category=None,
                subcategory=None,
                seller=ci.seller,
                company=None,
                quantity=int(ci.qty),          # CartItem.qty -> OrderItem.quantity
                unit_price=int(ci.price),      # CartItem.price -> OrderItem.unit_price
            )
            db.add(oi)

        # 5) vaciar carrito
        for ci in list(cart.items):
            db.delete(ci)

        db.commit()
        db.refresh(order)

        return order

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                "Error interno al generar la orden. "
                "El pedido queda en proceso hasta la verificación por parte del "
                "administrador para la liberación del producto."
            ),
        )
    except Exception as e:
        db.rollback()
        print(f"UNEXPECTED ERROR CHECKOUT: {e}")
        raise HTTPException(
            status_code=500,
            detail=(
                "Error inesperado al procesar el checkout. "
                "El pedido queda en proceso hasta la verificación por parte del "
                "administrador para la liberación del producto."
            ),
        )


@router.get("/seller", response_model=List[OrderOut])
def list_seller_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Órdenes donde el usuario logueado es vendedor.
    Filtra por OrderItem.seller (snapshot string).
    """
    seller_key = (user.nombre or "").strip().lower()

    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .order_by(Order.created_at.desc())
        .all()
    )

    filtered = []
    for o in orders:
        for it in (o.items or []):
            if (it.seller or "").strip().lower() == seller_key:
                filtered.append(o)
                break

    out: List[OrderOut] = []
    for o in filtered:
        items_out = [
            OrderItemOut(
                product_id=i.product_id,
                product_name=i.product_name,
                category=i.category,
                subcategory=i.subcategory,
                seller=i.seller,
                company=i.company,
                quantity=i.quantity,
                unit_price=i.unit_price,
            )
            for i in (o.items or [])
        ]

        out.append(
            OrderOut(
                id=o.id,
                user_id=o.user_id,
                user_name=o.user_name,           # ✅ ahora sí
                status=o.status,
                created_at=o.created_at,         # ✅ ahora sí
                total_amount=o.total_amount,
                items=items_out,
            )
        )
    return out
