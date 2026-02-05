-- Create scan_results table for storing ATS scan results
CREATE TABLE IF NOT EXISTS scan_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    overall_score INTEGER NOT NULL DEFAULT 0,
    field TEXT,
    keyword_relevance INTEGER DEFAULT 0,
    formatting_score INTEGER DEFAULT 0,
    experience_score INTEGER DEFAULT 0,
    strengths JSONB DEFAULT '[]'::jsonb,
    improvements JSONB DEFAULT '[]'::jsonb,
    links JSONB DEFAULT '{}'::jsonb,
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster user queries
CREATE INDEX IF NOT EXISTS idx_scan_results_user_id ON scan_results(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_scanned_at ON scan_results(scanned_at DESC);

-- Enable Row Level Security
ALTER TABLE scan_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own scan results
CREATE POLICY "Users can view own scan results"
    ON scan_results
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own scan results
CREATE POLICY "Users can insert own scan results"
    ON scan_results
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own scan results
CREATE POLICY "Users can delete own scan results"
    ON scan_results
    FOR DELETE
    USING (auth.uid() = user_id);

-- Policy: Service role can do everything (for backend operations)
CREATE POLICY "Service role full access"
    ON scan_results
    FOR ALL
    USING (true)
    WITH CHECK (true);
