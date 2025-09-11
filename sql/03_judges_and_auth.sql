-- ==================== JUDGES AND AUTHENTICATION DATA ====================
-- Judges data and authentication setup
-- Run after 02_songs_data.sql

-- Clear existing judges data
TRUNCATE TABLE judges RESTART IDENTITY CASCADE;
TRUNCATE TABLE auth_profiles RESTART IDENTITY CASCADE;

-- Insert judges
INSERT INTO judges (name, email, expertise) VALUES
('Vance Siahaan', 'vance.siahaan@gmail.com', 'Musik Gereja & Komposisi'),
('Alvin Giovanni Mingguw', 'alvin.mingguw@gmail.com', 'Teknologi & Sistem'),
('Dr. Musik Expert', 'musik.expert@example.com', 'Teori Musik & Harmoni'),
('Rev. Liturgi Specialist', 'liturgi.specialist@example.com', 'Liturgi & Musik Gereja'),
('Prof. Vocal Coach', 'vocal.coach@example.com', 'Teknik Vokal & Performance');

-- Insert auth profiles for judges
INSERT INTO auth_profiles (email, full_name, role, judge_id, provider) VALUES
('vance.siahaan@gmail.com', 'Vance Siahaan', 'judge', 1, 'google'),
('alvin.mingguw@gmail.com', 'Alvin Giovanni Mingguw', 'admin', 2, 'google'),
('musik.expert@example.com', 'Dr. Musik Expert', 'judge', 3, 'email'),
('liturgi.specialist@example.com', 'Rev. Liturgi Specialist', 'judge', 4, 'email'),
('vocal.coach@example.com', 'Prof. Vocal Coach', 'judge', 5, 'email');

-- Add admin user without judge_id (pure admin)
INSERT INTO auth_profiles (email, full_name, role, judge_id, provider) VALUES
('admin@gkiperumnas.org', 'System Administrator', 'admin', NULL, 'email');

-- Update timestamps
UPDATE judges SET updated_at = NOW();
UPDATE auth_profiles SET updated_at = NOW();
