from app.services.forecasting import forecast_series,classify_stock,recommend_reorder
def test_forecast_returns_requested_horizon():
 result=forecast_series([10,12,14,16,18],horizon=4)
 assert len(result['forecast'])==4
 assert all(value>=0 for value in result['forecast'])
 assert result['method']
def test_stock_risk_flags_low_cover():
 result=classify_stock(stock=2,demand_30d=60,lead_time_days=7)
 assert result['risk']=='high'
def test_reorder_quantity_nonnegative():
 result=recommend_reorder(stock=2,demand_30d=60,lead_time_days=7,buffer_days=14)
 assert result['recommended_quantity']>=0

def test_forecast_selects_model_using_chronological_holdout():
    result = forecast_series([5, 5, 5, 5, 5, 5, 5, 5], horizon=3)
    assert result["validation"]["type"] == "chronological holdout"
    assert result["metrics"]["mae"] == 0
    assert len(result["evaluation"]) == 3
    assert result["method"] in {item["model"] for item in result["evaluation"]}
    assert len(result["lower_bound"]) == 3
    assert len(result["upper_bound"]) == 3


def test_forecast_rejects_negative_and_non_finite_history():
    import pytest
    with pytest.raises(ValueError):
        forecast_series([1, -1, 2], 3)
    with pytest.raises(ValueError):
        forecast_series([1, float("nan"), 2], 3)


def test_zero_demand_does_not_divide_by_zero():
    result = classify_stock(stock=10, demand_30d=0, lead_time_days=7)
    assert result["days_of_cover"] is None
    assert result["risk"] == "low"


def test_reorder_target_respects_stock_and_lead_time():
    result = recommend_reorder(stock=100, demand_30d=30, lead_time_days=10, buffer_days=14)
    assert result["target_stock"] == 24
    assert result["recommended_quantity"] == 0
