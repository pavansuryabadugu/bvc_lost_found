from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Claim, Item, User
from ..notify import add_notification, send_whatsapp
from ..schemas import ClaimIn, ClaimStatusIn
from ..security import current_user

router = APIRouter(prefix="/api", tags=["claims"])


def claim_out(c: Claim) -> dict:
    return {"id": c.id, "item_id": c.item_id, "item_title": c.item.title,
            "claimant_name": f"{c.claimant.name} ({c.claimant.roll})", "answer": c.answer,
            "status": c.status}


def _claims(db: Session):
    return db.query(Claim).options(joinedload(Claim.item), joinedload(Claim.claimant))


@router.post("/items/{item_id}/claims")
def create_claim(item_id: int, data: ClaimIn, background: BackgroundTasks,
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item or item.status != "open":
        raise HTTPException(404, "This report is not open.")
    if item.owner_id == user.id:
        raise HTTPException(400, "You cannot claim your own report.")
    if db.query(Claim).filter(Claim.item_id == item_id, Claim.claimant_id == user.id).first():
        raise HTTPException(400, "You already sent a claim.")
    claim = Claim(item_id=item_id, claimant_id=user.id, answer=data.answer.strip())
    db.add(claim)
    msg = (f"{user.name} ({user.roll}) sent a claim on \"{item.title}\". "
           "Open My activity to approve or reject.")
    add_notification(db, item.owner_id, msg, item.id)
    add_notification(db, user.id, f"Your claim on \"{item.title}\" was sent to {item.owner.name}.", item.id)
    db.commit()
    background.add_task(send_whatsapp, item.owner.phone, f"🔔 BVC Lost & Found\n{msg}")
    return {"ok": True}


@router.get("/claims/mine")
def my_claims(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [claim_out(c) for c in _claims(db).filter(Claim.claimant_id == user.id).order_by(Claim.id.desc())]


@router.get("/claims/received")
def received_claims(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = _claims(db).join(Item).filter(Item.owner_id == user.id).order_by(Claim.id.desc())
    return [claim_out(c) for c in q]


@router.patch("/claims/{claim_id}")
def decide_claim(claim_id: int, data: ClaimStatusIn, background: BackgroundTasks,
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if not claim or claim.item.owner_id != user.id:
        raise HTTPException(404, "Claim not found.")
    if claim.status != "pending":
        raise HTTPException(400, "This claim was already decided.")
    claim.status = data.status
    msg = f"Your claim on \"{claim.item.title}\" was {data.status}."
    if data.status == "approved":
        claim.item.status = "returned"
        msg += f" Contact {user.name} on {user.phone} to collect it."
    add_notification(db, claim.claimant_id, msg, claim.item_id)
    db.commit()
    background.add_task(send_whatsapp, claim.claimant.phone, f"🔔 BVC Lost & Found\n{msg}")
    return {"ok": True}
