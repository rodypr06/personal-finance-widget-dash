import { DollarSign, Users, CreditCard, TrendingUp } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { SubscriptionsList } from "@/components/SubscriptionsList";
import { IncomeChart } from "@/components/IncomeChart";

// Mock data - in a real app this would come from an API
const mockSubscriptions = [
  { name: "Premium Plan", price: 29.99, status: "active" as const, nextBilling: "2024-05-01" },
  { name: "Basic Plan", price: 9.99, status: "active" as const, nextBilling: "2024-04-28" },
  { name: "Enterprise", price: 99.99, status: "pending" as const, nextBilling: "2024-05-15" },
];

const mockIncomeData = [
  { date: "Jan", amount: 2400 },
  { date: "Feb", amount: 3600 },
  { date: "Mar", amount: 3200 },
  { date: "Apr", amount: 4500 },
  { date: "May", amount: 4200 },
  { date: "Jun", amount: 5100 },
];

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Revenue"
            value="$24,400"
            icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 12, isPositive: true }}
          />
          <MetricCard
            title="Active Subscribers"
            value="2,451"
            icon={<Users className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 4.5, isPositive: true }}
          />
          <MetricCard
            title="Avg. Subscription"
            value="$39.99"
            icon={<CreditCard className="h-4 w-4 text-muted-foreground" />}
          />
          <MetricCard
            title="Growth Rate"
            value="+15.2%"
            icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
            trend={{ value: 2.4, isPositive: true }}
          />
        </div>

        {/* Charts and Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <IncomeChart data={mockIncomeData} />
          <div className="lg:col-span-1">
            <SubscriptionsList subscriptions={mockSubscriptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;