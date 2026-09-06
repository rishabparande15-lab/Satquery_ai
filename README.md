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
- Value: Your public backend HTTPS URL (or leave blank to use the Simulated Mode until the backend is hosted).

