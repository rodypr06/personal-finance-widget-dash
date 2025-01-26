import { IncomeChart } from "@/components/IncomeChart";
import { AddExpenseForm } from "@/components/AddExpenseForm";
import { SubscriptionsList } from "@/components/SubscriptionsList";

interface DashboardContentProps {
  expenses: Array<{
    id: string;
    name: string;
    price: number;
    status: "active" | "cancelled" | "pending";
    next_billing: string;
  }>;
  incomeChartData: Array<{
    date: string;
    amount: number;
  }>;
  onAddExpense: (expense: {
    name: string;
    price: number;
    status: "active" | "cancelled" | "pending";
    next_billing: string;
  }) => void;
  onAddIncome: (income: {
    amount: number;
    date: string;
    name: string;
  }) => void;
  onDeleteExpense: (id: string) => void;
}

export function DashboardContent({
  expenses,
  incomeChartData,
  onAddExpense,
  onAddIncome,
  onDeleteExpense,
}: DashboardContentProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div className="lg:col-span-3">
        <IncomeChart data={incomeChartData} />
      </div>
      <div className="lg:col-span-1 space-y-4">
        <AddExpenseForm 
          onAddExpense={onAddExpense}
          onAddIncome={onAddIncome}
        />
        <SubscriptionsList 
          subscriptions={expenses} 
          onDeleteExpense={onDeleteExpense}
        />
      </div>
    </div>
  );
}