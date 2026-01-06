
# Streetlight Optimization — Quick Start

This repository contains a FastAPI backend and a Vite + React frontend. Follow the steps below to run both services locally.

**Prerequisites:**
- Python 3.11.*
- Node.js 16+ and `npm`

**Backend (FastAPI)**

1. Open a terminal and change to the backend folder:

```bash
cd backend
```

2. Create and activate a virtual environment:

Windows (cmd):

```bash
python -m venv .venv
.venv\Scripts\activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Start the backend (runs FastAPI via Uvicorn):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend health endpoint is available at `http://127.0.0.1:8000/` and the API is mounted under `/api` (for example `http://127.0.0.1:8000/api/...`).

**Frontend (Vite + React)**

1. Open a new terminal and change to the frontend folder:

```bash
cd frontend
```

2. Install Node dependencies:

```bash
npm install
```

3. Start the frontend dev server:

```bash
npm run dev
```

Vite's dev server runs on `http://localhost:5173` by default. The frontend is configured to communicate with the backend at `http://127.0.0.1:8000`.

**Frontend environment file**

Create a `.env` file inside the `frontend` folder and add your Mapbox token

```dotenv
# Replace with your own Mapbox token
VITE_MAPBOX_TOKEN=your_mapbox_token_here
# API URL points to the backend started above
VITE_API_URL=http://127.0.0.1:8000
```

**Notes & Troubleshooting**
- If ports 8000 or 5173 are in use, stop the conflicting process or change the port in the run commands.
- Ensure the virtual environment is activated before installing or running the backend.

