import os
import json
import re
from datetime import datetime, timedelta
from openai import OpenAI

def parse_natural_date(text: str) -> str:
    """Parses natural language date strings (e.g., '5th November 2025', 'Nov 5 2025', '2025-11-05', 'yesterday', 'today') into YYYY-MM-DD format."""
    if not text:
        return None

    # 1. YYYY-MM-DD or YYYY/MM/DD
    iso_match = re.search(r'(\d{4})[\-\/](\d{1,2})[\-\/](\d{1,2})', text)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}"

    # 2. DD-MM-YYYY or DD/MM/YYYY
    dmy_match = re.search(r'(\d{1,2})[\-\/](\d{1,2})[\-\/](\d{4})', text)
    if dmy_match:
        d, m, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}"

    months_map = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
        'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }

    # 3. "5th November 2025", "5 November 2025", "5th Nov 2025"
    pattern1 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)\s+(\d{4})\b', text, re.IGNORECASE)
    if pattern1:
        d = int(pattern1.group(1))
        m_str = pattern1.group(2).lower()
        y = int(pattern1.group(3))
        if m_str in months_map:
            return f"{y:04d}-{months_map[m_str]:02d}-{d:02d}"

    # 4. "November 5 2025", "Nov 5th 2025"
    pattern2 = re.search(r'\b([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{4})\b', text, re.IGNORECASE)
    if pattern2:
        m_str = pattern2.group(1).lower()
        d = int(pattern2.group(2))
        y = int(pattern2.group(3))
        if m_str in months_map:
            return f"{y:04d}-{months_map[m_str]:02d}-{d:02d}"

    # 5. "5th November" or "November 5th" without year -> default to current year
    pattern3 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)\b', text, re.IGNORECASE)
    if pattern3:
        d = int(pattern3.group(1))
        m_str = pattern3.group(2).lower()
        if m_str in months_map:
            y = datetime.now().year
            return f"{y:04d}-{months_map[m_str]:02d}-{d:02d}"

    pattern4 = re.search(r'\b([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\b', text, re.IGNORECASE)
    if pattern4:
        m_str = pattern4.group(1).lower()
        d = int(pattern4.group(2))
        if m_str in months_map:
            y = datetime.now().year
            return f"{y:04d}-{months_map[m_str]:02d}-{d:02d}"

    lower = text.lower()
    if "yesterday" in lower:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if "today" in lower:
        return datetime.now().strftime("%Y-%m-%d")

    return None

def parse_month_year(text: str):
    """Extracts (year, month) tuple from text like 'November 2025', 'the month of November 2025', 'Nov 2025', '2025-11', '11/2025', 'in November'."""
    if not text:
        return None, None
    import re
    from datetime import datetime

    months_map = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
        'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }

    # Month name followed optionally by "of" and year e.g. "November 2025", "month of November 2025"
    pattern = r'\b(' + '|'.join(months_map.keys()) + r')\b(?:\s+of)?\s*(\d{4})?\b'
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        m_str = m.group(1).lower()
        y_str = m.group(2)
        if y_str:
            y = int(y_str)
        else:
            y_match = re.search(r'\b(20\d{2})\b', text)
            y = int(y_match.group(1)) if y_match else datetime.now().year
        return y, months_map[m_str]

    # ISO YYYY-MM
    m3 = re.search(r'\b(\d{4})[\-\/](\d{1,2})\b', text)
    if m3:
        return int(m3.group(1)), int(m3.group(2))

    return None, None


class BudgetMemory:

    """
    Memory component: Remembers every expense in the session so category totals stay correct.
    Also tracks income, savings goals, and category-specific budgets.
    """
    def __init__(self):
        self.expenses = []
        self.income = 0.0
        self.savings_goal = 0.0
        self.category_budgets = {}
        self.history_stack = []

    def _push_history(self, action_name: str):
        import copy
        snapshot = {
            "action": action_name,
            "expenses": copy.deepcopy(self.expenses),
            "income": self.income,
            "savings_goal": self.savings_goal,
            "category_budgets": copy.deepcopy(self.category_budgets)
        }
        self.history_stack.append(snapshot)
        if len(self.history_stack) > 25:
            self.history_stack.pop(0)

    def undo_last_action(self) -> str:
        if not self.history_stack:
            return "No previous action to undo."
        
        last_state = self.history_stack.pop()
        self.expenses = last_state["expenses"]
        self.income = last_state["income"]
        self.savings_goal = last_state["savings_goal"]
        self.category_budgets = last_state["category_budgets"]
        
        total_spent = sum(e["amount"] for e in self.expenses)
        return f"Successfully undid previous action ('{last_state['action']}'). Restored Income: ${self.income:,.2f}, Total Spent: ${total_spent:,.2f}."

    def set_income(self, amount: float) -> str:
        self._push_history(f"set_income(${amount:,.2f})")
        self.income = amount
        return f"Income set to {amount}."

    def set_category_budget(self, category: str, amount: float) -> str:
        self._push_history(f"set_category_budget({category}, ${amount:,.2f})")
        self.category_budgets[category] = amount
        return f"Budget for {category} set to {amount}."

    def add_expense(self, item: str, amount: float, category: str, date: str = None) -> str:
        self._push_history(f"add_expense({item}, ${amount:,.2f})")
        from datetime import datetime

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.expenses.append({
            "item": item,
            "amount": amount,
            "category": category,
            "date": date
        })
        
        warning = ""
        if category in self.category_budgets:
            spent_in_cat = sum(e["amount"] for e in self.expenses if e.get("category") == category)
            if spent_in_cat > self.category_budgets[category]:
                warning = f"\nWARNING: You have overspent in the '{category}' category! (Budget: {self.category_budgets[category]}, Spent: {spent_in_cat})"
        
        return f"Added expense: {item} (${amount:.2f}) in {category} on {date}.{warning}"

    def edit_expense(self, index: int = None, item_name: str = None, item: str = None, amount: float = None, change_amount: float = None, category: str = None, date: str = None) -> str:
        self._push_history(f"edit_expense({item_name or index or 'expense'})")
        target_idx = None

        if index is not None:
            try:
                idx = int(index)
                if 0 <= idx < len(self.expenses):
                    target_idx = idx
                elif 1 <= idx <= len(self.expenses):
                    target_idx = idx - 1
            except Exception:
                pass

        if target_idx is None and item_name:
            import re
            raw_q = str(item_name).strip()
            y_req, m_req = parse_month_year(raw_q)
            prefix_req = f"{y_req:04d}-{m_req:02d}" if (y_req and m_req) else None

            clean_query = re.sub(r'\b(?:the|price|cost|of|for|expense|expenses|item|as|to|my|total|spent|amount|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec|\d{4})\b', '', raw_q, flags=re.IGNORECASE).strip()
            if not clean_query:
                clean_query = raw_q.lower()
            
            best_idx = None
            for i, e in enumerate(self.expenses):
                exp_dt = e.get("date", "")
                if prefix_req and not exp_dt.startswith(prefix_req):
                    continue
                item_lower = e["item"].lower()
                cat_lower = e.get("category", "").lower()
                if clean_query in item_lower or item_lower in clean_query or clean_query in cat_lower:
                    best_idx = i
                    break

            if best_idx is None and prefix_req:
                for i, e in enumerate(self.expenses):
                    if e.get("date", "").startswith(prefix_req):
                        best_idx = i
                        break

            if best_idx is None:
                for i, e in enumerate(self.expenses):
                    item_lower = e["item"].lower()
                    cat_lower = e.get("category", "").lower()
                    if clean_query in item_lower or item_lower in clean_query or clean_query in cat_lower:
                        best_idx = i
                        break

            target_idx = best_idx


        if target_idx is not None and 0 <= target_idx < len(self.expenses):
            exp = self.expenses[target_idx]
            old_item = exp["item"]
            old_amt = exp["amount"]
            if item is not None and str(item).strip(): exp["item"] = str(item).strip()
            
            if change_amount is not None:
                exp["amount"] = max(0.0, float(old_amt) + float(change_amount))
            elif amount is not None:
                exp["amount"] = float(amount)

            if category is not None and str(category).strip(): exp["category"] = str(category).strip()
            if date is not None and str(date).strip(): exp["date"] = str(date).strip()
            
            adj_str = f" (Adjusted by ${float(change_amount):+.2f})" if change_amount is not None else ""
            return f"Successfully updated expense #{target_idx + 1} '{old_item}': {exp['item']} (${exp['amount']:.2f}){adj_str} in {exp['category']} on {exp['date']}."

        target_desc = f"index #{index}" if index is not None else f"item '{item_name}'"
        return f"No matching expense found for {target_desc}."



    def get_monthly_expenses(self, year: int, month: int) -> dict:
        prefix = f"{year:04d}-{month:02d}"
        monthly = [e for e in self.expenses if e.get("date", "").startswith(prefix)]
        total = sum(e["amount"] for e in monthly)
        return {
            "year": year,
            "month": month,
            "expenses": monthly,
            "total_spent": total
        }

    def get_monthly_summary(self, year: int, month: int) -> str:
        import calendar
        prefix = f"{year:04d}-{month:02d}"
        monthly = [e for e in self.expenses if e.get("date", "").startswith(prefix)]
        total_spent = sum(e["amount"] for e in monthly)
        
        days_in_month = calendar.monthrange(year, month)[1]
        daily_avg = total_spent / days_in_month if days_in_month > 0 else 0.0
        
        month_name = calendar.month_name[month]
        balance = self.income - total_spent
        
        cat_totals = {}
        for e in monthly:
            c = e.get("category", "General")
            cat_totals[c] = cat_totals.get(c, 0.0) + e["amount"]
            
        summary = (
            f"📅 **Complete Monthly Summary for {month_name} {year}**\n\n"
            f"• **Total Spent ({month_name} {year})**: ${total_spent:,.2f}\n"
            f"• **Daily Average Spend**: ${daily_avg:,.2f}/day\n"
            f"• **Available Income**: ${self.income:,.2f}\n"
            f"• **Net Balance**: ${balance:,.2f}\n\n"
        )
        
        if cat_totals:
            summary += "📊 **Category Breakdown:**\n"
            for c, amt in cat_totals.items():
                cap = self.category_budgets.get(c)
                cap_str = f" (Cap: ${cap:,.2f})" if cap else ""
                summary += f"• {c}: ${amt:,.2f}{cap_str}\n"
            summary += "\n"

        if monthly:
            summary += f"📆 **Expense Ledger ({len(monthly)} items):**\n"
            for idx, e in enumerate(monthly, 1):
                summary += f"{idx}. **{e['item']}** — ${e['amount']:,.2f} ({e.get('category', 'General')}) on {e.get('date')}\n"
        else:
            summary += f"ℹ️ No expenses recorded for {month_name} {year} yet."
            
        return summary


    def get_yearly_summary(self, year: int) -> dict:
        prefix = f"{year:04d}-"
        yearly = [e for e in self.expenses if e.get("date", "").startswith(prefix)]
        monthly_totals = {m: 0.0 for m in range(1, 13)}
        for e in yearly:
            try:
                m = int(e.get("date", "").split("-")[1])
                monthly_totals[m] += e["amount"]
            except Exception:
                pass
        return {
            "year": year,
            "monthly_totals": monthly_totals,
            "total_spent": sum(e["amount"] for e in yearly)
        }


    def get_summary(self, category: str = "all") -> str:
        if category and category.lower() != "all":
            spent = sum(e["amount"] for e in self.expenses if e.get("category") == category)
            cat_budget = self.category_budgets.get(category, "No budget set")
            return f"Category '{category}': Spent ${spent:.2f}. Budget limit: {cat_budget}."
        
        total_spent = sum(e["amount"] for e in self.expenses)
        balance = self.income - total_spent
        
        summary = f"Total Income: ${self.income:,.2f}\nTotal Spent: ${total_spent:,.2f}\nCurrent Balance: ${balance:,.2f}\nSavings Goal: ${self.savings_goal:,.2f}\n"
        if self.savings_goal > 0:
            if balance >= self.savings_goal:
                summary += "Status: You are on track to meet your savings goal!"
            else:
                summary += f"Status: You are short by ${self.savings_goal - balance:,.2f} to meet your savings goal."
                
        return summary

    def set_savings_goal(self, amount: float) -> str:
        self._push_history(f"set_savings_goal(${amount:,.2f})")
        self.savings_goal = amount
        return f"Savings goal set to {amount}."

    def delete_expense(self, item_name: str) -> str:
        self._push_history(f"delete_expense({item_name})")
        import re
        raw_query = str(item_name).strip().lower()
        clean_query = re.sub(r'\b(?:all|in my account|from my account|my account|in account|from account|account|expenses|expense|items|item|from|in|my)\b', '', raw_query, flags=re.IGNORECASE).strip()
        if not clean_query:
            clean_query = raw_query

        # Check numeric index deletion (1-indexed or 0-indexed)
        if clean_query.isdigit():
            idx = int(clean_query) - 1
            if 0 <= idx < len(self.expenses):
                removed = self.expenses.pop(idx)
                return f"Successfully deleted expense #{idx + 1} '{removed['item']}' (${removed['amount']:.2f})."
            return f"Expense index #{clean_query} out of bounds."

        # Check bulk or single deletion match
        matching_indices = []
        for i, e in enumerate(self.expenses):
            cat_name = e.get("category", "").lower()
            item_desc = e["item"].lower()
            
            is_sub_match = ("subscription" in clean_query or "subscriptions" in clean_query) and ("subscription" in item_desc or cat_name == "subscriptions")
            is_cat_match = (clean_query == cat_name)
            is_name_match = (clean_query in item_desc)

            if is_sub_match or is_cat_match or is_name_match:
                matching_indices.append(i)

        if matching_indices:
            removed_items = []
            for i in reversed(matching_indices):
                removed_items.append(self.expenses.pop(i))
            total_deleted_amt = sum(r["amount"] for r in removed_items)
            item_names = ", ".join([f"'{r['item']}'" for r in removed_items])
            return f"Successfully deleted {len(removed_items)} matching expense(s) ({item_names}) totaling ${total_deleted_amt:.2f}."

        return f"No matching expenses found for '{item_name}'."


    def delete_category_budget(self, category: str) -> str:
        self._push_history(f"delete_category_budget({category})")
        cat_title = category.strip().title()
        if cat_title in self.category_budgets:
            del self.category_budgets[cat_title]
            return f"Successfully removed category budget limit for '{cat_title}'."
        for k in list(self.category_budgets.keys()):
            if k.lower() == category.strip().lower():
                del self.category_budgets[k]
                return f"Successfully removed category budget limit for '{k}'."
        return f"No budget limit found for category '{category}'."

    def check_affordability(self, item: str, cost: float, category: str = "General") -> str:
        total_spent = sum(e["amount"] for e in self.expenses)
        balance = self.income - total_spent
        rem_balance = balance - cost
        
        cat_spent = sum(e["amount"] for e in self.expenses if e.get("category", "").lower() == category.lower())
        cat_limit = self.category_budgets.get(category.title(), 0)
        is_cat_over = (cat_limit > 0) and ((cat_spent + cost) > cat_limit)

        if balance >= cost:
            decision = f"✅ **Decision: YES, you can afford {item}!**\n\n"
            decision += f"• **Current Balance**: ${balance:,.2f}\n"
            decision += f"• **Item Cost**: ${cost:,.2f}\n"
            decision += f"• **Remaining Balance After**: ${rem_balance:,.2f}\n\n"
            if self.savings_goal > 0:
                if rem_balance >= self.savings_goal:
                    decision += f"✅ You will still hit your savings goal of ${self.savings_goal:,.2f}!\n"
                else:
                    decision += f"⚠️ Note: Buying this will dip your balance below your savings goal of ${self.savings_goal:,.2f} by ${self.savings_goal - rem_balance:,.2f}.\n"
            if is_cat_over:
                decision += f"⚠️ Category Notice: Buying this will exceed your '{category.title()}' category limit of ${cat_limit:,.2f}."
            return decision
        else:
            shortfall = cost - balance
            return (
                f"❌ **Decision: NO, you cannot comfortably afford {item}.**\n\n"
                f"• **Current Balance**: ${balance:,.2f}\n"
                f"• **Item Cost**: ${cost:,.2f}\n"
                f"• **Shortfall**: ${shortfall:,.2f}\n\n"
                f"💡 Consider increasing income or reducing other expenses before making this purchase."
            )

    def explain_architecture(self) -> str:
        return (
            "🤖 **VaultAI Agentic AI Architecture & Project Overview (CSE476 Demo)**\n\n"
            "1. **ReAct Plan-Act Loop**: Multi-turn reasoning engine that translates user intent into dynamic tool calls, executing actions on memory and presenting transparent tool execution traces.\n"
            "2. **Stateful BudgetMemory**: Manages session income, expenses, category spending limits, and savings goals with a 25-step undo stack for instant rollback.\n"
            "3. **Financial Tool Suite**: Includes native tools for adding, editing (relative +/- adjustments), deleting, checking affordability, forecasting spending, managing category caps, and undoing actions.\n"
            "4. **ML Predictive Forecasting & Health Scoring**: Uses Scikit-Learn `LinearRegression` to forecast next-month expenditure trends, detect overspend risks, and compute a 0-100 Financial Health Score.\n"
            "5. **Hybrid Execution Engine**: Supports both Cloud LLM (OpenAI API key) and an autonomous offline fallback parsing engine for guaranteed reliability during viva demonstrations."
        )

    def reset_memory(self) -> str:
        self._push_history("reset_memory")
        self.expenses = []
        self.income = 0.0
        self.savings_goal = 0.0
        self.category_budgets = {}
        return "Budget memory reset successfully. All income, expenses, category budgets, and savings goals have been cleared."





class BudgetAgent:
    def __init__(self, api_key=None, base_url="https://models.inference.ai.azure.com", model="gpt-4o"):
        """
        Initializes the agent. Uses GitHub Models by default, but can work with any OpenAI-compatible API.
        If no API key is provided, operates in smart autonomous agent fallback mode.
        """
        self.api_key = api_key or os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.offline_mode = False

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key, base_url=base_url)
            except Exception as e:
                print(f"[Warning] Failed to initialize OpenAI client: {e}. Switching to smart agent fallback mode.")
                self.offline_mode = True
        else:
            self.offline_mode = True
            print("[Info] No API key detected. Operating in smart autonomous agent engine mode.")

        self.model = model
        self.memory = BudgetMemory()
        
        self.system_prompt = (
            "You are a helpful Personal Budget Assistant & Financial AI Copilot (VaultAI). "
            "Use the provided tools to manage the user's budget, analyze financial health, check affordability, and predict spending trends. "
            "You must use tools whenever you need to add an expense, edit an expense, update a price, delete an expense, set income, set category budget caps, delete category budget caps, check affordability, forecast spending, undo an action, or explain the agent architecture. "
            "When answering questions like 'can I afford X?', always call the check_affordability or get_summary tool to evaluate balance, category limits, and savings goals, then explicitly explain your reasoning based on the tool's result."
        )

        self.chat_history = [{"role": "system", "content": self.system_prompt}]
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "set_income",
                    "description": "Sets the total available income or starting balance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "The amount of income"}
                        },
                        "required": ["amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_category_budget",
                    "description": "Sets a budget limit for a specific spending category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "amount": {"type": "number"}
                        },
                        "required": ["category", "amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_expense",
                    "description": "Adds an expense to the budget tracker.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string", "description": "Name of the item"},
                            "amount": {"type": "number", "description": "Cost of the item"},
                            "category": {"type": "string", "description": "Category (e.g. food, travel, rent)"}
                        },
                        "required": ["item", "amount", "category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_summary",
                    "description": "Gets a summary of spending. Pass a specific category, or 'all' for overall summary.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "Category name or 'all'"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_savings_goal",
                    "description": "Sets a target savings goal amount.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"}
                        },
                        "required": ["amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_expense",
                    "description": "Deletes or removes an existing expense by item name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string", "description": "Name or keyword of the expense item to delete"}
                        },
                        "required": ["item"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "predict_spending",
                    "description": "Uses Machine Learning to predict next month's total spending, category forecasts, and financial health score.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_expense",
                    "description": "Edits an existing expense record by index (0-indexed or 1-indexed) or item name/keyword, modifying item name, amount, category, or date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer", "description": "Index of the expense to edit (0-based or 1-based). Optional if item_name is provided."},
                            "item_name": {"type": "string", "description": "Name or keyword of the expense item to edit (e.g. 'YouTube Premium'). Optional if index is provided."},
                            "item": {"type": "string", "description": "New item name (optional)"},
                            "amount": {"type": "number", "description": "New expense amount / price (optional)"},
                            "category": {"type": "string", "description": "New expense category (optional)"},
                            "date": {"type": "string", "description": "New date in YYYY-MM-DD format (optional)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reset_memory",
                    "description": "Resets and clears all budget memory (income, expenses, category budgets, savings goals).",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_category_budget",

                    "description": "Removes or deletes a category budget limit.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "Category name to remove budget cap for"}
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_affordability",
                    "description": "Checks if the user can afford a specific purchase item based on available capital, category cap, and savings goal.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string", "description": "Item name"},
                            "cost": {"type": "number", "description": "Item cost"},
                            "category": {"type": "string", "description": "Category (optional)"}
                        },
                        "required": ["item", "cost"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_monthly_calendar",
                    "description": "Retrieves daily expense breakdown, daily average, and monthly total expenditure for a specific month and year.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "year": {"type": "integer", "description": "Year (e.g. 2026)"},
                            "month": {"type": "integer", "description": "Month number 1-12"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_yearly_summary",
                    "description": "Retrieves 12-month spending ledger and total expenditure for a given year.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "year": {"type": "integer", "description": "Year (e.g. 2026)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "explain_agent_architecture",
                    "description": "Explains the Agentic AI Plan-Act ReAct architecture, Stateful BudgetMemory, Toolset, and ML Forecasting Engine for project demonstration/viva.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "undo_last_action",
                    "description": "Undoes the previous action/task and restores income, expenses, category budgets, and savings goals to their previous state.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    def _execute_tool(self, func_name: str, args: dict) -> str:
        """Executes tool function on memory component."""
        if func_name == "set_income":
            return self.memory.set_income(float(args["amount"]))
        elif func_name == "set_category_budget":
            return self.memory.set_category_budget(str(args["category"]), float(args["amount"]))
        elif func_name == "delete_category_budget":
            return self.memory.delete_category_budget(str(args["category"]))
        elif func_name == "add_expense":
            date = args.get("date")
            return self.memory.add_expense(str(args["item"]), float(args["amount"]), str(args.get("category", "General")), date)
        elif func_name == "edit_expense":
            idx = args.get("index")
            item_name = args.get("item_name") or args.get("target") or args.get("item_keyword")
            item = args.get("item") or args.get("new_item")
            amount = args.get("amount") or args.get("new_amount") or args.get("price")
            change_amt = args.get("change_amount") or args.get("delta") or args.get("adjust_by")
            category = args.get("category") or args.get("new_category")
            date = args.get("date") or args.get("new_date")
            return self.memory.edit_expense(index=idx, item_name=item_name, item=item, amount=amount, change_amount=change_amt, category=category, date=date)

        elif func_name == "undo_last_action":
            return self.memory.undo_last_action()
        elif func_name == "delete_expense":
            return self.memory.delete_expense(str(args["item"]))
        elif func_name == "reset_memory":
            return self.memory.reset_memory()

        elif func_name == "get_summary":
            return self.memory.get_summary(args.get("category", "all"))
        elif func_name == "set_savings_goal":
            return self.memory.set_savings_goal(float(args["amount"]))
        elif func_name == "check_affordability":
            return self.memory.check_affordability(str(args["item"]), float(args["cost"]), str(args.get("category", "General")))
        elif func_name == "get_monthly_calendar":
            from datetime import datetime
            y = int(args.get("year", datetime.now().year))
            m = int(args.get("month", datetime.now().month))
            return self.memory.get_monthly_summary(y, m)

        elif func_name == "get_yearly_summary":
            from datetime import datetime
            y = int(args.get("year", datetime.now().year))
            info = self.memory.get_yearly_summary(y)
            return f"Yearly Expenditure ({y}): Total Spent is ${info['total_spent']:,.2f}."
        elif func_name == "explain_agent_architecture":
            return self.memory.explain_architecture()
        elif func_name == "predict_spending":
            from ml_engine import BudgetPredictor
            pred = BudgetPredictor().predict(self.memory.expenses, self.memory.category_budgets, self.memory.income, self.memory.savings_goal)
            return f"ML Forecast: Next month predicted total spending is ${pred['predicted_next_month_total']:,.2f} ({pred['trend_direction']} {pred['trend_percentage']}%). Health Score: {pred['health_score']['score']}/100 ({pred['health_score']['rating']})."
        else:
            return f"Error: Unknown function '{func_name}'"





    def chat_with_trace(self, user_message: str):
        """
        Executes plan-act loop and returns both final response and step-by-step tool trace logs.
        """
        trace = []
        if self.offline_mode or not self.client:
            return self._smart_fallback_chat_with_trace(user_message)

        print(f"\n[User]: {user_message}")
        self.chat_history.append({"role": "user", "content": user_message})

        step_count = 0
        try:
            while True:
                step_count += 1
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.chat_history,
                    tools=self.tools
                )
                
                message = response.choices[0].message
                self.chat_history.append(message)
                
                if not message.tool_calls:
                    print(f"[Agent]: {message.content}")
                    return {"response": message.content, "trace": trace}
                    
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    args_str = tool_call.function.arguments
                    print(f"  -> [Tool Call]: {func_name}({args_str})")
                    
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {}
                    
                    try:
                        result = self._execute_tool(func_name, args)
                    except Exception as e:
                        result = f"Error executing {func_name}: {str(e)}"
                        
                    print(f"  <- [Tool Result]: {result}")
                    trace.append({
                        "step": step_count,
                        "tool": func_name,
                        "args": args,
                        "result": str(result)
                    })
                    
                    self.chat_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
        except Exception as err:
            print(f"[Error in LLM loop]: {err}. Switching to smart agent fallback.")
            return self._smart_fallback_chat_with_trace(user_message)

    def chat(self, user_message: str):
        """
        Standard chat interface. Returns final text response string.
        """
        res = self.chat_with_trace(user_message)
        return res["response"]

    def _smart_fallback_chat_with_trace(self, user_message: str):
        """
        Smart autonomous agent engine when running without API keys or on API failure.
        Parses multi-step intent, executes tools on memory, and returns full agent trace log.
        """
        import re
        trace = []
        text = user_message.strip()
        lower = text.lower()
        response_parts = []
        step = 1

        # 0. Check UNDO / REVERT intent
        undo_keywords = ["undo", "revert", "rollback", "cancel last", "undo last", "undo previous", "undo that", "cancel action", "take back"]
        is_undo_intent = any(kw in lower for kw in undo_keywords)
        if is_undo_intent:
            res = self._execute_tool("undo_last_action", {})
            trace.append({"step": step, "tool": "undo_last_action", "args": {}, "result": res})
            step += 1
            response_parts.append(f"↩️ Executed `undo_last_action()`: {res}")
            return {"response": "\n\n".join(response_parts), "trace": trace}

        # 0.1 Check EXPLAIN ARCHITECTURE intent (Faculty / Viva Demo)
        is_explain_architecture = any(kw in lower for kw in ["explain agent", "explain architecture", "how agent works", "how does agent work", "what is react", "plan act loop", "plan-act", "viva", "faculty", "project overview", "how does ml work", "tell me about this project"])
        if is_explain_architecture:
            arch_res = self._execute_tool("explain_agent_architecture", {})
            trace.append({"step": step, "tool": "explain_agent_architecture", "args": {}, "result": "Explained Agentic AI ReAct Architecture & ML Engine"})
            step += 1
            response_parts.append(arch_res)

        # 1. Check reset memory intent
        is_reset_intent = any(kw in lower for kw in ["reset the memory", "reset memory", "clear memory", "restart memory", "reset session", "clear budget", "reset budget"])

        if is_reset_intent:
            res = self._execute_tool("reset_memory", {})
            trace.append({"step": step, "tool": "reset_memory", "args": {}, "result": res})
            step += 1
            response_parts.append(f"🔄 Executed `reset_memory()`: {res}")


        # 2. Check income / budget balance setting intent
        is_income_intent = (not is_reset_intent) and any(kw in lower for kw in ["income", "salary", "earn", "starting balance", "to my budget", "to budget", "to my income", "total income", "set another", "add another", "increase income", "add to income", "add to budget"])
        income_match = re.search(r'\$?(\d+(?:\.\d+)?)', text)

        if is_income_intent and income_match:
            amt = float(income_match.group(1))
            
            # Check if user wants to ADD to existing income (e.g. "add another 5000", "at 10000 to my income", "add 5000 to budget", "increase income")
            is_add_income = any(kw in lower for kw in ["add another", "set another", "add to income", "add to budget", "increase", "more", "add ", "ad ", "at ", "plus "])
            if is_add_income and self.memory.income > 0:
                new_income = self.memory.income + amt
                res = self._execute_tool("set_income", {"amount": new_income})
                trace.append({"step": step, "tool": "set_income", "args": {"amount": new_income}, "result": res})
                step += 1
                response_parts.append(f"✅ Executed `set_income({new_income})`: Added ${amt:,.2f} to budget income. New Total Income is ${new_income:,.2f}.")
            else:
                res = self._execute_tool("set_income", {"amount": amt})
                trace.append({"step": step, "tool": "set_income", "args": {"amount": amt}, "result": res})
                step += 1
                response_parts.append(f"✅ Executed `set_income({amt})`: {res}")


        # 2. Check savings goal setting intent
        savings_match = re.search(r'(?:savings goal|target savings|save)\s*\$?(\d+(?:\.\d+)?)', lower)
        if savings_match or "savings goal" in lower:
            amt = float(savings_match.group(1)) if savings_match else 1000.0
            res = self._execute_tool("set_savings_goal", {"amount": amt})
            trace.append({"step": step, "tool": "set_savings_goal", "args": {"amount": amt}, "result": res})
            step += 1
            response_parts.append(f"🎯 Executed `set_savings_goal({amt})`: {res}")

        # 3. Check category budget setting intent
        cat_budget_match = re.search(r'(?:budget for|limit for|set category budget|category budget)\s+([a-zA-Z]+)\s+(?:to|is|=)?\s*\$?(\d+(?:\.\d+)?)', lower)
        if cat_budget_match:
            cat = cat_budget_match.group(1).title()
            amt = float(cat_budget_match.group(2))
            res = self._execute_tool("set_category_budget", {"category": cat, "amount": amt})
            trace.append({"step": step, "tool": "set_category_budget", "args": {"category": cat, "amount": amt}, "result": res})
            step += 1
            response_parts.append(f"📊 Executed `set_category_budget('{cat}', {amt})`: {res}")

        # 4. Check DELETE / REMOVE expense intent
        is_delete_intent = any(kw in lower for kw in ["delete", "remove", "cancel", "erase", "drop"])
        if is_delete_intent:
            target_item = re.sub(r'\b(?:delete|remove|cancel|erase|drop|from my account|in my account|from account|in account|my account|account|expenses|expense|items|item|from|in|my)\b', '', lower, flags=re.IGNORECASE).strip().title()
            if not target_item:
                target_item = text.strip()
            
            res = self._execute_tool("delete_expense", {"item": target_item})
            trace.append({"step": step, "tool": "delete_expense", "args": {"item": target_item}, "result": res})
            step += 1
            response_parts.append(f"🗑️ Executed `delete_expense('{target_item}')`: {res}")

        # 5. Check EDIT / UPDATE / ADJUST / RELATIVE expense intent
        inc_words = ["increase", "increased", "raise", "raised", "hike", "hiked", "bump", "bumped", "boost", "boosted", "surge", "surged", "jumped", "up by", "add to", "plus"]
        dec_words = ["reduce", "reduced", "decrease", "decreased", "lower", "lowered", "deduct", "deducted", "cut", "down by", "minus", "drop", "dropped"]
        edit_keywords = ["edit", "update", "change", "modify", "correct", "adjust"] + inc_words + dec_words

        is_edit_intent = (not is_reset_intent) and (not is_income_intent) and (not is_delete_intent) and any(kw in lower for kw in edit_keywords) and not any(kw in lower for kw in ["income", "savings goal", "category budget", "limit for"])

        if is_edit_intent:
            pattern = r'(?:\b(?:so|then|and then|and|\;|\,)\b|(?<=\d)\s+(?=(?:' + '|'.join(edit_keywords) + r')\b))'
            sub_clauses = [c.strip() for c in re.split(pattern, lower) if c.strip()]
            if not sub_clauses:
                sub_clauses = [lower]

            last_num = None
            for s_clause in sub_clauses:
                if not any(kw in s_clause for kw in edit_keywords):
                    continue

                idx_match = re.search(r'(?:expense\s*#?|#)(\d+)', s_clause)
                target_idx = int(idx_match.group(1)) - 1 if idx_match else None

                nums = re.findall(r'\$?(\d+(?:\.\d+)?)', s_clause)
                val = float(nums[-1]) if nums else last_num
                if nums:
                    last_num = val

                is_inc = any(w in s_clause for w in inc_words)
                is_dec = any(w in s_clause for w in dec_words)

                amt = None
                change_amt = None
                if is_inc and val is not None:
                    change_amt = val
                elif is_dec and val is not None:
                    change_amt = -val
                else:
                    amt = val

                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', s_clause)
                exp_date = date_match.group(1) if date_match else None

                target_item = None
                if target_idx is None:
                    clean_target = re.sub(r'\b(?:edit|update|change|modify|correct|adjust|increase|increased|raise|raised|hike|hiked|bump|bumped|boost|boosted|surge|surged|jumped|reduce|reduced|decrease|decreased|lower|lowered|deduct|deducted|cut|dropped|got|by|from|the|amount|price|cost|of|to|as|for|expense|item|this|month|my|\$|\d+(?:\.\d+)?|\d{4}-\d{2}-\d{2})\b', '', s_clause, flags=re.IGNORECASE)
                    clean_target = re.sub(r'[\-\s]+', ' ', clean_target).strip()
                    
                    best_match = None
                    if clean_target:
                        for e in self.memory.expenses:
                            if clean_target in e["item"].lower() or e["item"].lower() in clean_target:
                                best_match = e["item"]
                                break
                    if not best_match and self.memory.expenses:
                        for e in self.memory.expenses:
                            words = [w for w in e["item"].lower().split() if len(w) > 2]
                            if any(w in s_clause for w in words):
                                best_match = e["item"]
                                break
                    
                    target_item = best_match or clean_target or None

                res = self._execute_tool("edit_expense", {"index": target_idx, "item_name": target_item, "amount": amt, "change_amount": change_amt, "date": exp_date})
                trace.append({"step": step, "tool": "edit_expense", "args": {"index": target_idx, "item_name": target_item, "amount": amt, "change_amount": change_amt, "date": exp_date}, "result": res})
                step += 1
                response_parts.append(f"✏️ Executed `edit_expense()`: {res}")


        # 6. Check ADD expense intent (Exclude income & savings goal & edit intents!)
        is_add_expense_intent = (not is_income_intent) and (not is_delete_intent) and (not is_edit_intent) and any(kw in lower for kw in ["add", "bought", "spent", "paid", "subscription", "expense", "cost"]) and not ("afford" in lower or "savings goal" in lower or "limit for" in lower)

        if is_add_expense_intent:
            exp_date = parse_natural_date(text)
            if not exp_date:
                y_p, m_p = parse_month_year(text)
                if y_p and m_p:
                    exp_date = f"{y_p:04d}-{m_p:02d}-01"

            nums = re.findall(r'\$?(\d+(?:\.\d+)?)', text)
            amt = float(nums[0]) if nums else None

            # Clean dates & stop-phrases from text to extract clean item name
            clean_text = re.sub(r'\b(?:on|dated|for the month of|the month of|month of|for month of|for month|in the month of|in month of|in month|for)?\s*\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+\s*\d{0,4}\b', '', text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\b(?:on|dated|for the month of|the month of|month of|for month of|for month|in the month of|in month of|in month|for)?\s*[a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?\s*\d{0,4}\b', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\b(?:on|dated|for the month of|the month of|month of|for month of|for month|in the month of|in month of|in month|for)?\s*[a-zA-Z]+\s+\d{4}\b', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\b(?:add|to my account|to account|my account|to my expenses|to expenses|to my total spent|to total spent|as my total spent|total spent|as my total|my total|my spent|as my|for the month of|the month of|month of|for month of|for month|the month|month|as|for|on|costing|\$|\d+(?:\.\d+)?|dollars)\b', '', clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'[\-\s]+', ' ', clean_text).strip()


            item_name = "General Expense"
            category = "Subscriptions" if "subscription" in lower else "General"

            if "rent" in lower:
                item_name = "Rent"
                category = "Housing"
                if not amt: amt = 500.0
            elif any(w in lower for w in ["trip", "vacation", "flight"]):
                item_name = "Trip"
                category = "Travel"
                if not amt: amt = 200.0
            elif any(w in lower for w in ["cloud core", "cloud"]):
                item_name = "Cloud Core Subscription"
                category = "Subscriptions"
                if not amt: amt = 15.0
            elif "youtube" in lower:
                item_name = "YouTube Premium Subscription"
                if not amt: amt = 13.99
                category = "Subscriptions"
            elif "spotify" in lower:
                item_name = "Spotify Subscription"
                if not amt: amt = 11.99
                category = "Subscriptions"
            elif "claude" in lower:
                item_name = "Claude Subscription"
                if not amt: amt = 20.00
                category = "Subscriptions"
            elif "chatgpt" in lower or "openai" in lower:
                item_name = "ChatGPT Plus Subscription"
                if not amt: amt = 20.00
                category = "Subscriptions"
            elif "netflix" in lower:
                item_name = "Netflix Subscription"
                if not amt: amt = 15.99
                category = "Subscriptions"
            elif any(w in lower for w in ["food", "lunch", "dinner", "burger", "pizza", "coffee", "groceries"]):
                item_name = "Food & Dining"
                category = "Food"
                if not amt: amt = 15.00
            elif any(w in lower for w in ["cab", "uber", "flight", "gas", "fuel", "travel"]):
                item_name = "Travel / Transport"
                category = "Travel"
                if not amt: amt = 25.00
            elif any(w in lower for w in ["rent", "power", "utility", "bill"]):
                item_name = "Housing & Rent"
                category = "Housing"
                if not amt: amt = 100.00
            elif any(w in lower for w in ["movie", "game", "shirt", "shoes", "shopping"]):
                item_name = "Shopping"
                category = "Shopping"
                if not amt: amt = 50.00
            else:
                if clean_text and len(clean_text) > 1:
                    words = clean_text.split()
                    item_name = " ".join(words[:4]).title()
                if not amt: amt = 15.00

            res = self._execute_tool("add_expense", {"item": item_name, "amount": amt, "category": category, "date": exp_date})
            trace.append({"step": step, "tool": "add_expense", "args": {"item": item_name, "amount": amt, "category": category, "date": exp_date}, "result": res})
            step += 1
            response_parts.append(f"💸 Executed `add_expense('{item_name}', ${amt:.2f}, '{category}', '{exp_date or 'Today'}')`: {res}")




        # 5. Check affordability intent "Can I afford X?"
        afford_match = re.search(r'(?:can i afford|should i buy|afford)\s+(?:a|an)?\s*([a-zA-Z0-9\s]+?)(?:\s+(?:for|at|costing)?\s*\$?(\d+(?:\.\d+)?))?', lower)
        if afford_match or "afford" in lower:
            item_name = afford_match.group(1).strip().title() if (afford_match and afford_match.group(1)) else "Item"
            cost_str = afford_match.group(2) if (afford_match and len(afford_match.groups()) > 1 and afford_match.group(2)) else None
            if not cost_str:
                nums = re.findall(r'\$?(\d+(?:\.\d+)?)', text)
                cost = float(nums[-1]) if nums else 100.0
            else:
                cost = float(cost_str)

            # Mandatory Plan-Act step for affordability: get_summary tool call first
            summary_res = self._execute_tool("get_summary", {"category": "all"})
            trace.append({"step": step, "tool": "get_summary", "args": {"category": "all"}, "result": summary_res})
            step += 1

            total_spent = sum(e["amount"] for e in self.memory.expenses)
            curr_balance = self.memory.income - total_spent
            rem_after = curr_balance - cost

            if curr_balance >= cost:
                reasoning = (
                    f"**Decision: YES, you can afford {item_name}!**\n\n"
                    f"• Current Balance: **${curr_balance:,.2f}**\n"
                    f"• Item Cost: **${cost:,.2f}**\n"
                    f"• Balance after purchase: **${rem_after:,.2f}**\n\n"
                )
                if self.memory.savings_goal > 0:
                    if rem_after >= self.memory.savings_goal:
                        reasoning += f"✅ You will still be on track to hit your savings goal of ${self.memory.savings_goal:,.2f}!"
                    else:
                        reasoning += f"⚠️ Note: Buying this will dip your balance below your savings goal of ${self.memory.savings_goal:,.2f} by ${self.memory.savings_goal - rem_after:,.2f}."
                response_parts.append(reasoning)
            else:
                shortfall = cost - curr_balance
                reasoning = (
                    f"**Decision: NO, you cannot comfortably afford {item_name}.**\n\n"
                    f"• Current Balance: **${curr_balance:,.2f}**\n"
                    f"• Item Cost: **${cost:,.2f}**\n"
                    f"• Shortfall: **${shortfall:,.2f}**\n\n"
                    f"💡 Consider lowering other expenses or increasing your income before making this purchase."
                )
                response_parts.append(reasoning)

        # 6. Check ML prediction / forecast intent
        if any(w in lower for w in ["predict", "forecast", "future", "health score", "ml model", "trend"]):
            pred_res = self._execute_tool("predict_spending", {})
            trace.append({"step": step, "tool": "predict_spending", "args": {}, "result": pred_res})
            step += 1
            response_parts.append(f"🤖 **Machine Learning Trend Analysis & Forecast:**\n\n{pred_res}")

        # 7. Check Month Summary / Temporal Info Intent (e.g. "show November 2025", "info for Nov 2025", "summary of 2025-11")
        y_parsed, m_parsed = parse_month_year(text)
        is_month_info_intent = (y_parsed and m_parsed) and any(kw in lower for kw in ["info", "summary", "show", "spending", "calendar", "breakdown", "report", "november", "december", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october"]) and not (is_add_expense_intent or is_delete_intent or is_edit_intent)

        if is_month_info_intent:
            res = self._execute_tool("get_monthly_calendar", {"year": y_parsed, "month": m_parsed})
            trace.append({"step": step, "tool": "get_monthly_calendar", "args": {"year": y_parsed, "month": m_parsed}, "result": res})
            step += 1
            response_parts.append(res)








        # 5. Check affordability intent "Can I afford X?"
        afford_match = re.search(r'(?:can i afford|should i buy|afford)\s+(?:a|an)?\s*([a-zA-Z0-9\s]+?)(?:\s+(?:for|at|costing)?\s*\$?(\d+(?:\.\d+)?))?', lower)
        if afford_match or "afford" in lower:
            item_name = afford_match.group(1).strip().title() if (afford_match and afford_match.group(1)) else "Item"
            cost_str = afford_match.group(2) if (afford_match and len(afford_match.groups()) > 1 and afford_match.group(2)) else None
            if not cost_str:
                nums = re.findall(r'\$?(\d+(?:\.\d+)?)', text)
                cost = float(nums[-1]) if nums else 100.0
            else:
                cost = float(cost_str)

            # Mandatory Plan-Act step for affordability: get_summary tool call first
            summary_res = self._execute_tool("get_summary", {"category": "all"})
            trace.append({"step": step, "tool": "get_summary", "args": {"category": "all"}, "result": summary_res})
            step += 1

            total_spent = sum(e["amount"] for e in self.memory.expenses)
            curr_balance = self.memory.income - total_spent
            rem_after = curr_balance - cost

            if curr_balance >= cost:
                reasoning = (
                    f"**Decision: YES, you can afford {item_name}!**\n\n"
                    f"• Current Balance: **${curr_balance:,.2f}**\n"
                    f"• Item Cost: **${cost:,.2f}**\n"
                    f"• Balance after purchase: **${rem_after:,.2f}**\n\n"
                )
                if self.memory.savings_goal > 0:
                    if rem_after >= self.memory.savings_goal:
                        reasoning += f"✅ You will still be on track to hit your savings goal of ${self.memory.savings_goal:,.2f}!"
                    else:
                        reasoning += f"⚠️ Note: Buying this will dip your balance below your savings goal of ${self.memory.savings_goal:,.2f} by ${self.memory.savings_goal - rem_after:,.2f}."
                response_parts.append(reasoning)
            else:
                shortfall = cost - curr_balance
                reasoning = (
                    f"**Decision: NO, you cannot comfortably afford {item_name}.**\n\n"
                    f"• Current Balance: **${curr_balance:,.2f}**\n"
                    f"• Item Cost: **${cost:,.2f}**\n"
                    f"• Shortfall: **${shortfall:,.2f}**\n\n"
                    f"💡 Consider lowering other expenses or increasing your income before making this purchase."
                )
                response_parts.append(reasoning)

        # 6. Check ML prediction / forecast intent
        if any(w in lower for w in ["predict", "forecast", "future", "health score", "ml model", "trend"]):
            pred_res = self._execute_tool("predict_spending", {})
            trace.append({"step": step, "tool": "predict_spending", "args": {}, "result": pred_res})
            step += 1
            response_parts.append(f"🤖 **Machine Learning Trend Analysis & Forecast:**\n\n{pred_res}")

        # 7. Summary intent or fallback
        if "summary" in lower or "status" in lower or "report" in lower or not response_parts:
            summary_res = self._execute_tool("get_summary", {"category": "all"})
            trace.append({"step": step, "tool": "get_summary", "args": {"category": "all"}, "result": summary_res})
            step += 1
            if not response_parts:
                total_spent = sum(e["amount"] for e in self.memory.expenses)
                curr_balance = self.memory.income - total_spent
                formatted_summary = (
                    f"📊 **Personal Budget Summary**\n\n"
                    f"• **Total Income**: ${self.memory.income:,.2f}\n"
                    f"• **Total Spent**: ${total_spent:,.2f}\n"
                    f"• **Current Balance**: ${curr_balance:,.2f}\n"
                    f"• **Savings Goal**: ${self.memory.savings_goal:,.2f}"
                )
                response_parts.append(formatted_summary)


        final_response = "\n\n".join(response_parts)
        return {"response": final_response, "trace": trace}


