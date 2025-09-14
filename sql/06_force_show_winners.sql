-- Add configuration to force show winners (for development/testing)
-- This allows showing winners section even before announcement date

INSERT INTO config (config_key, config_value, description, created_at, updated_at) VALUES
('FORCE_SHOW_WINNERS', 'TRUE', 'Force show winners section even before announcement date (for development/testing): TRUE or FALSE'),

-- Update timeline dates with proper format
('SUBMISSION_START_DATE', '1 Agustus 2025', 'Contest submission start date (display format)'),
('SUBMISSION_END_DATE', '31 Agustus 2025', 'Contest submission end date (display format)'),
('JUDGING_END_DATE', '3 September 2025', 'Judging period end date (display format)'),
('WINNER_ANNOUNCEMENT_DATE', '14 September 2025', 'Winner announcement date (display format)')

ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    updated_at = NOW();
