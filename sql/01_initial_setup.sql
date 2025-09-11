-- ==================== INITIAL DATABASE SETUP ====================
-- Complete database setup for Lomba Cipta Lagu Bulkel 2025
-- Run this file first to set up the entire database structure

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== CORE TABLES ====================

-- Songs table
CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    composer VARCHAR(255),
    audio_file_path VARCHAR(500),
    notation_file_path VARCHAR(500),
    lyrics_file_path VARCHAR(500),
    lyrics_text TEXT,
    chords_list TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Judges table
CREATE TABLE IF NOT EXISTS judges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    expertise VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Rubrics table
CREATE TABLE IF NOT EXISTS rubrics (
    id SERIAL PRIMARY KEY,
    rubric_key VARCHAR(50) UNIQUE NOT NULL,
    aspect_name VARCHAR(255) NOT NULL,
    description TEXT,
    max_score INTEGER DEFAULT 5,
    weight DECIMAL(5,2) DEFAULT 20.00,
    is_ai_assisted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id SERIAL PRIMARY KEY,
    judge_id INTEGER REFERENCES judges(id) ON DELETE CASCADE,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    rubric_scores JSONB,
    total_score DECIMAL(5,2),
    notes TEXT,
    is_final_submitted BOOLEAN DEFAULT FALSE,
    final_submitted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(judge_id, song_id)
);

-- Keywords table for theme analysis
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword_text VARCHAR(255) NOT NULL,
    keyword_type VARCHAR(50) DEFAULT 'keyword',
    weight DECIMAL(3,2) DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Configuration table
CREATE TABLE IF NOT EXISTS configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================== AUTHENTICATION TABLES ====================

-- Auth profiles table for user management
CREATE TABLE IF NOT EXISTS auth_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'judge',
    judge_id INTEGER REFERENCES judges(id),
    provider VARCHAR(50) DEFAULT 'email',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==================== INDEXES ====================

CREATE INDEX IF NOT EXISTS idx_evaluations_judge_song ON evaluations(judge_id, song_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_song ON evaluations(song_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_judge ON evaluations(judge_id);
CREATE INDEX IF NOT EXISTS idx_auth_profiles_email ON auth_profiles(email);
CREATE INDEX IF NOT EXISTS idx_auth_profiles_judge_id ON auth_profiles(judge_id);

-- ==================== INITIAL DATA ====================

-- Insert default rubrics
INSERT INTO rubrics (rubric_key, aspect_name, description, max_score, weight, is_ai_assisted) VALUES
('tema', 'Kesesuaian Tema', 'Seberapa sesuai lagu dengan tema "Waktu Bersama Harta Berharga" dan Efesus 5:15-16', 5, 20.00, TRUE),
('lirik', 'Kekuatan Lirik', 'Kualitas puitis, makna, dan kesesuaian dengan tema', 5, 20.00, TRUE),
('musik', 'Kekayaan Musik', 'Harmoni, melodi, dan kekayaan musikal', 5, 20.00, TRUE),
('kreativ', 'Kreativitas & Orisinalitas', 'Keunikan dan kreativitas dalam penyajian', 5, 20.00, FALSE),
('jemaat', 'Kesesuaian untuk Jemaat', 'Kemudahan untuk dinyanyikan jemaat semua usia', 5, 20.00, FALSE)
ON CONFLICT (rubric_key) DO NOTHING;

-- Insert theme keywords
INSERT INTO keywords (keyword_text, keyword_type, weight) VALUES
('waktu', 'keyword', 2.0),
('bersama', 'keyword', 2.0),
('harta', 'keyword', 2.0),
('berharga', 'keyword', 2.0),
('keluarga', 'keyword', 1.5),
('kasih', 'keyword', 1.5),
('berkat', 'keyword', 1.5),
('kebersamaan', 'keyword', 1.8),
('masa', 'keyword', 1.2),
('saat', 'keyword', 1.2),
('hari', 'keyword', 1.2),
('momen', 'keyword', 1.5),
('kekayaan', 'keyword', 1.5),
('mulia', 'keyword', 1.3),
('bernilai', 'keyword', 1.3),
('mahal', 'keyword', 1.0),
('ayah', 'keyword', 1.2),
('ibu', 'keyword', 1.2),
('anak', 'keyword', 1.2),
('rumah', 'keyword', 1.3),
('orang tua', 'phrase', 1.5),
('saudara', 'keyword', 1.2),
('tuhan', 'keyword', 1.8),
('allah', 'keyword', 1.8),
('iman', 'keyword', 1.5),
('doa', 'keyword', 1.3),
('syukur', 'keyword', 1.5),
('rohani', 'keyword', 1.3),
('arif', 'keyword', 1.8),
('bijaksana', 'keyword', 1.8),
('perhatikan', 'keyword', 1.5),
('saksama', 'keyword', 1.5),
('bebal', 'keyword', 1.3),
('jahat', 'keyword', 1.0),
('waktu bersama', 'phrase', 3.0),
('harta berharga', 'phrase', 3.0),
('waktu yang ada', 'phrase', 2.5),
('hari-hari ini', 'phrase', 2.0)
ON CONFLICT DO NOTHING;

-- Insert default configuration
INSERT INTO configuration (config_key, config_value, description) VALUES
('CONTEST_TITLE', 'Lomba Cipta Lagu Bulkel 2025', 'Title of the contest'),
('CONTEST_THEME', 'WAKTU BERSAMA HARTA BERHARGA', 'Main theme of the contest'),
('CONTEST_VERSE', 'Efesus 5:15-16', 'Biblical verse reference'),
('SHOW_AUTHOR', 'True', 'Whether to show song authors in results'),
('SHOW_NILAI_CHIP', 'True', 'Whether to show score chips in evaluation'),
('FINAL_SUBMIT_ENABLED', 'True', 'Enable final submission feature'),
('FORM_OPEN_TIME', '2025-01-01 00:00:00', 'When evaluation form opens'),
('FORM_CLOSE_TIME', '2025-12-31 23:59:59', 'When evaluation form closes'),
('WINNER_ANNOUNCEMENT_TIME', '2025-12-31 23:59:59', 'When winners can be announced'),
('USE_PREGENERATED_CERTIFICATES', 'False', 'Use pre-generated certificates from storage'),
('REQUIRE_CONFIRM_PANEL', 'False', 'Show confirmation panel (deprecated)')
ON CONFLICT (config_key) DO NOTHING;

-- ==================== COMMENTS ====================

COMMENT ON TABLE songs IS 'Contest songs with metadata and file paths';
COMMENT ON TABLE judges IS 'Contest judges information';
COMMENT ON TABLE rubrics IS 'Evaluation criteria and scoring rubrics';
COMMENT ON TABLE evaluations IS 'Judge evaluations of songs';
COMMENT ON TABLE keywords IS 'Keywords and phrases for theme analysis';
COMMENT ON TABLE configuration IS 'Application configuration settings';
COMMENT ON TABLE auth_profiles IS 'User authentication profiles';
