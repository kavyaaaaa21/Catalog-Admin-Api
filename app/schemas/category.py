from pydantic import BaseModel, ConfigDict

from app.schemas.common import Name, PartialUpdate, Slug


class CategoryCreate(BaseModel):
    name: Name
    slug: Slug
    is_active: bool = True


class CategoryUpdate(PartialUpdate):
    name: Name | None = None
    slug: Slug | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    is_active: bool
