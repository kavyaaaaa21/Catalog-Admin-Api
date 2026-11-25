from app.core.config import settings
from tests.conftest import product_payload


# ---- required tests -------------------------------------------------------
def test_login_success_and_failure(client):
    ok = client.post("/auth/login", json={"username": settings.admin_username, "password": settings.admin_password})
    assert ok.status_code == 200
    body = ok.json()
    assert body["token_type"] == "bearer" and body["access_token"]

    bad = client.post("/auth/login", json={"username": settings.admin_username, "password": "wrong"})
    assert bad.status_code == 401


def test_unauthorized_access(client):
    for method, url in [("get", "/products"), ("get", "/brands"), ("post", "/categories"), ("get", "/subcategories")]:
        assert getattr(client, method)(url).status_code == 401
    bad = client.get("/products", headers={"Authorization": "Bearer not-a-real-token"})
    assert bad.status_code == 401


def test_create_product_with_mismatched_subcategory_returns_422(client, auth_headers, catalog):
    # sub_b belongs to category B, but the product is placed in category A
    payload = product_payload(catalog, subcategory_id=catalog["sub_b"])
    res = client.post("/products", json=payload, headers=auth_headers)
    assert res.status_code == 422
    assert "does not belong to category" in res.json()["detail"]


def test_products_pagination(client, auth_headers, catalog):
    for n in range(1, 13):
        assert client.post("/products", json=product_payload(catalog, n), headers=auth_headers).status_code == 201

    res = client.get("/products?page=3&page_size=5", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 12 and body["page"] == 3 and body["page_size"] == 5
    assert len(body["items"]) == 2

    assert client.get("/products?page_size=51", headers=auth_headers).status_code == 422


# ---- extra coverage -------------------------------------------------------
def test_create_product_returns_contract_fields(client, auth_headers, catalog):
    res = client.post("/products", json=product_payload(catalog), headers=auth_headers)
    assert res.status_code == 201
    body = res.json()
    for field in ("id", "name", "price", "stock_quantity", "is_active"):
        assert field in body
    assert body["price"] == 99.99 and body["is_active"] is True


def test_duplicate_slug_and_sku_return_409(client, auth_headers, catalog):
    client.post("/products", json=product_payload(catalog, 1), headers=auth_headers)
    dup_slug = client.post("/products", json=product_payload(catalog, 2, slug="product-1"), headers=auth_headers)
    dup_sku = client.post("/products", json=product_payload(catalog, 3, sku="SKU-1"), headers=auth_headers)
    assert dup_slug.status_code == 409 and dup_sku.status_code == 409
    assert client.post("/brands", json={"name": "Acme", "slug": "other"}, headers=auth_headers).status_code == 409


def test_subcategory_name_unique_only_within_category(client, auth_headers, catalog):
    same_cat = client.post("/subcategories", json={"category_id": catalog["cat_a"], "name": "Phones", "slug": "p2"},
                           headers=auth_headers)
    other_cat = client.post("/subcategories", json={"category_id": catalog["cat_b"], "name": "Phones", "slug": "p3"},
                            headers=auth_headers)
    assert same_cat.status_code == 409
    assert other_cat.status_code == 201


def test_validation_errors_are_structured(client, auth_headers, catalog):
    bad = product_payload(catalog, slug="Bad Slug!", price=0, stock_quantity=-1)
    res = client.post("/products", json=bad, headers=auth_headers)
    assert res.status_code == 422
    fields = {e["field"] for e in res.json()["errors"]}
    assert {"slug", "price", "stock_quantity"} <= fields
    assert all("message" in e for e in res.json()["errors"])


def test_unknown_references_return_422(client, auth_headers, catalog):
    res = client.post("/products", json=product_payload(catalog, brand_id=9999), headers=auth_headers)
    assert res.status_code == 422 and "Brand" in res.json()["detail"]


def test_delete_blocked_when_products_exist_then_allowed(client, auth_headers, catalog):
    pid = client.post("/products", json=product_payload(catalog), headers=auth_headers).json()["id"]

    assert client.delete(f"/brands/{catalog['brand']}", headers=auth_headers).status_code == 409
    assert client.delete(f"/categories/{catalog['cat_a']}", headers=auth_headers).status_code == 409
    assert client.delete(f"/subcategories/{catalog['sub_a']}", headers=auth_headers).status_code == 409

    assert client.delete(f"/products/{pid}", headers=auth_headers).status_code == 204
    assert client.get(f"/products/{pid}", headers=auth_headers).status_code == 404

    assert client.delete(f"/subcategories/{catalog['sub_a']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/categories/{catalog['cat_a']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/brands/{catalog['brand']}", headers=auth_headers).status_code == 204


def test_partial_update_and_revalidation(client, auth_headers, catalog):
    pid = client.post("/products", json=product_payload(catalog), headers=auth_headers).json()["id"]

    ok = client.put(f"/products/{pid}", json={"price": 49.5, "stock_quantity": 0}, headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["price"] == 49.5 and ok.json()["name"] == "Product 1"

    # moving to category B without changing the sub-category breaks the rule
    bad = client.put(f"/products/{pid}", json={"category_id": catalog["cat_b"]}, headers=auth_headers)
    assert bad.status_code == 422

    moved = client.put(
        f"/products/{pid}",
        json={"category_id": catalog["cat_b"], "subcategory_id": catalog["sub_b"]},
        headers=auth_headers,
    )
    assert moved.status_code == 200

    assert client.put(f"/products/{pid}", json={"name": None}, headers=auth_headers).status_code == 422
    assert client.put("/products/9999", json={"price": 1}, headers=auth_headers).status_code == 404


def test_filters_and_subcategory_category_filter(client, auth_headers, catalog):
    client.post("/products", json=product_payload(catalog, 1), headers=auth_headers)
    client.post("/products", json=product_payload(catalog, 2, is_active=False), headers=auth_headers)

    active = client.get("/products?is_active=true", headers=auth_headers).json()
    assert active["total"] == 1
    assert client.get("/products?sku=SKU-2", headers=auth_headers).json()["total"] == 1
    assert client.get(f"/products?brand_id={catalog['brand']}", headers=auth_headers).json()["total"] == 2

    subs = client.get(f"/subcategories?category_id={catalog['cat_b']}", headers=auth_headers).json()
    assert [s["id"] for s in subs] == [catalog["sub_b"]]


def test_huge_integers_never_cause_500(client, auth_headers, catalog):
    huge = 10**20
    assert client.get(f"/brands/{huge}", headers=auth_headers).status_code == 422
    assert client.get(f"/products?page={huge}", headers=auth_headers).status_code == 422
    assert client.get(f"/subcategories?category_id={huge}", headers=auth_headers).status_code == 422
    res = client.post("/products", json=product_payload(catalog, brand_id=huge), headers=auth_headers)
    assert res.status_code == 422


def test_missing_ids_return_404(client, auth_headers):
    for url in ("/brands/999", "/categories/999", "/subcategories/999", "/products/999"):
        assert client.get(url, headers=auth_headers).status_code == 404
        assert client.delete(url, headers=auth_headers).status_code == 404


def test_malformed_json_is_structured_422(client, auth_headers):
    res = client.post("/brands", content="{bad", headers={**auth_headers, "Content-Type": "application/json"})
    assert res.status_code == 422 and res.json()["errors"][0]["field"] == "body"
