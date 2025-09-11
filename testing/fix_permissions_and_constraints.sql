-- Fix permissions and constraints for existing database
-- Run this if you already ran setup_database.sql but have permission/constraint issues

-- 1. Add missing foreign key constraints (with error handling)
DO $$
BEGIN
    -- Add audio file constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'songs_audio_file_id_fkey'
        AND table_name = 'songs'
    ) THEN
        ALTER TABLE songs ADD CONSTRAINT songs_audio_file_id_fkey
            FOREIGN KEY (audio_file_id) REFERENCES file_metadata(file_id);
    END IF;

    -- Add notation file constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'songs_notation_file_id_fkey'
        AND table_name = 'songs'
    ) THEN
        ALTER TABLE songs ADD CONSTRAINT songs_notation_file_id_fkey
            FOREIGN KEY (notation_file_id) REFERENCES file_metadata(file_id);
    END IF;

    -- Add lyrics file constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'songs_lyrics_file_id_fkey'
        AND table_name = 'songs'
    ) THEN
        ALTER TABLE songs ADD CONSTRAINT songs_lyrics_file_id_fkey
            FOREIGN KEY (lyrics_file_id) REFERENCES file_metadata(file_id);
    END IF;
END $$;

-- 2. Enable RLS on all tables (if not already enabled)
ALTER TABLE judges ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE songs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE winners ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuration ENABLE ROW LEVEL SECURITY;
ALTER TABLE meta ENABLE ROW LEVEL SECURITY;

-- 3. Create/recreate policies for public access
DROP POLICY IF EXISTS "Public read access" ON judges;
CREATE POLICY "Public read access" ON judges FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON rubrics;
CREATE POLICY "Public read access" ON rubrics FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON keywords;
CREATE POLICY "Public read access" ON keywords FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON variants;
CREATE POLICY "Public read access" ON variants FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON songs;
CREATE POLICY "Public read access" ON songs FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON evaluations;
CREATE POLICY "Public read access" ON evaluations FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON file_metadata;
CREATE POLICY "Public read access" ON file_metadata FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON winners;
CREATE POLICY "Public read access" ON winners FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON configuration;
CREATE POLICY "Public read access" ON configuration FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read access" ON meta;
CREATE POLICY "Public read access" ON meta FOR SELECT USING (true);

-- 4. Create policies for public write access (for evaluations)
DROP POLICY IF EXISTS "Public write access" ON evaluations;
CREATE POLICY "Public write access" ON evaluations FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Public update access" ON evaluations;
CREATE POLICY "Public update access" ON evaluations FOR UPDATE USING (true) WITH CHECK (true);

-- 5. Verify policies are created
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

SELECT 'Permissions and constraints fixed successfully!' as status;
