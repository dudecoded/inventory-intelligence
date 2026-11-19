# Architecture

## System
React + TypeScript (Vite) calls a versioned FastAPI API. Backend authentication uses signed bearer tokens and scrypt password hashes. SQLAlchemy persists users and products in SQLite by default. Inventory operations are scoped to the authenticated workspace.

## Current modules
- Authentication: register, login, profile update, signed tokens with expiry.
- Inventory: create/update/archive products, stock adjustments, owner-scoped SKU uniqueness, validation and CSV import/export.
- Dashboard: live catalogue KPIs including inventory value and stock-health counts.
- Analytics: category valuation and stock-health distribution derived from the current catalogue.
- Procurement: lead-time demand plus safety-buffer recommendations; purchase-order drafts are currently stored in browser local storage, not the backend.
- Forecasting: manually entered demand series; chronological holdout comparison of naive-last-value, recent moving-average and linear-trend baselines. Reports holdout MAE, RMSE, WAPE and bias. The selected baseline is refit to the full input series for the requested horizon.

## Decision-support assumptions
- Demand is a user-provided 30-day total converted to an average daily rate.
- Stock risk uses days-of-cover compared with supplier lead time and a slow-moving threshold.
- Reorder target is daily demand × (lead-time days + fixed buffer days).
- Recommendations do not yet account for MOQ, supplier constraints, budget, seasonality, intermittent demand, or forecast uncertainty.
- The forecast's approximate residual interval is not calibrated. A small holdout may make model selection unstable.

## Demo data and limitations
A new workspace on a browser may be seeded with illustrative products once. The Overview demand chart is illustrative and not linked to transactions. Suppliers, external integrations and settings remain placeholders. No operational sales transaction history is stored.

## Quality checks
GitHub Actions runs backend pytest and frontend TypeScript/Vite production build. The backend API integration tests use an isolated in-memory SQLite database.
