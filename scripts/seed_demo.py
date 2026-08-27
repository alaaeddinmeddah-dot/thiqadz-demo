from random import choice, randint, seed
from sqlmodel import Session, select
from app.database.session import create_db_and_tables, engine
from app.models.entities import Order, OrderStatus
from app.schemas.orders import OrderCreate
from app.services.orders import create_order, ensure_demo_merchant, update_order_status


def seed_session(session: Session) -> int:
    ensure_demo_merchant(session)
    if session.exec(select(Order)).first():
        return 0

    wilayas = ["Alger", "Oran", "Setif", "Constantine", "Blida", "Tizi Ouzou", "Annaba", "Batna", "Djelfa", "Bejaia"]
    categories = ["Cosmetique", "Vetements", "Accessoires", "Maison", "Electronique"]
    channels = ["Facebook", "Instagram", "Website", "WhatsApp", "Other"]
    phones = ["0551000001", "0551000002", "0662000003", "0773000004", "0551000005", "0662000006", "0773000007", "0551000008", "0662000009", "0773000010"]
    statuses = [OrderStatus.delivered, OrderStatus.delivered, OrderStatus.delivered, OrderStatus.refused, OrderStatus.cancelled, OrderStatus.pending]

    created = 0
    for i in range(28):
        payload = OrderCreate(
            phone=choice(phones),
            customer_name=f"Client Demo {i + 1}",
            wilaya=choice(wilayas),
            commune=choice(["Centre", "El Madania", "Akbou", "Bir Mourad Rais", ""]),
            amount_dzd=randint(2500, 36000),
            product_category=choice(categories),
            order_channel=choice(channels),
            is_confirmed=choice([True, True, False]),
            contact_attempts=randint(0, 5),
            note="Donnee demo sans client reel.",
        )
        order = create_order(session, payload)
        update_order_status(session, order.id, choice(statuses))
        created += 1
    return created


def run() -> None:
    seed(27)
    create_db_and_tables()
    with Session(engine) as session:
        created = seed_session(session)
    if created:
        print(f"Seeded {created} demo orders.")
    else:
        print("Demo data already exists.")


if __name__ == "__main__":
    run()
