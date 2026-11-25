from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.params import IdPath, IdQuery
from app.schemas.subcategory import SubCategoryCreate, SubCategoryResponse, SubCategoryUpdate
from app.services import subcategories as service

router = APIRouter(prefix="/subcategories", tags=["Sub-categories"])


@router.post("", response_model=SubCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_subcategory(payload: SubCategoryCreate, db: Session = Depends(get_db)):
    return service.create_subcategory(db, payload)


@router.get("", response_model=list[SubCategoryResponse])
def list_subcategories(category_id: IdQuery = None, db: Session = Depends(get_db)):
    return service.list_subcategories(db, category_id)


@router.get("/{subcategory_id}", response_model=SubCategoryResponse)
def get_subcategory(subcategory_id: IdPath, db: Session = Depends(get_db)):
    return service.get_subcategory(db, subcategory_id)


@router.put("/{subcategory_id}", response_model=SubCategoryResponse)
def update_subcategory(subcategory_id: IdPath, payload: SubCategoryUpdate, db: Session = Depends(get_db)):
    return service.update_subcategory(db, subcategory_id, payload)


@router.delete("/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_subcategory(subcategory_id: IdPath, db: Session = Depends(get_db)):
    service.delete_subcategory(db, subcategory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
