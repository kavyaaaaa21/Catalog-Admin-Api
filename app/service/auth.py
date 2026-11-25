from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models import AdminUser


def ensure_admin(db: Session) -> AdminUser:
    """Create the single admin user from .env if it does not exist yet."""
    admin = db.scalar(select(AdminUser).where(AdminUser.username == settings.admin_username))
    if admin is None:
        admin = AdminUser(
            username=settings.admin_username,
            hashed_password=hash_password(settings.admin_password),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin


def authenticate(db: Session, username: str, password: str) -> AdminUser | None:
    admin = db.scalar(select(AdminUser).where(AdminUser.username == username))
    if admin is None or not verify_password(password, admin.hashed_password):
        return None
    return admin
