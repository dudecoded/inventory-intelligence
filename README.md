# Stockwise — Inventory Intelligence

Inventory decision-support platform for small businesses and operations teams. The hackathon demo combines product catalogue management, stock risk heuristics, replenishment suggestions, and a transparent forecasting lab.

## What works today
- Email/password registration and login; passwords are stored using scrypt, not plaintext.
- Signed bearer tokens with expiry.
- User-scoped inventory CRUD, stock adjustments, and archive.
- SKU normalization and duplicate checks within a workspace.
- Inventory valuation from on-hand quantity × unit cost.
- Stock coverage / reorder recommendations with explicit assumptions.
- Forecast lab that compares naive, moving-average, and linear-trend baselines using a chronological holdout.
- CSV import/export with validation and formula-injection protection. Sample import template: `docs/inventory-import-template.csv`.
- Backend API integration tests and frontend production build in CI.

## Important limitations
This is a hackathon prototype, not a production inventory system. Demo inventory is illustrative and may be seeded into a new workspace. The chart on the Overview page is sample visualization and is not connected to sales history. The forecast lab accepts manually entered observations; it is not trained on a real business dataset. Stock risk and reorder quantities are transparent heuristics, not optimized or probabilistic decisions. Supplier, integrations, and some analytics screens remain UI placeholders.

## Stack
- Frontend: React, TypeScript, Vite, CSS
- Backend: FastAPI, SQLAlchemy, SQLite by default
- ML: NumPy and scikit-learn baselines

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

## Environment configuration
Backend variables are in `backend/.env.example`. Before deploying, set a strong random `SECRET_KEY`, production environment, and explicit CORS origins. The app rejects the development secret in production mode.

Frontend `VITE_API_URL` defaults to `http://localhost:8000/api/v1`.

## Roadmap to production-grade inventory intelligence
1. Import transaction-level sales with timestamps and stockout flags.
2. Build demand forecasting with time-series cross-validation, intermittent-demand methods, seasonality and prediction interval calibration.
3. Replace simple inventory coverage rules with service-level-aware safety stock.
4. Add supplier, purchase-order, MOQ, budget, and lead-time data.
5. Implement constrained replenishment optimization and simulate against historical demand.
6. Add data migrations, rate limiting, refresh/revocable sessions, audit logs, roles, and deployment observability.
7. Validate with real users and measure stockout reduction, waste reduction, and cash tied in inventory.

## Tests
Backend:
```powershell
cd backend
pytest -q
```
Frontend production build:
```powershell
cd frontend
npm run build
```
CI runs both checks on pushes and pull requests.
