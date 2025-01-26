import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Expense {
  id: string;
  name: string;
  price: number;
  status: 'active' | 'cancelled' | 'pending';
  next_billing: string;
}

interface SubscriptionsListProps {
  subscriptions: Expense[];
}

export function SubscriptionsList({ subscriptions }: SubscriptionsListProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Expenses</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {subscriptions.map((sub, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 rounded-lg bg-muted/50"
            >
              <div>
                <p className="font-medium">{sub.name}</p>
                <p className="text-sm text-muted-foreground">
                  Due: {sub.next_billing}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span className={cn(
                  "text-sm px-2 py-1 rounded",
                  {
                    "bg-success/20 text-success": sub.status === "active",
                    "bg-destructive/20 text-destructive": sub.status === "cancelled",
                    "bg-yellow-100 text-yellow-800": sub.status === "pending",
                  }
                )}>
                  {sub.status}
                </span>
                <span className="font-bold">${sub.price}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}