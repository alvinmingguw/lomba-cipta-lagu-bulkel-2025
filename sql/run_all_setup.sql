-- ==================== COMPLETE DATABASE SETUP ====================
-- Run this file to set up the entire database from scratch
-- This file includes all necessary setup in the correct order

-- 1. Initial setup (tables, indexes, basic data)
\i sql/01_initial_setup.sql

-- 2. Songs data
\i sql/02_songs_data.sql

-- 3. Judges and authentication
\i sql/03_judges_and_auth.sql

-- 4. Certificate configuration
\i add_certificate_config.sql

-- Final verification
SELECT 'Database setup completed successfully!' as status;
SELECT 
    (SELECT COUNT(*) FROM songs) as songs_count,
    (SELECT COUNT(*) FROM judges) as judges_count,
    (SELECT COUNT(*) FROM rubrics) as rubrics_count,
    (SELECT COUNT(*) FROM keywords) as keywords_count,
    (SELECT COUNT(*) FROM config) as config_count,
    (SELECT COUNT(*) FROM auth_profiles) as auth_profiles_count;
