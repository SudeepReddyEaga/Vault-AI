from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from recommender_engine import recommender

app = FastAPI(title="Rural Enterprise Platform - Recommendation ML Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomerRecRequest(BaseModel):
    category: str = "Dairy"
    margin_capital: float = 100000.0
    location: Optional[str] = "Baramati, Pune"

class SellerRecRequest(BaseModel):
    seller_id: int = 2

@app.get("/health")
def health():
    return {"status": "ok", "service": "recommendation-service", "timestamp": datetime.utcnow().isoformat()}

@app.post("/recommend/customer")
def get_customer_recommendations(req: CustomerRecRequest):
    """
    ML model for customer:
    Recommends essential equipment, supplies, and high-ROI strategies matching their proposed category and margin budget
    """
    res = recommender.recommend_for_customer(
        category=req.category,
        margin_capital=req.margin_capital,
        location=req.location or ""
    )
    return res

@app.post("/recommend/seller")
def get_seller_recommendations(req: SellerRecRequest):
    """
    ML model for seller:
    Recommends top-selling goods, turnover metrics, and high-demand inventory expansion opportunities
    """
    res = recommender.recommend_for_seller(seller_id=req.seller_id)
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
