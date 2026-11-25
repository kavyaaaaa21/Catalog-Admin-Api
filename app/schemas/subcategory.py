from pydantic import BaseModel, ConfigDict

from app.schemas.common import Id, Name, PartialUpdate, Slug


class SubCategoryCreate(BaseModel):
    category_id: Id
    name: Name
    slug: Slug
    is_active: bool = True


class SubCategoryUpdate(PartialUpdate):
    category_id: Id | None = None
    name: Name | None = None
    slug: Slug | None = None
    is_active: bool | None = None


class SubCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: Id
    name: str
    slug: str
    is_active: bool
