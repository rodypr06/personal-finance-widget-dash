import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { Database } from "https://deno.land/x/sqlite3@0.9.1/mod.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const db = new Database("finance.db");
    const method = req.method;
    const url = new URL(req.url);
    const path = url.pathname;

    // Get expenses
    if (method === 'GET') {
      const expenses = db.queryEntries<{
        id: string;
        name: string;
        price: number;
        status: string;
        next_billing: string;
        created_at: string;
      }>("SELECT * FROM expenses ORDER BY created_at DESC");
      
      return new Response(
        JSON.stringify({ expenses }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Add expense
    if (method === 'POST') {
      const { name, price, status, next_billing } = await req.json();
      const id = crypto.randomUUID();
      
      db.query(
        "INSERT INTO expenses (id, name, price, status, next_billing) VALUES (?, ?, ?, ?, ?)",
        [id, name, price, status, next_billing]
      );
      
      return new Response(
        JSON.stringify({ id }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Delete expense
    if (method === 'DELETE') {
      const { id } = await req.json();
      db.query("DELETE FROM expenses WHERE id = ?", [id]);
      
      return new Response(
        JSON.stringify({ success: true }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    return new Response(
      JSON.stringify({ error: 'Method not allowed' }),
      { status: 405, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})