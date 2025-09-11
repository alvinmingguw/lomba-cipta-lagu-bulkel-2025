-- Cleanup unused tables
-- This script removes tables that are not used in the production application

-- Drop winners table (not used in production)
DROP TABLE IF EXISTS winners CASCADE;

-- Note: Keeping auth_profiles and file_metadata as they are used in the application
-- auth_profiles: Used in services/auth_service.py for OAuth authentication
-- file_metadata: Used in services/file_service.py for file management

-- Add comment for future reference
COMMENT ON SCHEMA public IS 'Cleaned up unused tables on 2025-09-08';
