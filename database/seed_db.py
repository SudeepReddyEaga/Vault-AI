import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text

# Resolve paths
DB_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMERS_JSON = os.path.join(DB_DIR, "customers.json")
SELLERS_JSON = os.path.join(DB_DIR, "sellers.json")
SCHEMA_SQL = os.path.join(DB_DIR, "schema.sql")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword2026@localhost:5432/rural_platform_db")

def get_engine():
    """Tries PostgreSQL first; falls back to SQLite for local execution if Postgres is offline"""
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine, "postgresql"
    except Exception as e:
        print(f"[Notice] PostgreSQL not reachable directly ({e}). Using SQLite fallback 'rural_amazon.db'.")
        sqlite_path = os.path.join(DB_DIR, "rural_amazon.db")
        sqlite_engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
        return sqlite_engine, "sqlite"

def init_and_seed_database():
    """
    Reads customers.json and sellers.json, and seeds the relational database.
    """
    engine, db_type = get_engine()
    print(f"Connecting to database [{db_type}]...")

    # Load JSON files
    with open(CUSTOMERS_JSON, "r", encoding="utf-8") as f:
        customers_data: List[Dict[str, Any]] = json.load(f)

    with open(SELLERS_JSON, "r", encoding="utf-8") as f:
        sellers_data: List[Dict[str, Any]] = json.load(f)

    with engine.begin() as conn:
        # Create tables
        if db_type == "postgresql":
            with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
                schema_script = f.read()
            conn.execute(text(schema_script))
        else:
            # SQLite simplified schema creation
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS customer_profiles (
                    customer_id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    village TEXT,
                    block TEXT,
                    district TEXT,
                    state TEXT,
                    postal_code TEXT,
                    available_margin_capital REAL,
                    target_business_category TEXT,
                    eligible_concessional_scheme TEXT,
                    eligible_loan_amount REAL,
                    customer_tier TEXT,
                    shipping_address TEXT,
                    created_at TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS seller_profiles (
                    seller_id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE,
                    merchant_store_name TEXT,
                    legal_company_name TEXT,
                    seller_tier TEXT,
                    merchant_badge TEXT,
                    compliance_tax TEXT,
                    fulfillment_logistics TEXT,
                    merchant_performance TEXT,
                    financial_settlement TEXT,
                    created_at TEXT
                );
            """))

        # Seed Customers
        for c in customers_data:
            # Upsert User
            user_exists = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": c["email"]}).fetchone()
            if not user_exists:
                conn.execute(text("""
                    INSERT INTO users (id, email, password_hash, role, status)
                    VALUES (:id, :email, :password_hash, :role, :status)
                """), {
                    "id": c["user_id"],
                    "email": c["email"],
                    "password_hash": c["password_hash"],
                    "role": c["role"],
                    "status": c.get("status", "ACTIVE")
                })

            # Upsert Customer Profile
            prof = c["customer_profile"]
            addr = prof["shipping_address"]
            fin = prof["enterprise_financials"]
            tier = prof["amazon_membership"]

            cust_exists = conn.execute(text("SELECT customer_id FROM customer_profiles WHERE user_id = :uid"), {"uid": c["user_id"]}).fetchone()
            if not cust_exists:
                conn.execute(text("""
                    INSERT INTO customer_profiles (
                        customer_id, user_id, first_name, last_name, phone,
                        village, block, district, state, postal_code,
                        available_margin_capital, target_business_category,
                        eligible_concessional_scheme, eligible_loan_amount, customer_tier,
                        shipping_address
                    ) VALUES (
                        :cid, :uid, :fname, :lname, :phone,
                        :village, :block, :district, :state, :pcode,
                        :margin, :cat, :scheme, :loan, :tier,
                        :addr
                    )
                """), {
                    "cid": prof["customer_id"],
                    "uid": c["user_id"],
                    "fname": prof["first_name"],
                    "lname": prof["last_name"],
                    "phone": prof["phone"],
                    "village": addr["village"],
                    "block": addr["block"],
                    "district": addr["district"],
                    "state": addr["state"],
                    "pcode": addr["postal_code"],
                    "margin": fin["available_margin_capital"],
                    "cat": fin["target_business_category"],
                    "scheme": fin["eligible_concessional_scheme"],
                    "loan": fin["eligible_loan_amount"],
                    "tier": tier["customer_tier"],
                    "addr": json.dumps(addr)
                })

        # Seed Sellers
        for s in sellers_data:
            user_exists = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": s["email"]}).fetchone()
            if not user_exists:
                conn.execute(text("""
                    INSERT INTO users (id, email, password_hash, role, status)
                    VALUES (:id, :email, :password_hash, :role, :status)
                """), {
                    "id": s["user_id"],
                    "email": s["email"],
                    "password_hash": s["password_hash"],
                    "role": s["role"],
                    "status": s.get("status", "ACTIVE")
                })

            sprof = s["seller_profile"]
            seller_exists = conn.execute(text("SELECT seller_id FROM seller_profiles WHERE user_id = :uid"), {"uid": s["user_id"]}).fetchone()
            if not seller_exists:
                conn.execute(text("""
                    INSERT INTO seller_profiles (
                        seller_id, user_id, merchant_store_name, legal_company_name,
                        seller_tier, merchant_badge, compliance_tax, fulfillment_logistics,
                        merchant_performance, financial_settlement
                    ) VALUES (
                        :sid, :uid, :store_name, :legal_name,
                        :tier, :badge, :tax, :logistics, :perf, :settle
                    )
                """), {
                    "sid": sprof["seller_id"],
                    "uid": s["user_id"],
                    "store_name": sprof["merchant_store_name"],
                    "legal_name": sprof["legal_company_name"],
                    "tier": sprof["seller_tier"],
                    "badge": sprof["merchant_badge"],
                    "tax": json.dumps(sprof["compliance_tax"]),
                    "logistics": json.dumps(sprof["fulfillment_logistics"]),
                    "perf": json.dumps(sprof["merchant_performance"]),
                    "settle": json.dumps(sprof["financial_settlement"])
                })

    print(f"Successfully seeded {len(customers_data)} Customer Profiles and {len(sellers_data)} Seller Profiles into database.")

# Retrieval Methods from Database
def query_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    engine, _ = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT u.id, u.email, u.role, c.customer_id, c.first_name, c.last_name, c.phone,
                   c.village, c.block, c.district, c.available_margin_capital, c.target_business_category,
                   c.eligible_concessional_scheme, c.customer_tier, c.shipping_address
            FROM users u
            JOIN customer_profiles c ON u.id = c.user_id
            WHERE u.email = :email
        """), {"email": email}).fetchone()
        if row:
            return dict(row._mapping)
    return None

def query_seller_by_id(seller_id: int) -> Optional[Dict[str, Any]]:
    engine, _ = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT u.id as user_id, u.email, s.seller_id, s.merchant_store_name, s.legal_company_name,
                   s.seller_tier, s.merchant_badge, s.compliance_tax, s.fulfillment_logistics, s.merchant_performance
            FROM users u
            JOIN seller_profiles s ON u.id = s.user_id
            WHERE s.seller_id = :sid
        """), {"sid": seller_id}).fetchone()
        if row:
            res = dict(row._mapping)
            if isinstance(res.get("compliance_tax"), str):
                res["compliance_tax"] = json.loads(res["compliance_tax"])
            if isinstance(res.get("fulfillment_logistics"), str):
                res["fulfillment_logistics"] = json.loads(res["fulfillment_logistics"])
            if isinstance(res.get("merchant_performance"), str):
                res["merchant_performance"] = json.loads(res["merchant_performance"])
            return res
    return None

def list_all_customers() -> List[Dict[str, Any]]:
    engine, _ = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT u.id, u.email, c.customer_id, c.first_name, c.last_name, c.phone,
                   c.village, c.block, c.district, c.available_margin_capital, c.target_business_category,
                   c.eligible_concessional_scheme, c.customer_tier
            FROM users u
            JOIN customer_profiles c ON u.id = c.user_id
        """)).fetchall()
        return [dict(r._mapping) for r in rows]

def list_all_sellers() -> List[Dict[str, Any]]:
    engine, _ = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT u.id as user_id, u.email, s.seller_id, s.merchant_store_name, s.legal_company_name,
                   s.seller_tier, s.merchant_badge
            FROM users u
            JOIN seller_profiles s ON u.id = s.user_id
        """)).fetchall()
        return [dict(r._mapping) for r in rows]

if __name__ == "__main__":
    init_and_seed_database()
    print("\n--- Verifying Retrieval from Database ---")
    cust = query_customer_by_email("ramesh.patil@rural.in")
    print("Customer retrieved:", cust)
    seller = query_seller_by_id(501)
    print("Seller retrieved:", seller["merchant_store_name"], f"(Tier: {seller['seller_tier']})")
