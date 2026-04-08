import { createClient } from "@supabase/supabase-js";

// Credentials sourced from root .env → mirrored to frontend/.env.local with NEXT_PUBLIC_ prefix
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export const supabase = createClient(
  supabaseUrl || "https://placeholder.supabase.co",
  supabaseAnonKey || "placeholder-anon-key"
);

// True when real credentials are present (not placeholders)
export const isSupabaseConfigured =
  !!supabaseUrl &&
  supabaseUrl !== "https://placeholder.supabase.co" &&
  !supabaseUrl.includes("YOUR_PROJECT_REF");
