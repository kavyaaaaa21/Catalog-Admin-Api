import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db, make_engine
from app.main import app
from app.services.auth import ensure_admin


@pytest.fixture()
def client():
    """TestClient backed by a fresh in-memory SQLite DB per test."""
    engine = make_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with TestingSession() as db:
        ensure_admin(db)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)  # not used as a context manager -> startup hook is skipped
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    res = client.post("/auth/login", json={"username": settings.admin_username, "password": settings.admin_password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def catalog(client, auth_headers):
    """A brand, two categories and one sub-category in each."""
    def post(url, body):
        res = client.post(url, json=body, headers=auth_headers)
        assert res.status_code == 201, res.text
        return res.json()["id"]

    brand = post("/brands", {"name": "Acme", "slug": "acme"})
    cat_a = post("/categories", {"name": "Electronics", "slug": "electronics"})
    cat_b = post("/categories", {"name": "Fashion", "slug": "fashion"})
    sub_a = post("/subcategories", {"category_id": cat_a, "name": "Phones", "slug": "phones"})
    sub_b = post("/subcategories", {"category_id": cat_b, "name": "Shoes", "slug": "shoes"})
    return {"brand": brand, "cat_a": cat_a, "cat_b": cat_b, "sub_a": sub_a, "sub_b": sub_b}


def product_payload(catalog, n=1, **overrides):
    body = {
        "brand_id": catalog["brand"],
        "category_id": catalog["cat_a"],
        "subcategory_id": catalog["sub_a"],
        "name": f"Product {n}",
        "slug": f"product-{n}",
        "sku": f"SKU-{n}",
        "description": "desc",
        "price": 99.99,
        "stock_quantity": 5,
    }
    body.update(overrides)
    return body
