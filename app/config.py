import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'lostfound.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "72"))
ADMIN_ROLLS = {r.strip().upper() for r in os.getenv("ADMIN_ROLLS", "").split(",") if r.strip()}

TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MATCH_THRESHOLD = 60
