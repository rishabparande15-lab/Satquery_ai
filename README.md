# SatQuery AI

SatQuery AI is an interactive remote sensing vision-language assistant and Earth observation analysis platform. It pairs natural language and structured geospatial queries with live Sentinel-2 Cloud-Optimized GeoTIFF (COG) streaming via Rasterio to compute real surface vegetation indices (NDVI) with scientific integrity.

---

## 🚀 Quickstart & Local Development

### 1. Run the FastAPI Backend

From the repository root:

```bash
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run the FastAPI server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend health endpoint will be available at:
`http://localhost:8000/api/health`

To run backend tests:
```bash
python -m pytest -v backend/tests
```

---

### 2. Run the Frontend

In a separate terminal, navigate to the `frontend/` directory (or use workspace scripts from root):

```bash
# From workspace root
npm run dev

# Or directly from frontend/
cd frontend
npm install
npm run dev
```

The frontend will start at:
`http://localhost:5173`

---

## ⚙️ Environment Variables

### Frontend (`frontend/.env` or Netlify / Cloud Environment Variables)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Target URL for the FastAPI backend API |
| `VITE_API_BASE_URL` | *(optional fallback)* | Alternative prefix for API base URL |

For local paired development:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> [!IMPORTANT]
> **Why `http://localhost:8000` will NOT work on a publicly deployed frontend**:
> In a web browser accessing a public deployment (e.g. `https://satquery-ai.netlify.app`), `localhost` resolves to the visitor's own computer, not your server. For live public operation, deploy the FastAPI backend to a cloud host (Render, Railway, Fly.io, or AWS) and configure `NEXT_PUBLIC_API_BASE_URL` with that public HTTPS URL.

---

## 🌐 Deploying to Netlify (Free Tier)

The repository is configured for zero-configuration Netlify deployment with full SPA routing (`_redirects` and `netlify.toml`):

### Option A: If repository root is used
- **Build command**: `npm run build`
- **Publish directory**: `frontend/dist`

### Option B: If `frontend` is used as base directory
- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `dist`

### Environment Variables on Netlify:
- Go to **Site Configuration** > **Environment Variables**
- Key: `NEXT_PUBLIC_API_BASE_URL`
- Value: Your public backend HTTPS URL (e.g. `https://satquery-backend.onrender.com`).

---

## 🛰️ Deploying the FastAPI Backend (Free / Low Cost)

The backend has been configured with production manifests (`render.yaml`, `Procfile`, `Dockerfile`, and `requirements.txt`).

- **Production Entry Point**: `backend.app.main:app`
- **Production Server Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Endpoint**: `/api/health`

### Option 1: Render (Free Web Service — Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New** > **Web Service**.
2. Connect your GitHub repository: `https://github.com/rishabparande15-lab/Satquery_ai`.
3. Configure the service:
   - **Name**: `satquery-backend`
   - **Region**: Oregon (or nearest)
   - **Language**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. Set Environment Variables in Render:
   - `PYTHON_VERSION`: `3.11.9`
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGIN_REGEX`: `^https://.*\.netlify\.app$`
5. Click **Deploy Web Service**. Once deployed, copy your Render HTTPS URL (e.g. `https://satquery-backend.onrender.com`) and paste it into Netlify's `NEXT_PUBLIC_API_BASE_URL`.

### Option 2: Railway
1. Go to [Railway Dashboard](https://railway.app/) > **New Project** > **Deploy from GitHub repo**.
2. Select `rishabparande15-lab/Satquery_ai`.
3. Railway automatically detects the included `Dockerfile` and `Procfile`.
4. Generate a public domain under **Settings** > **Networking** > **Public Domain**.

### Option 3: Fly.io
```bash
fly launch
fly deploy
```
*(Uses the included `fly.toml` and `Dockerfile`)*


