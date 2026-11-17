import numpy as np
from sklearn.linear_model import LinearRegression

class BudgetPredictor:
    """
    Machine Learning Spending Predictor & Trend Analytics Engine.
    Uses linear regression and trend analysis to forecast next month's spending,
    evaluate financial health metrics, and flag overspend anomaly risks.
    """
    def __init__(self):
        self.model = LinearRegression()

    def predict(self, expenses, category_budgets, income, savings_goal=0.0):
        """
        Calculates ML spending forecast and trend metrics based on historical expense logs.
        """
        total_spent = sum(e.get("amount", 0) for e in expenses)
        cat_spending = {}
        for e in expenses:
            c = e.get("category", "General")
            cat_spending[c] = cat_spending.get(c, 0.0) + float(e.get("amount", 0))

        # Time-series regression feature modeling
        # If few expense data points, apply statistical exponential smoothing & category weighting
        n_items = len(expenses)
        if n_items >= 3:
            X = np.array(range(1, n_items + 1)).reshape(-1, 1)
            y = np.array([e.get("amount", 0) for e in expenses])
            self.model.fit(X, y)
            
            # Predict velocity
            avg_per_item = float(np.mean(y))
            trend_slope = float(self.model.coef_[0])
            # Forecast next month estimated items (~ 15 items per month)
            predicted_total = max(total_spent, float(total_spent * (1.0 + min(0.35, max(-0.2, trend_slope / (avg_per_item + 1e-5))))))
        else:
            # Baseline heuristic + 8% trend buffer
            predicted_total = total_spent * 1.08 if total_spent > 0 else (income * 0.4 if income > 0 else 500.0)

        # Category-wise predictions
        cat_predictions = {}
        risk_flags = []

        all_cats = set(list(cat_spending.keys()) + list(category_budgets.keys()))
        if not all_cats:
            all_cats = {"Food", "Housing", "Travel", "Subscriptions", "General"}

        for c in all_cats:
            spent = cat_spending.get(c, 0.0)
            limit = category_budgets.get(c, 0.0)
            
            # ML category growth factor
            if total_spent > 0:
                cat_weight = spent / total_spent
            else:
                cat_weight = 1.0 / len(all_cats)
                
            pred_cat_spent = max(spent, round(predicted_total * cat_weight, 2))
            cat_predictions[c] = pred_cat_spent

            if limit > 0 and pred_cat_spent > limit:
                diff = pred_cat_spent - limit
                risk_flags.append({
                    "category": c,
                    "limit": limit,
                    "predicted": pred_cat_spent,
                    "exceed_by": diff,
                    "severity": "HIGH" if diff > (limit * 0.2) else "MEDIUM"
                })

        # Calculate Financial Health Score (0 - 100)
        health_score = self.calculate_health_score(total_spent, income, savings_goal, category_budgets, cat_spending)

        # Trend trajectory (+/- %)
        trend_pct = round(((predicted_total - total_spent) / total_spent * 100), 1) if total_spent > 0 else 0.0

        return {
            "current_total_spent": round(total_spent, 2),
            "predicted_next_month_total": round(predicted_total, 2),
            "trend_percentage": trend_pct,
            "trend_direction": "UP" if trend_pct > 0 else ("DOWN" if trend_pct < 0 else "STABLE"),
            "category_predictions": cat_predictions,
            "risk_flags": risk_flags,
            "health_score": health_score
        }

    def calculate_health_score(self, total_spent, income, savings_goal, category_budgets, cat_spending):
        """
        Computes a Financial Health Index Score from 0 to 100.
        """
        score = 100.0

        # 1. Savings / Balance Ratio (40 points)
        if income > 0:
            balance = income - total_spent
            savings_ratio = balance / income
            if savings_ratio >= 0.3:
                score -= 0  # Perfect
            elif savings_ratio >= 0.15:
                score -= 10
            elif savings_ratio > 0:
                score -= 20
            else:
                score -= 40  # Negative balance
        else:
            score -= 25  # No income configured

        # 2. Category Budget Adherence (30 points)
        overspent_count = 0
        for c, limit in category_budgets.items():
            if limit > 0 and cat_spending.get(c, 0.0) > limit:
                overspent_count += 1
        
        score -= min(30, overspent_count * 15)

        # 3. Savings Goal Status (30 points)
        if savings_goal > 0:
            balance = income - total_spent
            if balance < savings_goal:
                score -= 15

        final_score = max(0, min(100, int(score)))

        if final_score >= 80:
            rating = "EXCELLENT"
        elif final_score >= 60:
            rating = "GOOD"
        elif final_score >= 40:
            rating = "FAIR"
        else:
            rating = "CRITICAL"

        return {
            "score": final_score,
            "rating": rating
        }
