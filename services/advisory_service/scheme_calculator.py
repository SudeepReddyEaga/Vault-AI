from typing import Dict, Any, List

def calculate_concessional_scheme(margin_capital: float) -> Dict[str, Any]:
    """
    Implements Module 2: Smart Financial Calculator & Scheme Router
    - Calculates Project Cost = Available Margin / 10%
    - Calculates Max Loan = 90% of Project Cost
    - Routes to Micro Finance (<= 1.40 Lakh) or Term Loan (1.40 Lakh to 50 Lakh)
    - Generates Quarterly Repayment Schedule factoring in 3 or 6 months Moratorium
    """
    margin = float(margin_capital)
    if margin <= 0:
        margin = 10000.0

    # 1. Financial Structuring
    project_cost = margin / 0.10  # 10% Margin Money -> 100% Project Cost
    raw_loan = project_cost * 0.90

    # 2. Scheme Auto-Selection Logic
    if project_cost <= 140000.0:
        # Micro Finance Scheme
        scheme_name = "Micro Finance Scheme"
        interest_rate = 6.5  # 6.5% p.a.
        tenure_years = 3     # 3 years
        moratorium_months = 3 # 3-month moratorium
        max_loan_cap = 125000.0 # Maximum Rs 1.25 Lakh
        eligible_loan = min(raw_loan, max_loan_cap)
        scheme_tier = "Tier 1: Micro Enterprise"
        capex_ratio = 0.65
        opex_ratio = 0.35
    elif project_cost <= 5000000.0:
        # Term Loan Scheme
        scheme_name = "Term Loan Scheme"
        interest_rate = 8.0  # 8.0% p.a.
        tenure_years = 7     # 7 years
        moratorium_months = 6 # 6-month moratorium
        max_loan_cap = 4500000.0 # Maximum Rs 45.00 Lakh
        eligible_loan = min(raw_loan, max_loan_cap)
        scheme_tier = "Tier 2: Medium/Term Enterprise"
        capex_ratio = 0.75
        opex_ratio = 0.25
    else:
        # Above standard ceiling
        scheme_name = "Special High-Cap Term Consortium"
        interest_rate = 8.5
        tenure_years = 7
        moratorium_months = 6
        max_loan_cap = 4500000.0
        eligible_loan = max_loan_cap
        scheme_tier = "Tier 3: Specialized Enterprise"
        capex_ratio = 0.80
        opex_ratio = 0.20

    # Capital Allocation
    capex_amount = project_cost * capex_ratio
    working_capital = project_cost * opex_ratio

    # 3. Quarterly Amortization & Moratorium Schedule
    total_months = tenure_years * 12
    total_quarters = total_months // 3
    moratorium_quarters = moratorium_months // 3
    repayment_quarters = total_quarters - moratorium_quarters

    quarterly_rate = (interest_rate / 100.0) / 4.0

    # Quarterly EMI calculation for repayment quarters
    if quarterly_rate > 0 and repayment_quarters > 0:
        quarterly_emi = (eligible_loan * quarterly_rate * ((1 + quarterly_rate) ** repayment_quarters)) / (((1 + quarterly_rate) ** repayment_quarters) - 1)
    else:
        quarterly_emi = eligible_loan / max(1, repayment_quarters)

    schedule: List[Dict[str, Any]] = []
    balance = eligible_loan

    for q in range(1, total_quarters + 1):
        month_label = f"Month {(q-1)*3 + 1} - Month {q*3}"
        quarter_interest = balance * quarterly_rate

        if q <= moratorium_quarters:
            # Moratorium period: Principal repayment is paused
            status = "Moratorium (Grace Period)"
            principal_paid = 0.0
            installment = quarter_interest  # Concessional schemes often only collect simple interest or defer
            note = f"Moratorium active (No principal deduction). Focus on initial setup and pilot operations."
        else:
            status = "Active Repayment"
            installment = quarterly_emi
            principal_paid = installment - quarter_interest
            if principal_paid > balance:
                principal_paid = balance
                installment = principal_paid + quarter_interest
            balance = max(0.0, balance - principal_paid)
            note = f"Regular quarterly installment."

        schedule.append({
            "quarter": q,
            "period": month_label,
            "status": status,
            "installment": round(installment, 2),
            "principal": round(principal_paid, 2),
            "interest": round(quarter_interest, 2),
            "remaining_balance": round(balance, 2),
            "note": note
        })

    # Summary Totals
    total_interest = sum(item["interest"] for item in schedule)
    total_repayment = eligible_loan + total_interest

    return {
        "available_margin": margin,
        "feasible_project_cost": round(project_cost, 2),
        "eligible_loan_amount": round(eligible_loan, 2),
        "margin_percentage": 10.0,
        "loan_percentage": 90.0,
        "scheme_name": scheme_name,
        "scheme_tier": scheme_tier,
        "interest_rate_pa": interest_rate,
        "tenure_years": tenure_years,
        "tenure_months": total_months,
        "moratorium_months": moratorium_months,
        "moratorium_quarters": moratorium_quarters,
        "quarterly_emi": round(quarterly_emi, 2),
        "approx_monthly_obligation": round(quarterly_emi / 3.0, 2),
        "capex_allocation": round(capex_amount, 2),
        "working_capital_allocation": round(working_capital, 2),
        "total_interest_payable": round(total_interest, 2),
        "total_cost_to_beneficiary": round(margin + total_repayment, 2),
        "amortization_schedule": schedule
    }
