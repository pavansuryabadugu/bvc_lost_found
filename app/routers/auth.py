from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import ADMIN_ROLLS
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn
from ..security import create_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_out(u: User) -> dict:
    return {"id": u.id, "name": u.name, "roll": u.roll, "branch": u.branch,
            "phone": u.phone, "email": u.email, "is_admin": u.is_admin}


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    roll, email = data.roll.strip().upper(), data.email.strip().lower()
    if db.query(User).filter((User.roll == roll) | (User.email == email)).first():
        raise HTTPException(400, "This roll number or email is already registered.")
    user = User(name=data.name.strip(), roll=roll, branch=data.branch, phone=data.phone,
                email=email, password_hash=hash_password(data.password),
                is_admin=roll in ADMIN_ROLLS)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": user_out(user)}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    ident = data.identifier.strip()
    user = db.query(User).filter((User.roll == ident.upper()) | (User.email == ident.lower())).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Wrong roll number/email or password.")
    return {"token": create_token(user.id), "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)
