from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.params import IdPath, IdQuery
from app.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from app.services import brands as service

router = APIRouter(prefix="/brands", tags=["Brand"])


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    return service.create_brand(db, payload)


@router.get("", response_model=list[BrandResponse])
def list_brands(db: Session = Depends(get_db)):
    return service.list_brands(db)


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(brand_id: IdPath, db: Session = Depends(get_db)):
    return service.get_brand(db, brand_id)


@router.put("/{brand_id}", response_model=BrandResponse)
def update_brand(brand_id: IdPath, payload: BrandUpdate, db: Session = Depends(get_db)):
    return service.update_brand(db, brand_id, payload)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_brand(brand_id: IdPath, db: Session = Depends(get_db)):
    service.delete_brand(db, brand_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)