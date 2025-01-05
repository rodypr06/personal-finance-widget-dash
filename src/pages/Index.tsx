import { useState } from "react";
import { DollarSign, Wallet, CreditCard, TrendingUp } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { SubscriptionsList } from "@/components/SubscriptionsList";
import { IncomeChart } from "@/components/IncomeChart";
import { AddExpenseForm } from "@/components/AddExpenseForm";

// Define the Expense type to ensure consistency
interface Expense {
  name: string;
  price: number;
  status: "active" | "cancelled" | "pending";
  nextBilling: string;
}

// Initial mock data
const initialMockSubscriptions: Expense[] = [
  { name: "Rent", price: 1200, status: "active", nextBilling: "2024-05-01" },
  { name: "Utilities", price: 150, status: "pending", nextBilling: "2024-04-28" },
  { name: "Internet", price: 60, status: "active", nextBilling: "2024-05-15" },
];

const mockIncomeData = [
  { date: "Jan", amount: 4200 },
  { date: "Feb", amount: 4200 },
  { date: "Mar", amount: 4500 },
  { date: "Apr", amount: 4200 },
  { date: "May", amount: 4800 },
  { date: "Jun", amount: 4200 },
];

const Index = () => {
  const [subscriptions, setSubscriptions] = useState<Expense[]>(initialMockSubscriptions);

  const handleAddExpense = (newExpense: Expense) => {
    setSubscriptions([...subscriptions, newExpense]);
  };

  // Calculate total monthly expenses
  const totalExpenses = subscriptions.reduce((sum, sub) => sum + sub.price, 0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
        <h1 className="text-3xl font-bold">Personal Finance Dashboard</h1>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Monthly Income"
            value="$4,200"
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

        {/* Charts and Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3">
            <IncomeChart data={mockIncomeData} />
          </div>
          <div className="lg:col-span-1 space-y-4">
            <AddExpenseForm onAddExpense={handleAddExpense} />
            <SubscriptionsList subscriptions={subscriptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;