from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR, UPLOAD_DIR
from .database import Base, engine
from .routers import admin, auth, claims, items, notifications

UPLOAD_DIR.mkdir(exist_ok=True)
Base.metadata.create_all(engine)

app = FastAPI(title="BVC Campus Lost & Found")
for r in (auth, items, claims, notifications, admin):
    app.include_router(r.router)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="site")  # keep last
