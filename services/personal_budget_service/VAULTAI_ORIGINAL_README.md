# Personal Budget Assistant (Agent & Web App)

**Tools & Memory:** This agent uses two primary tools as required: `add_expense` (records an expense in a given category and checks for budget violations) and `get_summary` (calculates total spent, remaining balance, and checks status against savings goal). It also uses helper tools like `set_income`, `set_category_budget`, and `set_savings_goal`. The memory system (`BudgetMemory`) tracks the user's income, expenses, category budgets, and savings goals across the entire conversation, ensuring that the latest balance and total spending are always accurate when the agent decides if an item is affordable.

**Honest Failure & Resolution:** During development, the agent initially struggled with answering "can I afford this?" because it would try to calculate the balance mathematically using its own prior conversational knowledge instead of calling the `get_summary` tool, which led to hallucinated or outdated balances. To fix this, I updated the system prompt to explicitly command the agent: "When answering questions like 'can I afford X?', always use the get_summary tool to check the current balance... explicitly decide and explain your reasoning based on the tool's result." This successfully forced the agent into a reliable plan-act loop for affordability questions.

**Group Contribution:** This was built as a solo project, but I implemented the "Group of 3 Add-on" by adding `set_savings_goal` and generating a warning when a category is overspent during `add_expense`.

---

## 🌟 Extraordinary Web App & AI Agent Copilot

The project includes an **interactive Dark Glassmorphism Financial Web Application** equipped with a live **AI Assistant Copilot Chatbot**:

- **Real-Time Plan-Act Tool Trace**: Collapsible badges inside the AI chat bubbles display the agent's exact step-by-step tool calls, parameters, and output results.
- **Financial Analytics Dashboard**: Visual Doughnut spending chart, Budget Limit vs Actual Bar Chart, and dynamic KPI cards.
- **Smart Affordability Checker Widget**: Instant evaluation of item cost against live balance and category limits.
- **Interactive Expense Ledger**: Add, search, filter, and delete expenses directly with live synchronization into the agent's memory.
- **Voice Assistant & Audio TTS**: Includes speech-to-text dictation and optional text-to-speech audio responses.

---

## How to Run

### Requirements
Ensure you have Python 3.9+ installed. Dependencies listed in `requirements.txt`:
- `openai`: To communicate with the LLM API (compatible with standard OpenAI or GitHub Models).
- `flask` & `flask-cors`: Web application backend server.
- `jupyter`: For notebook demonstration.

### Setup & Launch Instructions

#### 🌐 Option 1: Launch Web Application & AI Chatbot (Recommended)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the web app:
   - **Windows:** Double-click `run_app.bat` or run:
     ```bash
     python run_app.py
     ```
   - Your browser will automatically open [http://localhost:5000](http://localhost:5000)!

#### 📓 Option 2: Run Jupyter Notebook Demo
1. Start Jupyter:
   ```bash
   jupyter notebook
   ```
2. Open `demo.ipynb` and run the cells in order (`Shift + Enter`).

