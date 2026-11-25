from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError


def get_or_404(db: Session, model, obj_id: int, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise NotFoundError(f"{label} with id {obj_id} not found")
    return obj


def ensure_unique(db: Session, model, field: str, value, label: str, exclude_id: int | None = None):
    stmt = select(model.id).where(getattr(model, field) == value)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ConflictError(f"{label} with {field} '{value}' already exists", field=field)


def commit(db: Session):
    """Commit, translating any race-condition integrity error into a 409."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Operation violates a uniqueness or integrity constraint") from exc
