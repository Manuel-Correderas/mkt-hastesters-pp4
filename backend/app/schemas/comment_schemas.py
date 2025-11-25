# app/schemas/comment_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict

class CommentCreate(BaseModel):
    product_id: str = Field(..., description="ID del producto")
    rating: int = Field(..., ge=1, le=10)
    criteria: Optional[Dict[str, int]] = None
    comment: Optional[str] = None
    user_name: Optional[str] = None  # opcional si no hay auth

class CommentOut(BaseModel):
    id: str
    product_id: str
    user_name: Optional[str] = None
    rating: int
    criteria: Optional[dict] = None
    comment: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}
