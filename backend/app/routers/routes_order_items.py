from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models.models import OrderItem

router = APIRouter(prefix="/order_items", tags=["order_items"])


@router.get("", status_code=200)
def get_order_items(db: Session = Depends(get_db), user = Depends(get_current_user)):
    """
    Devuelve TODOS los order_items.
    El frontend después filtra por seller_id o buyer_id.
    """
    items = db.query(OrderItem).all()
    return [i.__dict__ for i in items]
