from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.entities import OrderStatus, RiskLevel
from app.services.phone import normalize_algerian_phone


class APIModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class MerchantCreate(APIModel):
    store_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = None
    wilaya: str = Field(min_length=2, max_length=80)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_algerian_phone(value)


class OrderCreate(APIModel):
    merchant_id: int = 1
    phone: str = Field(min_length=1, max_length=30)
    customer_name: str | None = None
    wilaya: str = Field(min_length=2, max_length=80)
    commune: str | None = None
    amount_dzd: int = Field(ge=0)
    product_category: str = Field(min_length=2, max_length=100)
    order_channel: str = Field(pattern="^(Facebook|Instagram|Website|WhatsApp|Other)$")
    is_confirmed: bool = False
    contact_attempts: int = Field(default=0, ge=0, le=20)
    note: str | None = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return normalize_algerian_phone(value)


class RiskResult(APIModel):
    score: int
    risk_level: RiskLevel
    recommendation: str
    reasons: list[str]
    created_at: datetime


class OrderRead(OrderCreate):
    id: int
    status: OrderStatus
    risk_score: int
    risk_level: RiskLevel
    recommendation: str
    reasons: list[str]
    created_at: datetime
    updated_at: datetime


class StatusUpdate(APIModel):
    status: OrderStatus


class CustomerStats(APIModel):
    phone: str
    total_orders: int
    delivered: int
    refused: int
    cancelled: int
    pending: int
    total_amount_dzd: int
    last_order_at: datetime | None
    success_rate: float
    last_risk_score: int | None
