import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ArrowDownIcon, ArrowUpIcon, TrendingUpIcon } from "lucide-react";

interface AvailableMoneyWidgetProps {
  income: number;
  expenses: number;
}

export function AvailableMoneyWidget({ income, expenses }: AvailableMoneyWidgetProps) {
  const available = income - expenses;
  const percentage = ((available / income) * 100).toFixed(1);

  // Mock data for the last 6 months with month-over-month change
  const chartData = [
    { month: 'Jan', amount: 2100, change: -2.5 },
    { month: 'Feb', amount: 2300, change: 9.5 },
    { month: 'Mar', amount: 1900, change: -17.4 },
    { month: 'Apr', amount: 2500, change: 31.6 },
    { month: 'May', amount: 2700, change: 8.0 },
    { month: 'Jun', amount: available, change: ((available - 2700) / 2700 * 100) },
  ];

  const lastMonthChange = chartData[chartData.length - 1].change;
  const isPositiveChange = lastMonthChange > 0;

  return (
    <Card className="transition-all hover:shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium">Available Money</CardTitle>
          <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <div className="text-3xl font-bold text-success">${available.toFixed(2)}</div>
            <div className="flex items-center space-x-2">
              <div className={`flex items-center ${isPositiveChange ? 'text-success' : 'text-destructive'}`}>
                {isPositiveChange ? (
                  <ArrowUpIcon className="h-4 w-4" />
                ) : (
                  <ArrowDownIcon className="h-4 w-4" />
                )}
                <span className="text-sm font-medium">{Math.abs(lastMonthChange).toFixed(1)}%</span>
              </div>
              <span className="text-sm text-muted-foreground">vs last month</span>
            </div>
            <div className="text-sm text-muted-foreground">
              {percentage}% of monthly income
            </div>
          </div>
          
          <div className="md:col-span-2 h-[150px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="month" 
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis 
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip 
                  formatter={(value: number) => [`$${value}`, 'Amount']}
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    border: 'none',
                    borderRadius: '4px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="amount"
                  stroke="#10b981"
                  fill="url(#colorAmount)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}