import { useState } from "react";
import { toast } from "sonner";
import { MetricsGrid } from "@/components/MetricsGrid";
import { DashboardContent } from "@/components/DashboardContent";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { AvailableMoneyWidget } from "@/components/AvailableMoneyWidget";

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
        
        <MetricsGrid 
          monthlyIncome={monthlyIncome}
          totalExpenses={totalExpenses}
        />

        <AvailableMoneyWidget 
          income={monthlyIncome} 
          expenses={totalExpenses} 
        />

        <DashboardContent 
          expenses={expenses}
          incomeChartData={incomeChartData}
          onAddExpense={handleAddExpense}
          onAddIncome={handleAddIncome}
          onDeleteExpense={handleDeleteExpense}
        />
      </div>
    </div>
  );
};

export default Index;