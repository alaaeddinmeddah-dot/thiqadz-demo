from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.core.config import get_settings
from app.database.session import get_session
from app.models.entities import Order, OrderStatus, RiskLevel
from app.schemas.orders import CustomerStats, MerchantCreate, OrderCreate, OrderRead, RiskResult, StatusUpdate
from app.services.orders import (
    create_merchant,
    create_order,
    customer_stats,
    dashboard_summary,
    order_to_dict,
    update_order_status,
)
from app.scoring.engine import RuleBasedRiskScorer
from app.services.orders import get_customer_history
from app.services.phone import normalize_algerian_phone


router = APIRouter(prefix="/api")


@router.post("/merchants")
def merchants(payload: MerchantCreate, session: Session = Depends(get_session)):
    return create_merchant(session, payload)


@router.post("/orders", response_model=OrderRead)
def orders_create(payload: OrderCreate, session: Session = Depends(get_session)):
    return order_to_dict(create_order(session, payload))


@router.get("/orders")
def orders_list(
    status: OrderStatus | None = None,
    wilaya: str | None = None,
    risk_level: RiskLevel | None = None,
    phone: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(Order).order_by(Order.created_at.desc())
    if status:
        statement = statement.where(Order.status == status)
    if wilaya:
        statement = statement.where(Order.wilaya == wilaya)
    if risk_level:
        statement = statement.where(Order.risk_level == risk_level)
    if phone:
        statement = statement.where(Order.phone.contains(normalize_algerian_phone(phone)))
    return [order_to_dict(o) for o in session.exec(statement).all()]


@router.get("/orders/{order_id}", response_model=OrderRead)
def orders_get(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_dict(order)


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
def orders_status(order_id: int, payload: StatusUpdate, session: Session = Depends(get_session)):
    order = update_order_status(session, order_id, payload.status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_dict(order)


@router.post("/risk/evaluate", response_model=RiskResult)
def risk_evaluate(payload: OrderCreate, session: Session = Depends(get_session)):
    order_data = payload.model_dump()
    order_data["phone"] = normalize_algerian_phone(payload.phone)
    order = Order(**order_data)
    result = RuleBasedRiskScorer().evaluate(order, get_customer_history(session, order.phone))
    return result


@router.get("/customers/{phone}", response_model=CustomerStats)
def customers_get(phone: str, session: Session = Depends(get_session)):
    return customer_stats(session, phone)


@router.get("/dashboard/summary")
def dashboard(session: Session = Depends(get_session)):
    return dashboard_summary(session, get_settings().refused_delivery_loss_dzd)
