from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  (register tables on Base.metadata)
from app.core.exceptions import AppError
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.routers import auth, brands, categories, products, subcategories
from app.routers.deps import get_current_admin
from app.services.auth import ensure_admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_admin(db)
    yield


app = FastAPI(
    title="ShopSphere - Catalog Admin API",
    description="Admin-only API for brands, categories, sub-categories and products.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = [str(p) for p in err["loc"]]
        field = ".".join(loc[1:]) or (loc[0] if loc else "body")
        if err["type"] == "json_invalid":
            field = "body"
        message = err["msg"].removeprefix("Value error, ")
        errors.append({"field": field, "message": message})
    return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    content: dict = {"detail": exc.message}
    if exc.field:
        content["errors"] = [{"field": exc.field, "message": exc.message}]
    return JSONResponse(status_code=exc.status_code, content=content)


# /auth/login is public; everything else requires a valid admin JWT.
app.include_router(auth.router)
protected = [Depends(get_current_admin)]
for r in (brands.router, categories.router, subcategories.router, products.router):
    app.include_router(r, dependencies=protected)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
