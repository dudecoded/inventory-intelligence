import numpy as np
from sklearn.linear_model import LinearRegression


def forecast_series(history: list[float], horizon: int = 7) -> dict:
    values = np.asarray(history, dtype=float)
    if values.ndim != 1 or len(values) < 3:
        raise ValueError("Provide at least 3 historical observations.")
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Historical observations must be finite and non-negative.")
    if not isinstance(horizon, int) or horizon < 1 or horizon > 90:
        raise ValueError("Forecast horizon must be between 1 and 90 days.")

    x = np.arange(len(values)).reshape(-1, 1)
    model = LinearRegression().fit(x, values)
    future = np.arange(len(values), len(values) + horizon).reshape(-1, 1)
    trend = np.maximum(model.predict(future), 0)
    recent_window = min(7, len(values))
    recent_mean = float(np.mean(values[-recent_window:]))
    forecast = np.maximum(0.65 * trend + 0.35 * recent_mean, 0)

    fitted = model.predict(x)
    mae = float(np.mean(np.abs(values - fitted)))
    return {
        "method": "Linear trend + recent moving-average blend",
        "forecast": [round(float(value), 2) for value in forecast],
        "mae": round(mae, 2),
        "metric_label": "In-sample trend MAE",
        "note": "Baseline only. This MAE is measured on training observations, not a holdout set. Validate with chronological holdout data before making purchasing decisions.",
    }


def classify_stock(stock: int, demand_30d: float, lead_time_days: int = 7) -> dict:
    daily_demand = max(demand_30d / 30, 0)
    if daily_demand == 0:
        days_cover = float("inf") if stock > 0 else 0
        label, risk = ("No recent demand", "low") if stock > 0 else ("No stock / no demand", "low")
    else:
        days_cover = stock / daily_demand
        if days_cover < lead_time_days:
            label, risk = "Stockout risk", "high"
        elif days_cover < lead_time_days * 1.5:
            label, risk = "Reorder soon", "medium"
        elif days_cover > 180:
            label, risk = "Slow-moving / excess", "medium"
        else:
            label, risk = "Healthy", "low"
    return {
        "label": label,
        "risk": risk,
        "days_of_cover": round(days_cover, 1) if np.isfinite(days_cover) else None,
        "estimated_daily_demand": round(daily_demand, 2),
        "model": "Inventory coverage heuristic",
        "note": "Transparent rule-based indicator; not a trained classifier.",
    }


def recommend_reorder(stock: int, demand_30d: float, lead_time_days: int = 7, buffer_days: int = 14) -> dict:
    daily_demand = max(demand_30d / 30, 0)
    target_stock = daily_demand * (lead_time_days + buffer_days)
    recommended_quantity = max(0, int(np.ceil(target_stock - stock)))
    return {
        "recommended_quantity": recommended_quantity,
        "target_stock": round(target_stock, 2),
        "lead_time_days": lead_time_days,
        "buffer_days": buffer_days,
        "method": "Lead-time demand + safety buffer heuristic",
        "note": "Does not account for MOQ, supplier constraints, budget, seasonality, or uncertainty.",
    }
