from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, get_db, Base
from models import Product, Order
from redis_cache import cache_manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rural Enterprise Platform - Marketplace Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class ProductCreate(BaseModel):
    seller_id: int = 2
    seller_name: str = "Kisan Agro Machinery"
    title: str
    category: str
    price: float
    cost_price: Optional[float] = None
    stock: int = 20
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    is_top_selling: Optional[bool] = False

class OrderCreate(BaseModel):
    customer_id: int = 1
    customer_name: str = "Ramesh Patil"
    product_id: int
    quantity: int = 1

# Seed rural demo products
@app.on_event("startup")
def seed_marketplace_products():
    db = next(get_db())
    try:
        count = db.query(Product).count()
        if count == 0:
            sample_products = [
                # Dairy
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Heavy Duty Automatic Milking Claw Unit", category="Dairy", price=18500.0, cost_price=12000.0, stock=25, description="Food-grade stainless steel cluster with high-durability pulsation line for 8-12 cows.", image_url="https://images.unsplash.com/photo-1527153857715-3908f2bae5e8?w=500&auto=format&fit=crop", sales_count=142, rating=4.9, is_top_selling=True),
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Micro Bulk Milk Cooler (100L Chiller)", category="Dairy", price=65000.0, cost_price=48000.0, stock=10, description="Rapid cooling from 35C to 4C in 2 hours. R134a eco refrigerant with thermal insulation.", image_url="https://images.unsplash.com/photo-1587293852726-70cdb56c2866?w=500&auto=format&fit=crop", sales_count=88, rating=4.8, is_top_selling=True),
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Enriched High-Protein Cattle Feed (50kg Bag)", category="Dairy", price=1450.0, cost_price=1100.0, stock=200, description="Contains bypass fat, minerals, vitamins, 22% crude protein for boosting milk yield by 15%.", image_url="https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=500&auto=format&fit=crop", sales_count=520, rating=4.9, is_top_selling=True),
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Ultrasonic Digital Milk Fat & SNF Analyzer", category="Dairy", price=24000.0, cost_price=17500.0, stock=15, description="Instant 30-second testing of fat %, SNF, density, and added water percentage.", image_url="https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500&auto=format&fit=crop", sales_count=65, rating=4.7, is_top_selling=False),
                
                # Textiles
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Industrial Direct-Drive High-Speed Sewing Machine", category="Textiles", price=19200.0, cost_price=13800.0, stock=30, description="Low-power servo motor with auto-trimmer, LED worklight, 5000 stitches/min.", image_url="https://images.unsplash.com/photo-1528458908752-6786cf88b9bf?w=500&auto=format&fit=crop", sales_count=190, rating=4.9, is_top_selling=True),
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="5-Thread Interlock Overedging Machine", category="Textiles", price=28000.0, cost_price=20500.0, stock=12, description="Heavy-duty hemming and edge-stitching for school uniform shirts, pants, and blouses.", image_url="https://images.unsplash.com/photo-1605518216938-7c31b7b14ad0?w=500&auto=format&fit=crop", sales_count=74, rating=4.6, is_top_selling=False),

                # Retail & Processing
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Compact Commercial Cold-Press Oil Expeller", category="Agro-processing", price=45000.0, cost_price=33000.0, stock=8, description="Pure mustard, groundnut, and sesame oil extraction with 42% yield rate.", image_url="https://images.unsplash.com/photo-1471193945509-9ad0617afabf?w=500&auto=format&fit=crop", sales_count=43, rating=4.8, is_top_selling=False),
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Continuous Band Nitrogen Bag Sealer", category="Retail", price=14800.0, cost_price=10200.0, stock=18, description="Airtight packaging for village spices, pulses, chips, and snacks with batch coding.", image_url="https://images.unsplash.com/photo-1530587191325-3db32d826c18?w=500&auto=format&fit=crop", sales_count=110, rating=4.7, is_top_selling=True),

                # Poultry & Solar
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="Automatic 500-Egg Poultry Incubator with Hatcher", category="Poultry", price=32000.0, cost_price=23000.0, stock=10, description="Digital humidity and temperature PID micro-controller with auto-turning rollers.", image_url="https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=500&auto=format&fit=crop", sales_count=52, rating=4.6, is_top_selling=False),
                Product(seller_id=2, seller_name="Kisan Agro Machinery", title="3HP Solar Water Pump System for Rural Enterprises", category="Agro-machinery", price=85000.0, cost_price=64000.0, stock=14, description="DC submersible pump with MPPT controller and mono-perc panels for zero-grid irrigation.", image_url="https://images.unsplash.com/photo-1509391365360-2e959784a276?w=500&auto=format&fit=crop", sales_count=98, rating=4.9, is_top_selling=True)
            ]
            db.add_all(sample_products)
            db.commit()
            print("Seeded 10 enterprise products into Marketplace DB.")
    except Exception as e:
        db.rollback()
        print(f"Product seed notice: {e}")
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "service": "marketplace-service", "timestamp": datetime.utcnow().isoformat()}

@app.get("/products/top-selling")
def get_top_selling_products(db: Session = Depends(get_db)):
    """
    Retrieves top-selling products using Redis cache for sub-millisecond response
    """
    cache_key = "marketplace:top_selling_products"
    cached = cache_manager.get(cache_key)
    if cached:
        return {"source": "redis_cache", "products": cached}

    # Fetch from database
    products = db.query(Product).order_by(Product.sales_count.desc()).limit(6).all()
    res = [
        {
            "id": p.id,
            "seller_id": p.seller_id,
            "seller_name": p.seller_name,
            "title": p.title,
            "category": p.category,
            "price": p.price,
            "cost_price": p.cost_price,
            "stock": p.stock,
            "description": p.description,
            "image_url": p.image_url,
            "sales_count": p.sales_count,
            "rating": p.rating,
            "is_top_selling": p.is_top_selling
        }
        for p in products
    ]
    # Cache in Redis with 120s TTL
    cache_manager.set(cache_key, res, ttl_seconds=120)
    return {"source": "database_cached_to_redis", "products": res}

@app.get("/products")
def list_products(
    category: Optional[str] = None,
    seller_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    cache_key = f"marketplace:products:cat_{category or 'all'}:seller_{seller_id or 'all'}"
    cached = cache_manager.get(cache_key)
    if cached:
        return {"source": "redis_cache", "products": cached}

    query = db.query(Product)
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if seller_id:
        query = query.filter(Product.seller_id == seller_id)

    products = query.order_by(Product.id.asc()).all()
    res = [
        {
            "id": p.id,
            "seller_id": p.seller_id,
            "seller_name": p.seller_name,
            "title": p.title,
            "category": p.category,
            "price": p.price,
            "cost_price": p.cost_price,
            "stock": p.stock,
            "description": p.description,
            "image_url": p.image_url,
            "sales_count": p.sales_count,
            "rating": p.rating,
            "is_top_selling": p.is_top_selling
        }
        for p in products
    ]
    cache_manager.set(cache_key, res, ttl_seconds=60)
    return {"source": "database_cached_to_redis", "products": res}

@app.post("/products")
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    cost = product_in.cost_price if product_in.cost_price else round(product_in.price * 0.72, 2)
    new_prod = Product(
        seller_id=product_in.seller_id,
        seller_name=product_in.seller_name,
        title=product_in.title,
        category=product_in.category,
        price=product_in.price,
        cost_price=cost,
        stock=product_in.stock,
        description=product_in.description or "",
        image_url=product_in.image_url or "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500&auto=format&fit=crop",
        is_top_selling=product_in.is_top_selling or False
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)

    # Invalidate caches
    cache_manager.delete("marketplace:top_selling_products")
    return new_prod

@app.post("/orders")
def place_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == order_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < order_in.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock available")

    total = product.price * order_in.quantity
    product.stock -= order_in.quantity
    product.sales_count += order_in.quantity

    new_order = Order(
        customer_id=order_in.customer_id,
        customer_name=order_in.customer_name,
        seller_id=product.seller_id,
        product_id=product.id,
        product_title=product.title,
        quantity=order_in.quantity,
        unit_price=product.price,
        total_price=total,
        status="Confirmed"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Invalidate cache
    cache_manager.delete("marketplace:top_selling_products")

    return {
        "order_id": new_order.id,
        "product_title": product.title,
        "quantity": order_in.quantity,
        "total_price": total,
        "status": new_order.status,
        "message": f"Order #{new_order.id} placed successfully! Beneficiary purchase recorded for SCA equipment tracking."
    }

@app.get("/orders/customer/{customer_id}")
def get_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.id.desc()).all()
    return orders

@app.get("/orders/seller/{seller_id}")
def get_seller_orders(seller_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.seller_id == seller_id).order_by(Order.id.desc()).all()
    return orders

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
