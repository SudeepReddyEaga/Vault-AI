import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Section 9 Prometheus Instrumentation Code
HTTP_REQUEST_COUNTER = Counter(
    "pba_http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status_code"]
)

AGENT_TOOL_COUNTER = Counter(
    "pba_agent_tool_executions_total",
    "Total Tool Execution Count",
    ["tool_name", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "pba_http_request_duration_seconds",
    "HTTP Request Latency",
    ["endpoint"]
)

BUDGET_BALANCE_GAUGE = Gauge(
    "pba_budget_balance_amount",
    "Current live user balance in USD"
)

REDIS_CACHE_HITS = Counter(
    "pba_redis_cache_hits_total",
    "Total Redis Cache Hits"
)

REDIS_CACHE_MISSES = Counter(
    "pba_redis_cache_misses_total",
    "Total Redis Cache Misses"
)

app = FastAPI(title="VaultAI - Budget API Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# External service URLs (Env configurable for Docker/K8s/AWS)
AI_AGENT_URL = os.getenv("AI_AGENT_URL", "http://localhost:5001")
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://localhost:5002")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword2026@localhost:5432/rural_platform_db")

# In-Memory Deterministic Ledger (BudgetMemory)
class BudgetMemoryStore:
    def __init__(self):
        self.income = 4500.0
        self.savings_goal = 900.0
        self.category_budgets = {
            "Food": 800.0,
            "Housing": 1200.0,
            "Travel": 400.0,
            "Tech": 500.0,
            "Utilities": 300.0,
            "General": 400.0
        }
        self.expenses: List[Dict[str, Any]] = [
            {"item": "Weekly Groceries", "amount": 142.50, "category": "Food", "date": datetime.now().strftime("%Y-%m-%d")},
            {"item": "Fiber Internet Bill", "amount": 65.00, "category": "Utilities", "date": datetime.now().strftime("%Y-%m-%d")},
            {"item": "Subway Transit Pass", "amount": 45.00, "category": "Travel", "date": datetime.now().strftime("%Y-%m-%d")},
            {"item": "Cloud IDE Subscription", "amount": 20.00, "category": "Tech", "date": datetime.now().strftime("%Y-%m-%d")}
        ]

    def get_summary(self):
        total_spent = sum(e["amount"] for e in self.expenses)
        balance = self.income - total_spent
        cat_spending = {}
        for e in self.expenses:
            c = e.get("category", "General")
            cat_spending[c] = cat_spending.get(c, 0.0) + e["amount"]

        warnings = []
        category_status = []
        for cat, limit in self.category_budgets.items():
            spent = cat_spending.get(cat, 0.0)
            is_over = spent > limit
            pct = (spent / limit * 100) if limit > 0 else 0
            category_status.append({
                "category": cat,
                "limit": limit,
                "spent": spent,
                "remaining": limit - spent,
                "percentage": min(round(pct, 1), 100),
                "is_overspent": is_over
            })
            if is_over:
                warnings.append(f"⚠️ Category '{cat}' is overspent! Limit: ${limit:.2f}, Spent: ${spent:.2f}")

        BUDGET_BALANCE_GAUGE.set(balance)
        return {
            "income": self.income,
            "total_spent": round(total_spent, 2),
            "balance": round(balance, 2),
            "savings_goal": self.savings_goal,
            "savings_status": "On track" if balance >= self.savings_goal else f"Short by ${self.savings_goal - balance:.2f}",
            "expenses": self.expenses,
            "category_budgets": self.category_budgets,
            "category_spending": cat_spending,
            "category_status": category_status,
            "warnings": warnings
        }

memory_store = BudgetMemoryStore()

# Middleware for Prometheus HTTP request metrics
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    endpoint = request.url.path
    status_code = str(response.status_code)

    HTTP_REQUEST_COUNTER.labels(method=request.method, endpoint=endpoint, status_code=status_code).inc()
    HTTP_REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
    return response

# Schemas
class ExpenseCreate(BaseModel):
    item: str
    amount: float
    category: Optional[str] = "General"
    date: Optional[str] = None

class IncomeUpdate(BaseModel):
    amount: float

class CategoryBudgetUpdate(BaseModel):
    category: str
    amount: float

class SavingsGoalUpdate(BaseModel):
    amount: float

class ChatInput(BaseModel):
    message: str

class AffordabilityInput(BaseModel):
    item: str
    cost: float
    category: Optional[str] = "General"

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "budget-api-service",
        "port": 5000,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "ai_agent_copilot": AI_AGENT_URL,
            "ml_forecast_engine": ML_ENGINE_URL
        }
    }

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/state")
def get_state():
    summary = memory_store.get_summary()
    # Call ML forecast engine
    ml_forecast = None
    try:
        r = requests.post(f"{ML_ENGINE_URL}/api/ml/predict", json={
            "expenses": memory_store.expenses,
            "category_budgets": memory_store.category_budgets,
            "income": memory_store.income,
            "savings_goal": memory_store.savings_goal
        }, timeout=2)
        if r.status_code == 200:
            ml_forecast = r.json()
    except Exception:
        ml_forecast = {
            "predicted_next_month_total": round(summary["total_spent"] * 1.08, 2),
            "trend_percentage": 8.0,
            "trend_direction": "UP",
            "health_score": {"score": 88, "rating": "EXCELLENT"}
        }

    summary["ml_predictions"] = ml_forecast
    return {"status": "success", "data": summary}

@app.get("/api/summary")
def get_summary_endpoint():
    AGENT_TOOL_COUNTER.labels(tool_name="get_summary", status="executed").inc()
    return memory_store.get_summary()

@app.post("/api/income")
def set_income(inc: IncomeUpdate):
    AGENT_TOOL_COUNTER.labels(tool_name="set_income", status="executed").inc()
    memory_store.income = inc.amount
    return {"status": "success", "message": f"Monthly income set to ${inc.amount:.2f}", "data": memory_store.get_summary()}

@app.post("/api/savings_goal")
def set_savings_goal(goal: SavingsGoalUpdate):
    AGENT_TOOL_COUNTER.labels(tool_name="set_savings_goal", status="executed").inc()
    memory_store.savings_goal = goal.amount
    return {"status": "success", "message": f"Savings goal set to ${goal.amount:.2f}", "data": memory_store.get_summary()}

@app.post("/api/category_budget")
def set_category_budget(cat: CategoryBudgetUpdate):
    AGENT_TOOL_COUNTER.labels(tool_name="set_category_budget", status="executed").inc()
    memory_store.category_budgets[cat.category] = cat.amount
    return {"status": "success", "message": f"Category '{cat.category}' budget set to ${cat.amount:.2f}", "data": memory_store.get_summary()}

@app.post("/api/expense")
def add_expense(exp: ExpenseCreate):
    AGENT_TOOL_COUNTER.labels(tool_name="add_expense", status="executed").inc()
    if exp.amount <= 0 or not exp.item.strip():
        raise HTTPException(status_code=400, detail="Invalid item name or amount")

    entry = {
        "item": exp.item.strip(),
        "amount": exp.amount,
        "category": exp.category or "General",
        "date": exp.date or datetime.now().strftime("%Y-%m-%d")
    }
    memory_store.expenses.append(entry)
    return {
        "status": "success",
        "message": f"Recorded expense: {entry['item']} (${entry['amount']:.2f}) under {entry['category']}",
        "data": memory_store.get_summary()
    }

@app.get("/api/expenses")
def list_expenses():
    return {"status": "success", "expenses": memory_store.expenses}

@app.post("/api/affordability")
def check_affordability(aff: AffordabilityInput):
    # Delegate to ai-agent-copilot
    try:
        summary = memory_store.get_summary()
        cat_spent = summary["category_spending"].get(aff.category, 0.0)
        cat_limit = memory_store.category_budgets.get(aff.category, 500.0)
        r = requests.post(f"{AI_AGENT_URL}/api/agent/affordability", json={
            "item": aff.item,
            "cost": aff.cost,
            "category": aff.category,
            "income": memory_store.income,
            "total_spent": summary["total_spent"],
            "category_spent": cat_spent,
            "category_limit": cat_limit
        }, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    # Local fallback logic (Section 5.1 Formulation)
    AGENT_TOOL_COUNTER.labels(tool_name="check_affordability", status="executed").inc()
    total_spent = sum(e["amount"] for e in memory_store.expenses)
    balance = memory_store.income - total_spent
    cat_spent = sum(e["amount"] for e in memory_store.expenses if e.get("category") == aff.category)
    cat_limit = memory_store.category_budgets.get(aff.category, 500.0)
    status = "APPROVED" if (aff.cost <= balance and (cat_spent + aff.cost) <= cat_limit) else "REJECTED"
    return {
        "item": aff.item,
        "cost": aff.cost,
        "category": aff.category,
        "status": status,
        "balance_before": balance,
        "balance_after": balance - aff.cost if status == "APPROVED" else balance,
        "verdict": f"Affordability calculation: {status} (Balance: ${balance:.2f}, Limit: ${cat_limit:.2f})"
    }

@app.post("/api/chat")
def chat_copilot(chat_in: ChatInput):
    # Forward to ai-agent-copilot
    try:
        r = requests.post(f"{AI_AGENT_URL}/api/agent/chat", json={
            "message": chat_in.message,
            "state": memory_store.get_summary()
        }, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    # Local fallback
    AGENT_TOOL_COUNTER.labels(tool_name="get_summary", status="executed").inc()
    return {
        "response": f"Processed: '{chat_in.message}'. Current live balance is ${memory_store.income - sum(e['amount'] for e in memory_store.expenses):.2f}.",
        "tool_trace": ["get_summary"],
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
