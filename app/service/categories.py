from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models import Category, Product
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.common import commit, ensure_unique, get_or_404

LABEL = "Category"


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.id)))


def get_category(db: Session, category_id: int) -> Category:
    return get_or_404(db, Category, category_id, LABEL)


def create_category(db: Session, data: CategoryCreate) -> Category:
    ensure_unique(db, Category, "name", data.name, LABEL)
    ensure_unique(db, Category, "slug", data.slug, LABEL)
    category = Category(**data.model_dump())
    db.add(category)
    commit(db)
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    values = data.model_dump(exclude_unset=True)
    for field in ("name", "slug"):
        if field in values:
            ensure_unique(db, Category, field, values[field], LABEL, exclude_id=category_id)
    for key, value in values.items():
        setattr(category, key, value)
    commit(db)
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    count = db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id))
    if count:
        raise ConflictError(f"Cannot delete category {category_id}: it still has {count} product(s)")
    db.delete(category)  # its (product-free) sub-categories are cascaded
    commit(db)
