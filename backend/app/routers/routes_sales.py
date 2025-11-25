from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from ..deps import get_db, get_current_user
from ..models.models import Order, OrderItem

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/history")
def sales_history(
    seller_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Devuelve ventas reales del vendedor usando Order + OrderItem y filtrando por seller_id REAL (UUID).
    """
    q = (
        db.query(OrderItem, Order)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(OrderItem.seller_id == seller_id)
    )

    # filtros opcionales
    if start:
        q = q.filter(Order.created_at >= start)
    if end:
        q = q.filter(Order.created_at <= end)
    if search:
        s = f"%{search}%"
        q = q.filter(OrderItem.product_name.ilike(s))

    data = []
    for item, order in q.all():

        data.append({
            "id": item.id,
            "product_name": item.product_name,
            "category": item.category,
            "subcategory": item.subcategory,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item.quantity * item.unit_price,
            "date": order.created_at.isoformat(),
            "client_name": order.user_name,
            "client_address": "—",
            "invoice": f"FAC-{order.id[:8]}",
            "status": order.status.upper(),
            "product_rating": None,
            "client_rating": None,
            "stock_at_sale": None,
        })

    return data
