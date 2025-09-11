-- Force disable RLS and grant full permissions
-- This is the nuclear option for development/testing

-- 1. Drop ALL policies first
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Drop all policies on all tables
    FOR r IN (
        SELECT schemaname, tablename, policyname 
        FROM pg_policies 
        WHERE schemaname = 'public'
    ) LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', r.policyname, r.schemaname, r.tablename);
    END LOOP;
END $$;

-- 2. Disable RLS on all tables
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

-- 3. Grant full permissions to anon role (for development)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO anon;

-- 4. Grant full permissions to authenticated role
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

-- 5. Verify RLS is disabled
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN '❌ RLS ENABLED' 
        ELSE '✅ RLS DISABLED' 
    END as status
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('judges', 'rubrics', 'keywords', 'variants', 'songs', 'evaluations', 'file_metadata', 'winners', 'configuration', 'meta')
ORDER BY tablename;

-- 6. Verify no policies exist
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ NO POLICIES FOUND'
        ELSE '❌ POLICIES STILL EXIST: ' || COUNT(*)::text
    END as policy_status
FROM pg_policies 
WHERE schemaname = 'public';

-- 7. Test data access
SELECT 'Testing data access...' as test;
SELECT COUNT(*) as judge_count FROM judges;
SELECT COUNT(*) as rubric_count FROM rubrics;
SELECT COUNT(*) as song_count FROM songs;

SELECT '🎉 RLS COMPLETELY DISABLED - FULL ACCESS GRANTED!' as final_status;
