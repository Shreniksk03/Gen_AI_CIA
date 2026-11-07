-- ==============================================================================
-- FRAUD SENTINEL — MIGRATION 001: ALIGN SUPABASE POSTGRESQL SCHEMA
-- Safe, idempotent migration to add extended columns to public.transactions
-- Run in Supabase Dashboard -> SQL Editor (https://supabase.com/dashboard/project/_/sql)
-- ==============================================================================

-- 1. Ensure UUID extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Add missing columns safely to public.transactions without data loss
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'LOW';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS review_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS merchant VARCHAR(255) DEFAULT 'Global Payment Terminal';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS merchant_category VARCHAR(100) DEFAULT 'Online Retail';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS location VARCHAR(255) DEFAULT 'Secure POS Gateway';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS card_last4 VARCHAR(10) DEFAULT '4242';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS model_version VARCHAR(50) DEFAULT 'xgboost-tree-explainer-v2.0';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS analyst_notes TEXT;
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS top_contributors JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS summary_narrative JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now());

-- 3. Create analyst audit history table if not exists
CREATE TABLE IF NOT EXISTS public.transaction_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES public.transactions(id) ON DELETE CASCADE,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    analyst_notes TEXT,
    reviewed_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. Fast Telemetry Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_time ON public.transactions (transaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_fraud_prob ON public.transactions (fraud_probability DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_flagged ON public.transactions (is_flagged);
CREATE INDEX IF NOT EXISTS idx_transactions_risk_level ON public.transactions (risk_level);
CREATE INDEX IF NOT EXISTS idx_transactions_review_status ON public.transactions (review_status);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON public.transactions (merchant);
CREATE INDEX IF NOT EXISTS idx_reviews_tx_id ON public.transaction_reviews (transaction_id);

-- 5. Row Level Security (RLS) Configuration
-- We keep RLS enabled for high security!
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_reviews ENABLE ROW LEVEL SECURITY;

-- Service Role Key (SUPABASE_SERVICE_ROLE_KEY) automatically bypasses RLS on the server.
-- Optional scoped read-only policy for authenticated/anon dashboard telemetry:
DROP POLICY IF EXISTS "Allow public read telemetry" ON public.transactions;
CREATE POLICY "Allow public read telemetry"
ON public.transactions
FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "Allow public read reviews" ON public.transaction_reviews;
CREATE POLICY "Allow public read reviews"
ON public.transaction_reviews
FOR SELECT
TO anon, authenticated
USING (true);

-- Reload PostgREST schema cache so new columns are immediately detected
NOTIFY pgrst, 'reload schema';

