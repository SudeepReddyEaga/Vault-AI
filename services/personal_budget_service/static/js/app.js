/* ==========================================================================
   PERSONAL BUDGET ASSISTANT - APP INTERACTIVITY & AI AGENT COPILOT
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let appState = {
        income: 0,
        total_spent: 0,
        balance: 0,
        savings_goal: 0,
        savings_status: '',
        expenses: [],
        category_budgets: {},
        category_status: [],
        category_spending: {},
        warnings: [],
        offline_mode: false
    };

    let doughnutChart = null;
    let barChart = null;
    let ttsEnabled = true;
    let globalTraces = [];


    // --- DOM Elements ---
    const pageTitle = document.getElementById('pageTitle');
    const alertContainer = document.getElementById('alertContainer');
    const modeStatusText = document.getElementById('modeStatusText');

    // KPI Elements
    const kpiIncome = document.getElementById('kpiIncome');
    const kpiSpent = document.getElementById('kpiSpent');
    const kpiSpentPercent = document.getElementById('kpiSpentPercent');
    const kpiBalance = document.getElementById('kpiBalance');
    const balanceProgressBar = document.getElementById('balanceProgressBar');
    const kpiSavingsGoal = document.getElementById('kpiSavingsGoal');
    const kpiSavingsBadge = document.getElementById('kpiSavingsBadge');

    // Category Elements
    const categoryGrid = document.getElementById('categoryGrid');
    const categoryLimitsList = document.getElementById('categoryLimitsList');
    const expenseCategoryFilter = document.getElementById('expenseCategoryFilter');

    // Expense Table Elements
    const expenseTableBody = document.getElementById('expenseTableBody');
    const expenseSearchInput = document.getElementById('expenseSearchInput');

    // Chat Drawer Elements
    const chatDrawer = document.getElementById('chatDrawer');
    const btnToggleChat = document.getElementById('btnToggleChat');
    const btnCloseChat = document.getElementById('btnCloseChat');
    const btnClearChat = document.getElementById('btnClearChat');
    const btnTTSToggle = document.getElementById('btnTTSToggle');
    const ttsIcon = document.getElementById('ttsIcon');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const btnSendChat = document.getElementById('btnSendChat');
    const btnMicInput = document.getElementById('btnMicInput');
    const promptPills = document.querySelectorAll('.prompt-pill');

    // Trace Container
    const globalTraceContainer = document.getElementById('globalTraceContainer');

    // Modals & Buttons
    const btnQuickIncome = document.getElementById('btnQuickIncome');
    const btnQuickSavings = document.getElementById('btnQuickSavings');
    const btnResetSession = document.getElementById('btnResetSession');
    const btnOpenAddExpenseModal = document.getElementById('btnOpenAddExpenseModal');

    const modalIncome = document.getElementById('modalIncome');
    const modalSavings = document.getElementById('modalSavings');
    const modalExpense = document.getElementById('modalExpense');

    // --- Fetch State from API ---
    async function fetchState(year = currentCalYear, month = currentCalMonth) {
        try {
            const res = await fetch(`/api/state?year=${year}&month=${month}`);
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
            }
        } catch (err) {
            console.error('Failed to fetch budget state:', err);
        }
    }


    // --- Main UI Render Dispatcher ---
    function renderUI() {
        // Mode status
        modeStatusText.textContent = appState.offline_mode ? 'Autonomous Local Agent' : 'Cloud LLM Connected';

        // 1. KPI Cards
        kpiIncome.textContent = formatCurrency(appState.income);
        kpiSpent.textContent = formatCurrency(appState.total_spent);
        kpiBalance.textContent = formatCurrency(appState.balance);
        kpiSavingsGoal.textContent = formatCurrency(appState.savings_goal);

        const spentPct = appState.income > 0 ? ((appState.total_spent / appState.income) * 100).toFixed(1) : 0;
        kpiSpentPercent.textContent = `${spentPct}% of income spent`;

        const remPct = appState.income > 0 ? Math.max(0, Math.min(100, ((appState.balance / appState.income) * 100))) : 0;
        balanceProgressBar.style.width = `${remPct}%`;

        if (appState.savings_goal > 0) {
            if (appState.balance >= appState.savings_goal) {
                kpiSavingsBadge.className = 'badge badge-success';
                kpiSavingsBadge.textContent = '🎯 Target Achieved!';
            } else {
                kpiSavingsBadge.className = 'badge badge-warning';
                kpiSavingsBadge.textContent = `Short by ${formatCurrency(appState.savings_goal - appState.balance)}`;
            }
        } else {
            kpiSavingsBadge.className = 'badge badge-info';
            kpiSavingsBadge.textContent = 'No Goal Set';
        }

        // 2. Alert Banners
        renderAlerts();

        // 3. Category Health Grid & Limits
        renderCategories();

        // 4. Expense Table
        renderExpenses();

        // 5. Update Category Filter Dropdown
        updateCategoryFilterOptions();

        // 6. Charts & Calendar
        renderCharts();
        renderCalendar();
    }


    // --- Format Helpers ---
    function formatCurrency(val) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0);
    }

    // --- Alert Banner Rendering ---
    function renderAlerts() {
        alertContainer.innerHTML = '';
        if (appState.warnings && appState.warnings.length > 0) {
            appState.warnings.forEach(warn => {
                const div = document.createElement('div');
                div.className = warn.includes('overspent') ? 'alert-banner alert-danger' : 'alert-banner alert-warning';
                div.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span>${warn}</span>`;
                alertContainer.appendChild(div);
            });
        }
    }

    // --- Render Categories Grid ---
    function renderCategories() {
        categoryGrid.innerHTML = '';
        categoryLimitsList.innerHTML = '';

        const categories = Object.keys(appState.category_budgets);

        if (categories.length === 0) {
            categoryGrid.innerHTML = `<div class="text-muted text-center w-100 py-3">No category budget limits configured yet. Click 'Set Limits' to add one.</div>`;
            categoryLimitsList.innerHTML = `<div class="text-muted text-center py-2">No category limits set.</div>`;
            return;
        }

        categories.forEach(cat => {
            const limit = appState.category_budgets[cat];
            const spent = appState.category_spending[cat] || 0;
            const rem = limit - spent;
            const pct = Math.min(100, Math.round((spent / limit) * 100));
            const isOver = spent > limit;

            // Health Card
            const card = document.createElement('div');
            card.className = 'cat-card';
            card.innerHTML = `
                <div class="cat-header">
                    <span class="cat-title">${escapeHtml(cat)}</span>
                    <span class="badge ${isOver ? 'badge-danger' : (pct > 80 ? 'badge-warning' : 'badge-success')}">
                        ${isOver ? 'OVERSPENT' : `${pct}% Spent`}
                    </span>
                </div>
                <div class="cat-amounts">
                    Spent ${formatCurrency(spent)} of ${formatCurrency(limit)} limit
                </div>
                <div class="progress-bar-wrap">
                    <div class="progress-bar-fill" style="width: ${pct}%; background: ${isOver ? 'var(--accent-coral)' : (pct > 80 ? 'var(--accent-amber)' : 'var(--accent-emerald)')};"></div>
                </div>
            `;
            categoryGrid.appendChild(card);

            // Limit Item
            const item = document.createElement('div');
            item.className = 'category-limit-item';
            item.innerHTML = `
                <div>
                    <strong>${escapeHtml(cat)}</strong>
                    <div class="text-muted" style="font-size: 0.8rem;">Monthly Cap</div>
                </div>
                <div>
                    <span class="badge badge-info" style="font-size: 0.9rem;">${formatCurrency(limit)}</span>
                </div>
            `;
            categoryLimitsList.appendChild(item);
        });
    }

    // --- Update Filter Dropdown ---
    function updateCategoryFilterOptions() {
        const currentVal = expenseCategoryFilter.value;
        const cats = new Set(appState.expenses.map(e => e.category || 'General'));
        Object.keys(appState.category_budgets).forEach(c => cats.add(c));

        expenseCategoryFilter.innerHTML = '<option value="all">All Categories</option>';
        cats.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            expenseCategoryFilter.appendChild(opt);
        });
        expenseCategoryFilter.value = currentVal;
    }

    // --- Render Expenses Table ---
    function renderExpenses() {
        expenseTableBody.innerHTML = '';
        const search = expenseSearchInput.value.toLowerCase().trim();
        const filterCat = expenseCategoryFilter.value;

        const activeList = appState.filtered_expenses || appState.expenses;
        const filtered = activeList.filter((e, idx) => {
            const matchSearch = e.item.toLowerCase().includes(search) || (e.category && e.category.toLowerCase().includes(search));
            const matchCat = filterCat === 'all' || e.category === filterCat;
            return matchSearch && matchCat;
        });


        if (filtered.length === 0) {
            expenseTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No matching expenses found.</td></tr>`;
            return;
        }

        filtered.forEach((e, idx) => {
            let originalIndex = appState.expenses.indexOf(e);
            if (originalIndex === -1) {
                originalIndex = appState.expenses.findIndex(x => 
                    x.item === e.item && 
                    x.amount === e.amount && 
                    (x.category || 'General') === (e.category || 'General') && 
                    (x.date || '') === (e.date || '')
                );
            }
            if (originalIndex === -1) originalIndex = idx;

            const tr = document.createElement('tr');
            const expDate = e.date || new Date().toISOString().split('T')[0];
            tr.innerHTML = `
                <td>${originalIndex + 1}</td>
                <td><strong>${escapeHtml(e.item)}</strong><br><small class="text-muted">${expDate}</small></td>
                <td><span class="badge badge-info">${escapeHtml(e.category || 'General')}</span></td>
                <td><strong style="color: var(--accent-coral);">${formatCurrency(e.amount)}</strong></td>
                <td>
                    <button class="icon-btn edit-expense-btn" data-index="${originalIndex}" data-item="${escapeHtml(e.item)}" title="Edit Expense">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    <button class="icon-btn delete-expense-btn" data-index="${originalIndex}" data-item="${escapeHtml(e.item)}" title="Delete Expense">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            `;
            expenseTableBody.appendChild(tr);
        });

        // Attach edit & delete listeners
        document.querySelectorAll('.edit-expense-btn').forEach(btn => {
            btn.addEventListener('click', (evt) => {
                const idx = parseInt(evt.currentTarget.getAttribute('data-index'));
                openEditExpenseModal(idx);
            });
        });

        document.querySelectorAll('.delete-expense-btn').forEach(btn => {
            btn.addEventListener('click', async (evt) => {
                const idx = parseInt(evt.currentTarget.getAttribute('data-index'));
                const itemName = evt.currentTarget.getAttribute('data-item');
                if (confirm(`Are you sure you want to delete '${itemName}'?`)) {
                    await deleteExpense(idx, itemName);
                }
            });
        });
    }



    let mlChart = null;

    const palettes = {
        cyber: ['#6366f1', '#10b981', '#f59e0b', '#f43f5e', '#06b6d4', '#8b5cf6'],
        sunset: ['#f43f5e', '#f97316', '#eab308', '#ec4899', '#8b5cf6', '#3b82f6'],
        emerald: ['#10b981', '#14b8a6', '#06b6d4', '#0284c7', '#34d399', '#a7f3d0'],
        royal: ['#8b5cf6', '#d946ef', '#eab308', '#f43f5e', '#6366f1', '#fbbf24']
    };

    // --- Audio Voice Response Helper ---
    function speakText(text) {
        if (ttsEnabled && window.speechSynthesis) {
            window.speechSynthesis.cancel(); // stop previous speech
            let cleanText = text.replace(/[#*`_~]/g, ''); // strip markdown
            cleanText = cleanText.replace(/https?:\/\/\S+/g, '');
            cleanText = cleanText.replace(/•/g, ' ');
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => v.lang && v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('Zira')));
            if (preferredVoice) utterance.voice = preferredVoice;

            window.speechSynthesis.speak(utterance);
        }
    }


    // --- Render Chart.js Analytics & Personalization ---
    function renderCharts() {
        const catLabels = Object.keys(appState.category_spending);
        const catData = Object.values(appState.category_spending);

        const chartType = document.getElementById('spendingChartTypeSelector')?.value || 'doughnut';
        const paletteKey = document.getElementById('chartColorPaletteSelector')?.value || 'cyber';
        const chosenColors = palettes[paletteKey] || palettes.cyber;

        const doughnutLabels = catLabels.length > 0 ? catLabels : ['Unallocated'];
        const doughnutValues = catData.length > 0 ? catData : [1];

        // Spending Category Chart (Update cleanly or Create once)
        const canvas1 = document.getElementById('spendingDoughnutChart');
        if (canvas1) {
            if (doughnutChart && doughnutChart.config.type === chartType) {
                doughnutChart.data.labels = doughnutLabels;
                doughnutChart.data.datasets[0].data = doughnutValues;
                doughnutChart.data.datasets[0].backgroundColor = chosenColors;
                doughnutChart.update('none');
            } else {
                if (doughnutChart) doughnutChart.destroy();
                const ctx1 = canvas1.getContext('2d');
                doughnutChart = new Chart(ctx1, {
                    type: chartType,
                    data: {
                        labels: doughnutLabels,
                        datasets: [{
                            data: doughnutValues,
                            backgroundColor: chosenColors,
                            borderWidth: 2,
                            borderColor: '#121524'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 250 },
                        plugins: {
                            legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Inter' } } }
                        }
                    }
                });
            }
        }

        // Bar Chart (Category Limit vs Spent)
        const canvas2 = document.getElementById('budgetBarChart');
        if (canvas2) {
            const allCats = Array.from(new Set([...Object.keys(appState.category_budgets), ...catLabels]));
            const limitSeries = allCats.map(c => appState.category_budgets[c] || 0);
            const spentSeries = allCats.map(c => appState.category_spending[c] || 0);

            const barLabels = allCats.length > 0 ? allCats : ['Food', 'Travel', 'Shopping'];
            const barLimits = limitSeries.length > 0 ? limitSeries : [500, 300, 200];
            const barSpent = spentSeries.length > 0 ? spentSeries : [0, 0, 0];

            if (barChart) {
                barChart.data.labels = barLabels;
                barChart.data.datasets[0].data = barLimits;
                barChart.data.datasets[1].data = barSpent;
                barChart.update('none');
            } else {
                const ctx2 = canvas2.getContext('2d');
                barChart = new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: barLabels,
                        datasets: [
                            {
                                label: 'Budget Limit ($)',
                                data: barLimits,
                                backgroundColor: 'rgba(99, 102, 241, 0.4)',
                                borderColor: '#6366f1',
                                borderWidth: 1
                            },
                            {
                                label: 'Actual Spent ($)',
                                data: barSpent,
                                backgroundColor: 'rgba(244, 63, 94, 0.7)',
                                borderColor: '#f43f5e',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 250 },
                        plugins: {
                            legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Inter' } } }
                        },
                        scales: {
                            x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                            y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                        }
                    }
                });
            }
        }

        // Render ML Forecast Tab Metrics & Chart
        renderMLForecast();
    }


    // --- Render ML Forecast Analytics ---
    function renderMLForecast() {
        const ml = appState.ml_predictions;
        if (!ml) return;

        // KPI Cards
        const predValEl = document.getElementById('mlPredictedSpend');
        const trendBadge = document.getElementById('mlTrendBadge');
        const healthScoreEl = document.getElementById('mlHealthScore');
        const healthBadge = document.getElementById('mlHealthBadge');
        const riskContainer = document.getElementById('mlRiskContainer');

        if (predValEl) predValEl.textContent = formatCurrency(ml.predicted_next_month_total);
        if (trendBadge) {
            trendBadge.textContent = `Trend: ${ml.trend_direction} (${ml.trend_percentage}%)`;
            trendBadge.className = `badge ${ml.trend_percentage > 0 ? 'badge-warning' : 'badge-success'}`;
        }
        if (healthScoreEl && ml.health_score) {
            healthScoreEl.textContent = `${ml.health_score.score} / 100`;
            if (healthBadge) {
                healthBadge.textContent = `Rating: ${ml.health_score.rating}`;
                healthBadge.className = `badge ${ml.health_score.score >= 80 ? 'badge-success' : (ml.health_score.score >= 60 ? 'badge-info' : 'badge-danger')}`;
            }
        }

        // ML Risk Container
        if (riskContainer) {
            riskContainer.innerHTML = '';
            if (ml.risk_flags && ml.risk_flags.length > 0) {
                ml.risk_flags.forEach(r => {
                    const item = document.createElement('div');
                    item.className = 'category-limit-item';
                    item.innerHTML = `
                        <div>
                            <strong>${escapeHtml(r.category)}</strong>
                            <div class="text-muted" style="font-size: 0.8rem;">Limit: ${formatCurrency(r.limit)} | Predicted: ${formatCurrency(r.predicted)}</div>
                        </div>
                        <div>
                            <span class="badge badge-danger">Exceeds by ${formatCurrency(r.exceed_by)}</span>
                        </div>
                    `;
                    riskContainer.appendChild(item);
                });
            } else {
                riskContainer.innerHTML = `<div class="text-muted text-center py-3">✅ No overspend risks predicted for next month.</div>`;
            }
        }

        // ML Forecast Chart (Current Actual vs ML Predicted)
        const ctx3 = document.getElementById('mlForecastChart')?.getContext('2d');
        if (ctx3) {
            if (mlChart) mlChart.destroy();
            const catNames = Object.keys(ml.category_predictions || {});
            const actualVals = catNames.map(c => appState.category_spending[c] || 0);
            const predVals = catNames.map(c => ml.category_predictions[c] || 0);

            mlChart = new Chart(ctx3, {
                type: 'bar',
                data: {
                    labels: catNames.length > 0 ? catNames : ['Food', 'General'],
                    datasets: [
                        {
                            label: 'Current Actual Spent ($)',
                            data: actualVals.length > 0 ? actualVals : [0, 0],
                            backgroundColor: 'rgba(6, 182, 212, 0.6)',
                            borderColor: '#06b6d4',
                            borderWidth: 1
                        },
                        {
                            label: 'ML Forecast Next Month ($)',
                            data: predVals.length > 0 ? predVals : [150, 100],
                            backgroundColor: 'rgba(139, 92, 246, 0.7)',
                            borderColor: '#8b5cf6',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Inter' } } }
                    },
                    scales: {
                        x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    }
                }
            });
        }
    }


    let yearlyChart = null;
    let currentCalYear = new Date().getFullYear();
    let currentCalMonth = new Date().getMonth() + 1;


    // --- Render Financial Calendar & Yearly Ledger ---
    async function renderCalendar(year = currentCalYear, month = currentCalMonth) {
        currentCalYear = year;
        currentCalMonth = month;

        const globalM = document.getElementById('globalMonthSelect');
        const globalY = document.getElementById('globalYearSelect');
        if (globalM && month !== undefined) globalM.value = month;
        if (globalY && year !== undefined) globalY.value = year;

        const monthSelect = document.getElementById('calendarMonthSelect');
        const yearSelect = document.getElementById('calendarYearSelect');
        const titleEl = document.getElementById('calendarMonthYearTitle');
        const gridEl = document.getElementById('calendarCellsGrid');

        if (monthSelect && month !== undefined) monthSelect.value = month;
        if (yearSelect && year !== undefined) yearSelect.value = year;

        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

        if (titleEl) {
            const mText = month === 'all' ? 'All Months' : (monthNames[month - 1] || '');
            const yText = year === 'all' ? 'All Years' : year;
            titleEl.innerHTML = `<i class="fa-solid fa-calendar"></i> ${mText} ${yText}`;
        }


        try {
            const [calRes, yearRes] = await Promise.all([
                fetch(`/api/calendar?year=${year}&month=${month}`).then(r => r.json()),
                fetch(`/api/yearly?year=${year}`).then(r => r.json())
            ]);

            const dailyTotals = calRes.daily_totals || {};
            const monthlySpent = calRes.total_spent || 0;
            const yearlyTotal = yearRes.total_spent || 0;
            const daysInMonth = new Date(year, month, 0).getDate();
            const dailyAvg = daysInMonth > 0 ? monthlySpent / daysInMonth : 0;

            if (document.getElementById('calIncome')) document.getElementById('calIncome').textContent = formatCurrency(appState.income);
            if (document.getElementById('calMonthlySpent')) document.getElementById('calMonthlySpent').textContent = formatCurrency(monthlySpent);
            if (document.getElementById('calBalance')) document.getElementById('calBalance').textContent = formatCurrency(appState.income - monthlySpent);
            if (document.getElementById('calDailyAverage')) document.getElementById('calDailyAverage').textContent = formatCurrency(dailyAvg);


            // Build 7x5 Calendar Grid
            if (gridEl) {
                gridEl.innerHTML = '';
                // Get day of week for 1st day (0 = Sun, 1 = Mon, ...)
                let firstDay = new Date(year, month - 1, 1).getDay();
                firstDay = (firstDay === 0) ? 6 : firstDay - 1; // Mon = 0, Sun = 6

                // Empty cells for offset
                for (let i = 0; i < firstDay; i++) {
                    const emptyCell = document.createElement('div');
                    emptyCell.className = 'calendar-day-cell cell-empty';
                    gridEl.appendChild(emptyCell);
                }

                const todayStr = new Date().toISOString().split('T')[0];

                for (let d = 1; d <= daysInMonth; d++) {
                    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
                    const daySpent = dailyTotals[dateStr] || 0;

                    const cell = document.createElement('div');
                    cell.className = `calendar-day-cell ${dateStr === todayStr ? 'cell-today' : ''}`;
                    
                    cell.innerHTML = `
                        <div class="cell-header">
                            <span class="cell-number">${d}</span>
                            ${daySpent > 0 ? `<span class="cell-badge">$${daySpent.toFixed(0)}</span>` : ''}
                        </div>
                        <div class="cell-dots">
                            ${daySpent > 0 ? '<span class="expense-dot"></span>' : ''}
                        </div>
                    `;

                    // Click cell to add expense on that historical date!
                    cell.addEventListener('click', () => {
                        document.getElementById('modalItemDate').value = dateStr;
                        document.getElementById('modalExpense').classList.remove('hidden');
                    });

                    gridEl.appendChild(cell);
                }
            }

            // Render 12-Month Yearly Expenditure Chart
            const ctxY = document.getElementById('yearlySpendChart')?.getContext('2d');
            if (ctxY && yearRes.monthly_totals) {
                if (yearlyChart) yearlyChart.destroy();
                const mTotals = Object.values(yearRes.monthly_totals);

                yearlyChart = new Chart(ctxY, {
                    type: 'bar',
                    data: {
                        labels: monthNames.map(m => m.substring(0, 3)),
                        datasets: [{
                            label: `Expenditure (${year})`,
                            data: mTotals,
                            backgroundColor: 'rgba(99, 102, 241, 0.7)',
                            borderColor: '#6366f1',
                            borderWidth: 1,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Inter' } } }
                        },
                        scales: {
                            x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                            y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                        }
                    }
                });
            }

        } catch (err) {
            console.error('Calendar load error:', err);
        }
    }

    // --- Open Edit Expense Modal ---
    function openEditExpenseModal(index) {
        if (index < 0 || index >= appState.expenses.length) return;
        const exp = appState.expenses[index];

        document.getElementById('editExpenseIndex').value = index;
        document.getElementById('editItemName').value = exp.item;
        document.getElementById('editItemAmount').value = exp.amount;
        document.getElementById('editItemCategory').value = exp.category || 'General';
        document.getElementById('editItemDate').value = exp.date || new Date().toISOString().split('T')[0];

        document.getElementById('modalEditExpense').classList.remove('hidden');
    }

    async function deleteExpense(index, itemName = null) {
        try {
            const res = await fetch('/api/expense/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index, item: itemName, year: currentCalYear, month: currentCalMonth })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
                renderCalendar(currentCalYear, currentCalMonth);
            } else {
                alert(`Delete failed: ${data.message}`);
            }
        } catch (err) {
            console.error('Delete expense error:', err);
        }
    }


    // --- AI Chat Interface & Plan-Act Trace Logic ---
    async function sendChatMessage(userMsg) {
        if (!userMsg) return;

        // Render user message
        appendMessage('user', userMsg);
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Add loading bot bubble
        const loadingId = appendLoadingMessage();

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg })
            });

            const data = await res.json();
            removeMessage(loadingId);

            if (data.status === 'success') {
                appState = data.data;
                renderUI();

                // Auto-sync Financial Calendar view if tool trace operated on a specific date/month/year!
                if (data.trace && data.trace.length > 0) {
                    for (const t of data.trace) {
                        let y = t.args?.year;
                        let m = t.args?.month;
                        if (!y || !m) {
                            const dtStr = t.args?.date || t.result;
                            const mMatch = (dtStr || '').match(/(\d{4})[\-\/](\d{1,2})/);
                            if (mMatch) {
                                y = parseInt(mMatch[1]);
                                m = parseInt(mMatch[2]);
                            }
                        }
                        if (y && m) {
                            renderCalendar(y, m);
                            break;
                        }
                    }
                }

                // Append Bot response with Plan-Act Tool Trace Badge!
                appendBotResponse(data.response, data.trace);


                // Add trace to global trace log
                if (data.trace && data.trace.length > 0) {
                    globalTraces.push({ userMsg, trace: data.trace, timestamp: new Date().toLocaleTimeString() });
                    renderGlobalTraces();
                }

                // Trigger confetti if savings goal met!
                if (appState.savings_goal > 0 && appState.balance >= appState.savings_goal) {
                    if (window.confetti) confetti({ particleCount: 80, spread: 60, origin: { y: 0.6 } });
                }

                // AI Assistant Voice Audio Response (Reads back answer aloud!)
                speakText(data.response);
            } else {
                appendMessage('bot', `⚠️ Error: ${data.message}`);
                speakText(`Error: ${data.message}`);
            }
        } catch (err) {
            removeMessage(loadingId);
            appendMessage('bot', `⚠️ Connection error: Failed to reach AI Agent.`);
            speakText("Connection error: Failed to reach AI Agent.");
            console.error('Chat error:', err);
        }
    }


    function appendMessage(role, text) {
        const div = document.createElement('div');
        div.className = `message ${role}-message`;
        div.innerHTML = `
            <div class="message-content">
                <p>${formatMarkdown(text)}</p>
            </div>
            <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        `;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendBotResponse(responseMsg, trace) {
        const div = document.createElement('div');
        div.className = 'message bot-message';

        let traceHtml = '';
        if (trace && trace.length > 0) {
            traceHtml = `
                <details class="tool-trace-badge">
                    <summary><i class="fa-solid fa-microchip"></i> ⚡ Executed ${trace.length} Agent Tool Call(s)</summary>
                    ${trace.map(t => `
                        <div class="tool-trace-step">
                            <div>Step ${t.step}: <span class="tool-call-fn">${t.tool}</span>(<span class="tool-call-args">${JSON.stringify(t.args)}</span>)</div>
                            <span class="tool-call-res">└─ Result: ${escapeHtml(t.result)}</span>
                        </div>
                    `).join('')}
                </details>
            `;
        }

        div.innerHTML = `
            <div class="message-content">
                ${traceHtml}
                <div>${formatMarkdown(responseMsg)}</div>
            </div>
            <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        `;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendLoadingMessage() {
        const id = 'loading-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message bot-message';
        div.innerHTML = `
            <div class="message-content">
                <p><i class="fa-solid fa-circle-notch fa-spin"></i> VaultAI Agent planning tool calls...</p>
            </div>
        `;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // --- Markdown Formatter ---
    function formatMarkdown(str) {
        if (!str) return '';
        let text = (str || '').toString();

        // 1. Code blocks ```code```
        text = text.replace(/```([\s\S]*?)```/g, (match, p1) => {
            return `<pre class="chat-code-block"><code>${escapeHtml(p1.trim())}</code></pre>`;
        });

        // 2. Inline code `code`
        text = text.replace(/`([^`]+)`/g, (match, p1) => `<code>${escapeHtml(p1)}</code>`);

        // 3. Bold **text**
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // 4. Bullet lists (lines starting with • or - or *)
        const lines = text.split('\n');
        let html = '';
        let inList = false;

        lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.startsWith('•') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                if (!inList) {
                    html += '<ul class="chat-bullet-list">';
                    inList = true;
                }
                const content = trimmed.replace(/^[•\-\*]\s*/, '');
                html += `<li>${content}</li>`;
            } else {
                if (inList) {
                    html += '</ul>';
                    inList = false;
                }
                if (trimmed.length > 0) {
                    html += `<p>${trimmed}</p>`;
                }
            }
        });
        if (inList) html += '</ul>';

        return html || `<p>${escapeHtml(str)}</p>`;
    }

    function escapeHtml(unsafe) {
        return (unsafe || '').toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --- Render Global Plan-Act Traces Tab ---
    function renderGlobalTraces() {
        if (globalTraces.length === 0) return;
        globalTraceContainer.innerHTML = '';

        globalTraces.forEach((item, index) => {
            const box = document.createElement('div');
            box.className = 'glass-panel mt-3';
            box.innerHTML = `
                <div class="flex-between">
                    <div>
                        <strong>Prompt #${index + 1}:</strong> <em>"${escapeHtml(item.userMsg)}"</em>
                    </div>
                    <span class="text-muted" style="font-size: 0.8rem;">${item.timestamp}</span>
                </div>
                <div class="tool-trace-badge mt-3" style="font-size: 0.85rem;">
                    ${item.trace.map(t => `
                        <div class="tool-trace-step" style="padding: 0.5rem 0;">
                            <div><strong>Step ${t.step}:</strong> Tool <code>${t.tool}</code> called with parameters <code>${JSON.stringify(t.args)}</code></div>
                            <div class="tool-call-res" style="margin-top: 0.3rem;"><strong>Output:</strong> ${escapeHtml(t.result)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            globalTraceContainer.prepend(box);
        });
    }

    // --- Event Listeners & Event Handlers ---
    // Sidebar Navigation
    document.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.getAttribute('data-tab');

            document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');

            pageTitle.textContent = link.querySelector('span').textContent;
        });
    });

    // Chart Personalization Selectors
    document.getElementById('spendingChartTypeSelector')?.addEventListener('change', renderCharts);
    document.getElementById('chartColorPaletteSelector')?.addEventListener('change', renderCharts);

    // Continuous Hands-Free Voice Command Mode
    let continuousVoiceActive = false;
    let voiceRecognitionInstance = null;
    const btnVoiceControl = document.getElementById('btnVoiceControl');

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        voiceRecognitionInstance = new SpeechRec();
        voiceRecognitionInstance.continuous = true;
        voiceRecognitionInstance.interimResults = false;

        voiceRecognitionInstance.onresult = (e) => {
            const lastResultIndex = e.results.length - 1;
            const command = e.results[lastResultIndex][0].transcript.trim();
            console.log('Voice Command Received:', command);

            if (command) {
                // Auto-send voice command to AI Assistant and trigger auto narration!
                ttsEnabled = true;
                chatDrawer.classList.remove('closed');
                document.body.classList.add('chat-open');
                sendChatMessage(command);
            }
        };

        voiceRecognitionInstance.onerror = (e) => console.log('Voice recognition error:', e.error);
        voiceRecognitionInstance.onend = () => {
            if (continuousVoiceActive) {
                try { voiceRecognitionInstance.start(); } catch(err) {}
            }
        };

        btnVoiceControl?.addEventListener('click', () => {
            continuousVoiceActive = !continuousVoiceActive;
            const icon = document.getElementById('voiceControlIcon');
            const txt = document.getElementById('voiceControlText');

            if (continuousVoiceActive) {
                btnVoiceControl.classList.add('listening');
                if (icon) icon.className = 'fa-solid fa-microphone text-danger';
                if (txt) txt.textContent = 'Listening...';
                try { voiceRecognitionInstance.start(); } catch(err) {}
                speakText("Continuous voice command mode activated. Speak your financial commands anytime.");
            } else {
                btnVoiceControl.classList.remove('listening');
                if (icon) icon.className = 'fa-solid fa-microphone-slash';
                if (txt) txt.textContent = 'Voice Commands';
                try { voiceRecognitionInstance.stop(); } catch(err) {}
                speakText("Voice mode paused.");
            }
        });
    }

    // Chat Drawer Toggle
    function toggleChatDrawer() {
        chatDrawer.classList.toggle('closed');
        const isOpen = !chatDrawer.classList.contains('closed');
        if (isOpen) {
            document.body.classList.add('chat-open');
        } else {
            document.body.classList.remove('chat-open');
        }
    }

    btnToggleChat?.addEventListener('click', toggleChatDrawer);
    btnCloseChat?.addEventListener('click', () => {
        chatDrawer?.classList.add('closed');
        document.body.classList.remove('chat-open');
    });

    btnClearChat?.addEventListener('click', () => {
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-content"><p>👋 Chat memory cleared. Ask me anything!</p></div>
                </div>
            `;
        }
    });

    // Stop Voice Output Button (Immediately cancels active speech synthesis)
    const btnStopAudio = document.getElementById('btnStopAudio');
    btnStopAudio?.addEventListener('click', () => {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
    });

    // Voice Response Mute/Unmute Toggle
    btnTTSToggle?.addEventListener('click', () => {
        ttsEnabled = !ttsEnabled;
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel(); // immediately stop active voice output
        }
        if (ttsIcon) ttsIcon.className = ttsEnabled ? 'fa-solid fa-volume-high' : 'fa-solid fa-volume-xmark text-muted';
        if (btnTTSToggle) btnTTSToggle.title = ttsEnabled ? 'Voice Output ON (Click to Mute)' : 'Voice Output OFF (Click to Enable)';
    });

    // Quick Prompt Pills
    promptPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const prompt = pill.getAttribute('data-prompt');
            chatDrawer?.classList.remove('closed');
            sendChatMessage(prompt);
        });
    });

    // Send Chat
    btnSendChat?.addEventListener('click', () => sendChatMessage(chatInput?.value.trim()));
    chatInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage(chatInput.value.trim());
        }
    });

    // Speech Recognition (Dictation)
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRec();
        recognition.continuous = false;
        recognition.interimResults = false;

        btnMicInput?.addEventListener('click', () => {
            btnMicInput.classList.add('recording');
            recognition.start();
        });


        recognition.onresult = (e) => {
            btnMicInput.classList.remove('recording');
            const transcript = e.results[0][0].transcript;
            chatInput.value = transcript;
            sendChatMessage(transcript);
        };

        recognition.onerror = () => btnMicInput.classList.remove('recording');
        recognition.onend = () => btnMicInput.classList.remove('recording');
    } else {
        btnMicInput.style.display = 'none';
    }

    // Modal Control Handlers
    btnQuickIncome?.addEventListener('click', () => modalIncome?.classList.remove('hidden'));
    document.getElementById('btnCloseModalIncome')?.addEventListener('click', () => modalIncome?.classList.add('hidden'));
    document.getElementById('btnCancelModalIncome')?.addEventListener('click', () => modalIncome?.classList.add('hidden'));

    btnQuickSavings?.addEventListener('click', () => modalSavings?.classList.remove('hidden'));
    document.getElementById('btnCloseModalSavings')?.addEventListener('click', () => modalSavings?.classList.add('hidden'));
    document.getElementById('btnCancelModalSavings')?.addEventListener('click', () => modalSavings?.classList.add('hidden'));

    btnOpenAddExpenseModal?.addEventListener('click', () => modalExpense?.classList.remove('hidden'));
    document.getElementById('btnCloseModalExpense')?.addEventListener('click', () => modalExpense?.classList.add('hidden'));
    document.getElementById('btnCancelModalExpense')?.addEventListener('click', () => modalExpense?.classList.add('hidden'));

    // Forms
    document.getElementById('formModalIncome')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const amt = parseFloat(document.getElementById('incomeAmountInput')?.value || '0');
        if (amt >= 0) {
            const res = await fetch('/api/income', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amt })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
                modalIncome?.classList.add('hidden');
                speakText(`Income updated to $${amt.toFixed(2)}.`);
            }
        }
    });

    document.getElementById('formModalSavings')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const amt = parseFloat(document.getElementById('savingsAmountInput')?.value || '0');
        if (amt >= 0) {
            const res = await fetch('/api/savings_goal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amt })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
                modalSavings?.classList.add('hidden');
                speakText(`Savings goal updated to $${amt.toFixed(2)}.`);
            }
        }
    });

    document.getElementById('formCategoryBudget')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cat = document.getElementById('catNameInput')?.value.trim();
        const amt = parseFloat(document.getElementById('catLimitInput')?.value || '0');
        if (cat && amt >= 0) {
            const res = await fetch('/api/category_budget', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category: cat, amount: amt })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
                if (document.getElementById('catNameInput')) document.getElementById('catNameInput').value = '';
                if (document.getElementById('catLimitInput')) document.getElementById('catLimitInput').value = '';
                speakText(`Category budget for ${cat} set to $${amt.toFixed(2)}.`);
            }
        }
    });

    document.getElementById('formAddExpenseModal')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const item = document.getElementById('modalItemName')?.value.trim();
        const amt = parseFloat(document.getElementById('modalItemAmount')?.value || '0');
        const cat = document.getElementById('modalItemCategory')?.value.trim() || 'General';
        const date = document.getElementById('modalItemDate')?.value || new Date().toISOString().split('T')[0];

        if (item && amt > 0) {
            const res = await fetch('/api/expense', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item, amount: amt, category: cat, date })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
                modalExpense?.classList.add('hidden');
                if (document.getElementById('modalItemName')) document.getElementById('modalItemName').value = '';
                if (document.getElementById('modalItemAmount')) document.getElementById('modalItemAmount').value = '';
                speakText(`Added expense ${item} for $${amt.toFixed(2)} in ${cat} on ${date}.`);
            }
        }
    });

    // Edit Expense Modal Handlers
    const modalEditExpense = document.getElementById('modalEditExpense');
    document.getElementById('btnCloseModalEditExpense')?.addEventListener('click', () => modalEditExpense?.classList.add('hidden'));
    document.getElementById('btnCancelModalEditExpense')?.addEventListener('click', () => modalEditExpense?.classList.add('hidden'));

    document.getElementById('formEditExpenseModal')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const idx = parseInt(document.getElementById('editExpenseIndex')?.value || '-1');
        const item = document.getElementById('editItemName')?.value.trim();
        const amt = parseFloat(document.getElementById('editItemAmount')?.value || '0');
        const cat = document.getElementById('editItemCategory')?.value.trim();
        const date = document.getElementById('editItemDate')?.value;

        if (idx >= 0 && item && amt >= 0) {
            const res = await fetch('/api/expense/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index: idx, item, amount: amt, category: cat, date })
            });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                renderUI();
                modalEditExpense?.classList.add('hidden');
                speakText(`Updated expense ${item} for $${amt.toFixed(2)} on ${date}.`);
            }
        }
    });

    // Financial Calendar & Global Period Switcher Controls
    const globalMonthSelect = document.getElementById('globalMonthSelect');
    const globalYearSelect = document.getElementById('globalYearSelect');

    function onPeriodScopeChange(newYear, newMonth) {
        currentCalYear = newYear;
        currentCalMonth = newMonth;
        fetchState(currentCalYear, currentCalMonth);
        renderCalendar(currentCalYear, currentCalMonth);
    }

    globalMonthSelect?.addEventListener('change', (e) => {
        const val = e.target.value;
        const m = val === 'all' ? 'all' : parseInt(val);
        onPeriodScopeChange(currentCalYear, m);
    });

    globalYearSelect?.addEventListener('change', (e) => {
        const val = e.target.value;
        const y = val === 'all' ? 'all' : parseInt(val);
        onPeriodScopeChange(y, currentCalMonth);
    });

    document.getElementById('calendarMonthSelect')?.addEventListener('change', (e) => {
        const val = e.target.value;
        const m = val === 'all' ? 'all' : parseInt(val);
        onPeriodScopeChange(currentCalYear, m);
    });

    document.getElementById('calendarYearSelect')?.addEventListener('change', (e) => {
        const val = e.target.value;
        const y = val === 'all' ? 'all' : parseInt(val);
        onPeriodScopeChange(y, currentCalMonth);
    });



    document.getElementById('btnPrevMonth')?.addEventListener('click', () => {
        let m = currentCalMonth - 1;
        let y = currentCalYear;
        if (m < 1) { m = 12; y--; }
        renderCalendar(y, m);
    });

    document.getElementById('btnNextMonth')?.addEventListener('click', () => {
        let m = currentCalMonth + 1;
        let y = currentCalYear;
        if (m > 12) { m = 1; y++; }
        renderCalendar(y, m);
    });

    // Affordability Form
    document.getElementById('formAffordabilityCheck')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const item = document.getElementById('affItem')?.value.trim();
        const cost = parseFloat(document.getElementById('affCost')?.value || '0');
        const category = document.getElementById('affCategory')?.value;

        try {
            const res = await fetch('/api/affordability', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item, cost, category })
            });
            const data = await res.json();
            const card = document.getElementById('affordabilityResultCard');

            if (data.status === 'success' && card) {
                card.classList.remove('hidden');
                card.className = `result-card mt-4 ${data.affordable ? 'affordable' : 'unaffordable'}`;

                card.innerHTML = `
                    <div class="text-center">
                        <i class="fa-solid ${data.affordable ? 'fa-circle-check text-success' : 'fa-circle-xmark text-danger'}" style="font-size: 2.5rem;"></i>
                        <h3 class="mt-2">${data.affordable ? `YES! You can afford ${escapeHtml(item)}` : `NO! Cannot afford ${escapeHtml(item)}`}</h3>
                    </div>
                    <div class="mt-3">
                        <div class="flex-between py-1"><span>Current Balance:</span> <strong>${formatCurrency(data.current_balance)}</strong></div>
                        <div class="flex-between py-1"><span>Item Cost:</span> <strong style="color: var(--accent-coral);">${formatCurrency(data.cost)}</strong></div>
                        <div class="flex-between py-1"><span>Balance After Purchase:</span> <strong>${formatCurrency(data.remaining_balance)}</strong></div>
                        ${data.category_overspent_warning ? `
                            <div class="alert-banner alert-danger mt-3">
                                <i class="fa-solid fa-triangle-exclamation"></i>
                                <span>Warning: Purchase will exceed your ${escapeHtml(category)} category budget limit of ${formatCurrency(data.category_limit)}!</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
        } catch (err) {
            console.error('Affordability error:', err);
        }
    });

    // Reset Memory
    btnResetSession?.addEventListener('click', async () => {
        if (confirm('Are you sure you want to reset all income, expenses, and chat history?')) {
            const res = await fetch('/api/reset', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                appState = data.data;
                globalTraces = [];
                renderUI();
                renderGlobalTraces();
                alert('Budget memory reset successfully!');
            }
        }
    });

    // Search and Filter Listeners
    expenseSearchInput?.addEventListener('input', renderExpenses);
    expenseCategoryFilter?.addEventListener('change', renderExpenses);

    // Bootstrap
    fetchState();
});

