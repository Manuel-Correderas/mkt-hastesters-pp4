# backend/app/schemas/cart_schemas.py
from pydantic import BaseModel, Field
from typing import List

class CartItemOut(BaseModel):
    id: str
    product_id: str
    name: str
    price: int = Field(ge=0)
    qty: int = Field(ge=1)
    image: str | None = None
    seller: str | None = None
    stock_snapshot: int

    class Config:
        from_attributes = True

class CartOut(BaseModel):
    id: str
    user_id: str
    items: List[CartItemOut] = []
    total: int = 0

    class Config:
        from_attributes = True

class CartUpdateQty(BaseModel):
    qty: int = Field(ge=1)
