# CityFix — Educational City Issue Reporting Web App

A classroom-only civic reporting prototype for a team of 4. Users can see demo issue pins on a map of Almaty, submit new problems (with optional photos), browse/filter reports, view a category dashboard, and change simulated statuses. **This is not connected to municipal agencies and does not submit official complaints.**

## Tech stack

- Frontend: React 18 + Vite 5 + React Leaflet + CSS
- Backend: FastAPI + Python + SQLite
- Maps: OpenStreetMap tile service (requires internet to load map tiles; reports and database can work offline)
- Photo storage: `backend/uploads/` local directory (up to 5 MB)

## Requirements

- Python 3.10–3.13
- Node.js 20+ and npm

## Run locally

Open two terminals in the project directory.

**Terminal 1 — API**

On macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

On Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — React UI**

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. API docs are at **http://localhost:8000/docs**.

The SQLite database is auto-created and seeded with 3 sample issues on first run.

## Demo flow

1. Open Map and inspect pins with different statuses.
2. Click **Report an issue**. Enter title, description, category, click on the location picker map and optionally choose a photo.
3. Click **Submit report**. See it on the map.
4. Go to **All reports**, filter by category and open the report.
5. Set status to **In Progress**, then **Resolved**.
6. Visit **Dashboard** to see category counts.

## API

- `GET /api/health`
- `GET /api/issues`
- `POST /api/issues` (multipart form)
- `PATCH /api/issues/{id}/status` (JSON `{ "status": "Resolved" }`)

## Team division

1. Frontend: page components and responsive UI.
2. Backend: API and validation.
3. Database + maps: SQLite integration and map behavior.
4. Dashboard + testing: charts/stats, QA, demo script.

## Important limitations

- This is **MVP v0.1**, not the complete final specification. There is no registration, role-based access control, voting, or production-grade moderation yet.
- Anyone who can access the local API can change status. **Never expose the backend publicly** without authentication, authorization, stricter upload controls and security review.
- Map tiles are loaded from OSM online by default. For a truly offline presentation, set up an appropriately licensed offline map tile source or use screenshots as a fallback; do not bulk-download OSM public tiles.
- `backend/cityfix.sqlite3` and `backend/uploads/` contain local demo data and are intentionally excluded from Git.
- Only use invented demonstration reports or obtain consent for real-world images/locations.

## Tests

From `backend`, with virtual environment active:

```bash
pytest -q
```
