import os
import sys
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import User, CustomerProfile, SellerProfile
from security import verify_password, get_password_hash, create_access_token, decode_access_token

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GraminUdyam - Auth & Profile Service (Amazon-Grade Schema)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Paths to seed JSON files
CANDIDATE_ROOTS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    os.path.abspath(os.path.join(os.path.dirname(__file__))),
    os.getcwd(),
    "/app",
]

def find_json_path(filename: str) -> str:
    for base in CANDIDATE_ROOTS:
        p = os.path.join(base, "database", filename)
        if os.path.exists(p):
            return p
    return os.path.join(CANDIDATE_ROOTS[0], "database", filename)

CUSTOMERS_JSON = find_json_path("customers.json")
SELLERS_JSON = find_json_path("sellers.json")

# Schemas
class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    role: str = "customer"  # "customer" or "seller"
    phone: Optional[str] = "9876543210"
    village: Optional[str] = "Gokulgaon"
    block: Optional[str] = "Baramati"
    district: Optional[str] = "Pune"
    state: Optional[str] = "Maharashtra"
    margin_capital: Optional[float] = 100000.0
    business_category: Optional[str] = "Dairy"

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str
    user_id: int

# Startup Seeder from database/customers.json & database/sellers.json
@app.on_event("startup")
def seed_from_json_database():
    db = next(get_db())
    try:
        # 1. Seed from customers.json
        if os.path.exists(CUSTOMERS_JSON):
            with open(CUSTOMERS_JSON, "r", encoding="utf-8") as f:
                customers_data = json.load(f)
            for c in customers_data:
                user = db.query(User).filter(User.email == c["email"]).first()
                if not user:
                    prof = c["customer_profile"]
                    addr = prof["shipping_address"]
                    fin = prof["enterprise_financials"]
                    user = User(
                        id=c["user_id"],
                        email=c["email"],
                        hashed_password=get_password_hash("password123"),
                        name=f"{prof['first_name']} {prof['last_name']}",
                        role="customer",
                        phone=prof["phone"],
                        village=addr["village"],
                        block=addr["block"],
                        district=addr["district"],
                        state=addr["state"],
                        margin_capital=fin["available_margin_capital"],
                        business_category=fin["target_business_category"],
                        status="ACTIVE"
                    )
                    db.add(user)
                    db.flush()

                    # Create CustomerProfile
                    cust_prof = CustomerProfile(
                        customer_id=prof["customer_id"],
                        user_id=user.id,
                        first_name=prof["first_name"],
                        last_name=prof["last_name"],
                        phone=prof["phone"],
                        avatar_url=prof.get("avatar_url"),
                        kyc_status=prof.get("kyc_status", "VERIFIED_AADHAAR"),
                        village=addr["village"],
                        block=addr["block"],
                        district=addr["district"],
                        state=addr["state"],
                        postal_code=addr["postal_code"],
                        available_margin_capital=fin["available_margin_capital"],
                        target_business_category=fin["target_business_category"],
                        eligible_concessional_scheme=fin.get("eligible_concessional_scheme", "Term Loan Scheme"),
                        eligible_loan_amount=fin.get("eligible_loan_amount", 900000.0),
                        customer_tier=prof.get("amazon_membership", {}).get("customer_tier", "PRIME_RURAL_BENEFICIARY"),
                        shipping_address_json=json.dumps(addr)
                    )
                    db.add(cust_prof)

        # 2. Seed from sellers.json
        if os.path.exists(SELLERS_JSON):
            with open(SELLERS_JSON, "r", encoding="utf-8") as f:
                sellers_data = json.load(f)
            for s in sellers_data:
                user = db.query(User).filter(User.email == s["email"]).first()
                if not user:
                    sprof = s["seller_profile"]
                    wh = sprof.get("fulfillment_logistics", {}).get("primary_warehouse", {})
                    user = User(
                        id=s["user_id"],
                        email=s["email"],
                        hashed_password=get_password_hash("password123"),
                        name=sprof["merchant_store_name"],
                        role="seller",
                        phone="+91-9876509988",
                        village="MIDC Industrial Area",
                        block="Baramati",
                        district=wh.get("district", "Pune"),
                        state=wh.get("state", "Maharashtra"),
                        margin_capital=500000.0,
                        business_category="Machinery & Supplies",
                        status="ACTIVE"
                    )
                    db.add(user)
                    db.flush()

                    seller_prof = SellerProfile(
                        seller_id=sprof["seller_id"],
                        user_id=user.id,
                        merchant_store_name=sprof["merchant_store_name"],
                        legal_company_name=sprof["legal_company_name"],
                        seller_tier=sprof.get("seller_tier", "PLATINUM_RURAL_HUB"),
                        merchant_badge=sprof.get("merchant_badge", "Amazon Fulfilled & SCA Certified"),
                        compliance_tax_json=json.dumps(sprof.get("compliance_tax", {})),
                        fulfillment_logistics_json=json.dumps(sprof.get("fulfillment_logistics", {})),
                        merchant_performance_json=json.dumps(sprof.get("merchant_performance", {})),
                        financial_settlement_json=json.dumps(sprof.get("financial_settlement", {}))
                    )
                    db.add(seller_prof)

        db.commit()
        print("Startup: Database successfully synchronized with database/customers.json and database/sellers.json.")
    except Exception as e:
        db.rollback()
        print(f"Startup DB seed note: {e}")
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service", "timestamp": datetime.utcnow().isoformat()}

@app.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        name=user_data.name,
        role=user_data.role.lower(),
        phone=user_data.phone,
        village=user_data.village,
        block=user_data.block,
        district=user_data.district,
        state=user_data.state,
        margin_capital=user_data.margin_capital,
        business_category=user_data.business_category
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "role": new_user.role, "user_id": new_user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": new_user.role,
        "name": new_user.name,
        "email": new_user.email,
        "user_id": new_user.id
    }

@app.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "user_id": user.id
    }

@app.get("/me")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    res = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "phone": current_user.phone,
        "village": current_user.village,
        "block": current_user.block,
        "district": current_user.district,
        "state": current_user.state,
        "margin_capital": current_user.margin_capital,
        "business_category": current_user.business_category,
        "created_at": current_user.created_at
    }
    if current_user.role == "customer" and current_user.customer_profile:
        cp = current_user.customer_profile
        res["customer_profile"] = {
            "customer_id": cp.customer_id,
            "customer_tier": cp.customer_tier,
            "kyc_status": cp.kyc_status,
            "eligible_concessional_scheme": cp.eligible_concessional_scheme,
            "eligible_loan_amount": cp.eligible_loan_amount
        }
    elif current_user.role == "seller" and current_user.seller_profile:
        sp = current_user.seller_profile
        res["seller_profile"] = {
            "seller_id": sp.seller_id,
            "store_name": sp.merchant_store_name,
            "seller_tier": sp.seller_tier,
            "merchant_badge": sp.merchant_badge
        }
    return res

# Amazon-Style Relational Queries
@app.get("/customers")
def get_all_customers(db: Session = Depends(get_db)):
    """Retrieves all Customer profiles from PostgreSQL"""
    customers = db.query(CustomerProfile).all()
    results = []
    for c in customers:
        results.append({
            "customer_id": c.customer_id,
            "user_id": c.user_id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone": c.phone,
            "village": c.village,
            "block": c.block,
            "district": c.district,
            "state": c.state,
            "available_margin_capital": c.available_margin_capital,
            "target_business_category": c.target_business_category,
            "eligible_concessional_scheme": c.eligible_concessional_scheme,
            "eligible_loan_amount": c.eligible_loan_amount,
            "customer_tier": c.customer_tier,
            "shipping_address": json.loads(c.shipping_address_json) if c.shipping_address_json else {}
        })
    return {"total_count": len(results), "customers": results}

@app.get("/sellers")
def get_all_sellers(db: Session = Depends(get_db)):
    """Retrieves all Seller profiles from PostgreSQL"""
    sellers = db.query(SellerProfile).all()
    results = []
    for s in sellers:
        results.append({
            "seller_id": s.seller_id,
            "user_id": s.user_id,
            "merchant_store_name": s.merchant_store_name,
            "legal_company_name": s.legal_company_name,
            "seller_tier": s.seller_tier,
            "merchant_badge": s.merchant_badge,
            "compliance_tax": json.loads(s.compliance_tax_json) if s.compliance_tax_json else {},
            "fulfillment_logistics": json.loads(s.fulfillment_logistics_json) if s.fulfillment_logistics_json else {},
            "merchant_performance": json.loads(s.merchant_performance_json) if s.merchant_performance_json else {}
        })
    return {"total_count": len(results), "sellers": results}

@app.get("/customers/{customer_id}")
def get_customer_by_id(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "customer_id": c.customer_id,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "phone": c.phone,
        "village": c.village,
        "block": c.block,
        "district": c.district,
        "available_margin_capital": c.available_margin_capital,
        "target_business_category": c.target_business_category,
        "eligible_concessional_scheme": c.eligible_concessional_scheme,
        "shipping_address": json.loads(c.shipping_address_json) if c.shipping_address_json else {}
    }

@app.get("/sellers/{seller_id}")
def get_seller_by_id(seller_id: int, db: Session = Depends(get_db)):
    s = db.query(SellerProfile).filter(SellerProfile.seller_id == seller_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Seller not found")
    return {
        "seller_id": s.seller_id,
        "merchant_store_name": s.merchant_store_name,
        "legal_company_name": s.legal_company_name,
        "seller_tier": s.seller_tier,
        "merchant_badge": s.merchant_badge,
        "fulfillment_logistics": json.loads(s.fulfillment_logistics_json) if s.fulfillment_logistics_json else {},
        "merchant_performance": json.loads(s.merchant_performance_json) if s.merchant_performance_json else {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
