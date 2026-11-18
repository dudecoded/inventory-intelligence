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
