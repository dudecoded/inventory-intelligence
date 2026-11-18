# Architecture

React + TypeScript calls the versioned FastAPI API. Backend authentication uses signed bearer tokens and password hashes; SQLAlchemy persists users and products in SQLite by default. Inventory endpoints are user-scoped.

Decision services:
- Demand baseline: scikit-learn linear trend blended with recent mean.
- Stock risk: interpretable days-of-cover rule.
- Replenishment: lead-time demand plus safety buffer.

These are initial baselines. Real model training/evaluation requires historical SKU-level sales data, chronological validation, and explicit metrics. Demo values and in-sample MAE are not operational guarantees.
