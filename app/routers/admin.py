from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Claim, Item, User
from ..security import admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    count = lambda *f: db.query(func.count(Item.id)).filter(*f).scalar()  # noqa: E731
    return {
        "students": db.query(func.count(User.id)).scalar(),
        "total": count(), "lost": count(Item.type == "lost"), "found": count(Item.type == "found"),
        "returned": count(Item.status == "returned"),
        "pending_claims": db.query(func.count(Claim.id)).filter(Claim.status == "pending").scalar(),
    }
