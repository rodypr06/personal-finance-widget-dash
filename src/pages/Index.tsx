import { DollarSign, Wallet, CreditCard, TrendingUp } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { SubscriptionsList } from "@/components/SubscriptionsList";
import { IncomeChart } from "@/components/IncomeChart";
import { AddExpenseForm } from "@/components/AddExpenseForm";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { AvailableMoneyWidget } from "@/components/AvailableMoneyWidget";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { supabase, type Expense, type IncomeHistory } from "@/lib/supabase";
import { toast } from "sonner";
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { useEffect, useState } from "react";

const Index = () => {
  const queryClient = useQueryClient();
  const [session, setSession] = useState(null);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Fetch expenses
  const { data: expenses = [], isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('expenses')
        .select('*')
        .order('next_billing', { ascending: true });
      
      if (error) {
        toast.error('Failed to fetch expenses');
        throw error;
      }
      
      return data as Expense[];
    },
    enabled: !!session, // Only fetch when user is authenticated
  });

  // Fetch income history
  const { data: incomeHistory = [], isLoading: incomeLoading } = useQuery({
    queryKey: ['income'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('income_history')
        .select('*')
        .order('date', { ascending: true });
      
      if (error) {
        toast.error('Failed to fetch income history');
        throw error;
      }
      
      return data as IncomeHistory[];
    },
    enabled: !!session, // Only fetch when user is authenticated
  });

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

  const handleAddExpense = async (newExpense: Omit<Expense, 'id' | 'created_at'>) => {
    if (!session?.user?.id) {
      toast.error('You must be logged in to add expenses');
      return;
    }

    const { error } = await supabase
      .from('expenses')
      .insert([{ ...newExpense, user_id: session.user.id }]);

    if (error) {
      toast.error('Failed to add expense');
      return;
    }

    toast.success('Expense added successfully');
    queryClient.invalidateQueries({ queryKey: ['expenses'] });
  };

  if (!session) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Auth 
            supabaseClient={supabase}
            appearance={{ theme: ThemeSupa }}
            providers={['google']}
          />
        </div>
      </div>
    );
  }

  if (expensesLoading || incomeLoading) {
    return <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
    </div>;
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="flex justify-between items-center mb-8">
        <DarkModeToggle />
        <button
          onClick={() => supabase.auth.signOut()}
          className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
        >
          Sign Out
        </button>
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
            <AddExpenseForm onAddExpense={handleAddExpense} />
            <SubscriptionsList subscriptions={expenses} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;