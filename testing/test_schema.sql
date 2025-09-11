-- Quick test to verify all column names are correct
-- Run this in Supabase SQL Editor to test schema

-- Test 1: Create tables (should not error)
CREATE TABLE IF NOT EXISTS test_judges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS test_rubrics (
    id SERIAL PRIMARY KEY,
    rubric_key VARCHAR(100) NOT NULL UNIQUE,
    aspect_name VARCHAR(255) NOT NULL,
    weight DECIMAL(5,2) DEFAULT 1.0,
    min_score INTEGER DEFAULT 1,
    max_score INTEGER DEFAULT 5,
    description_1 TEXT,
    description_2 TEXT,
    description_3 TEXT,
    description_4 TEXT,
    description_5 TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS test_songs (
    id SERIAL PRIMARY KEY,
    song_code VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    composer VARCHAR(255),
    audio_file_path TEXT,
    notation_file_path TEXT,
    lyrics_file_path TEXT,
    audio_file_id VARCHAR(255),
    notation_file_id VARCHAR(255),
    lyrics_file_id VARCHAR(255),
    lyrics_text TEXT,
    chords_list TEXT,
    lyrics_with_chords TEXT,
    full_score TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS test_winners (
    id SERIAL PRIMARY KEY,
    song_id INTEGER REFERENCES test_songs(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    prize_description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Test 2: Create indexes (should not error)
CREATE INDEX IF NOT EXISTS idx_test_songs_active ON test_songs(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_test_judges_active ON test_judges(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_test_rubrics_active ON test_rubrics(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_test_rubrics_key ON test_rubrics(rubric_key);
CREATE INDEX IF NOT EXISTS idx_test_winners_position ON test_winners(position);

-- Test 3: Insert test data (should not error)
INSERT INTO test_judges (name, is_active) VALUES ('Test Judge', true);
INSERT INTO test_rubrics (rubric_key, aspect_name, weight, is_active) VALUES ('test', 'Test Aspect', 20.0, true);
INSERT INTO test_songs (song_code, title, display_name, composer, is_active) VALUES ('TEST01', 'Test Song', 'TEST01 - Test Song', 'Test Composer', true);

-- Test 4: Query test (should not error)
SELECT 
    j.name,
    j.is_active,
    r.rubric_key,
    r.aspect_name,
    s.song_code,
    s.display_name,
    s.is_active
FROM test_judges j
CROSS JOIN test_rubrics r
CROSS JOIN test_songs s
WHERE j.is_active = true 
  AND r.is_active = true 
  AND s.is_active = true;

-- Cleanup
DROP TABLE IF EXISTS test_winners;
DROP TABLE IF EXISTS test_songs;
DROP TABLE IF EXISTS test_rubrics;
DROP TABLE IF EXISTS test_judges;

-- Success message
SELECT 'All column names are correct! ✅' as status;
