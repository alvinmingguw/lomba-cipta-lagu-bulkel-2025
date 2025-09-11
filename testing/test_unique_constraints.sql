-- Test file to verify UNIQUE constraints work correctly
-- Run this after setup_database.sql to test constraints

-- Test 1: Verify UNIQUE constraints exist
SELECT 'Testing UNIQUE constraints...' as step;

SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    tc.constraint_type
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'UNIQUE'
    AND tc.table_name = 'songs'
ORDER BY tc.constraint_name;

-- Test 2: Test song_code UNIQUE constraint
SELECT 'Testing song_code UNIQUE constraint...' as step;

-- This should work (first insert)
INSERT INTO songs (song_code, title, composer, is_active) 
VALUES ('TEST01', 'Test Song 1', 'Test Composer', true);

-- This should fail (duplicate song_code)
-- INSERT INTO songs (song_code, title, composer, is_active) 
-- VALUES ('TEST01', 'Different Title', 'Test Composer', true);

-- Test 3: Test title UNIQUE constraint
SELECT 'Testing title UNIQUE constraint...' as step;

-- This should work (different song_code, different title)
INSERT INTO songs (song_code, title, composer, is_active) 
VALUES ('TEST02', 'Test Song 2', 'Test Composer', true);

-- This should fail (duplicate title)
-- INSERT INTO songs (song_code, title, composer, is_active) 
-- VALUES ('TEST03', 'Test Song 1', 'Test Composer', true);

-- Test 4: Test ON CONFLICT with title
SELECT 'Testing ON CONFLICT (title)...' as step;

-- This should work with ON CONFLICT
INSERT INTO songs (song_code, title, composer, is_active) 
VALUES ('TEST03', 'Test Song 1', 'Different Composer', true)
ON CONFLICT (title) DO NOTHING;

-- Test 5: Test ON CONFLICT with song_code
SELECT 'Testing ON CONFLICT (song_code)...' as step;

-- This should work with ON CONFLICT
INSERT INTO songs (song_code, title, composer, is_active) 
VALUES ('TEST01', 'Different Title Again', 'Different Composer', true)
ON CONFLICT (song_code) DO NOTHING;

-- Test 6: Verify test data
SELECT 'Verifying test data...' as step;
SELECT song_code, title, composer FROM songs WHERE song_code LIKE 'TEST%';

-- Cleanup test data
DELETE FROM songs WHERE song_code LIKE 'TEST%';

-- Test 7: Verify cleanup
SELECT 'Verifying cleanup...' as step;
SELECT COUNT(*) as remaining_test_songs FROM songs WHERE song_code LIKE 'TEST%';

SELECT 'UNIQUE constraints test completed! ✅' as status;
