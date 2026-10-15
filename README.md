# BVC Campus Lost & Found

Lost-and-found website for Bonam Venkata Chalamayya Engineering College, Odalarevu.

- Students register (name, roll number, branch, WhatsApp number, email) and log in.
- **Nothing is visible without login.**
- A report records the object, exact location, exact date and time, and an optional photo.
- Every other registered student gets an in-app alert and a WhatsApp message.
- Smart matching between lost and found reports (category, block, date, keywords).
- Claims with a verification question; the poster approves or rejects.
- Admin dashboard and report removal for roll numbers listed in `ADMIN_ROLLS`.

Stack: FastAPI, SQLAlchemy, SQLite (PostgreSQL ready), JWT login, plain HTML/CSS/JS frontend.

## Run in VS Code

1. Open this folder in VS Code (File > Open Folder). Install the **Python** extension.
2. Open a terminal (Ctrl+`) and run:

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
uvicorn app.main:app --reload
```

3. Open http://127.0.0.1:8000 for the website and http://127.0.0.1:8000/docs for the API docs.
   Or press **F5** in VS Code (the launch config is in `.vscode/launch.json`).

To make yourself admin, put your roll number in `ADMIN_ROLLS` in `.env` **before** registering.

## Folder layout

```
app/
  main.py          app setup, serves the website
  config.py        settings from .env
  database.py      database connection
  models.py        users, items, claims, notifications
  schemas.py       request validation
  security.py      password hashing, JWT login
  matching.py      lost/found match scoring
  notify.py        in-app alerts + WhatsApp sending
  routers/         auth, items, claims, notifications, admin
static/            index.html, style.css, app.js, logo.webp
uploads/           uploaded photos
```

## WhatsApp messages

Without Twilio keys, messages are **printed in the terminal** (dry run), so you can test everything.
For real messages, create a Twilio account, fill `TWILIO_SID`, `TWILIO_TOKEN` and
`TWILIO_WHATSAPP_FROM` in `.env`. Things to know:

- With the Twilio sandbox, each student must first send the join code to the sandbox number.
- For a production sender, WhatsApp requires an approved business account and approved
  message templates for messages you start. Plan for this approval step with the college.
- The code assumes Indian numbers (`+91`); change it in `app/notify.py` if needed.

## Before the college uses it

- Set a long random `SECRET_KEY` in `.env`.
- Use PostgreSQL: `pip install psycopg2-binary` and set `DATABASE_URL`.
- Deploy behind HTTPS (for example on Render) and keep photo uploads on a persistent disk
  or move them to cloud storage such as Cloudinary.
- Tables are created automatically on startup; add Alembic migrations if the schema will change.
