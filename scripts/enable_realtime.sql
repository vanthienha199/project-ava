-- Enable Supabase Realtime on agent tables
-- Paste this into Supabase Dashboard -> SQL Editor -> New Query -> Run

-- 1. Enable realtime on tables the Live page watches
ALTER PUBLICATION supabase_realtime ADD TABLE runs;
ALTER PUBLICATION supabase_realtime ADD TABLE iterations;
ALTER PUBLICATION supabase_realtime ADD TABLE test_results;

-- 2. Allow anonymous UPDATE on runs (reporter needs to PATCH running rows)
CREATE POLICY "anon_update_runs" ON runs FOR UPDATE TO anon USING (true) WITH CHECK (true);
