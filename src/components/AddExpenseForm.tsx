import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

interface AddExpenseFormProps {
  onAddExpense: (expense: {
    name: string;
    price: number;
    status: "active" | "cancelled" | "pending";
    next_billing: string;
  }) => void;
  onAddIncome: (income: {
    amount: number;
    date: string;
  }) => void;
}

export function AddExpenseForm({ onAddExpense, onAddIncome }: AddExpenseFormProps) {
  const [entryType, setEntryType] = useState<"expense" | "income">("expense");
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [status, setStatus] = useState<"active" | "cancelled" | "pending">("active");
  const [date, setDate] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (entryType === "expense") {
      if (!name || !amount || !date) {
        toast.error("Please fill in all fields");
        return;
      }

      onAddExpense({
        name,
        price: parseFloat(amount),
        status,
        next_billing: date,
      });
    } else {
      if (!amount || !date) {
        toast.error("Please fill in all fields");
        return;
      }

      onAddIncome({
        amount: parseFloat(amount),
        date,
      });
    }

    // Reset form
    setName("");
    setAmount("");
    setStatus("active");
    setDate("");
    
    toast.success(`${entryType === "expense" ? "Expense" : "Income"} added successfully`);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-white rounded-lg shadow-sm dark:bg-gray-800">
      <div className="space-y-2">
        <RadioGroup
          value={entryType}
          onValueChange={(value: "expense" | "income") => setEntryType(value)}
          className="flex gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="expense" id="expense" />
            <Label htmlFor="expense">Expense</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="income" id="income" />
            <Label htmlFor="income">Income</Label>
          </div>
        </RadioGroup>
      </div>

      {entryType === "expense" && (
        <div className="space-y-2">
          <Input
            placeholder="Expense name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
      )}
      
      <div className="space-y-2">
        <Input
          type="number"
          step="0.01"
          placeholder={`${entryType === "expense" ? "Amount" : "Income amount"}`}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </div>

      {entryType === "expense" && (
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
      )}

      <div className="space-y-2">
        <Input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>

      <Button type="submit" className="w-full">
        Add {entryType === "expense" ? "Expense" : "Income"}
      </Button>
    </form>
  );
}