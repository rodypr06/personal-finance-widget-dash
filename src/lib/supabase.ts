import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);

// Type definitions for our database tables
export interface Expense {
  id: string;
  name: string;
  price: number;
  status: 'active' | 'cancelled' | 'pending';
  next_billing: string;
  created_at: string;
}

export interface IncomeHistory {
  id: string;
  amount: number;
  date: string;
  created_at: string;
}