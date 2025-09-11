-- Fix permissions only (skip foreign key constraints for now)
-- Run this if you have permission errors

-- 1. Enable RLS on all tables (safe to run multiple times)
ALTER TABLE judges ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE songs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE winners ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration ENABLE ROW LEVEL SECURITY;
ALTER TABLE meta ENABLE ROW LEVEL SECURITY;

-- 2. Create/recreate policies for public access
DROP POLICY IF EXISTS "Public read access" ON judges;
CREATE POLICY "Public read access" ON judges FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON rubrics;
CREATE POLICY "Public read access" ON rubrics FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON keywords;
CREATE POLICY "Public read access" ON keywords FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON variants;
CREATE POLICY "Public read access" ON variants FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON songs;
CREATE POLICY "Public read access" ON songs FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON evaluations;
CREATE POLICY "Public read access" ON evaluations FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON file_metadata;
CREATE POLICY "Public read access" ON file_metadata FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON winners;
CREATE POLICY "Public read access" ON winners FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON configuration;
CREATE POLICY "Public read access" ON configuration FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON meta;
CREATE POLICY "Public read access" ON meta FOR SELECT USING (true);

-- 3. Create policies for public write access (for evaluations)
DROP POLICY IF EXISTS "Public write access" ON evaluations;
CREATE POLICY "Public write access" ON evaluations FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Public update access" ON evaluations;
CREATE POLICY "Public update access" ON evaluations FOR UPDATE USING (true) WITH CHECK (true);

-- 4. Verify policies are created
SELECT 'Checking policies...' as status;
SELECT 
    tablename,
    policyname,
    cmd
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

SELECT 'Permissions fixed successfully!' as status;
