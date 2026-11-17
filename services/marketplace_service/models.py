from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, index=True, nullable=False)
    seller_name = Column(String, default="Kisan Agro Supplies")
    title = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)  # Dairy, Textiles, Retail, Poultry, Agro-machinery
    price = Column(Float, nullable=False)
    cost_price = Column(Float, default=0.0)  # For seller profit analytics
    stock = Column(Integer, default=50)
    description = Column(String, default="")
    image_url = Column(String, default="")
    sales_count = Column(Integer, default=0)
    rating = Column(Float, default=4.8)
    is_top_selling = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    customer_name = Column(String, default="Ramesh Patil")
    seller_id = Column(Integer, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_title = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="Confirmed")  # Confirmed, Dispatched, Delivered
    created_at = Column(DateTime, default=datetime.utcnow)
