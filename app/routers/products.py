from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.params import IdPath, IdQuery
from app.schemas.product import ProductCreate, ProductPage, ProductResponse, ProductUpdate
from app.services import products as service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    return service.create_product(db, payload)


@router.get("", response_model=ProductPage)
def list_products(
    page: int = Query(default=1, ge=1, le=1_000_000),
    page_size: int = Query(default=10, ge=1, le=50),
    brand_id: IdQuery = None,
    category_id: IdQuery = None,
    subcategory_id: IdQuery = None,
    is_active: bool | None = None,
    sku: str | None = None,
    db: Session = Depends(get_db),
):
    return service.list_products(db, page, page_size, brand_id, category_id, subcategory_id, is_active, sku)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: IdPath, db: Session = Depends(get_db)):
    return service.get_product(db, product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: IdPath, payload: ProductUpdate, db: Session = Depends(get_db)):
    return service.update_product(db, product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product(product_id: IdPath, db: Session = Depends(get_db)):
    service.delete_product(db, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
