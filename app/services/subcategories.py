from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError
from app.models import Category, Product, SubCategory
from app.schemas.subcategory import SubCategoryCreate, SubCategoryUpdate
from app.services.common import commit, get_or_404

LABEL = "Sub-category"


def _ensure_category_exists(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise BusinessRuleError(f"Category with id {category_id} does not exist", field="category_id")


def _ensure_name_free(db: Session, category_id: int, name: str, exclude_id: int | None = None) -> None:
    stmt = select(SubCategory.id).where(SubCategory.category_id == category_id, SubCategory.name == name)
    if exclude_id is not None:
        stmt = stmt.where(SubCategory.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ConflictError(f"Sub-category '{name}' already exists in category {category_id}", field="name")


def _product_count(db: Session, subcategory_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Product).where(Product.subcategory_id == subcategory_id)) or 0


def list_subcategories(db: Session, category_id: int | None = None) -> list[SubCategory]:
    stmt = select(SubCategory).order_by(SubCategory.id)
    if category_id is not None:
        stmt = stmt.where(SubCategory.category_id == category_id)
    return list(db.scalars(stmt))


def get_subcategory(db: Session, subcategory_id: int) -> SubCategory:
    return get_or_404(db, SubCategory, subcategory_id, LABEL)


def create_subcategory(db: Session, data: SubCategoryCreate) -> SubCategory:
    _ensure_category_exists(db, data.category_id)
    _ensure_name_free(db, data.category_id, data.name)
    sub = SubCategory(**data.model_dump())
    db.add(sub)
    commit(db)
    db.refresh(sub)
    return sub


def update_subcategory(db: Session, subcategory_id: int, data: SubCategoryUpdate) -> SubCategory:
    sub = get_subcategory(db, subcategory_id)
    values = data.model_dump(exclude_unset=True)

    new_category_id = values.get("category_id", sub.category_id)
    new_name = values.get("name", sub.name)

    if new_category_id != sub.category_id:
        _ensure_category_exists(db, new_category_id)
        if _product_count(db, subcategory_id):
            raise ConflictError(
                f"Cannot move sub-category {subcategory_id} to another category: it still has products"
            )
    if "category_id" in values or "name" in values:
        _ensure_name_free(db, new_category_id, new_name, exclude_id=subcategory_id)

    for key, value in values.items():
        setattr(sub, key, value)
    commit(db)
    db.refresh(sub)
    return sub


def delete_subcategory(db: Session, subcategory_id: int) -> None:
    sub = get_subcategory(db, subcategory_id)
    count = _product_count(db, subcategory_id)
    if count:
        raise ConflictError(f"Cannot delete sub-category {subcategory_id}: it still has {count} product(s)")
    db.delete(sub)
    commit(db)
