from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_name:str="Inventory Intelligence API"
 environment:str="development"
 api_v1_prefix:str="/api/v1"
 database_url:str="sqlite:///./inventory_intelligence.db"
 secret_key:str="replace-this-development-secret-before-deployment"
 cors_origins:list[str]=["http://localhost:5173","http://127.0.0.1:5173"]
 model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
