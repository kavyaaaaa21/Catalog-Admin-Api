from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.common import Id, PartialUpdate, Slug

ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Sku = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
Price = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]


class ProductCreate(BaseModel):
    brand_id: Id
    category_id: Id
    subcategory_id: Id
    name: ProductName
    slug: Slug
    sku: Sku
    description: str | None = None
    price: Price
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductUpdate(PartialUpdate):
    nullable_fields = {"description"}

    brand_id: Id | None = None
    category_id: Id | None = None
    subcategory_id: Id | None = None
    name: ProductName | None = None
    slug: Slug | None = None
    sku: Sku | None = None
    description: str | None = None
    price: Price | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Integration contract: the order service reads id, name, price,
    stock_quantity and is_active - keep these names exactly."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    brand_id: Id
    category_id: Id
    subcategory_id: Id
    name: str
    slug: str
    sku: str
    description: str | None
    price: float
    stock_quantity: int
    is_active: bool
    created_at: datetime


class ProductPage(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
