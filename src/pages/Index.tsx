import { DollarSign, Wallet, CreditCard, TrendingUp } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { SubscriptionsList } from "@/components/SubscriptionsList";
import { IncomeChart } from "@/components/IncomeChart";
import { AddExpenseForm } from "@/components/AddExpenseForm";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { AvailableMoneyWidget } from "@/components/AvailableMoneyWidget";
import { useState } from "react";
import { toast } from "sonner";

interface Expense {
  id: string;
  name: string;
  price: number;
  status: 'active' | 'cancelled' | 'pending';
  next_billing: string;
  created_at: string;
}

interface Income {
  id: string;
  amount: number;
  date: string;
  name: string;
  created_at: string;
}

const Index = () => {
  const [expenses, setExpenses] = useState<Expense[]>([
    {
      id: '1',
      name: 'Netflix',
      price: 15.99,
      status: 'active',
      next_billing: '2024-03-15',
      created_at: new Date().toISOString(),
    },
    {
      id: '2',
      name: 'Spotify',
      price: 9.99,
      status: 'active',
      next_billing: '2024-03-20',
      created_at: new Date().toISOString(),
    }
  ]);

  const [incomeHistory, setIncomeHistory] = useState<Income[]>([
    {
      id: '1',
      amount: 5000,
      date: '2024-03-01',
      name: 'Salary',
      created_at: new Date().toISOString(),
    }
  ]);

  // Calculate total monthly expenses
  const totalExpenses = expenses.reduce((sum, expense) => sum + expense.price, 0);
  
  // Get the most recent monthly income
  const monthlyIncome = incomeHistory.length > 0 
    ? incomeHistory[incomeHistory.length - 1].amount 
    : 0;

  // Format income data for the chart
  const incomeChartData = incomeHistory.map(income => ({
    date: new Date(income.date).toLocaleString('default', { month: 'short' }),
    amount: income.amount
  }));

  const handleAddExpense = (newExpense: any) => {
    const expense: Expense = {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      ...newExpense
    };
    setExpenses([...expenses, expense]);
    toast.success('Expense added successfully');
  };

  const handleAddIncome = (newIncome: any) => {
    const income: Income = {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      ...newIncome
    };
    setIncomeHistory([...incomeHistory, income]);
    toast.success('Income added successfully');
  };

  const handleDeleteExpense = (id: string) => {
    setExpenses(expenses.filter(expense => expense.id !== id));
    toast.success('Expense deleted successfully');
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="flex justify-end mb-8">
        <DarkModeToggle />
      </div>
      <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
        <h1 className="text-3xl font-bold">Personal Finance Dashboard</h1>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Monthly Income"
            value={`$${monthlyIncome}`}
            icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 12, isPositive: true }}
          />
          <MetricCard
            title="Total Savings"
            value="$12,450"
            icon={<Wallet className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 8.5, isPositive: true }}
          />
          <MetricCard
            title="Monthly Expenses"
            value={`$${totalExpenses.toFixed(2)}`}
            icon={<CreditCard className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 2.4, isPositive: false }}
          />
          <MetricCard
            title="Savings Rate"
            value="32.5%"
            icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 4.2, isPositive: true }}
          />
        </div>

        {/* Available Money Widget */}
        <AvailableMoneyWidget income={monthlyIncome} expenses={totalExpenses} />

        {/* Charts and Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3">
            <IncomeChart data={incomeChartData} />
          </div>
          <div className="lg:col-span-1 space-y-4">
            <AddExpenseForm 
              onAddExpense={handleAddExpense}
              onAddIncome={handleAddIncome}
            />
            <SubscriptionsList 
              subscriptions={expenses} 
              onDeleteExpense={handleDeleteExpense}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;