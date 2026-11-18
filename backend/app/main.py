from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import api_router
from app.core.config import settings
from app.core.database import Base,engine
from app import models
Base.metadata.create_all(bind=engine)
app=FastAPI(title=settings.app_name,version="0.2.0",description="Inventory, forecasting, risk and replenishment API.")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(api_router,prefix=settings.api_v1_prefix)
@app.get("/",tags=["health"])
def root():return {"message":"Inventory Intelligence API","docs":"/docs"}
@app.get("/health",tags=["health"])
def health():return {"status":"ok","environment":settings.environment}
