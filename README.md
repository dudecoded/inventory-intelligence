# Stockwise — Inventory Intelligence

Inventory decision-support platform for small businesses and operations teams. The hackathon demo combines product catalogue management, stock risk heuristics, replenishment suggestions, and a transparent forecasting lab.

## What works today
- Email/password registration and login; passwords are stored using scrypt, not plaintext.
- Signed bearer tokens with expiry.
- User-scoped inventory CRUD, guarded stock adjustments, stock-movement audit history, and archive.\n- Recorded sales ledger: sales decrement stock, reject overselling, update rolling 30-day demand, and drive live sales analytics.
- SKU normalization and duplicate checks within a workspace.
- Inventory valuation from on-hand quantity × unit cost.
- Supplier directory with contact and lead-time details.\n- Persistent supplier-linked purchase orders with draft/sent/received/cancelled states; receiving an order updates inventory exactly once and records the receipt.\n- SKU-level daily sales history and forecasts using recorded sales, plus a live daily sales trend.
- Forecast lab that compares naive, moving-average, and linear-trend baselines using a chronological holdout.
- CSV import/export with validation and formula-injection protection. Sample import template: `docs/inventory-import-template.csv`.
- Backend API integration tests and frontend production build in CI.

## Important limitations
This is a hackathon prototype, not a production inventory system. Demo inventory is illustrative and may be seeded into a new workspace. The Overview sales trend is populated only from recorded transactions. New workspaces may be seeded with illustrative catalogue items, but sales are never fabricated. Forecast baselines are simple and require sufficient recorded demand; they are not deep-learning forecasts. Stock risk and reorder quantities are transparent heuristics, not optimized or probabilistic decisions. External ERP integrations, multi-warehouse operations, supplier performance scoring, returns, taxes, and advanced demand seasonality remain outside the current prototype.

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
CI runs backend tests, the frontend production build, and a production-dependency audit on pushes and pull requests. The dev-tool audit report may still flag the upstream Picomatch advisory; no upstream patched release is available as of this review.
