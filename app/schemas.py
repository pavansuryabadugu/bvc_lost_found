from typing import Literal

from pydantic import BaseModel, Field

EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    roll: str = Field(min_length=3, max_length=30)
    branch: str = Field(min_length=1, max_length=30)
    phone: str = Field(pattern=r"^\d{10}$")
    email: str = Field(pattern=EMAIL_RE, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    identifier: str  # roll number or email
    password: str


class ClaimIn(BaseModel):
    answer: str = Field(min_length=1, max_length=1000)


class ClaimStatusIn(BaseModel):
    status: Literal["approved", "rejected"]
