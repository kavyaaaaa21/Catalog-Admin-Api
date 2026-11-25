# ShopSphere – Catalog Admin API (BE-1)

Admin-only REST API for brands, categories, sub-categories and products.
Built with **FastAPI, SQLAlchemy 2, Pydantic v2, SQLite, JWT (PyJWT) and bcrypt**.

## Project layout
```
app/
  core/      config (env), security (bcrypt + JWT), custom exceptions
  db/        Base, engine/session, seed script
  models/    SQLAlchemy models (AdminUser, Brand, Category, SubCategory, Product)
  schemas/   Pydantic Create / Update / Response schemas
  services/  business rules (uniqueness, references, delete guards, pagination)
  routers/   thin HTTP layer + auth dependency
  main.py    app, exception handlers, router wiring
tests/       pytest + TestClient
```

## Setup
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # edit secrets if you like
python -m app.db.seed                                  # creates tables, admin + sample data
uvicorn app.main:app --reload
```
Swagger UI: http://localhost:8000/docs  (click **Authorize**, paste the token from `/auth/login`).

**Admin test credentials** (from `.env.example`): `admin` / `Admin@12345`

```bash
curl -X POST localhost:8000/auth/login -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"Admin@12345"}'
```

## Run tests
```bash
pytest -q
```

## Docker (bonus)
```bash
docker compose up --build      # API on :8000, seeded automatically
```

## Endpoints
All endpoints except `/auth/login` need `Authorization: Bearer <token>` (401 otherwise). Token expiry: 30 min.

| Resource | Endpoints |
|---|---|
| Auth | `POST /auth/login` (JSON `{username, password}`) |
| Brands | `POST/GET /brands`, `GET/PUT/DELETE /brands/{id}` |
| Categories | `POST/GET /categories`, `GET/PUT/DELETE /categories/{id}` |
| Sub-categories | `POST/GET /subcategories` (`?category_id=`), `GET/PUT/DELETE /subcategories/{id}` |
| Products | `POST/GET /products`, `GET/PUT/DELETE /products/{id}` |

`GET /products` query params: `page` (default 1), `page_size` (default 10, max 50), and the bonus filters
`brand_id`, `category_id`, `subcategory_id`, `is_active`, `sku`. Returns `{items, total, page, page_size}`.

## Status codes & rules
- `201` create, `204` delete, `404` missing, `409` duplicate / blocked delete, `422` validation or business-rule error.
- Product's sub-category must belong to its category; brand/category/sub-category ids must exist (422).
- Slugs: lowercase letters, digits, hyphens. `price > 0`, `stock_quantity >= 0`.
- Deleting a brand / category / sub-category that still has products → `409`. Deleting a product is allowed.
- Deleting a (product-free) category also removes its sub-categories.
- Moving a sub-category to another category is blocked (409) while it has products.
- Update (`PUT`) is partial: send only the fields to change; explicit `null` is rejected (except product `description`).

Validation error shape:
```json
{"detail": "Validation failed", "errors": [{"field": "price", "message": "Input should be greater than 0"}]}
```

## Integration contract
The order service reads `id`, `name`, `price`, `stock_quantity`, `is_active` from products – names are unchanged in
`ProductResponse`.
