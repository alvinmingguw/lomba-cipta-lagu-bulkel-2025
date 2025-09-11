-- Test file to verify all INSERT statements work correctly
-- Run this to test individual INSERT statements

-- Test 1: Configuration (3 columns)
INSERT INTO configuration (key, value, description) VALUES
('TEST_KEY', 'test_value', 'Test configuration')
ON CONFLICT (key) DO NOTHING;

-- Test 2: Meta (3 columns)  
INSERT INTO meta (key, value, description) VALUES
('test_meta', 'test_value', 'Test meta')
ON CONFLICT (key) DO NOTHING;

-- Test 3: Judges (2 columns)
INSERT INTO judges (name, is_active) VALUES
('Test Judge', true)
ON CONFLICT (name) DO NOTHING;

-- Test 4: Rubrics (11 columns) - THIS WAS THE PROBLEM!
INSERT INTO rubrics (rubric_key, aspect_name, weight, min_score, max_score, description_1, description_2, description_3, description_4, description_5, is_active) VALUES
('test', 'Test Aspect', 20.0, 1, 5, 'Desc 1', 'Desc 2', 'Desc 3', 'Desc 4', 'Desc 5', true)
ON CONFLICT (rubric_key) DO NOTHING;

-- Test 5: Keywords (4 columns)
INSERT INTO keywords (keyword_type, keyword_text, weight, is_active) VALUES
('keyword', 'test', 1.0, true)
ON CONFLICT DO NOTHING;

-- Test 6: Variants (2 columns)
INSERT INTO variants (source_name, target_key) VALUES
('Test Source', 'test_target')
ON CONFLICT DO NOTHING;

-- Test 7: Evaluations (6 columns)
INSERT INTO evaluations (judge_id, song_id, rubric_scores, total_score, notes, created_at) VALUES
(1, 1, '{"test": 5}', 5.0, 'Test evaluation', NOW())
ON CONFLICT (judge_id, song_id) DO UPDATE SET
    rubric_scores = EXCLUDED.rubric_scores,
    total_score = EXCLUDED.total_score,
    notes = EXCLUDED.notes,
    updated_at = NOW();

-- Cleanup test data
DELETE FROM evaluations WHERE notes = 'Test evaluation';
DELETE FROM variants WHERE source_name = 'Test Source';
DELETE FROM keywords WHERE keyword_text = 'test';
DELETE FROM rubrics WHERE rubric_key = 'test';
DELETE FROM judges WHERE name = 'Test Judge';
DELETE FROM meta WHERE key = 'test_meta';
DELETE FROM configuration WHERE key = 'TEST_KEY';

SELECT 'All INSERT statements work correctly! ✅' as status;
