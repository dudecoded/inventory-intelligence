import numpy as np
from sklearn.linear_model import LinearRegression


def _predict(method: str, train: np.ndarray, horizon: int) -> np.ndarray:
    if method == "Naive last value":
        return np.repeat(float(train[-1]), horizon)
    if method == "Recent moving average":
        return np.repeat(float(np.mean(train[-min(7, len(train)): ])), horizon)
    x = np.arange(len(train)).reshape(-1, 1)
    future = np.arange(len(train), len(train) + horizon).reshape(-1, 1)
    model = LinearRegression().fit(x, train)
    return np.maximum(model.predict(future), 0)


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    errors = actual - predicted
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    denominator = float(np.sum(np.abs(actual)))
    wape = float(np.sum(np.abs(errors)) / denominator * 100) if denominator else None
    bias = float(np.mean(predicted - actual))
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "wape_percent": round(wape, 2) if wape is not None else None, "bias": round(bias, 3)}


def forecast_series(history: list[float], horizon: int = 7) -> dict:
    values = np.asarray(history, dtype=float)
    if values.ndim != 1 or len(values) < 3:
        raise ValueError("Provide at least 3 historical observations.")
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Historical observations must be finite and non-negative.")
    if not isinstance(horizon, int) or horizon < 1 or horizon > 90:
        raise ValueError("Forecast horizon must be between 1 and 90 days.")

    # Chronological holdout: reserve the most recent observations for model selection.
    holdout_size = max(1, min(7, len(values) // 5))
    train = values[:-holdout_size]
    holdout = values[-holdout_size:]
    if len(train) < 2:
        train = values[:-1]
        holdout = values[-1:]

    candidates = ["Naive last value", "Recent moving average", "Linear trend"]
    evaluation = []
    for method in candidates:
        predictions = _predict(method, train, len(holdout))
        evaluation.append({"model": method, **_metrics(holdout, predictions)})
    selected = min(evaluation, key=lambda item: item["mae"])

    final_forecast = _predict(selected["model"], values, horizon)
    selected_holdout = _predict(selected["model"], train, len(holdout))
    residuals = holdout - selected_holdout
    uncertainty = float(np.sqrt(np.mean(residuals ** 2))) if len(residuals) else 0.0
    lower = np.maximum(final_forecast - 1.96 * uncertainty, 0)
    upper = final_forecast + 1.96 * uncertainty

    return {
        "method": selected["model"],
        "forecast": [round(float(value), 2) for value in final_forecast],
        "lower_bound": [round(float(value), 2) for value in lower],
        "upper_bound": [round(float(value), 2) for value in upper],
        "evaluation": evaluation,
        "validation": {"type": "chronological holdout", "observations": int(len(holdout))},
        "metrics": {key: selected[key] for key in ("mae", "rmse", "wape_percent", "bias")},
        "metric_label": "Holdout MAE",
        "note": "Small-sample baseline comparison using a chronological holdout. The uncertainty band is an approximate residual-based interval, not a calibrated prediction interval. Validate on more historical data before business decisions.",
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
