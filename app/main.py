from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import create_db_and_tables, engine, get_session
from app.models.entities import Order
from app.schemas.orders import OrderCreate
from app.services.orders import create_order, dashboard_summary, ensure_demo_merchant, order_to_dict, update_order_status
from app.models.entities import OrderStatus
from scripts.seed_demo import seed_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    create_db_and_tables()
    with Session(engine) as session:
        ensure_demo_merchant(session)
        if settings.auto_seed_demo:
            seed_session(session)
    yield


settings = get_settings()
templates = Jinja2Templates(directory="app/templates")
app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"^http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}):8000$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["content-type"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session), status: str = "", wilaya: str = "", risk: str = "", phone: str = ""):
    summary = dashboard_summary(session, settings.refused_delivery_loss_dzd)
    statement = select(Order).order_by(Order.created_at.desc())
    if status:
        statement = statement.where(Order.status == status)
    if wilaya:
        statement = statement.where(Order.wilaya == wilaya)
    if risk:
        statement = statement.where(Order.risk_level == risk)
    if phone:
        statement = statement.where(Order.phone.contains(phone))
    orders = [order_to_dict(o) for o in session.exec(statement).all()]
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"summary": summary, "orders": orders, "filters": {"status": status, "wilaya": wilaya, "risk": risk, "phone": phone}},
    )


@app.get("/evaluate", response_class=HTMLResponse)
def evaluate_page(request: Request):
    return templates.TemplateResponse(request, "evaluate.html", {"result": None})


@app.post("/evaluate", response_class=HTMLResponse)
def evaluate_submit(
    request: Request,
    phone: str = Form(...),
    customer_name: str = Form(""),
    wilaya: str = Form(...),
    commune: str = Form(""),
    amount_dzd: int = Form(...),
    product_category: str = Form(...),
    order_channel: str = Form(...),
    is_confirmed: bool = Form(False),
    contact_attempts: int = Form(0),
    note: str = Form(""),
    session: Session = Depends(get_session),
):
    payload = OrderCreate(
        phone=phone,
        customer_name=customer_name or None,
        wilaya=wilaya,
        commune=commune or None,
        amount_dzd=amount_dzd,
        product_category=product_category,
        order_channel=order_channel,
        is_confirmed=is_confirmed,
        contact_attempts=contact_attempts,
        note=note or None,
    )
    order = create_order(session, payload)
    return templates.TemplateResponse(request, "evaluate.html", {"result": order_to_dict(order)})


@app.post("/orders/{order_id}/status")
def web_update_status(order_id: int, status: OrderStatus = Form(...), session: Session = Depends(get_session)):
    update_order_status(session, order_id, status)
    return RedirectResponse("/dashboard", status_code=303)
