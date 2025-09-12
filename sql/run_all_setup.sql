-- ==================== COMPLETE DATABASE SETUP ====================
-- Run this file to set up the entire database from scratch
-- This file includes all necessary setup in the correct order
--
-- Usage: Copy entire contents to Supabase SQL Editor and run
-- Or use psql: psql -d your_database -f sql/run_all_setup.sql

-- 1. Initial setup (tables, indexes, basic data)
\i 01_initial_setup.sql

-- 2. Songs data
\i 02_songs_data.sql

-- 3. Judges and authentication
\i 03_judges_and_auth.sql

-- 4. Certificate configuration
\i 04_certificate_config.sql

-- 5. Winner display configuration
\i 05_winner_display_config.sql

-- 6. Cleanup unused tables (optional)
-- \i 06_cleanup_unused_tables.sql

-- 7. Cleanup meta table (optional)
-- \i 07_cleanup_meta_table.sql

-- Final verification
SELECT 'Database setup completed successfully!' as status;
SELECT
    (SELECT COUNT(*) FROM songs) as songs_count,
    (SELECT COUNT(*) FROM judges) as judges_count,
    (SELECT COUNT(*) FROM rubrics) as rubrics_count,
    (SELECT COUNT(*) FROM keywords) as keywords_count,
    (SELECT COUNT(*) FROM config) as config_count,
    (SELECT COUNT(*) FROM auth_profiles) as auth_profiles_count;
