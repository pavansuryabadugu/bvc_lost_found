import re

from sqlalchemy.orm import Session

from .config import MATCH_THRESHOLD
from .models import Item


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", text.lower()))


def score(a: Item, b: Item) -> int:
    """Same category +40, same block +30, within 3 days +15, shared keyword +15."""
    s = 0
    if a.category == b.category:
        s += 40
    if a.location == b.location:
        s += 30
    if abs((a.occurred_at - b.occurred_at).total_seconds()) <= 3 * 86400:
        s += 15
    if _words(f"{a.title} {a.description}") & _words(f"{b.title} {b.description}"):
        s += 15
    return s


def find_matches(db: Session, item: Item) -> list[tuple[Item, int]]:
    other = "found" if item.type == "lost" else "lost"
    rows = db.query(Item).filter(Item.type == other, Item.status == "open").all()
    scored = [(o, score(item, o)) for o in rows]
    return sorted([(o, s) for o, s in scored if s >= MATCH_THRESHOLD], key=lambda x: -x[1])
