# ML / Decision Intelligence

Integrated baseline services:
- Forecast: scikit-learn LinearRegression over chronological index blended with recent moving average.
- Inventory risk: transparent stock-cover heuristic, not a trained classifier.
- Replenishment: lead-time demand + safety buffer.

No historical business dataset is bundled, so these models are not trained and validated for a real company. Production steps: ingest SKU/date sales; chronological holdout; compare naive, seasonal-naive, ETS and ML; evaluate MAE/RMSE/WAPE/MASE and bias; add prediction intervals; validate recommendation constraints.
