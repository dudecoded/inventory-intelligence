from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company: str = Field(default="My Workspace", min_length=1, max_length=160)

    @field_validator("name", "company")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    company: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    company: Optional[str] = Field(default=None, min_length=1, max_length=160)

    @field_validator("name", "company")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="Uncategorized", min_length=1, max_length=120)
    stock: int = Field(default=0, ge=0)
    demand_30d: float = Field(default=0, ge=0, allow_inf_nan=False)
    unit_cost: float = Field(default=0, ge=0, allow_inf_nan=False)
    lead_time_days: int = Field(default=7, ge=0, le=365)

    @field_validator("sku", "name", "category")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.upper()


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(default=None, min_length=1, max_length=80)
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[str] = Field(default=None, min_length=1, max_length=120)
    stock: Optional[int] = Field(default=None, ge=0)
    demand_30d: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    unit_cost: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    lead_time_days: Optional[int] = Field(default=None, ge=0, le=365)

    @field_validator("sku", "name", "category")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("sku")
    @classmethod
    def normalize_optional_sku(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    stock: int
    demand_30d: float
    unit_cost: float
    lead_time_days: int

    model_config = ConfigDict(from_attributes=True)


class ProductAdjust(BaseModel):
    delta: int = Field(ge=-1000000, le=1000000)

    @field_validator("delta")
    @classmethod
    def reject_zero_adjustment(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Stock adjustment must not be zero.")
        return value


class ForecastRequest(BaseModel):
    history: list[float] = Field(min_length=3, max_length=365, allow_inf_nan=False)
    horizon: int = Field(default=7, ge=1, le=90)

    @field_validator("history")
    @classmethod
    def validate_history(cls, values: list[float]) -> list[float]:
        if any(value < 0 for value in values):
            raise ValueError("Historical demand values must be non-negative.")
        return values


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    contact_name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=40)
    lead_time_days: int = Field(default=7, ge=0, le=365)
    notes: str = Field(default="", max_length=1000)

    @field_validator("name", "contact_name", "email", "phone", "notes")
    @classmethod
    def clean_supplier_text(cls, value: str) -> str:
        return value.strip()


class SaleCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1000000)
    unit_price: float = Field(default=0, ge=0, allow_inf_nan=False)
    reference: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=500)


class PurchaseOrderLineCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1000000)
    unit_cost: float = Field(default=0, ge=0, allow_inf_nan=False)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int | None = None
    notes: str = Field(default="", max_length=500)
    expected_at: str | None = None
    items: list[PurchaseOrderLineCreate] = Field(min_length=1, max_length=100)


class PurchaseOrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|sent|cancelled)$")
