# Architecture

## Request flow
1. Frontend requests inventory and sales data from FastAPI.
2. Backend validates inputs and retrieves relevant data.
3. Forecasting estimates demand over a selected horizon.
4. Risk analysis compares projected demand with available and incoming stock.
5. Optimization proposes replenishment quantities under explicit constraints.
6. API returns recommendations with metrics, assumptions, and explanations.

## Boundaries
- API: HTTP validation and response serialization.
- Services: business workflows and orchestration.
- ML: feature engineering, training, inference, evaluation.
- Optimization: constrained procurement decisions.
- Persistence: products, suppliers, sales, inventory snapshots, forecasts, recommendations.

Initial local development can use SQLite. Configure PostgreSQL later through DATABASE_URL.
