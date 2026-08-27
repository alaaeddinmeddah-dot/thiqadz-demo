from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AccountStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    demo = "demo"


class OrderStatus(str, Enum):
    pending = "Pending"
    delivered = "Delivered"
    refused = "Refused"
    cancelled = "Cancelled"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Merchant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    store_name: str = Field(index=True, min_length=2, max_length=120)
    phone: str = Field(index=True, max_length=20)
    email: str | None = Field(default=None, max_length=120)
    wilaya: str = Field(index=True, max_length=80)
    account_status: AccountStatus = Field(default=AccountStatus.active)
    registered_at: datetime = Field(default_factory=utc_now)


class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    merchant_id: int = Field(foreign_key="merchant.id", index=True)
    phone: str = Field(index=True, max_length=20)
    customer_name: str | None = Field(default=None, max_length=120)
    wilaya: str = Field(index=True, max_length=80)
    commune: str | None = Field(default=None, max_length=80)
    amount_dzd: int = Field(ge=0)
    product_category: str = Field(max_length=100)
    order_channel: str = Field(max_length=40)
    is_confirmed: bool = False
    contact_attempts: int = Field(default=0, ge=0, le=20)
    note: str | None = Field(default=None, max_length=500)
    status: OrderStatus = Field(default=OrderStatus.pending, index=True)
    risk_score: int = Field(default=0, ge=0, le=100)
    risk_level: RiskLevel = Field(default=RiskLevel.medium, index=True)
    recommendation: str = Field(default="")
    reasons: str = Field(default="[]")
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)
