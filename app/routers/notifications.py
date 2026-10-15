from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification, User
from ..security import current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = (db.query(Notification).filter(Notification.user_id == user.id)
            .order_by(Notification.id.desc()).limit(100).all())
    return [{"id": n.id, "message": n.message, "item_id": n.item_id, "is_read": n.is_read} for n in rows]


@router.get("/unread")
def unread(user: User = Depends(current_user), db: Session = Depends(get_db)):
    n = (db.query(func.count(Notification.id))
         .filter(Notification.user_id == user.id, Notification.is_read.is_(False)).scalar())
    return {"unread": n}


@router.post("/read-all")
def read_all(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id).update({"is_read": True})
    db.commit()
    return {"ok": True}
