from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password,verify_password,create_access_token,decode_access_token
from app.models import User,Product
from app.schemas import RegisterRequest,LoginRequest,TokenOut,UserOut,UserUpdate,ProductCreate,ProductUpdate,ProductOut,ProductAdjust,ForecastRequest
from app.services.forecasting import forecast_series,classify_stock,recommend_reorder
api_router=APIRouter();bearer=HTTPBearer(auto_error=False)
def current_user(credentials:HTTPAuthorizationCredentials|None=Depends(bearer),db:Session=Depends(get_db)):
 if not credentials:raise HTTPException(401,"Authentication required")
 subject=decode_access_token(credentials.credentials)
 if not subject:raise HTTPException(401,"Invalid or expired token")
 try:user=db.get(User,int(subject))
 except (TypeError,ValueError):user=None
 if not user:raise HTTPException(401,"User not found")
 return user
@api_router.get("/status",tags=["health"])
def api_status():return {"status":"available","version":"v1"}
@api_router.post("/auth/register",response_model=TokenOut,status_code=201,tags=["auth"])
def register(payload:RegisterRequest,db:Session=Depends(get_db)):
 email=payload.email.lower()
 if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,"Email already registered")
 user=User(email=email,name=payload.name,password_hash=hash_password(payload.password),company=payload.company)
 db.add(user);db.commit();db.refresh(user)
 return {"access_token":create_access_token(str(user.id)),"user":user}
@api_router.post("/auth/login",response_model=TokenOut,tags=["auth"])
def login(payload:LoginRequest,db:Session=Depends(get_db)):
 user=db.scalar(select(User).where(User.email==payload.email.lower()))
 if not user or not verify_password(payload.password,user.password_hash):raise HTTPException(401,"Incorrect email or password")
 return {"access_token":create_access_token(str(user.id)),"user":user}
@api_router.get("/auth/me",response_model=UserOut,tags=["auth"])
def me(user:User=Depends(current_user)):return user
@api_router.patch("/auth/me",response_model=UserOut,tags=["auth"])
def update_me(payload:UserUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 for field,value in payload.model_dump(exclude_unset=True).items():setattr(user,field,value)
 db.commit();db.refresh(user);return user
@api_router.get("/products",response_model=list[ProductOut],tags=["inventory"])
def list_products(user:User=Depends(current_user),db:Session=Depends(get_db)):
 return db.scalars(select(Product).where(Product.owner_id==user.id,Product.active==True).order_by(Product.name)).all()
@api_router.post("/products",response_model=ProductOut,status_code=201,tags=["inventory"])
def create_product(payload:ProductCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 if db.scalar(select(Product).where(Product.sku==payload.sku,Product.owner_id==user.id)):raise HTTPException(409,"SKU already exists")
 product=Product(**payload.model_dump(),owner_id=user.id);db.add(product);db.commit();db.refresh(product);return product
@api_router.patch("/products/{product_id}",response_model=ProductOut,tags=["inventory"])
def update_product(product_id:int,payload:ProductUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 product=db.scalar(select(Product).where(Product.id==product_id,Product.owner_id==user.id,Product.active==True))
 if not product:raise HTTPException(404,"Product not found")
 updates=payload.model_dump(exclude_unset=True)
 if "sku" in updates and db.scalar(select(Product).where(Product.sku==updates["sku"],Product.owner_id==user.id,Product.id!=product_id,Product.active==True)):raise HTTPException(409,"SKU already exists")
 for field,value in updates.items():setattr(product,field,value)
 db.commit();db.refresh(product);return product\n@api_router.patch("/products/{product_id}/stock",response_model=ProductOut,tags=["inventory"])
def adjust_stock(product_id:int,payload:ProductAdjust,user:User=Depends(current_user),db:Session=Depends(get_db)):
 product=db.scalar(select(Product).where(Product.id==product_id,Product.owner_id==user.id,Product.active==True))
 if not product:raise HTTPException(404,"Product not found")
 product.stock=max(0,product.stock+payload.delta);db.commit();db.refresh(product);return product
@api_router.delete("/products/{product_id}",tags=["inventory"])
def archive_product(product_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
 product=db.scalar(select(Product).where(Product.id==product_id,Product.owner_id==user.id))
 if not product:raise HTTPException(404,"Product not found")
 product.active=False;db.commit();return {"ok":True}
@api_router.get("/products/insights",tags=["ml"])
def product_insights(user:User=Depends(current_user),db:Session=Depends(get_db)):
 items=db.scalars(select(Product).where(Product.owner_id==user.id,Product.active==True)).all()
 return [{"product_id":p.id,"sku":p.sku,"name":p.name,**classify_stock(p.stock,p.demand_30d,p.lead_time_days),**recommend_reorder(p.stock,p.demand_30d,p.lead_time_days)} for p in items]
@api_router.post("/ml/forecast",tags=["ml"])
def forecast(payload:ForecastRequest,user:User=Depends(current_user)):
 try:return forecast_series(payload.history,payload.horizon)
 except ValueError as exc:raise HTTPException(422,str(exc))
