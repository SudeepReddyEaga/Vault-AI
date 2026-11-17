import os
import sys
import json
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import jwt
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add current folder to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import BudgetAgent, BudgetMemory
from ml_engine import BudgetPredictor

app = FastAPI(title="GraminUdyam - Personal Budget Assistant Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-rural-enterprise-jwt-key-2026")
JWT_ALGORITHM = "HS256"

def fallback_decode_jwt(token_str: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token_str.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            rem = len(payload_b64) % 4
            if rem > 0:
                payload_b64 += "=" * (4 - rem)
            return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        pass
    return None

# In-memory store of user agents: user_id or email -> BudgetAgent
user_agents: Dict[str, BudgetAgent] = {}
ml_predictor = BudgetPredictor()

def decode_user_jwt(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extracts user information from Bearer JWT token"""
    if not authorization:
        # Fallback to default demo user profile
        return {
            "sub": "ramesh.dairy@rural.in",
            "name": "Ramesh Patil",
            "role": "customer",
            "user_id": 1,
            "margin_capital": 100000.0,
            "business_category": "Dairy"
        }
    
    token = authorization.replace("Bearer ", "").strip()
    if HAS_PYJWT:
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            pass

    # Fallback decode
    decoded = fallback_decode_jwt(token)
    if decoded and isinstance(decoded, dict):
        return decoded

    return {
        "sub": "ramesh.dairy@rural.in",
        "name": "Ramesh Patil",
        "role": "customer",
        "user_id": 1,
        "margin_capital": 100000.0,
        "business_category": "Dairy"
    }

def get_or_create_user_agent(user_info: Dict[str, Any]) -> BudgetAgent:
    user_key = str(user_info.get("sub", user_info.get("user_id", "default_user")))
    if user_key not in user_agents:
        agent = BudgetAgent()
        # Seed initial sensible baseline synced with their margin capital if available
        margin = float(user_info.get("margin_capital", 100000.0))
        # Initial personal monthly drawing / income estimate (e.g. 35% of monthly revenue)
        estimated_monthly_income = max(35000.0, margin * 0.35)
        agent.memory.set_income(estimated_monthly_income)
        user_agents[user_key] = agent
    return user_agents[user_key]

# Pydantic Schemas
class ExpenseIn(BaseModel):
    item: str
    amount: float
    category: str = "General"
    date: Optional[str] = None

class IncomeIn(BaseModel):
    amount: float

class CategoryBudgetIn(BaseModel):
    category: str
    amount: float

class SavingsGoalIn(BaseModel):
    amount: float

class AffordabilityIn(BaseModel):
    item: str
    cost: float
    category: Optional[str] = "General"

class ChatIn(BaseModel):
    message: str

class AutoSetupIn(BaseModel):
    monthly_income: Optional[float] = None
    savings_target: Optional[float] = None

@app.get("/health")
def health():
    return {"status": "ok", "service": "personal-budget-service", "port": 8006, "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/budget/state")
def get_budget_state(user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    """
    Returns full state of user's personal budget assistant,
    evaluating missing fields, ML predictions, and category overspends.
    """
    agent = get_or_create_user_agent(user_info)
    mem = agent.memory

    total_spent = sum(e["amount"] for e in mem.expenses)
    balance = mem.income - total_spent

    # Check for missing fields
    missing_fields = []
    if mem.income <= 0:
        missing_fields.append("Monthly Income")
    if not mem.category_budgets:
        missing_fields.append("Category Budgets (Food, Housing, Travel, etc.)")
    if mem.savings_goal <= 0:
        missing_fields.append("Target Savings Goal")
    if len(mem.expenses) == 0:
        missing_fields.append("Recent Expense Records")

    has_missing_fields = len(missing_fields) > 0

    # Category breakdown
    cat_spending = {}
    for e in mem.expenses:
        c = e.get("category", "General")
        cat_spending[c] = cat_spending.get(c, 0.0) + float(e["amount"])

    category_status = []
    warnings = []
    for cat, limit in mem.category_budgets.items():
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
            warnings.append(f"⚠️ Category '{cat}' is overspent! Limit: ₹{limit:,.2f}, Spent: ₹{spent:,.2f}")

    savings_status = "No goal set"
    if mem.savings_goal > 0:
        if balance >= mem.savings_goal:
            savings_status = f"On track! (Balance ₹{balance:,.2f} >= Goal ₹{mem.savings_goal:,.2f})"
        else:
            diff = mem.savings_goal - balance
            savings_status = f"Short by ₹{diff:,.2f} (Goal: ₹{mem.savings_goal:,.2f})"
            warnings.append(f"🎯 Savings Goal Notice: Short by ₹{diff:,.2f} to hit target ₹{mem.savings_goal:,.2f}")

    # ML Predictions
    ml_data = ml_predictor.predict(mem.expenses, mem.category_budgets, mem.income, mem.savings_goal)

    return {
        "user_name": user_info.get("name", "Beneficiary"),
        "user_email": user_info.get("sub", ""),
        "income": mem.income,
        "total_spent": total_spent,
        "balance": balance,
        "savings_goal": mem.savings_goal,
        "savings_status": savings_status,
        "expenses": mem.expenses,
        "category_budgets": mem.category_budgets,
        "category_spending": cat_spending,
        "category_status": category_status,
        "warnings": warnings,
        "has_missing_fields": has_missing_fields,
        "missing_fields": missing_fields,
        "ml_forecast": ml_data,
        "offline_mode": agent.offline_mode
    }

@app.post("/api/budget/generate-report")
def generate_auto_report(setup: AutoSetupIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    """
    Auto-generates recommended budget, category caps, savings target,
    and seed baseline expenses synced with the user's enterprise profile.
    """
    agent = get_or_create_user_agent(user_info)
    mem = agent.memory

    margin = float(user_info.get("margin_capital", 100000.0))
    monthly_inc = setup.monthly_income if setup.monthly_income and setup.monthly_income > 0 else max(38000.0, margin * 0.38)
    mem.set_income(monthly_inc)

    # 50-30-20 Rule for Personal Finance
    # Needs (50%): Housing, Groceries/Food, Utilities
    # Wants (30%): Personal, Travel, Subscriptions
    # Savings (20%): Reserve fund
    mem.set_category_budget("Food & Groceries", round(monthly_inc * 0.25, 2))
    mem.set_category_budget("Household & Utilities", round(monthly_inc * 0.20, 2))
    mem.set_category_budget("Travel & Transport", round(monthly_inc * 0.12, 2))
    mem.set_category_budget("Personal & General", round(monthly_inc * 0.13, 2))
    mem.set_category_budget("Health & Emergency", round(monthly_inc * 0.10, 2))

    savings = setup.savings_target if setup.savings_target and setup.savings_target > 0 else round(monthly_inc * 0.20, 2)
    mem.set_savings_goal(savings)

    # Add realistic starter expenses if empty
    if len(mem.expenses) == 0:
        today = datetime.now().strftime("%Y-%m-%d")
        mem.add_expense("Monthly Village Ration & Groceries", round(monthly_inc * 0.15, 2), "Food & Groceries", today)
        mem.add_expense("Electricity & Water Utility Bill", round(monthly_inc * 0.06, 2), "Household & Utilities", today)
        mem.add_expense("Motorcycle Fuel & Local Bus Pass", round(monthly_inc * 0.04, 2), "Travel & Transport", today)

    return {
        "status": "success",
        "message": f"Successfully generated personal financial budget report tailored for {user_info.get('name', 'Beneficiary')}! Monthly income set to ₹{monthly_inc:,.2f} with 5 category limits and savings target ₹{savings:,.2f}.",
        "state": get_budget_state(user_info)
    }

@app.post("/api/budget/chat")
def chat_with_agent(chat_in: ChatIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    """
    Executes ReAct plan-act loop with BudgetAgent,
    returning transparent step-by-step tool calls and conversational response.
    """
    agent = get_or_create_user_agent(user_info)
    user_msg = chat_in.message.strip()

    # Run agent loop
    result = agent.run(user_msg)

    # Tool trace extraction
    tool_trace = result.get("tool_trace", [])
    if not tool_trace and "executed_tools" in result:
        tool_trace = result["executed_tools"]

    return {
        "response": result.get("response", "Action executed."),
        "tool_trace": tool_trace,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/budget/expense")
def add_expense(exp: ExpenseIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    msg = agent.memory.add_expense(exp.item, exp.amount, exp.category, exp.date)
    return {"message": msg, "state": get_budget_state(user_info)}

@app.post("/api/budget/income")
def set_income(inc: IncomeIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    msg = agent.memory.set_income(inc.amount)
    return {"message": msg, "state": get_budget_state(user_info)}

@app.post("/api/budget/category-budget")
def set_category_budget(cat: CategoryBudgetIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    msg = agent.memory.set_category_budget(cat.category, cat.amount)
    return {"message": msg, "state": get_budget_state(user_info)}

@app.post("/api/budget/savings-goal")
def set_savings_goal(goal: SavingsGoalIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    msg = agent.memory.set_savings_goal(goal.amount)
    return {"message": msg, "state": get_budget_state(user_info)}

@app.post("/api/budget/affordability")
def check_affordability(item_in: AffordabilityIn, user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    res = agent.memory.check_affordability(item_in.item, item_in.cost, item_in.category or "General")
    return {"result": res}

@app.post("/api/budget/undo")
def undo_last_action(user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    msg = agent.memory.undo_last_action()
    return {"message": msg, "state": get_budget_state(user_info)}

@app.post("/api/budget/reset")
def reset_memory(user_info: Dict[str, Any] = Depends(decode_user_jwt)):
    agent = get_or_create_user_agent(user_info)
    msg = agent.memory.reset_memory()
    return {"message": msg, "state": get_budget_state(user_info)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
