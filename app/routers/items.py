import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from ..config import MAX_PHOTO_BYTES, UPLOAD_DIR
from ..database import get_db
from ..matching import find_matches
from ..models import Claim, Item, User
from ..notify import add_notification, broadcast_whatsapp
from ..security import current_user

router = APIRouter(prefix="/api/items", tags=["items"])
CATEGORIES = {"Electronics", "Books", "ID & Cards", "Keys", "Clothing", "Bags", "Other"}


def item_out(i: Item) -> dict:
    return {
        "id": i.id, "type": i.type, "title": i.title, "description": i.description,
        "category": i.category, "location": i.location, "exact_location": i.exact_location,
        "occurred_at": i.occurred_at.isoformat(timespec="minutes"),
        "image_url": f"/uploads/{i.image_path}" if i.image_path else None,
        "question": i.verification_question, "status": i.status,
        "owner_id": i.owner_id, "owner_name": f"{i.owner.name} ({i.owner.branch})",
    }


def whatsapp_text(i: Item) -> str:
    when = i.occurred_at.strftime("%d %b %Y, %I:%M %p")
    return (f"🔔 BVC Lost & Found\n{i.type.upper()}: {i.title}\n"
            f"Where: {i.location} – {i.exact_location}\nWhen: {when}\n"
            f"Reported by {i.owner.name} ({i.owner.branch}).\n"
            "Login to the BVC Lost & Found site to view or claim.")


def save_photo(photo: UploadFile) -> str:
    if not (photo.content_type or "").startswith("image/"):
        raise HTTPException(400, "Photo must be an image.")
    data = photo.file.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(400, "Photo is larger than 5 MB.")
    ext = Path(photo.filename or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / name).write_bytes(data)
    return name


@router.get("")
def list_items(q: str = "", type: str = "", category: str = "", mine: bool = False,
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = db.query(Item).options(joinedload(Item.owner))
    if mine:
        query = query.filter(Item.owner_id == user.id)
    if type in ("lost", "found"):
        query = query.filter(Item.type == type)
    if category:
        query = query.filter(Item.category == category)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(Item.title.ilike(like) | Item.description.ilike(like)
                             | Item.location.ilike(like) | Item.exact_location.ilike(like))
    return [item_out(i) for i in query.order_by(Item.created_at.desc(), Item.id.desc()).limit(200)]


@router.post("")
def create_item(
    background: BackgroundTasks,
    type: str = Form(...), title: str = Form(...), description: str = Form(""),
    category: str = Form(...), location: str = Form(...), exact_location: str = Form(...),
    occurred_at: str = Form(...), verification_question: str = Form(""),
    photo: UploadFile | None = File(None),
    user: User = Depends(current_user), db: Session = Depends(get_db),
):
    if type not in ("lost", "found"):
        raise HTTPException(400, "Type must be lost or found.")
    if category not in CATEGORIES:
        raise HTTPException(400, "Unknown category.")
    if not title.strip() or not exact_location.strip():
        raise HTTPException(400, "Object name and exact location are required.")
    try:
        when = datetime.fromisoformat(occurred_at)
    except ValueError:
        raise HTTPException(400, "Invalid date/time.")
    item = Item(owner_id=user.id, type=type, title=title.strip(), description=description.strip(),
                category=category, location=location, exact_location=exact_location.strip(),
                occurred_at=when, verification_question=verification_question.strip(),
                image_path=save_photo(photo) if photo and photo.filename else None)
    db.add(item)
    db.commit()
    db.refresh(item)

    # 1) in-app alert + WhatsApp message for every other registered student
    text = whatsapp_text(item)
    others = db.query(User).filter(User.id != user.id).all()
    for u in others:
        add_notification(db, u.id,
                         f"New {type} report: \"{item.title}\" at {item.location} "
                         f"({item.exact_location}) on {when:%d %b, %I:%M %p}.", item.id)
    background.add_task(broadcast_whatsapp, [u.phone for u in others], text)

    # 2) smart match: tell the owner of the matching lost report
    for other, pct in find_matches(db, item):
        lost = item if item.type == "lost" else other
        found = other if item.type == "lost" else item
        add_notification(db, lost.owner_id,
                         f"Possible match ({pct}%) for your lost \"{lost.title}\": "
                         f"found \"{found.title}\" at {found.location}.", found.id)
    db.commit()
    return {"item": item_out(item), "notified": len(others), "whatsapp_text": text}


@router.get("/{item_id}")
def get_item(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Report not found.")
    mine = db.query(Claim).filter(Claim.item_id == item_id, Claim.claimant_id == user.id).first()
    out = item_out(item)
    out["my_claim"] = mine.status if mine else None
    out["matches"] = [{**item_out(o), "score": s} for o, s in find_matches(db, item)]
    return out


@router.delete("/{item_id}")
def delete_item(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Report not found.")
    if item.owner_id != user.id and not user.is_admin:
        raise HTTPException(403, "You can only delete your own reports.")
    db.delete(item)
    db.commit()
    return {"ok": True}
