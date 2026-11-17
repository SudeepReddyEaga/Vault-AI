from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="customer")  # "customer" or "seller"
    phone = Column(String, nullable=True)
    village = Column(String, default="Shivaji Nagar")
    block = Column(String, default="Baramati")
    district = Column(String, default="Pune")
    state = Column(String, default="Maharashtra")
    margin_capital = Column(Float, default=100000.0)
    business_category = Column(String, default="Dairy")
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False)

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    customer_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    kyc_status = Column(String, default="VERIFIED_AADHAAR")
    village = Column(String, nullable=False)
    block = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    available_margin_capital = Column(Float, default=100000.0)
    target_business_category = Column(String, default="Dairy")
    eligible_concessional_scheme = Column(String, default="Term Loan Scheme")
    eligible_loan_amount = Column(Float, default=900000.0)
    customer_tier = Column(String, default="PRIME_RURAL_BENEFICIARY")
    shipping_address_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="customer_profile")

class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    seller_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    merchant_store_name = Column(String, nullable=False)
    legal_company_name = Column(String, nullable=False)
    seller_tier = Column(String, default="PLATINUM_RURAL_HUB")
    merchant_badge = Column(String, default="Amazon Fulfilled (FBA) & SCA Certified")
    compliance_tax_json = Column(Text, nullable=True)
    fulfillment_logistics_json = Column(Text, nullable=True)
    merchant_performance_json = Column(Text, nullable=True)
    financial_settlement_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="seller_profile")
