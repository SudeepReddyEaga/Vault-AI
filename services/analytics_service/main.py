from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ml_analytics import analytics_engine

app = FastAPI(title="Rural Enterprise Platform - Analytics ML Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomerAnalyticsRequest(BaseModel):
    margin_capital: float = 100000.0
    business_category: str = "Dairy"
    current_spending: Optional[float] = 0.0

class SellerAnalyticsRequest(BaseModel):
    seller_id: int = 2

@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service", "timestamp": datetime.utcnow().isoformat()}

@app.post("/analytics/customer-spending")
def get_customer_spending_analytics(req: CustomerAnalyticsRequest):
    """
    ML model for customer financial spending:
    Computes DSCR, working capital runway, cash flow projection, and Financial Health Score
    """
    res = analytics_engine.compute_customer_spending_analytics(
        margin_capital=req.margin_capital,
        business_category=req.business_category,
        current_spending=req.current_spending or 0.0
    )
    return res

@app.post("/analytics/seller-sales")
def get_seller_sales_analytics(req: SellerAnalyticsRequest):
    """
    ML model for seller sales & profit:
    Uses Linear Regression to forecast next 30/60/90 days revenue, gross profit, and margin matrix
    """
    res = analytics_engine.compute_seller_sales_analytics(seller_id=req.seller_id)
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
