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

### Frontend (`frontend/.env` or Vercel Environment Variables)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Target URL for the FastAPI backend API |
| `VITE_API_BASE_URL` | *(optional fallback)* | Alternative prefix for API base URL |

For local development:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For production on Vercel:
Set `NEXT_PUBLIC_API_BASE_URL` in the Vercel Project Settings to your deployed backend URL (e.g. `https://your-backend-api.onrender.com` or custom domain).

---

## 🌐 Deploying to Vercel

The repository is preconfigured for zero-friction Vercel deployment:

1. **Connect GitHub Repository**: Import `https://github.com/rishabparande15-lab/Satquery_ai` into Vercel.
2. **Build Settings**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (or leave as root; root `vercel.json` and `package.json` proxy the build)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. **Environment Variables**:
   - Add `NEXT_PUBLIC_API_BASE_URL` pointing to your production backend.
