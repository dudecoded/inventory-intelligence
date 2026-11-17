# Inventory Intelligence

AI-powered inventory planning and decision-support platform combining demand forecasting, stock-risk analysis, and constrained replenishment recommendations.

## Planned capabilities
- Product-level demand forecasting over configurable horizons.
- Stockout, overstock, and slow-moving inventory signals.
- Replenishment recommendations under budget, lead-time, and supplier constraints.
- Dashboard for inventory KPIs, forecasts, alerts, and recommendations.

## Architecture
React + TypeScript → FastAPI → application services → ML forecasting / risk scoring / optimization → database.

## Repository layout
- `frontend/` — React client
- `backend/` — FastAPI application and API contracts
- `ml/` — preprocessing, forecasting, risk modelling, evaluation
- `optimization/` — procurement optimization
- `data/` — local datasets (not committed)
- `notebooks/` — exploratory analysis
- `docs/` — architecture and data contracts

## Backend quick start
Requires Python 3.11+.
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Frontend
Requires Node.js 20+. See `frontend/README.md`.

## Configuration
Copy `backend/.env.example` to `backend/.env`. Never commit credentials, API keys, database passwords, or real customer data. SQLite is the initial local-development default; PostgreSQL can be configured through `DATABASE_URL`.

## Data and model integrity
Use chronological train/validation/test splits for time-series evaluation. Do not present synthetic/demo results as real-world model performance. Recommendations must expose assumptions and constraints.

## Status
Foundation scaffold. Features and models will be implemented incrementally and validated with tests.
