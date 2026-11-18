# Hackathon demo script (3–4 minutes)

## Opening (20 seconds)
"Most inventory tools tell a business what it has. Stockwise is built to help it decide what to do next: identify risk, estimate demand, and turn a signal into an order."

## 1. Dashboard (30 seconds)
- Point out the live product count, inventory valuation, and low-stock count.
- Explain that valuation is computed from quantity × unit cost—not a hard-coded KPI.
- Be explicit that the demand chart is illustrative until transaction data is connected.

## 2. Inventory (45 seconds)
- Search a SKU using the search bar or Ctrl/Cmd+K.
- Show status filters and quick stock adjustment.
- Edit a product's unit cost and lead time to show that the risk logic responds to operational inputs.
- Import a CSV, then export the inventory.

## 3. Forecast lab (60 seconds)
- Enter chronological observations, oldest first.
- Run the forecast.
- Show the chronological holdout comparison between naive, moving-average and linear-trend baselines.
- Explain MAE/RMSE/WAPE and that the selected baseline is chosen on a holdout—not by in-sample fit.
- State the limitation: the demo series is illustrative and small; real deployment needs dated SKU sales and stockout-aware validation.

## 4. Procurement (45 seconds)
- Show the low-stock recommendations.
- Explain the transparent calculation: average daily demand × (lead time + safety buffer), less stock on hand.
- Adjust order quantities and save a purchase-order draft. Drafts are currently browser-local.

## 5. Analytics (30 seconds)
- Show category inventory valuation and stock-health distribution.
- Explain what the platform deliberately does not claim yet: turnover and historical stockout metrics require transaction history.

## Closing (20 seconds)
"Stockwise makes its recommendations explainable. Our next step is to validate forecasting against real SKU-level sales, then optimize orders under supplier, budget, and service-level constraints."
