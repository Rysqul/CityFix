"""CityFix educational API. All statuses are simulated, not municipal updates."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("CITYFIX_DB", ROOT / "cityfix.sqlite3"))
UPLOADS = Path(os.environ.get("CITYFIX_UPLOADS", ROOT / "uploads"))
UPLOADS.mkdir(parents=True, exist_ok=True)
CATEGORIES = {"Road", "Lighting", "Waste", "Sidewalk", "Other"}
STATUSES = {"New", "In Progress", "Resolved"}
MAX_IMAGE = 5 * 1024 * 1024


from contextlib import asynccontextmanager, contextmanager  

@contextmanager
def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'New',
            image_url TEXT,
            created_at TEXT NOT NULL
        )""")
        if c.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 0:
            c.executemany("""INSERT INTO issues
              (title,description,category,latitude,longitude,status,image_url,created_at)
              VALUES (?,?,?,?,?,?,?,?)""", [
                ("Broken streetlight", "A streetlight has stopped working near the crossing.", "Lighting", 43.2382, 76.9451, "New", None, datetime.now(timezone.utc).isoformat()),
                ("Pothole on road", "Uneven road surface near the junction.", "Road", 43.2510, 76.9280, "In Progress", None, datetime.now(timezone.utc).isoformat()),
                ("Overflowing bin", "Waste collection is needed here.", "Waste", 43.2450, 76.9560, "Resolved", None, datetime.now(timezone.utc).isoformat()),
            ])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CityFix API", version="0.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST", "PATCH"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")


class StatusUpdate(BaseModel):
    status: str


def as_issue(row):
    return dict(row)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/issues")
def list_issues():
    with connect() as c:
        return [as_issue(r) for r in c.execute("SELECT * FROM issues ORDER BY id DESC")]


@app.post("/api/issues", status_code=201)
async def create_issue(
    title: str = Form(..., min_length=3, max_length=100),
    description: str = Form(..., min_length=5, max_length=2000),
    category: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile | None = File(None),
):
    if category not in CATEGORIES:
        raise HTTPException(400, "Invalid category")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise HTTPException(400, "Invalid coordinates")
    image_url = None
    if image and image.filename:
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(image.content_type)
        if not ext:
            raise HTTPException(400, "Only JPEG, PNG or WebP images are allowed")
        data = await image.read(MAX_IMAGE + 1)
        if len(data) > MAX_IMAGE:
            raise HTTPException(413, "Maximum image size is 5 MB")
        # Check file signatures; content type supplied by browser is not sufficient.
        fmt = ("jpeg" if data.startswith(bytes.fromhex("ffd8ff")) else "png" if data.startswith(bytes.fromhex("89504e470d0a1a0a")) else "webp" if len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP" else None)
        if fmt not in ("jpeg", "png", "webp") or (fmt == "jpeg" and ext != ".jpg") or (fmt == "png" and ext != ".png") or (fmt == "webp" and ext != ".webp"):
            raise HTTPException(400, "Invalid image file")
        fname = f"{uuid.uuid4().hex}{ext}"
        (UPLOADS / fname).write_bytes(data)
        image_url = f"/uploads/{fname}"
    with connect() as c:
        cur = c.execute("""INSERT INTO issues(title,description,category,latitude,longitude,status,image_url,created_at)
              VALUES(?,?,?,?,?,?,?,?)""", (title.strip(), description.strip(), category, latitude, longitude, "New", image_url, datetime.now(timezone.utc).isoformat()))
        return as_issue(c.execute("SELECT * FROM issues WHERE id=?", (cur.lastrowid,)).fetchone())


@app.patch("/api/issues/{issue_id}/status")
def update_status(issue_id: int, payload: StatusUpdate):
    # Classroom demo only. Do NOT expose this unauthenticated endpoint on the public internet.
    if payload.status not in STATUSES:
        raise HTTPException(400, "Invalid status")
    with connect() as c:
        cur = c.execute("UPDATE issues SET status=? WHERE id=?", (payload.status, issue_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Issue not found")
        return as_issue(c.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone())
