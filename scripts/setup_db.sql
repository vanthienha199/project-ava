-- Project Ava: Supabase Database Setup
-- Paste this into Supabase Dashboard -> SQL Editor -> New Query -> Run
--
-- Creates tables: designs, runs, iterations, failures, test_results
-- Enables RLS with anonymous read on all, anonymous insert on result tables

-- ============================================================
-- 1. TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS designs (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL UNIQUE,
    category    text NOT NULL,
    toplevel    text NOT NULL,
    verilog_source text NOT NULL,
    spec        text NOT NULL,
    files       jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS runs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    design_id       uuid REFERENCES designs(id) ON DELETE SET NULL,
    design_name     text NOT NULL,
    backend         text NOT NULL DEFAULT 'claude_cli',
    model           text NOT NULL DEFAULT 'claude-cli',
    passed          boolean NOT NULL,
    total_tests     int NOT NULL DEFAULT 0,
    pass_count      int NOT NULL DEFAULT 0,
    fail_count      int NOT NULL DEFAULT 0,
    iterations      int NOT NULL DEFAULT 0,
    corrections     int NOT NULL DEFAULT 0,
    reboots         int NOT NULL DEFAULT 0,
    total_latency_ms double precision,
    tokens_in       int DEFAULT 0,
    tokens_out      int DEFAULT 0,
    testbench_code  text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS iterations (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            uuid NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    iteration_number  int NOT NULL,
    iteration_type    text NOT NULL,
    ic                int NOT NULL DEFAULT 0,
    ir                int NOT NULL DEFAULT 0,
    passed            boolean NOT NULL,
    pass_count        int NOT NULL DEFAULT 0,
    fail_count        int NOT NULL DEFAULT 0,
    llm_latency_ms    double precision,
    sim_latency_ms    double precision,
    created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS failures (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id  uuid NOT NULL REFERENCES iterations(id) ON DELETE CASCADE,
    run_id        uuid NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    category      text NOT NULL,
    summary       text,
    fixable       boolean,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_results (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        uuid NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    test_name     text NOT NULL,
    status        text NOT NULL,
    sim_time_ns   double precision,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- 2. INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_runs_design_id ON runs(design_id);
CREATE INDEX IF NOT EXISTS idx_runs_design_name ON runs(design_name);
CREATE INDEX IF NOT EXISTS idx_runs_backend ON runs(backend);
CREATE INDEX IF NOT EXISTS idx_iterations_run_id ON iterations(run_id);
CREATE INDEX IF NOT EXISTS idx_failures_run_id ON failures(run_id);
CREATE INDEX IF NOT EXISTS idx_failures_iteration_id ON failures(iteration_id);
CREATE INDEX IF NOT EXISTS idx_test_results_run_id ON test_results(run_id);

-- ============================================================
-- 3. ROW LEVEL SECURITY
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE designs ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE iterations ENABLE ROW LEVEL SECURITY;
ALTER TABLE failures ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_results ENABLE ROW LEVEL SECURITY;

-- Anonymous SELECT on all tables
CREATE POLICY "anon_select_designs" ON designs FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select_runs" ON runs FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select_iterations" ON iterations FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select_failures" ON failures FOR SELECT TO anon USING (true);
CREATE POLICY "anon_select_test_results" ON test_results FOR SELECT TO anon USING (true);

-- Anonymous INSERT on result tables (not designs -- those are seeded once)
CREATE POLICY "anon_insert_runs" ON runs FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_insert_iterations" ON iterations FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_insert_failures" ON failures FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "anon_insert_test_results" ON test_results FOR INSERT TO anon WITH CHECK (true);

-- Also allow anon insert on designs (for initial seeding via script)
CREATE POLICY "anon_insert_designs" ON designs FOR INSERT TO anon WITH CHECK (true);
