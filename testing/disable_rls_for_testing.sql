-- Disable RLS for testing purposes
-- This is the simplest way to fix permission issues during development

-- Disable RLS on all tables
ALTER TABLE judges DISABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics DISABLE ROW LEVEL SECURITY;
ALTER TABLE keywords DISABLE ROW LEVEL SECURITY;
ALTER TABLE variants DISABLE ROW LEVEL SECURITY;
ALTER TABLE songs DISABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations DISABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata DISABLE ROW LEVEL SECURITY;
ALTER TABLE winners DISABLE ROW LEVEL SECURITY;
ALTER TABLE configuration DISABLE ROW LEVEL SECURITY;
ALTER TABLE meta DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies (to clean up)
DROP POLICY IF EXISTS "Public read access" ON judges;
DROP POLICY IF EXISTS "Public read access" ON rubrics;
DROP POLICY IF EXISTS "Public read access" ON keywords;
DROP POLICY IF EXISTS "Public read access" ON variants;
DROP POLICY IF EXISTS "Public read access" ON songs;
DROP POLICY IF EXISTS "Public read access" ON evaluations;
DROP POLICY IF EXISTS "Public read access" ON file_metadata;
DROP POLICY IF EXISTS "Public read access" ON winners;
DROP POLICY IF EXISTS "Public read access" ON configuration;
DROP POLICY IF EXISTS "Public read access" ON meta;
DROP POLICY IF EXISTS "Public write access" ON evaluations;
DROP POLICY IF EXISTS "Public update access" ON evaluations;

-- Verify RLS is disabled
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('judges', 'rubrics', 'keywords', 'variants', 'songs', 'evaluations', 'file_metadata', 'winners', 'configuration', 'meta')
ORDER BY tablename;

SELECT 'RLS disabled for all tables - full access granted for testing!' as status;
