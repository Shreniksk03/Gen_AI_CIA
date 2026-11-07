-- Supabase PostgreSQL Schema for Financial Fraud Detection System
-- Run in Supabase Dashboard -> SQL Editor

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_time TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    amount NUMERIC(12, 2) NOT NULL,
    v_features JSONB NOT NULL,
    fraud_probability DOUBLE PRECISION NOT NULL,
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW',
    review_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    merchant VARCHAR(255) DEFAULT 'Global Payment Terminal',
    merchant_category VARCHAR(100) DEFAULT 'Online Retail',
    location VARCHAR(255) DEFAULT 'Secure POS Gateway',
    card_last4 VARCHAR(10) DEFAULT '4242',
    model_version VARCHAR(50) DEFAULT 'xgboost-tree-explainer-v2.0',
    analyst_notes TEXT,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    shap_explanations JSONB NOT NULL,
    top_contributors JSONB,
    summary_narrative JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Audit history table for analyst reviews
CREATE TABLE IF NOT EXISTS transaction_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    analyst_notes TEXT,
    reviewed_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Fast telemetry indexes
CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions (transaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_fraud_prob ON transactions (fraud_probability DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_flagged ON transactions (is_flagged);
CREATE INDEX IF NOT EXISTS idx_transactions_risk_level ON transactions (risk_level);
CREATE INDEX IF NOT EXISTS idx_transactions_review_status ON transactions (review_status);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant_cat ON transactions (merchant_category);
CREATE INDEX IF NOT EXISTS idx_reviews_tx_id ON transaction_reviews (transaction_id);

-- Row Level Security (RLS) Settings
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_reviews ENABLE ROW LEVEL SECURITY;

-- Allow trusted backend inserts (when using anon or authenticated roles)
DROP POLICY IF EXISTS "Allow backend insert" ON transactions;
CREATE POLICY "Allow backend insert" 
ON transactions 
FOR INSERT 
TO anon, authenticated 
WITH CHECK (true);

-- Allow telemetry reads for live dashboard feeds
DROP POLICY IF EXISTS "Allow backend select" ON transactions;
CREATE POLICY "Allow backend select" 
ON transactions 
FOR SELECT 
TO anon, authenticated 
USING (true);

-- Allow updates for analyst review workflow
DROP POLICY IF EXISTS "Allow backend update" ON transactions;
CREATE POLICY "Allow backend update" 
ON transactions 
FOR UPDATE 
TO anon, authenticated 
USING (true);

DROP POLICY IF EXISTS "Allow reviews insert" ON transaction_reviews;
CREATE POLICY "Allow reviews insert" 
ON transaction_reviews 
FOR INSERT 
TO anon, authenticated 
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow reviews select" ON transaction_reviews;
CREATE POLICY "Allow reviews select" 
ON transaction_reviews 
FOR SELECT 
TO anon, authenticated 
USING (true);

-- Note: When the backend uses SUPABASE_SERVICE_ROLE_KEY, it bypasses RLS automatically.
