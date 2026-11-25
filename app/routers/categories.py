from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.routers.params import IdPath, IdQuery
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import categories as service
router = APIRouter(prefix="/categories", tags=["Category"])
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    return service.create_category(db, payload)
@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: IdPath, db: Session = Depends(get_db)):
    return service.get_category(db, category_id)
@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: IdPath, payload: CategoryUpdate, db: Session = Depends(get_db)):
    return service.update_category(db, category_id, payload)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_category(category_id: IdPath, db: Session = Depends(get_db)):
    service.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)