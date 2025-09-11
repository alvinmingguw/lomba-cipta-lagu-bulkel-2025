-- Cleanup unused meta table
-- This script removes the meta table that is not used in the production application

-- Check if meta table exists and has data
SELECT 'meta table data before cleanup:' as info;
SELECT COUNT(*) as count FROM meta;

-- Drop meta table (not used in production)
DROP TABLE IF EXISTS meta CASCADE;

-- Verify cleanup
SELECT 'meta table cleanup completed!' as status;

-- Add comment for future reference
COMMENT ON SCHEMA public IS 'Cleaned up unused meta table on 2025-09-11';

-- Final verification - this should show all remaining tables
SELECT 'Remaining tables:' as info;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
