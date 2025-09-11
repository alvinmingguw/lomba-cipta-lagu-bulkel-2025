-- Add configuration for winner display layout and PDF options
-- These configurations control how multiple versions of songs are displayed

INSERT INTO config (config_key, config_value, description, created_at, updated_at) VALUES
-- Winner display layout configuration
('WINNER_DISPLAY_LAYOUT', 'TABS', 'Layout for multiple versions: TABS (current tabbed layout) or COLUMNS (side-by-side with full score)'),

-- PDF document display configuration  
('SHOW_PDF_DOCUMENTS', 'TRUE', 'Whether to show PDF document links: TRUE (show PDF buttons) or FALSE (hide PDF buttons since text versions are available)')

ON CONFLICT (config_key) DO UPDATE SET
    description = EXCLUDED.description,
    updated_at = NOW();

-- Add comments for clarity
COMMENT ON TABLE config IS 'Application configuration settings for the song contest system including winner display options';
