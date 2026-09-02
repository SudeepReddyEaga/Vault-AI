import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Ensure current folder is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import BudgetAgent, BudgetMemory
from ml_engine import BudgetPredictor

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Global Agent and ML Predictor Instances
global_agent = BudgetAgent()
ml_predictor = BudgetPredictor()

def get_state_dict(year=None, month=None):
    if year is None and request:
        try:
            year = request.args.get("year") or (request.get_json() or {}).get("year")
        except Exception:
            pass
    if month is None and request:
        try:
            month = request.args.get("month") or (request.get_json() or {}).get("month")
        except Exception:
            pass

    mem = global_agent.memory

    # Filter expenses by year and month if provided
    scoped_expenses = mem.expenses
    if year and str(year).lower() != "all" and month and str(month).lower() != "all":
        try:
            prefix = f"{int(year):04d}-{int(month):02d}"
            scoped_expenses = [e for e in mem.expenses if e.get("date", "").startswith(prefix)]
        except Exception:
            scoped_expenses = mem.expenses
    elif year and str(year).lower() != "all":
        try:
            prefix = f"{int(year):04d}-"
            scoped_expenses = [e for e in mem.expenses if e.get("date", "").startswith(prefix)]
        except Exception:
            scoped_expenses = mem.expenses

    total_spent = sum(e["amount"] for e in scoped_expenses)
    balance = mem.income - total_spent
    
    # Calculate category spending breakdown for scoped expenses
    cat_spending = {}
    for e in scoped_expenses:
        c = e.get("category", "General")
        cat_spending[c] = cat_spending.get(c, 0.0) + float(e["amount"])
        
    # Check overspent categories for scoped expenses
    warnings = []
    category_status = []
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
            warnings.append(f"⚠️ Category '{cat}' is overspent! Limit: ${limit:,.2f}, Spent: ${spent:,.2f}")

    # Check savings goal status
    savings_status = "No goal set"
    if mem.savings_goal > 0:
        if balance >= mem.savings_goal:
            savings_status = f"On track! (Balance ${balance:,.2f} >= Goal ${mem.savings_goal:,.2f})"
        else:
            diff = mem.savings_goal - balance
            savings_status = f"Short by ${diff:,.2f} (Goal: ${mem.savings_goal:,.2f})"
            warnings.append(f"🎯 Savings Goal Notice: Short by ${diff:,.2f} to hit target ${mem.savings_goal:,.2f}")

    # Run ML Prediction Engine
    ml_data = ml_predictor.predict(scoped_expenses, mem.category_budgets, mem.income, mem.savings_goal)

    return {
        "income": mem.income,
        "total_spent": total_spent,
        "balance": balance,
        "savings_goal": mem.savings_goal,
        "savings_status": savings_status,
        "expenses": mem.expenses,
        "filtered_expenses": scoped_expenses,
        "category_budgets": mem.category_budgets,
        "category_status": category_status,
        "category_spending": cat_spending,
        "warnings": warnings,
        "offline_mode": global_agent.offline_mode,
        "ml_predictions": ml_data,
        "selected_year": year,
        "selected_month": month
    }


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state", methods=["GET"])
def api_state():
    y = request.args.get("year")
    m = request.args.get("month")
    return jsonify({"status": "success", "data": get_state_dict(y, m)})


@app.route("/api/income", methods=["POST"])
def api_set_income():
    data = request.get_json() or {}
    try:
        amt = float(data.get("amount", 0))
        msg = global_agent.memory.set_income(amt)
        return jsonify({"status": "success", "message": msg, "data": get_state_dict()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/savings_goal", methods=["POST"])
def api_set_savings_goal():
    data = request.get_json() or {}
    try:
        amt = float(data.get("amount", 0))
        msg = global_agent.memory.set_savings_goal(amt)
        return jsonify({"status": "success", "message": msg, "data": get_state_dict()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/category_budget", methods=["POST"])
def api_set_category_budget():
    data = request.get_json() or {}
    try:
        category = str(data.get("category", "")).strip()
        amt = float(data.get("amount", 0))
        if not category:
            return jsonify({"status": "error", "message": "Category name required"}), 400
        msg = global_agent.memory.set_category_budget(category, amt)
        return jsonify({"status": "success", "message": msg, "data": get_state_dict()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/expense", methods=["POST"])
def api_add_expense():
    data = request.get_json() or {}
    try:
        item = str(data.get("item", "")).strip()
        amt = float(data.get("amount", 0))
        category = str(data.get("category", "General")).strip()
        if not item or amt <= 0:
            return jsonify({"status": "error", "message": "Valid item name and amount > 0 required"}), 400
        msg = global_agent.memory.add_expense(item, amt, category)
        return jsonify({"status": "success", "message": msg, "data": get_state_dict()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/expense/delete", methods=["POST"])
def api_delete_expense():
    data = request.get_json() or {}
    try:
        idx = int(data.get("index", -1))
        item_name = data.get("item")
        year = data.get("year") or request.args.get("year")
        month = data.get("month") or request.args.get("month")

        if 0 <= idx < len(global_agent.memory.expenses):
            deleted = global_agent.memory.expenses.pop(idx)
            return jsonify({"status": "success", "message": f"Deleted '{deleted['item']}'", "data": get_state_dict(year, month)})
        elif item_name and str(item_name).strip():
            msg = global_agent.memory.delete_expense(str(item_name))
            return jsonify({"status": "success", "message": msg, "data": get_state_dict(year, month)})
        return jsonify({"status": "error", "message": "Invalid expense index or item"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/expense/edit", methods=["POST"])
def api_edit_expense():
    data = request.get_json() or {}
    try:
        idx = int(data.get("index", -1))
        item_name = data.get("item_name")
        amt = float(data["amount"]) if ("amount" in data and data["amount"] is not None) else None
        year = data.get("year") or request.args.get("year")
        month = data.get("month") or request.args.get("month")
        msg = global_agent.memory.edit_expense(
            index=idx if idx >= 0 else None,
            item_name=item_name,
            item=data.get("item"),
            amount=amt,
            category=data.get("category"),
            date=data.get("date")
        )
        if "Successfully updated" in msg:
            return jsonify({"status": "success", "message": msg, "data": get_state_dict(year, month)})
        return jsonify({"status": "error", "message": msg}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400



@app.route("/api/calendar", methods=["GET"])
def api_get_calendar():
    from datetime import datetime
    try:
        year = int(request.args.get("year", datetime.now().year))
        month = int(request.args.get("month", datetime.now().month))
        monthly_info = global_agent.memory.get_monthly_expenses(year, month)
        
        # Aggregate daily totals
        daily_totals = {}
        for e in monthly_info["expenses"]:
            d = e.get("date", "")
            daily_totals[d] = daily_totals.get(d, 0.0) + e["amount"]
            
        return jsonify({
            "status": "success",
            "year": year,
            "month": month,
            "expenses": monthly_info["expenses"],
            "total_spent": monthly_info["total_spent"],
            "daily_totals": daily_totals
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/yearly", methods=["GET"])
def api_get_yearly():
    from datetime import datetime
    try:
        year = int(request.args.get("year", datetime.now().year))
        yearly_info = global_agent.memory.get_yearly_summary(year)
        return jsonify({
            "status": "success",
            "year": year,
            "monthly_totals": yearly_info["monthly_totals"],
            "total_spent": yearly_info["total_spent"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/affordability", methods=["POST"])
def api_check_affordability():
    data = request.get_json() or {}
    try:
        item = str(data.get("item", "Item")).strip()
        cost = float(data.get("cost", 0))
        category = str(data.get("category", "General")).strip()
        
        mem = global_agent.memory
        total_spent = sum(e["amount"] for e in mem.expenses)
        curr_balance = mem.income - total_spent
        rem_balance = curr_balance - cost
        affordable = curr_balance >= cost
        
        cat_spent = sum(e["amount"] for e in mem.expenses if e.get("category", "").lower() == category.lower())
        cat_limit = mem.category_budgets.get(category, 0)
        cat_overspent = (cat_limit > 0) and ((cat_spent + cost) > cat_limit)
        
        return jsonify({
            "status": "success",
            "item": item,
            "cost": cost,
            "category": category,
            "affordable": affordable,
            "current_balance": curr_balance,
            "remaining_balance": rem_balance,
            "category_limit": cat_limit,
            "category_spent_after": cat_spent + cost,
            "category_overspent_warning": cat_overspent,
            "data": get_state_dict()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    user_msg = str(data.get("message", "")).strip()
    year = data.get("year") or request.args.get("year")
    month = data.get("month") or request.args.get("month")
    if not user_msg:
        return jsonify({"status": "error", "message": "Empty message"}), 400
        
    try:
        res = global_agent.chat_with_trace(user_msg)
        
        trace_y, trace_m = None, None
        if res.get("trace"):
            for t in res["trace"]:
                if t.get("args", {}).get("year") and t.get("args", {}).get("month"):
                    trace_y = t["args"]["year"]
                    trace_m = t["args"]["month"]
                    break
                dt_str = t.get("args", {}).get("date")
                if dt_str:
                    import re
                    m_match = re.search(r'(\d{4})[\-\/](\d{1,2})', str(dt_str))
                    if m_match:
                        trace_y = int(m_match.group(1))
                        trace_m = int(m_match.group(2))
                        break

        eff_year = trace_y or year
        eff_month = trace_m or month

        return jsonify({
            "status": "success",
            "response": res["response"],
            "trace": res["trace"],
            "data": get_state_dict(eff_year, eff_month)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def api_reset():
    global global_agent
    global_agent.memory = BudgetMemory()
    global_agent.chat_history = [{"role": "system", "content": global_agent.system_prompt}]
    return jsonify({"status": "success", "message": "Budget memory reset successfully", "data": get_state_dict()})

@app.route("/api/undo", methods=["POST"])
def api_undo():
    msg = global_agent.memory.undo_last_action()
    return jsonify({"status": "success", "message": msg, "data": get_state_dict()})


@app.route("/api/ml/predict", methods=["GET", "POST"])
def api_ml_predict():
    mem = global_agent.memory
    ml_data = ml_predictor.predict(mem.expenses, mem.category_budgets, mem.income, mem.savings_goal)
    return jsonify({"status": "success", "ml": ml_data, "data": get_state_dict()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Personal Budget Assistant Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)


