import { DollarSign, Wallet, CreditCard, TrendingUp } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";

interface MetricsGridProps {
  monthlyIncome: number;
  totalExpenses: number;
}

export function MetricsGrid({ monthlyIncome, totalExpenses }: MetricsGridProps) {
  return (
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
  );
}