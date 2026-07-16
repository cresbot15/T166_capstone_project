# TeamUp

Repository for group T166's IFB398 + IFB399 IT capstone project

# Prerequisites

| Tool | Version |
|---|---|
| Python | 3.13 |
| Node.js | 20+ |
| UV (recommended) | latest |

# Running locally

Both services must be running at the same time.
API requires environment variable JWT_SECRET to be set.

### Backend (FastAPI)

```bash
cd backend
uv sync
uv run fastapi dev src/main.py
```

API runs at **http://localhost:8000**

Interactive docs available at http://localhost:8000/docs once the API is running

### Frontend (SvelteKit)

```bash
cd frontend
npm install
npm run dev
```

App runs at **http://localhost:5173**
