# Frontend

React + TypeScript + Vite application for Inventory Intelligence.

## Run
```bash
npm install
npm run dev
```

Set `VITE_API_URL` in `.env` (default: `http://localhost:8000/api/v1`). The app uses FastAPI for registration/login, account profile, product persistence, stock adjustment, inventory insights, and forecast inference. The UI seeds illustrative sample products for a newly registered workspace; replace them with real data before operational use.

## Model integrations
- Forecast lab: user-entered history → API baseline LinearRegression trend blended with recent moving average.
- Procurement page: API inventory coverage + lead-time/buffer replenishment recommendations.
- Forecast and risk methods are transparent baselines, not trained/validated production models.
