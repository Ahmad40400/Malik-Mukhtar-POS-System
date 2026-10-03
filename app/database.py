# app/database.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import bcrypt
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "pos.db"

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


from app.models import (
    User, Category, Product, Customer, Sale, SaleItem, HeldSale,
    HeldSaleItem, InventoryMovement, Setting, CreditCustomer, CreditTransaction
)


def init_db():
    Base.metadata.create_all(engine)

    # ===== AUTO MIGRATION: Add wholesale_min_qty if missing =====
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(products)")
    existing_cols = {row[1] for row in cur.fetchall()}
    if "wholesale_min_qty" not in existing_cols:
        cur.execute("ALTER TABLE products ADD COLUMN wholesale_min_qty FLOAT DEFAULT 0")
        conn.commit()
        print("✅ Added column: wholesale_min_qty")
    conn.close()
    # ===== END MIGRATION =====

    with SessionLocal() as s:
        if not s.query(User).first():
            pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
            s.add(User(username="admin", password_hash=pw, role="Admin", active=True))
        if not s.query(Category).first():
            cats = ["Grocery", "Beverages", "Personal Care", "Household", "Other"]
            s.add_all([Category(name=x) for x in cats])
        if not s.query(Product).first():
            grocery = s.query(Category).filter_by(name="Grocery").first()
            bev = s.query(Category).filter_by(name="Beverages").first()
            samples = [
                ("Milk 1L", "100001", "SKU-001", 220, 260, 240, 12, 25, grocery),
                ("Bread", "100002", "SKU-002", 120, 150, 140, 10, 30, grocery),
                ("Coca Cola 1.5L", "100003", "SKU-003", 180, 210, 195, 12, 20, bev),
                ("Pepsi 1.5L", "100004", "SKU-004", 180, 210, 195, 12, 20, bev),
                ("Biscuits", "100005", "SKU-005", 70, 90, 80, 24, 40, grocery),
            ]
            for n, b, sku, buy, retail, whole, wqty, stock, cat in samples:
                s.add(Product(name=n, barcode=b, sku=sku,
                              purchase_price=buy,
                              selling_price=retail,
                              wholesale_price=whole,
                              wholesale_min_qty=wqty,
                              stock_quantity=stock,
                              minimum_stock=5, category=cat))
        defaults = {
            "shop_name": "My Retail Store",
            "shop_address": "Pakistan",
            "shop_phone": "",
            "receipt_footer": "Thank you for shopping with us!",
            "currency": "PKR",
            "receipt_width": "80mm",
        }
        for k, v in defaults.items():
            if not s.query(Setting).filter_by(key=k).first():
                s.add(Setting(key=k, value=v))
        s.commit()