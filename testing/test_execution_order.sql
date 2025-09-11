-- Test file to verify correct execution order
-- Run this step by step to test the execution order

-- STEP 1: Test setup_database.sql components
-- This should work without any foreign key errors

-- Test table creation
SELECT 'Testing table creation...' as step;

-- Test data master inserts (no foreign keys)
SELECT 'Testing judges...' as step;
SELECT COUNT(*) as judge_count FROM judges;

SELECT 'Testing rubrics...' as step;
SELECT COUNT(*) as rubric_count FROM rubrics;

SELECT 'Testing keywords...' as step;
SELECT COUNT(*) as keyword_count FROM keywords;

SELECT 'Testing variants...' as step;
SELECT COUNT(*) as variant_count FROM variants;

-- STEP 2: Test that songs table is empty (before songs_data_complete.sql)
SELECT 'Testing songs table (should be empty)...' as step;
SELECT COUNT(*) as song_count FROM songs;

-- STEP 3: Test that evaluations table is empty (before evaluations_data.sql)
SELECT 'Testing evaluations table (should be empty)...' as step;
SELECT COUNT(*) as evaluation_count FROM evaluations;

-- STEP 4: Test foreign key constraints exist
SELECT 'Testing foreign key constraints...' as step;
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('evaluations', 'winners')
ORDER BY tc.table_name, tc.constraint_name;

-- STEP 5: Verify expected counts after setup_database.sql
SELECT 'Expected counts after setup_database.sql:' as summary;
SELECT 
    'judges' as table_name, 
    COUNT(*) as count,
    'Expected: 7' as expected
FROM judges
UNION ALL
SELECT 
    'rubrics', 
    COUNT(*),
    'Expected: 5'
FROM rubrics
UNION ALL
SELECT 
    'keywords', 
    COUNT(*),
    'Expected: 11'
FROM keywords
UNION ALL
SELECT 
    'variants', 
    COUNT(*),
    'Expected: 18'
FROM variants
UNION ALL
SELECT 
    'songs', 
    COUNT(*),
    'Expected: 0 (until songs_data_complete.sql)'
FROM songs
UNION ALL
SELECT 
    'evaluations', 
    COUNT(*),
    'Expected: 0 (until evaluations_data.sql)'
FROM evaluations;

SELECT 'setup_database.sql test completed! ✅' as status;
