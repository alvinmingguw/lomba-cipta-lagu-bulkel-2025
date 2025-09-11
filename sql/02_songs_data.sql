-- ==================== SONGS DATA ====================
-- Complete song data for Lomba Cipta Lagu Bulkel 2025
-- Run after 01_initial_setup.sql

-- Clear existing songs data
TRUNCATE TABLE songs RESTART IDENTITY CASCADE;

-- Insert all contest songs
INSERT INTO songs (title, composer, audio_file_path, notation_file_path, lyrics_file_path, lyrics_text, chords_list) VALUES

('Harta Yang Sjati', 'Ananta Garcia Nathanael Ginting', 
'Song01_Audio_Harta Yang Sjati-converted.mp3', 
'Song01_Notasi_Harta Yang Sjati.pdf', 
'Song01_Syair_Harta Yang Sjati.pdf',
'Waktu bersama keluarga
Harta yang paling berharga
Kasih yang terjalin erat
Berkat Tuhan yang melimpah

Dalam suka dan duka
Kita saling menguatkan
Doa yang tak pernah putus
Menjadi kekuatan kita

Reff:
Harta yang sjati
Bukan emas dan berlian
Tapi waktu bersama
Keluarga tercinta

Waktu yang Tuhan berikan
Gunakan dengan bijaksana
Seperti firman-Nya berkata
Efesus lima lima belas

Bridge:
Perhatikanlah dengan saksama
Bagaimana kita hidup
Jangan seperti orang bebal
Tapi seperti orang arif

(Kembali ke Reff)',
'C G Am F C G C'),

('Doa Untuk Keluargaku', 'Andrian', 
'Song02_Audio_Doa Untuk Keluargaku-converted.mp3', 
'Song02_Notasi_Doa Untuk Keluargaku.pdf', 
'Song02_Syair_Doa Untuk Keluargaku.pdf',
'Tuhan, berkati keluargaku
Dalam kasih-Mu yang kekal
Waktu bersama yang berharga
Jadikan berkat bagi semua

Ayah, ibu, dan anak-anak
Bersatu dalam doa-Mu
Harta yang tak ternilai
Adalah kebersamaan ini

Reff:
Doa untuk keluargaku
Ya Tuhan dengarkan
Waktu bersama harta berharga
Berkat-Mu melimpahkan

Efesus lima lima belas
Firman-Mu yang mengingatkan
Gunakan waktu dengan arif
Dalam kasih yang sejati

Bridge:
Hari-hari yang Engkau berikan
Jadikan penuh makna
Keluarga yang Kau percayakan
Harta yang paling berharga

(Kembali ke Reff)',
'G D Em C G D G'),

('Indah Bersama Keluargaku', 'Gabriella Louise Maurent Sihombing', 
'Song03_Audio_Indah Bersama Keluargaku-converted.mp3', 
'Song03_Notasi_Indah Bersama Keluargaku.pdf', 
'Song03_Syair_Indah Bersama Keluargaku.pdf',
'Indah bersama keluargaku
Waktu yang tak tergantikan
Harta berharga di hatiku
Kasih yang tak pernah pudar

Dalam tawa dan tangisan
Kita saling berbagi
Doa yang menguatkan
Berkat Tuhan yang nyata

Reff:
Keluargaku harta berharga
Waktu bersama yang indah
Tuhan memberkati kita
Dalam kasih yang sejati

Efesus lima lima belas enam
Mengingatkan kita semua
Gunakan waktu dengan bijak
Seperti orang yang arif

Bridge:
Perhatikan dengan saksama
Bagaimana kita menjalani
Hari-hari yang Tuhan berikan
Dengan penuh syukur

(Kembali ke Reff)',
'F C Dm Bb F C F'),

('Waktu Bersama, Harta Berharga', 'Merys Ngestuti Siahaan', 
'Song04_Audio_Waktu Bersama, Harta Berharga-converted.mp3', 
'Song04_Notasi_Waktu Bersama, Harta Berharga.pdf', 
'Song04_Syair_Waktu Bersama, Harta Berharga.pdf',
'Waktu bersama, harta berharga
Keluarga yang Tuhan berikan
Dalam suka dan duka
Kita saling menguatkan

Kasih yang terjalin erat
Doa yang tak pernah putus
Berkat Tuhan melimpah
Dalam kebersamaan kita

Reff:
Waktu bersama harta berharga
Lebih dari emas dan perak
Keluarga yang Tuhan percayakan
Harta yang tak ternilai

Efesus lima lima belas
Firman Tuhan mengingatkan
Gunakan waktu dengan arif
Jangan seperti orang bebal

Bridge:
Perhatikanlah dengan saksama
Bagaimana kita hidup
Hari-hari ini adalah jahat
Gunakan waktu yang ada

(Kembali ke Reff)',
'D A Bm G D A D'),

('Waktu Bersama Harta Berharga', 'Parulian Simanjuntak', 
'Song05_Audio_Waktu Bersama Harta Berharga-converted.mp3', 
'Song05_Notasi_Waktu Bersama Harta Berharga.pdf', 
'Song05_Syair_Waktu Bersama Harta Berharga.pdf',
'Waktu bersama harta berharga
Keluarga adalah segalanya
Tuhan memberkati kita
Dalam kasih yang sejati

Ayah, ibu, dan anak-anak
Bersatu dalam doa
Harta yang tak terbeli
Adalah kebersamaan ini

Reff:
Harta berharga waktu bersama
Keluarga yang Tuhan berikan
Kasih yang tak pernah pudar
Berkat yang melimpah

Efesus lima lima belas enam
Mengingatkan kita semua
Pergunakan waktu yang ada
Karena hari-hari ini jahat

Bridge:
Seperti orang arif
Bukan seperti orang bebal
Perhatikan dengan saksama
Bagaimana kita hidup

(Kembali ke Reff)',
'A E F#m D A E A'),

('Bangunlah, GKI Perumnas', 'Sigit Hascarya', 
'Song06_Audio_Bangunlah, GKI Perumnas-converted.mp3', 
'Song06_Notasi_Bangunlah, GKI Perumnas.pdf', 
'Song06_Syair_Bangunlah, GKI Perumnas.pdf',
'Bangunlah, GKI Perumnas
Waktu bersama harta berharga
Keluarga Allah yang bersatu
Dalam kasih yang sejati

Jemaat yang Tuhan kasihi
Bersama membangun iman
Waktu yang Tuhan berikan
Gunakan dengan bijaksana

Reff:
GKI Perumnas bangunlah
Dalam kasih yang sejati
Waktu bersama harta berharga
Keluarga Allah yang bersatu

Efesus lima lima belas
Firman yang menguatkan
Perhatikan dengan saksama
Bagaimana kita hidup

Bridge:
Jangan seperti orang bebal
Tapi seperti orang arif
Pergunakan waktu yang ada
Karena hari-hari ini jahat

(Kembali ke Reff)',
'E B C#m A E B E'),

('Keluarga Dekat Keluarga Berkat', 'Surya Giri Kurniawan', 
'Song07_Audio_Keluarga Dekat Keluarga Berkat-converted.mp3', 
'Song07_Notasi_Keluarga Dekat Keluarga Berkat.pdf', 
'Song07_Syair_Keluarga Dekat Keluarga Berkat.pdf',
'Keluarga dekat keluarga berkat
Waktu bersama harta berharga
Tuhan memberkati kita
Dalam kasih yang kekal

Ayah dan ibu yang mengasihi
Anak-anak yang taat
Bersama membangun rumah
Yang penuh dengan berkat

Reff:
Keluarga dekat keluarga berkat
Harta yang tak ternilai
Waktu bersama yang indah
Berkat Tuhan yang nyata

Efesus lima lima belas enam
Mengingatkan kita semua
Gunakan waktu dengan arif
Seperti yang Tuhan kehendaki

Bridge:
Perhatikanlah dengan saksama
Bagaimana kita menjalani
Hari-hari yang Tuhan berikan
Dengan penuh syukur

(Kembali ke Reff)',
'Bb F Gm Eb Bb F Bb'),

('Keluarga Dekat Keluarga Berkat v2', 'Swannie', 
'Song08_Audio_Keluarga Dekat Keluarga Berkat v2-converted.mp3', 
'Song08_Notasi_Keluarga Dekat Keluarga Berkat v2.pdf', 
'Song08_Syair_Keluarga Dekat Keluarga Berkat v2.pdf',
'Keluarga dekat keluarga berkat
Waktu bersama yang berharga
Kasih Tuhan yang melimpah
Dalam kebersamaan kita

Doa yang menguatkan
Iman yang tak pernah pudar
Berkat yang Tuhan berikan
Harta yang tak terbeli

Reff:
Keluarga berkat keluarga dekat
Waktu bersama harta berharga
Tuhan memberkati kita
Dalam kasih yang sejati

Efesus lima lima belas
Firman yang mengingatkan
Pergunakan waktu yang ada
Dengan penuh kebijaksanaan

Bridge:
Jangan seperti orang bebal
Tapi seperti orang arif
Perhatikan dengan saksama
Bagaimana kita hidup

(Kembali ke Reff)',
'C G Am F C G C'),

('Indahnya-Keluarga', 'Yosef Arta', 
'Song09_Audio_Indahnya-Keluarga-converted.mp3', 
'Song09_Notasi_Indahnya-Keluarga.pdf', 
'Song09_Syair_Indahnya-Keluarga.pdf',
'Indahnya keluarga
Waktu bersama yang berharga
Tuhan memberkati kita
Dalam kasih yang kekal

Ayah, ibu, dan anak-anak
Bersatu dalam doa
Harta yang tak ternilai
Adalah kebersamaan ini

Reff:
Indahnya keluarga
Harta berharga di hati
Waktu bersama yang indah
Berkat Tuhan yang nyata

Efesus lima lima belas enam
Mengingatkan kita semua
Gunakan waktu dengan bijak
Seperti orang yang arif

Bridge:
Perhatikanlah dengan saksama
Bagaimana kita menjalani
Hari-hari yang Tuhan berikan
Dengan penuh syukur

(Kembali ke Reff)',
'G D Em C G D G'),

('Kasihilah Keluargamu', 'Yoseph Harris', 
'Song10_Audio_Kasihilah Keluargamu-converted.mp3', 
'Song10_Notasi_Kasihilah Keluargamu.pdf', 
'Song10_Syair_Kasihilah Keluargamu.pdf',
'Kasihilah keluargamu
Waktu bersama harta berharga
Tuhan telah memberikan
Berkat yang tak terhingga

Dalam suka dan duka
Kita saling menguatkan
Doa yang tak pernah putus
Menjadi kekuatan kita

Reff:
Kasihilah keluargamu
Harta yang paling berharga
Waktu bersama yang indah
Berkat Tuhan yang melimpah

Efesus lima lima belas
Firman Tuhan mengingatkan
Pergunakan waktu yang ada
Dengan penuh kebijaksanaan

Bridge:
Jangan seperti orang bebal
Tapi seperti orang arif
Perhatikan dengan saksama
Bagaimana kita hidup

(Kembali ke Reff)',
'F C Dm Bb F C F'),

('Keluarga Bahagia', 'Tidak diketahui', 
'Song11_Audio_Keluarga Bahagia-converted.mp3', 
'Song11_Notasi_Keluarga Bahagia.pdf', 
'Song11_Syair_Keluarga Bahagia.pdf',
'Keluarga bahagia
Waktu bersama yang berharga
Tuhan memberkati kita
Dalam kasih yang sejati

Ayah dan ibu yang mengasihi
Anak-anak yang berbakti
Bersama membangun rumah
Yang penuh dengan berkat

Reff:
Keluarga bahagia
Harta yang tak ternilai
Waktu bersama yang indah
Berkat Tuhan yang nyata

Efesus lima lima belas enam
Mengingatkan kita semua
Gunakan waktu dengan arif
Seperti yang Tuhan kehendaki

Bridge:
Perhatikanlah dengan saksama
Bagaimana kita menjalani
Hari-hari yang Tuhan berikan
Dengan penuh syukur

(Kembali ke Reff)',
'D A Bm G D A D');

-- Update timestamps
UPDATE songs SET updated_at = NOW();
