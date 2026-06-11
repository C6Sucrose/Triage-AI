import { createClient as _createSupabaseClient, SupabaseClient } from "@supabase/supabase-js";

let _cachedClient: SupabaseClient | null = null;

export function createAnonClient(): SupabaseClient {
  if (_cachedClient) return _cachedClient;

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !anonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables",
    );
  }

  _cachedClient = _createSupabaseClient(supabaseUrl, anonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  return _cachedClient;
}