import numpy as np
from sklearn.linear_model import LinearRegression
def forecast_series(history:list[float],horizon:int=7)->dict:
 values=np.asarray(history,dtype=float)
 if len(values)<3 or not np.all(np.isfinite(values)) or np.any(values<0):raise ValueError("Provide at least 3 non-negative historical observations.")
 x=np.arange(len(values)).reshape(-1,1);model=LinearRegression().fit(x,values)
 future=np.arange(len(values),len(values)+horizon).reshape(-1,1)
 trend=np.maximum(model.predict(future),0);recent=float(np.mean(values[-min(7,len(values)):]))
 result=np.maximum(.65*trend+.35*recent,0);fitted=np.maximum(model.predict(x),0)
 return {"method":"Linear trend + recent moving-average blend","forecast":[round(float(v),2) for v in result],"mae":round(float(np.mean(np.abs(values-fitted))),2),"note":"Baseline only. Validate on chronological holdout data before production decisions."}
def classify_stock(stock:int,demand_30d:float,lead_time_days:int=7)->dict:
 daily=max(demand_30d/30,0.001);cover=stock/daily
 if cover<lead_time_days:label,risk="Stockout risk","high"
 elif cover<lead_time_days*1.5:label,risk="Reorder soon","medium"
 elif cover>180:label,risk="Slow-moving / excess","medium"
 else:label,risk="Healthy","low"
 return {"label":label,"risk":risk,"days_of_cover":round(cover,1),"estimated_daily_demand":round(daily,2),"model":"Inventory coverage heuristic","note":"Transparent rule, not a trained classifier."}
def recommend_reorder(stock:int,demand_30d:float,lead_time_days:int=7,buffer_days:int=14)->dict:
 daily=max(demand_30d/30,0);target=daily*(lead_time_days+buffer_days);qty=max(0,round(target-stock))
 return {"recommended_quantity":qty,"target_stock":round(target),"lead_time_days":lead_time_days,"buffer_days":buffer_days,"method":"Lead-time demand + safety buffer"}
