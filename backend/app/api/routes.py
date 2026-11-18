from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models import User, Product
from app.schemas import (
    RegisterRequest, LoginRequest, TokenOut, UserOut, UserUpdate,
    ProductCreate, ProductUpdate, ProductOut, ProductAdjust, ForecastRequest,
)
from app.services.forecasting import forecast_series, classify_stock, recommend_reorder

api_router = APIRouter()
bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    subject = decode_access_token(credentials.credentials)
    if not subject:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        user = db.get(User, int(subject))
    except (TypeError, ValueError):
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _owned_active_product(db: Session, user_id: int, product_id: int) -> Product:
    product = db.scalar(select(Product).where(
        Product.id == product_id, Product.owner_id == user_id, Product.active.is_(True)
    ))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@api_router.get("/status", tags=["health"])
def api_status():
    return {"status": "available", "version": "v1"}


@api_router.post("/auth/register", response_model=TokenOut, status_code=201, tags=["auth"])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, name=payload.name, password_hash=hash_password(payload.password), company=payload.company)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    return {"access_token": create_access_token(str(user.id)), "user": user}


@api_router.post("/auth/login", response_model=TokenOut, tags=["auth"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(str(user.id)), "user": user}


@api_router.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(user: User = Depends(current_user)):
    return user


@api_router.patch("/auth/me", response_model=UserOut, tags=["auth"])
def update_me(payload: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return user
    for field, value in updates.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@api_router.get("/dashboard/summary", tags=["analytics"])
def dashboard_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    products = db.scalars(select(Product).where(Product.owner_id == user.id, Product.active.is_(True))).all()
    inventory_value = sum(p.stock * p.unit_cost for p in products)
    low_stock = []
    overstock = []
    high_risk = []
    for product in products:
        insight = classify_stock(product.stock, product.demand_30d, product.lead_time_days)
        if insight["label"] in {"Stockout risk", "Reorder soon"}:
            low_stock.append(product)
        if insight["label"] == "Slow-moving / excess":
            overstock.append(product)
        if insight["risk"] == "high":
            high_risk.append(product)
    return {
        "active_products": len(products),
        "inventory_value": round(inventory_value, 2),
        "low_stock_count": len(low_stock),
        "overstock_count": len(overstock),
        "high_risk_count": len(high_risk),
        "healthy_count": max(0, len(products) - len(low_stock) - len(overstock)),
        "inventory_value_currency": "INR",
        "data_source": "database",
    }


@api_router.get("/products", response_model=list[ProductOut], tags=["inventory"])
def list_products(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Product).where(
        Product.owner_id == user.id, Product.active.is_(True)
    ).order_by(Product.name.asc())).all()


@api_router.post("/products", response_model=ProductOut, status_code=201, tags=["inventory"])
def create_product(payload: ProductCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    sku = payload.sku.upper()
    if db.scalar(select(Product.id).where(Product.sku == sku, Product.owner_id == user.id)):
        raise HTTPException(status_code=409, detail="SKU already exists in this workspace")
    product = Product(**payload.model_dump(exclude={"sku"}), sku=sku, owner_id=user.id)
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU already exists in this workspace")
    db.refresh(product)
    return product


@api_router.patch("/products/{product_id}", response_model=ProductOut, tags=["inventory"])
def update_product(product_id: int, payload: ProductUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    product = _owned_active_product(db, user.id, product_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return product
    if "sku" in updates:
        sku = updates["sku"].upper()
        if db.scalar(select(Product.id).where(Product.sku == sku, Product.owner_id == user.id, Product.id != product_id)):
            raise HTTPException(status_code=409, detail="SKU already exists in this workspace")
        updates["sku"] = sku
    for field, value in updates.items():
        setattr(product, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product update conflicts with an existing SKU")
    db.refresh(product)
    return product


@api_router.patch("/products/{product_id}/stock", response_model=ProductOut, tags=["inventory"])
def adjust_stock(product_id: int, payload: ProductAdjust, user: User = Depends(current_user), db: Session = Depends(get_db)):
    product = _owned_active_product(db, user.id, product_id)
    product.stock = max(0, product.stock + payload.delta)
    db.commit()
    db.refresh(product)
    return product


@api_router.delete("/products/{product_id}", tags=["inventory"])
def archive_product(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.id == product_id, Product.owner_id == user.id))
    if not product or not product.active:
        raise HTTPException(status_code=404, detail="Product not found")
    product.active = False
    db.commit()
    return {"ok": True, "archived_product_id": product_id}


@api_router.get("/products/insights", tags=["ml"])
def product_insights(user: User = Depends(current_user), db: Session = Depends(get_db)):
    products = db.scalars(select(Product).where(Product.owner_id == user.id, Product.active.is_(True))).all()
    return [
        {
            "product_id": product.id,
            "sku": product.sku,
            "name": product.name,
            **classify_stock(product.stock, product.demand_30d, product.lead_time_days),
            **recommend_reorder(product.stock, product.demand_30d, product.lead_time_days),
        }
        for product in products
    ]


@api_router.post("/ml/forecast", tags=["ml"])
def forecast(payload: ForecastRequest, user: User = Depends(current_user)):
    try:
        return forecast_series(payload.history, payload.horizon)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
