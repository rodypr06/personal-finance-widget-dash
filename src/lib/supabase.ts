import { createClient } from '@supabase/supabase-js';

// Ensure we have the environment variables
const supabaseUrl = 'https://bibzeducbhsxlelgpxrc.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpYnplZHVjYmhzeGxlbGdweHJjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDg2MjY1NzcsImV4cCI6MjAyNDIwMjU3N30.YB_HHH3W3_GlDff1EBBpRtqvyGr-tsG0Q8UXxeJfwBY';

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase URL or Key');
}

export const supabase = createClient(supabaseUrl, supabaseKey);

// Type definitions for our database tables
export interface Expense {
  id: string;
  name: string;
  price: number;
  status: 'active' | 'cancelled' | 'pending';
  next_billing: string;
  created_at: string;
  user_id: string;
}

export interface IncomeHistory {
  id: string;
  amount: number;
  date: string;
  created_at: string;
  user_id: string;
}