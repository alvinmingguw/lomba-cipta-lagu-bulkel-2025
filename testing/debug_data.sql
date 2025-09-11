-- Debug script to check if data exists in database
-- Run this in Supabase SQL Editor to verify data

-- 1. Check if tables exist and have data
SELECT 'judges' as table_name, COUNT(*) as count FROM judges
UNION ALL
SELECT 'rubrics', COUNT(*) FROM rubrics
UNION ALL
SELECT 'songs', COUNT(*) FROM songs
UNION ALL
SELECT 'evaluations', COUNT(*) FROM evaluations
UNION ALL
SELECT 'keywords', COUNT(*) FROM keywords
UNION ALL
SELECT 'variants', COUNT(*) FROM variants
UNION ALL
SELECT 'configuration', COUNT(*) FROM configuration
UNION ALL
SELECT 'meta', COUNT(*) FROM meta;

-- 2. Check judges data specifically
SELECT 'Judges data:' as info;
SELECT id, name, is_active FROM judges ORDER BY id;

-- 3. Check rubrics data specifically  
SELECT 'Rubrics data:' as info;
SELECT id, rubric_key, aspect_name, is_active FROM rubrics ORDER BY id;

-- 4. Check songs data specifically
SELECT 'Songs data:' as info;
SELECT id, song_code, title, is_active FROM songs ORDER BY id;

-- 5. Check if is_active column has correct values
SELECT 'Active judges:' as info;
SELECT COUNT(*) as active_judges FROM judges WHERE is_active = true;

SELECT 'Active rubrics:' as info;
SELECT COUNT(*) as active_rubrics FROM rubrics WHERE is_active = true;

SELECT 'Active songs:' as info;
SELECT COUNT(*) as active_songs FROM songs WHERE is_active = true;

-- 6. Check configuration
SELECT 'Configuration:' as info;
SELECT key, value FROM configuration ORDER BY key;
