from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models import Brand, Product
from app.schemas.brand import BrandCreate, BrandUpdate
from app.services.common import commit, ensure_unique, get_or_404

LABEL = "Brand"


def list_brands(db: Session) -> list[Brand]:
    return list(db.scalars(select(Brand).order_by(Brand.id)))


def get_brand(db: Session, brand_id: int) -> Brand:
    return get_or_404(db, Brand, brand_id, LABEL)


def create_brand(db: Session, data: BrandCreate) -> Brand:
    ensure_unique(db, Brand, "name", data.name, LABEL)
    ensure_unique(db, Brand, "slug", data.slug, LABEL)
    brand = Brand(**data.model_dump())
    db.add(brand)
    commit(db)
    db.refresh(brand)
    return brand


def update_brand(db: Session, brand_id: int, data: BrandUpdate) -> Brand:
    brand = get_brand(db, brand_id)
    values = data.model_dump(exclude_unset=True)
    for field in ("name", "slug"):
        if field in values:
            ensure_unique(db, Brand, field, values[field], LABEL, exclude_id=brand_id)
    for key, value in values.items():
        setattr(brand, key, value)
    commit(db)
    db.refresh(brand)
    return brand


def delete_brand(db: Session, brand_id: int) -> None:
    brand = get_brand(db, brand_id)
    count = db.scalar(select(func.count()).select_from(Product).where(Product.brand_id == brand_id))
    if count:
        raise ConflictError(f"Cannot delete brand {brand_id}: it still has {count} product(s)")
    db.delete(brand)
    commit(db)
