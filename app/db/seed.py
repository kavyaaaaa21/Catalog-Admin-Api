"""Seed the admin user plus sample catalog data.  Run:  python -m app.db.seed"""
from sqlalchemy import func, select

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Brand, Category, Product, SubCategory
from app.services.auth import ensure_admin


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_admin(db)

        if db.scalar(select(func.count()).select_from(Brand)):
            print("Catalog already seeded - admin ensured, nothing else to do.")
            return

        brands = {
            "Apple": Brand(name="Apple", slug="apple"),
            "Samsung": Brand(name="Samsung", slug="samsung"),
            "Nike": Brand(name="Nike", slug="nike"),
        }
        electronics = Category(name="Electronics", slug="electronics")
        fashion = Category(name="Fashion", slug="fashion")
        phones = SubCategory(category=electronics, name="Smartphones", slug="smartphones")
        laptops = SubCategory(category=electronics, name="Laptops", slug="laptops")
        shoes = SubCategory(category=fashion, name="Shoes", slug="shoes")

        db.add_all([*brands.values(), electronics, fashion, phones, laptops, shoes])
        db.flush()

        db.add_all(
            [
                Product(brand=brands["Apple"], category=electronics, subcategory=phones,
                        name="iPhone 15", slug="iphone-15", sku="APL-IP15-128",
                        description="128GB smartphone", price=79900, stock_quantity=25),
                Product(brand=brands["Samsung"], category=electronics, subcategory=phones,
                        name="Galaxy S24", slug="galaxy-s24", sku="SAM-S24-256",
                        description="256GB smartphone", price=74999, stock_quantity=40),
                Product(brand=brands["Apple"], category=electronics, subcategory=laptops,
                        name="MacBook Air M2", slug="macbook-air-m2", sku="APL-MBA-M2",
                        description="13-inch laptop", price=99900, stock_quantity=10),
                Product(brand=brands["Nike"], category=fashion, subcategory=shoes,
                        name="Air Zoom Pegasus", slug="air-zoom-pegasus", sku="NKE-PEG-42",
                        description="Running shoes", price=10995.50, stock_quantity=60),
            ]
        )
        db.commit()
        print("Seeded admin user, 3 brands, 2 categories, 3 sub-categories and 4 products.")


if __name__ == "__main__":
    seed()
