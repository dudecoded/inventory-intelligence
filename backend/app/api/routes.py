from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models import User, Product, Supplier, InventoryTransaction, PurchaseOrder, PurchaseOrderItem
from app.schemas import (
    RegisterRequest, LoginRequest, TokenOut, UserOut, UserUpdate,
    ProductCreate, ProductUpdate, ProductOut, ProductAdjust, ForecastRequest,\n    SupplierCreate, SaleCreate, PurchaseOrderCreate, PurchaseOrderStatusUpdate,
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


def _owned_product(db: Session, user_id: int, product_id: int) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id, Product.owner_id == user_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@api_router.get("/suppliers", tags=["suppliers"])
def list_suppliers(user: User = Depends(current_user), db: Session = Depends(get_db)):
    suppliers = db.scalars(select(Supplier).where(Supplier.owner_id == user.id, Supplier.active.is_(True)).order_by(Supplier.name)).all()
    return [{"id": x.id, "name": x.name, "contact_name": x.contact_name, "email": x.email, "phone": x.phone, "lead_time_days": x.lead_time_days, "notes": x.notes} for x in suppliers]


@api_router.post("/suppliers", status_code=201, tags=["suppliers"])
def create_supplier(payload: SupplierCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    supplier = Supplier(**payload.model_dump(), owner_id=user.id)
    db.add(supplier)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A supplier with this name already exists")
    db.refresh(supplier)
    return {"id": supplier.id, **payload.model_dump()}


@api_router.patch("/suppliers/{supplier_id}", tags=["suppliers"])
def update_supplier(supplier_id: int, payload: SupplierCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    supplier = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.owner_id == user.id, Supplier.active.is_(True)))
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for key, value in payload.model_dump().items():
        setattr(supplier, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A supplier with this name already exists")
    db.refresh(supplier)
    return {"id": supplier.id, **payload.model_dump()}


@api_router.delete("/suppliers/{supplier_id}", tags=["suppliers"])
def archive_supplier(supplier_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    supplier = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.owner_id == user.id, Supplier.active.is_(True)))
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.active = False
    db.commit()
    return {"ok": True}


@api_router.post("/sales", status_code=201, tags=["sales"])
def record_sale(payload: SaleCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    product = _owned_active_product(db, user.id, payload.product_id)
    if payload.quantity > product.stock:
        raise HTTPException(status_code=409, detail=f"Insufficient stock: {product.stock} units available")
    product.stock -= payload.quantity
    tx = InventoryTransaction(product_id=product.id, owner_id=user.id, transaction_type="sale", quantity=payload.quantity, unit_price=payload.unit_price or product.unit_cost, reference=payload.reference, notes=payload.notes)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return {"id": tx.id, "product_id": product.id, "sku": product.sku, "quantity": tx.quantity, "unit_price": tx.unit_price, "revenue": round(tx.quantity * tx.unit_price, 2), "stock_remaining": product.stock, "occurred_at": tx.occurred_at}


@api_router.get("/sales", tags=["sales"])
def list_sales(user: User = Depends(current_user), db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)):
    rows = db.execute(select(InventoryTransaction, Product).join(Product, Product.id == InventoryTransaction.product_id).where(InventoryTransaction.owner_id == user.id, InventoryTransaction.transaction_type == "sale").order_by(InventoryTransaction.occurred_at.desc()).limit(limit)).all()
    return [{"id": tx.id, "product_id": product.id, "sku": product.sku, "product_name": product.name, "quantity": tx.quantity, "unit_price": tx.unit_price, "revenue": round(tx.quantity * tx.unit_price, 2), "reference": tx.reference, "notes": tx.notes, "occurred_at": tx.occurred_at} for tx, product in rows]


@api_router.get("/sales/summary", tags=["sales"])
def sales_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(func.count(InventoryTransaction.id), func.coalesce(func.sum(InventoryTransaction.quantity), 0), func.coalesce(func.sum(InventoryTransaction.quantity * InventoryTransaction.unit_price), 0)).where(InventoryTransaction.owner_id == user.id, InventoryTransaction.transaction_type == "sale")).one()
    return {"transactions": int(rows[0]), "units_sold": int(rows[1]), "revenue": round(float(rows[2]), 2), "currency": "INR", "source": "recorded_sales"}


@api_router.get("/products/{product_id}/sales-history", tags=["sales"])
def product_sales_history(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db), days: int = Query(default=90, ge=7, le=365)):
    from datetime import datetime, timedelta
    product = _owned_product(db, user.id, product_id)
    since = datetime.utcnow() - timedelta(days=days - 1)
    rows = db.execute(select(func.date(InventoryTransaction.occurred_at), func.sum(InventoryTransaction.quantity)).where(InventoryTransaction.owner_id == user.id, InventoryTransaction.product_id == product.id, InventoryTransaction.transaction_type == "sale", InventoryTransaction.occurred_at >= since).group_by(func.date(InventoryTransaction.occurred_at)).order_by(func.date(InventoryTransaction.occurred_at))).all()
    daily = {str(day): int(quantity) for day, quantity in rows}
    return {"product_id": product.id, "sku": product.sku, "days": days, "history": [{"date": (since.date() + timedelta(days=i)).isoformat(), "quantity": daily.get((since.date() + timedelta(days=i)).isoformat(), 0)} for i in range(days)], "total_units": sum(daily.values())}


@api_router.post("/ml/forecast/product/{product_id}", tags=["ml"])
def forecast_product(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db), horizon: int = Query(default=14, ge=1, le=90), days: int = Query(default=90, ge=7, le=365)):
    history = product_sales_history(product_id, user, db, days)["history"]
    values = [row["quantity"] for row in history]
    if sum(values) == 0:
        raise HTTPException(status_code=422, detail="No recorded sales in this period. Record sales before forecasting this SKU.")
    if sum(values) < 3:
        raise HTTPException(status_code=422, detail="At least three non-zero sales observations are required.")
    try:
        result = forecast_series(values, horizon)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    result["source"] = "recorded_daily_sales"
    result["history_days"] = days
    result["historical_units"] = sum(values)
    return result


@api_router.post("/purchase-orders", status_code=201, tags=["procurement"])
def create_purchase_order(payload: PurchaseOrderCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    supplier = None
    if payload.supplier_id is not None:
        supplier = db.scalar(select(Supplier).where(Supplier.id == payload.supplier_id, Supplier.owner_id == user.id, Supplier.active.is_(True)))
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
    product_ids = [line.product_id for line in payload.items]
    products = db.scalars(select(Product).where(Product.owner_id == user.id, Product.active.is_(True), Product.id.in_(product_ids))).all()
    by_id = {p.id: p for p in products}
    if len(by_id) != len(set(product_ids)):
        raise HTTPException(status_code=404, detail="One or more products were not found")
    from datetime import datetime
    expected_at = None
    if payload.expected_at:
        try:
            expected_at = datetime.fromisoformat(payload.expected_at.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(status_code=422, detail="expected_at must be an ISO date or datetime")
    import uuid
    order = PurchaseOrder(order_number="PO-" + uuid.uuid4().hex[:10].upper(), supplier_id=supplier.id if supplier else None, owner_id=user.id, status="draft", notes=payload.notes, expected_at=expected_at)
    db.add(order)
    db.flush()
    for line in payload.items:
        db.add(PurchaseOrderItem(purchase_order_id=order.id, product_id=line.product_id, quantity=line.quantity, unit_cost=line.unit_cost if line.unit_cost else by_id[line.product_id].unit_cost))
    db.commit()
    db.refresh(order)
    return purchase_order_detail(order.id, user, db)


def purchase_order_detail(order_id: int, user: User, db: Session):
    order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == order_id, PurchaseOrder.owner_id == user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    rows = db.execute(select(PurchaseOrderItem, Product).join(Product, Product.id == PurchaseOrderItem.product_id).where(PurchaseOrderItem.purchase_order_id == order.id)).all()
    supplier = db.get(Supplier, order.supplier_id) if order.supplier_id else None
    items = [{"id": item.id, "product_id": product.id, "sku": product.sku, "name": product.name, "quantity": item.quantity, "unit_cost": item.unit_cost, "line_total": round(item.quantity * item.unit_cost, 2)} for item, product in rows]
    return {"id": order.id, "order_number": order.order_number, "supplier_id": order.supplier_id, "supplier_name": supplier.name if supplier else "Unassigned", "status": order.status, "notes": order.notes, "created_at": order.created_at, "expected_at": order.expected_at, "received_at": order.received_at, "items": items, "total": round(sum(x["line_total"] for x in items), 2)}


@api_router.get("/purchase-orders", tags=["procurement"])
def list_purchase_orders(user: User = Depends(current_user), db: Session = Depends(get_db)):
    orders = db.scalars(select(PurchaseOrder).where(PurchaseOrder.owner_id == user.id).order_by(PurchaseOrder.created_at.desc())).all()
    return [purchase_order_detail(order.id, user, db) for order in orders]


@api_router.patch("/purchase-orders/{order_id}", tags=["procurement"])
def update_purchase_order(order_id: int, payload: PurchaseOrderStatusUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == order_id, PurchaseOrder.owner_id == user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status in {"received", "cancelled"}:
        raise HTTPException(status_code=409, detail="This purchase order can no longer be changed")
    order.status = payload.status
    db.commit()
    return purchase_order_detail(order.id, user, db)


@api_router.post("/purchase-orders/{order_id}/receive", tags=["procurement"])
def receive_purchase_order(order_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == order_id, PurchaseOrder.owner_id == user.id))
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status not in {"draft", "sent"}:
        raise HTTPException(status_code=409, detail="Only draft or sent orders can be received")
    rows = db.execute(select(PurchaseOrderItem, Product).join(Product, Product.id == PurchaseOrderItem.product_id).where(PurchaseOrderItem.purchase_order_id == order.id)).all()
    for item, product in rows:
        product.stock += item.quantity
        db.add(InventoryTransaction(product_id=product.id, owner_id=user.id, transaction_type="receipt", quantity=item.quantity, unit_price=item.unit_cost, reference=order.order_number, notes="Purchase order received"))
    from datetime import datetime
    order.status = "received"
    order.received_at = datetime.utcnow()
    db.commit()
    return purchase_order_detail(order.id, user, db)


@api_router.get("/inventory/transactions", tags=["inventory"])
def list_inventory_transactions(user: User = Depends(current_user), db: Session = Depends(get_db), limit: int = Query(default=100, ge=1, le=500)):
    rows = db.execute(select(InventoryTransaction, Product).join(Product, Product.id == InventoryTransaction.product_id).where(InventoryTransaction.owner_id == user.id).order_by(InventoryTransaction.occurred_at.desc()).limit(limit)).all()
    return [{"id": tx.id, "sku": product.sku, "product_name": product.name, "type": tx.transaction_type, "quantity": tx.quantity, "unit_price": tx.unit_price, "reference": tx.reference, "notes": tx.notes, "occurred_at": tx.occurred_at} for tx, product in rows]
