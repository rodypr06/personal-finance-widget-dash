import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

interface AddExpenseFormProps {
  onAddExpense: (expense: {
    name: string;
    price: number;
    status: "active" | "cancelled" | "pending";
    nextBilling: string;
  }) => void;
}

export function AddExpenseForm({ onAddExpense }: AddExpenseFormProps) {
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [status, setStatus] = useState<"active" | "cancelled" | "pending">("active");
  const [nextBilling, setNextBilling] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !price || !nextBilling) {
      toast.error("Please fill in all fields");
      return;
    }

    onAddExpense({
      name,
      price: parseFloat(price),
      status,
      nextBilling,
    });

    // Reset form
    setName("");
    setPrice("");
    setStatus("active");
    setNextBilling("");
    
    toast.success("Expense added successfully");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-white rounded-lg shadow-sm">
      <div className="space-y-2">
        <Input
          placeholder="Expense name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      
      <div className="space-y-2">
        <Input
          type="number"
          step="0.01"
          placeholder="Amount"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Select value={status} onValueChange={(value: "active" | "cancelled" | "pending") => setStatus(value)}>
          <SelectTrigger>
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Input
          type="date"
          value={nextBilling}
          onChange={(e) => setNextBilling(e.target.value)}
        />
      </div>

      <Button type="submit" className="w-full">
        Add Expense
      </Button>
    </form>
  );
}