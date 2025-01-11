import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface AvailableMoneyWidgetProps {
  income: number;
  expenses: number;
}

export function AvailableMoneyWidget({ income, expenses }: AvailableMoneyWidgetProps) {
  const available = income - expenses;
  const percentage = ((available / income) * 100).toFixed(1);

  // Mock data for the last 6 months
  const chartData = [
    { month: 'Jan', amount: 2100 },
    { month: 'Feb', amount: 2300 },
    { month: 'Mar', amount: 1900 },
    { month: 'Apr', amount: 2500 },
    { month: 'May', amount: 2700 },
    { month: 'Jun', amount: available },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card className="transition-all hover:shadow-lg">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Available Money</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-success">${available.toFixed(2)}</div>
          <p className="mt-2 text-xs text-muted-foreground">
            {percentage}% of monthly income
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Available Money Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="amount"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}