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

    // Get income history
    if (method === 'GET') {
      const income = db.queryEntries<{
        id: string;
        amount: number;
        date: string;
        name: string;
        created_at: string;
      }>("SELECT * FROM income_history ORDER BY date DESC");
      
      return new Response(
        JSON.stringify({ income }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Add income
    if (method === 'POST') {
      const { amount, date, name } = await req.json();
      const id = crypto.randomUUID();
      
      db.query(
        "INSERT INTO income_history (id, amount, date, name) VALUES (?, ?, ?, ?)",
        [id, amount, date, name]
      );
      
      return new Response(
        JSON.stringify({ id }),
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