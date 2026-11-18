# Inventory Intelligence

Inventory decision-support application combining product management, demand forecasting baselines, inventory risk analysis, and replenishment planning.

## Current implementation
- React dashboard with dark neon-inspired UI, responsive layout, login/register, account profile.
- FastAPI API with password hashing, signed bearer tokens, profile update, user-scoped product CRUD/stock adjustment.
- SQLite persistence by default.
- ML baseline forecast endpoint: scikit-learn linear trend blended with recent moving average.
- Inventory risk: transparent stock coverage heuristic.
- Procurement recommendation: lead-time demand + safety buffer.
- CSV export, search, stock status filtering, quick adjustments, forecast lab.

**Model caveat:** There is no real historical dataset or trained production model in this repository. Forecast/risk/replenishment components are baseline decision-support logic. Demo workspace sample products are illustrative.

## Run locally

### Backend (PowerShell)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

### Frontend
```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```
Open the Vite URL printed by the command.

## Environment
Backend `SECRET_KEY` must be changed to a long random secret before deployment. Frontend `VITE_API_URL` defaults to `http://localhost:8000/api/v1`.

## Evaluation roadmap
Use dated SKU sales and stockout-aware observations; validate forecasts with chronological splits; compare baseline models; report MAE/RMSE/WAPE/MASE and bias; add calibrated prediction intervals; test replenishment against budget, lead-time, MOQ and supplier constraints.
