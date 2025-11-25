from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderItemIn(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    seller: Optional[str] = None
    company: Optional[str] = None
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)

class OrderCreate(BaseModel):
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    status: str = "Entregado"
    items: List[OrderItemIn]

class OrderItemOut(OrderItemIn):
    id: str

class OrderOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    status: str
    created_at: datetime
    total_amount: int
    items: List[OrderItemOut]

    model_config = {"from_attributes": True}
