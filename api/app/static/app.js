/**
 * Finance Automation - Client-side Application
 * Handles dashboard updates, charts, and API communication
 */

// ========================================
// Configuration
// ========================================

const CONFIG = {
    apiBaseUrl: '/api',
    chartColors: {
        primary: '#00D4FF',
        secondary: '#A855F7',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6',
        purple: '#C084FC',
        cyan: '#67E8F9'
    },
    categoryColors: {
        'Groceries': '#10B981',
        'Dining': '#F59E0B',
        'Transport': '#3B82F6',
        'Fuel': '#EF4444',
        'Utilities': '#A855F7',
        'Subscriptions': '#00D4FF',
        'Shopping': '#C084FC',
        'Healthcare': '#10B981',
        'Entertainment': '#F59E0B',
        'Travel': '#3B82F6'
    }
};

// ========================================
// API Client
// ========================================

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async getSummary(month) {
        return this.request(`/report/summary?month=${month}`);
    }

    async getAlerts() {
        return this.request('/alerts');
    }

    async getTransactions(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/transactions?${params}`);
    }

    async categorizeTransaction(id) {
        return this.request(`/categorize/${id}`, { method: 'POST' });
    }

    async finalizeTransaction(id, data) {
        return this.request(`/finalize/${id}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// ========================================
// Chart Utilities
// ========================================

class ChartManager {
    constructor() {
        this.charts = {};
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#E0E0E0',
                        font: {
                            family: 'Inter, sans-serif'
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#9CA3AF'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#9CA3AF',
                        callback: function(value) {
                            return '$' + (value / 100).toFixed(0);
                        }
                    }
                }
            }
        };
    }

    createDonutChart(canvasId, data, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const colors = labels.map(label =>
            CONFIG.categoryColors[label] || CONFIG.chartColors.primary
        );

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#E0E0E0',
                            padding: 15,
                            font: {
                                family: 'Inter, sans-serif',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${FinanceApp.formatCurrency(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    createLineChart(canvasId, data, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily Spending',
                    data: data,
                    borderColor: CONFIG.chartColors.primary,
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Spent: ${FinanceApp.formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    createBarChart(canvasId, data, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        const colors = labels.map(label =>
            CONFIG.categoryColors[label] || CONFIG.chartColors.secondary
        );

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Amount',
                    data: data,
                    backgroundColor: colors,
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        display: false
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    createTrendChart(canvasId, incomeData, expenseData, labels) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Income',
                        data: incomeData,
                        borderColor: CONFIG.chartColors.success,
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        tension: 0.4
                    },
                    {
                        label: 'Expenses',
                        data: expenseData,
                        borderColor: CONFIG.chartColors.danger,
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        tension: 0.4
                    }
                ]
            },
            options: this.defaultOptions
        });

        return this.charts[canvasId];
    }
}

// ========================================
// Dashboard Controller
// ========================================

class Dashboard {
    constructor() {
        this.api = new ApiClient(CONFIG.apiBaseUrl);
        this.charts = new ChartManager();
        this.currentMonth = this.getCurrentMonth();
    }

    getCurrentMonth() {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    }

    async init() {
        this.initMonthSelector();
        await this.loadData();
        this.setupEventListeners();
    }

    initMonthSelector() {
        const selector = document.getElementById('month-selector');
        if (!selector) return;

        const now = new Date();
        const months = [];

        // Generate last 12 months
        for (let i = 0; i < 12; i++) {
            const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
            const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            const label = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
            months.push({ value, label });
        }

        selector.innerHTML = months.map(m =>
            `<option value="${m.value}" ${m.value === this.currentMonth ? 'selected' : ''}>${m.label}</option>`
        ).join('');
    }

    setupEventListeners() {
        const selector = document.getElementById('month-selector');
        if (selector) {
            selector.addEventListener('change', (e) => {
                this.currentMonth = e.target.value;
                this.loadData();
            });
        }
    }

    async loadData() {
        try {
            const data = await this.api.getSummary(this.currentMonth);
            this.updateSummaryCards(data);
            this.updateCharts(data);
            this.updateTables(data);
        } catch (error) {
            FinanceApp.showError('Failed to load dashboard data: ' + error.message);
        }
    }

    updateSummaryCards(data) {
        // Total Income
        const incomeEl = document.getElementById('total-income');
        const totalIncome = data.totals_by_category
            ?.filter(c => c.category === 'Income')
            .reduce((sum, c) => sum + c.amount_cents, 0) || 0;
        incomeEl.textContent = FinanceApp.formatCurrency(totalIncome);

        // Total Expenses
        const expensesEl = document.getElementById('total-expenses');
        const totalExpenses = data.totals_by_category
            ?.filter(c => c.category !== 'Income')
            .reduce((sum, c) => sum + c.amount_cents, 0) || 0;
        expensesEl.textContent = FinanceApp.formatCurrency(totalExpenses);

        // Net Savings
        const savingsEl = document.getElementById('net-savings');
        const netSavings = totalIncome - totalExpenses;
        savingsEl.textContent = FinanceApp.formatCurrency(netSavings);

        // Savings Rate
        const rateEl = document.getElementById('savings-rate');
        const savingsRate = totalIncome > 0 ? (netSavings / totalIncome) : 0;
        rateEl.textContent = FinanceApp.formatPercent(savingsRate);
    }

    updateCharts(data) {
        // Category Donut Chart
        if (data.totals_by_category) {
            const categories = data.totals_by_category
                .filter(c => c.category !== 'Income')
                .sort((a, b) => b.amount_cents - a.amount_cents)
                .slice(0, 5);

            this.charts.createDonutChart(
                'category-chart',
                categories.map(c => c.amount_cents),
                categories.map(c => c.category)
            );
        }

        // Daily Spending Chart
        if (data.timeseries) {
            this.charts.createLineChart(
                'daily-chart',
                data.timeseries.map(t => t.sum_cents),
                data.timeseries.map(t => new Date(t.date).getDate())
            );
        }
    }

    updateTables(data) {
        // Top Vendors
        const vendorsBody = document.getElementById('vendors-table-body');
        if (vendorsBody && data.top_vendors) {
            vendorsBody.innerHTML = data.top_vendors
                .slice(0, 10)
                .map(v => `
                    <tr>
                        <td><strong>${v.vendor || 'Unknown'}</strong></td>
                        <td class="text-red">${FinanceApp.formatCurrency(v.amount_cents)}</td>
                        <td>${v.transaction_count || 0}</td>
                        <td>${FinanceApp.formatCurrency(v.amount_cents / (v.transaction_count || 1))}</td>
                        <td><span class="badge">${v.category || 'Uncategorized'}</span></td>
                    </tr>
                `).join('');
        }

        // Recent Transactions (mock data for now)
        const txnsBody = document.getElementById('transactions-table-body');
        if (txnsBody) {
            txnsBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No recent transactions</td></tr>';
        }
    }
}

// ========================================
// Reports Controller
// ========================================

class Reports {
    constructor() {
        this.api = new ApiClient(CONFIG.apiBaseUrl);
        this.charts = new ChartManager();
    }

    async init() {
        this.initDatePickers();
        await this.loadData();
        window.reportsInstance = this;
    }

    initDatePickers() {
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

        const startDate = document.getElementById('start-date');
        const endDate = document.getElementById('end-date');

        if (startDate) {
            startDate.value = firstDay.toISOString().split('T')[0];
        }
        if (endDate) {
            endDate.value = lastDay.toISOString().split('T')[0];
        }
    }

    async loadData() {
        try {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;

            // For now, use summary endpoint
            const month = startDate.substring(0, 7);
            const data = await this.api.getSummary(month);

            this.updateStatistics(data);
            this.updateCharts(data);
            this.loadTransactions();
        } catch (error) {
            FinanceApp.showError('Failed to load report data: ' + error.message);
        }
    }

    updateStatistics(data) {
        document.getElementById('report-total-txns').textContent =
            data.totals_by_category?.reduce((sum, c) => sum + (c.count || 0), 0) || 0;

        const totalAmount = data.totals_by_category
            ?.reduce((sum, c) => sum + c.amount_cents, 0) || 0;
        const days = 30; // Approximate
        document.getElementById('report-avg-daily').textContent =
            FinanceApp.formatCurrency(totalAmount / days);

        document.getElementById('report-max-expense').textContent = '$0.00';
        document.getElementById('report-category-count').textContent =
            data.totals_by_category?.length || 0;
    }

    updateCharts(data) {
        // Monthly trend (mock for now)
        if (data.timeseries) {
            const labels = data.timeseries.map(t => FinanceApp.formatDate(t.date));
            const expenses = data.timeseries.map(t => t.sum_cents);
            const income = data.timeseries.map(() => 0);

            this.charts.createTrendChart('trend-chart', income, expenses, labels);
        }

        // Category bar chart
        if (data.totals_by_category) {
            const top10 = data.totals_by_category
                .sort((a, b) => b.amount_cents - a.amount_cents)
                .slice(0, 10);

            this.charts.createBarChart(
                'category-bar-chart',
                top10.map(c => c.amount_cents),
                top10.map(c => c.category)
            );
        }
    }

    async loadTransactions(page = 1) {
        const tbody = document.getElementById('report-table-body');
        if (!tbody) return;

        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No transactions found</td></tr>';
        document.getElementById('showing-count').textContent = '0';
    }

    sortTable(column, ascending) {
        // TODO: Implement table sorting
        console.log('Sort column', column, 'ascending:', ascending);
    }
}

// ========================================
// Global Functions
// ========================================

function sortTable(column) {
    console.log('Sort table by column', column);
    // TODO: Implement sorting logic
}

// Export for use in templates
window.Dashboard = Dashboard;
window.Reports = Reports;
