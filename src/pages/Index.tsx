import { useState, useEffect } from "react";
import { toast } from "sonner";
import { MetricsGrid } from "@/components/MetricsGrid";
import { DashboardContent } from "@/components/DashboardContent";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { AvailableMoneyWidget } from "@/components/AvailableMoneyWidget";
import { supabase } from "@/integrations/supabase/client";

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
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [incomeHistory, setIncomeHistory] = useState<Income[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch expenses
      const expensesResponse = await fetch(`${supabase.supabaseUrl}/functions/v1/expenses`, {
        headers: {
          Authorization: `Bearer ${supabase.supabaseKey}`,
        },
      });
      const expensesData = await expensesResponse.json();
      
      // Fetch income
      const incomeResponse = await fetch(`${supabase.supabaseUrl}/functions/v1/income`, {
        headers: {
          Authorization: `Bearer ${supabase.supabaseKey}`,
        },
      });
      const incomeData = await incomeResponse.json();
      
      setExpenses(expensesData.expenses || []);
      setIncomeHistory(incomeData.income || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async (newExpense: {
    name: string;
    price: number;
    status: "active" | "cancelled" | "pending";
    next_billing: string;
  }) => {
    try {
      const response = await fetch(`${supabase.supabaseUrl}/functions/v1/expenses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${supabase.supabaseKey}`,
        },
        body: JSON.stringify(newExpense),
      });
      
      if (!response.ok) throw new Error('Failed to add expense');
      
      await fetchData();
      toast.success('Expense added successfully');
    } catch (error) {
      console.error('Error adding expense:', error);
      toast.error('Failed to add expense');
    }
  };

  const handleAddIncome = async (newIncome: {
    amount: number;
    date: string;
    name: string;
  }) => {
    try {
      const response = await fetch(`${supabase.supabaseUrl}/functions/v1/income`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${supabase.supabaseKey}`,
        },
        body: JSON.stringify(newIncome),
      });
      
      if (!response.ok) throw new Error('Failed to add income');
      
      await fetchData();
      toast.success('Income added successfully');
    } catch (error) {
      console.error('Error adding income:', error);
      toast.error('Failed to add income');
    }
  };

  const handleDeleteExpense = async (id: string) => {
    try {
      const response = await fetch(`${supabase.supabaseUrl}/functions/v1/expenses`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${supabase.supabaseKey}`,
        },
        body: JSON.stringify({ id }),
      });
      
      if (!response.ok) throw new Error('Failed to delete expense');
      
      await fetchData();
      toast.success('Expense deleted successfully');
    } catch (error) {
      console.error('Error deleting expense:', error);
      toast.error('Failed to delete expense');
    }
  };

  // Calculate total monthly expenses
  const totalExpenses = expenses.reduce((sum, expense) => sum + expense.price, 0);
  
  // Get the most recent monthly income
  const monthlyIncome = incomeHistory.length > 0 
    ? incomeHistory[0].amount 
    : 0;

  // Format income data for the chart
  const incomeChartData = incomeHistory.map(income => ({
    date: new Date(income.date).toLocaleString('default', { month: 'short' }),
    amount: income.amount
  }));

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

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