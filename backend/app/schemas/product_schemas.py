# backend/app/schemas/product_schemas.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class ProductImageOut(BaseModel):
    id: str
    url: HttpUrl | str
    sort_order: int
    class Config:
        from_attributes = True

class ProductCommentOut(BaseModel):
    id: str
    user_id: str
    rating: int
    text: Optional[str] = None
    created_at: str
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., max_length=120)
    description: Optional[str] = None
    price: int = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    condition: str = Field("NUEVO", pattern="^(NUEVO|USADO)$")
    category_id: Optional[str] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True

    pay_method: Optional[str] = None
    network: Optional[str] = None
    alias: Optional[str] = None
    wallet: Optional[str] = None


class ProductCreate(ProductBase):
    images: Optional[List[str]] = None  # lista de URLs

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    condition: Optional[str] = Field(None, pattern="^(NUEVO|USADO)$")
    category_id: Optional[str] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    images: Optional[List[str]] = None

class ProductOut(ProductBase):
    id: str
    seller_id: str
    rating: float = 0.0
    sold_count: int = 0
    images: List[ProductImageOut] = []
    seller_name: Optional[str] = None
    class Config:
        from_attributes = True
