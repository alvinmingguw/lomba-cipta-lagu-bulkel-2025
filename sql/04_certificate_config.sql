-- Add certificate configuration option
-- This allows using pre-generated certificates from Supabase storage instead of generating on-the-fly

INSERT INTO config (config_key, config_value, description, created_at, updated_at) 
VALUES (
    'USE_PREGENERATED_CERTIFICATES',
    'False',
    'Set to True to use pre-generated certificates from Supabase storage certificates/ folder instead of generating on-the-fly',
    NOW(),
    NOW()
) ON CONFLICT (config_key) DO UPDATE SET
    description = EXCLUDED.description,
    updated_at = NOW();

-- Add comment for clarity
COMMENT ON TABLE config IS 'Application configuration settings for the song contest system';
