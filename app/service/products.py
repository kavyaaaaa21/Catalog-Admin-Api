from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.models import Brand, Category, Product, SubCategory
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.common import commit, ensure_unique, get_or_404

LABEL = "Product"


def _validate_references(db: Session, brand_id: int, category_id: int, subcategory_id: int) -> None:
    if db.get(Brand, brand_id) is None:
        raise BusinessRuleError(f"Brand with id {brand_id} does not exist", field="brand_id")
    if db.get(Category, category_id) is None:
        raise BusinessRuleError(f"Category with id {category_id} does not exist", field="category_id")
    sub = db.get(SubCategory, subcategory_id)
    if sub is None:
        raise BusinessRuleError(f"Sub-category with id {subcategory_id} does not exist", field="subcategory_id")
    if sub.category_id != category_id:
        raise BusinessRuleError(
            f"Sub-category {subcategory_id} does not belong to category {category_id} "
            f"(it belongs to category {sub.category_id})",
            field="subcategory_id",
        )


def list_products(
    db: Session,
    page: int,
    page_size: int,
    brand_id: int | None = None,
    category_id: int | None = None,
    subcategory_id: int | None = None,
    is_active: bool | None = None,
    sku: str | None = None,
) -> dict:
    stmt = select(Product)
    if brand_id is not None:
        stmt = stmt.where(Product.brand_id == brand_id)
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if subcategory_id is not None:
        stmt = stmt.where(Product.subcategory_id == subcategory_id)
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
    if sku is not None:
        stmt = stmt.where(Product.sku == sku)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_product(db: Session, product_id: int) -> Product:
    return get_or_404(db, Product, product_id, LABEL)


def create_product(db: Session, data: ProductCreate) -> Product:
    _validate_references(db, data.brand_id, data.category_id, data.subcategory_id)
    ensure_unique(db, Product, "slug", data.slug, LABEL)
    ensure_unique(db, Product, "sku", data.sku, LABEL)
    product = Product(**data.model_dump())
    db.add(product)
    commit(db)
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    values = data.model_dump(exclude_unset=True)

    for field in ("slug", "sku"):
        if field in values:
            ensure_unique(db, Product, field, values[field], LABEL, exclude_id=product_id)

    # Re-check the brand/category/sub-category combination using merged values.
    if {"brand_id", "category_id", "subcategory_id"} & values.keys():
        _validate_references(
            db,
            values.get("brand_id", product.brand_id),
            values.get("category_id", product.category_id),
            values.get("subcategory_id", product.subcategory_id),
        )

    for key, value in values.items():
        setattr(product, key, value)
    commit(db)
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    db.delete(product)
    commit(db)
