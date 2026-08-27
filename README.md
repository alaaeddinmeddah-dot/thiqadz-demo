# ThiqaDZ

ThiqaDZ is a local MVP for Algerian COD e-commerce merchants. It helps a merchant evaluate order risk before shipping by producing a transparent rule-based Risk Score from 0 to 100 with reasons and a recommendation.

## Features

- Merchant creation API
- Order creation and status update
- Rule-based scoring engine, not fake AI
- Customer profile by normalized Algerian phone number
- Dashboard with filters and delivery metrics
- RTL Arabic landing page and quick order evaluation screen
- Idempotent demo seed data
- REST API docs at `/docs`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade -r requirements.txt
Copy-Item .env.example .env
python -m scripts.seed_demo
```

## Run Locally On The Computer

`127.0.0.1` only opens on the same computer:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- Landing page: http://127.0.0.1:8000/
- Dashboard: http://127.0.0.1:8000/dashboard
- Quick evaluation: http://127.0.0.1:8000/evaluate
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Run On Local Wi-Fi For Phone Preview

Start Uvicorn on all local interfaces:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Find the computer IPv4 address:

```powershell
ipconfig
```

Look for `IPv4 Address`, then open it from the phone on the same Wi-Fi, for example:

```text
http://192.168.1.5:8000/
```

If Windows Firewall asks, allow access on the private network only for the demo.

## Production Demo Deployment

This project includes `render.yaml`, `Procfile`, and `runtime.txt` for a free Render-style Python web service.

Build command:

```bash
python -m pip install --upgrade pip && python -m pip install -r requirements.txt
```

Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Important demo note: the free web service uses local SQLite. If the hosting platform does not provide persistent disk on the free plan, demo data can be recreated automatically on startup via `AUTO_SEED_DEMO=true`, but it should not be presented as permanent production storage.

## Tests

```powershell
python -m pytest
```

## Demo Credentials

No real authentication is enabled in this MVP. Demo mode values are documented for future login work:

- Username: `demo`
- Password: `demo123`

## Project Structure

- `app/main.py`: FastAPI app, web pages, health endpoint
- `app/api/routes.py`: REST API
- `app/models/entities.py`: SQLModel database models
- `app/schemas/orders.py`: Pydantic V2 schemas
- `app/services/orders.py`: order, dashboard, and customer logic
- `app/services/phone.py`: Algerian phone normalization
- `app/scoring/engine.py`: independent rule-based risk scoring
- `app/templates/`: Jinja2 pages
- `app/static/`: CSS
- `scripts/seed_demo.py`: local demo data
- `tests/`: pytest suite

## Current Limits

- No production authentication yet
- SQLite is used for local MVP only
- Scoring is rule-based until enough real merchant data exists
- No paid APIs or external integrations are connected
- Demo data is synthetic and does not represent real customers

## Future Extensions

- Shopify and WooCommerce adapters
- Telegram bot
- WhatsApp Business API adapter
- Delivery company API adapters
- Machine learning model trained on merchant outcomes
- Multi-tenant SaaS permissions
- Subscription billing
