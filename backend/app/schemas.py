from pydantic import BaseModel,ConfigDict,EmailStr,Field
from typing import Optional
class RegisterRequest(BaseModel):
 name:str=Field(min_length=2,max_length=120)
 email:EmailStr
 password:str=Field(min_length=8,max_length=128)
 company:str=Field(default="My Workspace",max_length=160)
class LoginRequest(BaseModel):
 email:EmailStr
 password:str
class UserOut(BaseModel):
 id:int;name:str;email:EmailStr;company:str;role:str
 model_config=ConfigDict(from_attributes=True)
class TokenOut(BaseModel):
 access_token:str;token_type:str="bearer";user:UserOut
class UserUpdate(BaseModel):
 name:Optional[str]=Field(default=None,min_length=2,max_length=120)
 company:Optional[str]=Field(default=None,max_length=160)
class ProductCreate(BaseModel):
 sku:str=Field(min_length=1,max_length=80)
 name:str=Field(min_length=1,max_length=200)
 category:str="Uncategorized"
 stock:int=Field(default=0,ge=0)
 demand_30d:float=Field(default=0,ge=0)
 unit_cost:float=Field(default=0,ge=0)
 lead_time_days:int=Field(default=7,ge=0)
class ProductUpdate(BaseModel):
 sku:Optional[str]=Field(default=None,min_length=1,max_length=80)
 name:Optional[str]=Field(default=None,min_length=1,max_length=200)
 category:Optional[str]=None
 stock:Optional[int]=Field(default=None,ge=0)
 demand_30d:Optional[float]=Field(default=None,ge=0)
 unit_cost:Optional[float]=Field(default=None,ge=0)
 lead_time_days:Optional[int]=Field(default=None,ge=0)
class ProductOut(ProductCreate):
 id:int
 model_config=ConfigDict(from_attributes=True)
class ProductAdjust(BaseModel):
 delta:int
class ForecastRequest(BaseModel):
 history:list[float]=Field(min_length=3)
 horizon:int=Field(default=7,ge=1,le=90)
