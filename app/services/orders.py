import json
from datetime import UTC, datetime, timedelta
from sqlmodel import Session, select
from app.models.entities import Merchant, Order, OrderStatus, RiskLevel
from app.schemas.orders import CustomerStats, MerchantCreate, OrderCreate
from app.scoring.engine import CustomerHistory, RuleBasedRiskScorer
from app.services.phone import normalize_algerian_phone


def ensure_demo_merchant(session: Session) -> Merchant:
    merchant = session.exec(select(Merchant).where(Merchant.id == 1)).first()
    if merchant:
        return merchant
    merchant = Merchant(
        store_name="ThiqaDZ Demo Store",
        phone="+213555000001",
        email="demo@thiqa.local",
        wilaya="Alger",
        account_status="demo",
    )
    session.add(merchant)
    session.commit()
    session.refresh(merchant)
    return merchant


def create_merchant(session: Session, payload: MerchantCreate) -> Merchant:
    merchant = Merchant(
        store_name=payload.store_name,
        phone=normalize_algerian_phone(payload.phone),
        email=payload.email,
        wilaya=payload.wilaya,
    )
    session.add(merchant)
    session.commit()
    session.refresh(merchant)
    return merchant


def get_customer_history(session: Session, phone: str, exclude_order_id: int | None = None) -> CustomerHistory:
    normalized = normalize_algerian_phone(phone)
    statement = select(Order).where(Order.phone == normalized)
    if exclude_order_id:
        statement = statement.where(Order.id != exclude_order_id)
    orders = session.exec(statement).all()
    recent_cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=24)
    return CustomerHistory(
        total_orders=len(orders),
        delivered=sum(1 for o in orders if o.status == OrderStatus.delivered),
        refused=sum(1 for o in orders if o.status == OrderStatus.refused),
        cancelled=sum(1 for o in orders if o.status == OrderStatus.cancelled),
        recent_same_pending=sum(1 for o in orders if o.status == OrderStatus.pending and o.created_at >= recent_cutoff),
    )


def score_order(session: Session, order: Order) -> Order:
    history = get_customer_history(session, order.phone, order.id)
    result = RuleBasedRiskScorer().evaluate(order, history)
    order.risk_score = result.score
    order.risk_level = result.risk_level
    order.recommendation = result.recommendation
    order.reasons = json.dumps(result.reasons, ensure_ascii=False)
    order.updated_at = datetime.now(UTC).replace(tzinfo=None)
    return order


def create_order(session: Session, payload: OrderCreate) -> Order:
    ensure_demo_merchant(session)
    order = Order(**payload.model_dump())
    order.phone = normalize_algerian_phone(payload.phone)
    score_order(session, order)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def update_order_status(session: Session, order_id: int, status: OrderStatus) -> Order | None:
    order = session.get(Order, order_id)
    if not order:
        return None
    order.status = status
    score_order(session, order)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def order_to_dict(order: Order) -> dict:
    data = order.model_dump()
    data["reasons"] = json.loads(order.reasons or "[]")
    return data


def customer_stats(session: Session, phone: str) -> CustomerStats:
    normalized = normalize_algerian_phone(phone)
    orders = session.exec(select(Order).where(Order.phone == normalized).order_by(Order.created_at.desc())).all()
    delivered = sum(1 for o in orders if o.status == OrderStatus.delivered)
    refused = sum(1 for o in orders if o.status == OrderStatus.refused)
    cancelled = sum(1 for o in orders if o.status == OrderStatus.cancelled)
    pending = sum(1 for o in orders if o.status == OrderStatus.pending)
    finished = delivered + refused + cancelled
    return CustomerStats(
        phone=normalized,
        total_orders=len(orders),
        delivered=delivered,
        refused=refused,
        cancelled=cancelled,
        pending=pending,
        total_amount_dzd=sum(o.amount_dzd for o in orders),
        last_order_at=orders[0].created_at if orders else None,
        success_rate=round((delivered / finished) * 100, 1) if finished else 0,
        last_risk_score=orders[0].risk_score if orders else None,
    )


def dashboard_summary(session: Session, refused_loss_dzd: int = 700) -> dict:
    orders = session.exec(select(Order).order_by(Order.created_at.desc())).all()
    delivered = sum(1 for o in orders if o.status == OrderStatus.delivered)
    refused = sum(1 for o in orders if o.status == OrderStatus.refused)
    finished = delivered + refused + sum(1 for o in orders if o.status == OrderStatus.cancelled)
    return {
        "total_orders": len(orders),
        "low_risk": sum(1 for o in orders if o.risk_level == RiskLevel.low),
        "medium_risk": sum(1 for o in orders if o.risk_level == RiskLevel.medium),
        "high_risk": sum(1 for o in orders if o.risk_level == RiskLevel.high),
        "delivered": delivered,
        "refused": refused,
        "delivery_rate": round((delivered / finished) * 100, 1) if finished else 0,
        "estimated_refused_loss_dzd": refused * refused_loss_dzd,
        "recent_orders": [order_to_dict(o) for o in orders[:10]],
    }
