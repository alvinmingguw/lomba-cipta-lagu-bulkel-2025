# SQL Execution Order Guide

## 📋 **URUTAN EKSEKUSI SQL (WAJIB BERURUTAN!)**

### **1️⃣ PERTAMA: `setup_database.sql`**
```bash
# Di Supabase SQL Editor
# Copy-paste dan run file ini
```

**Isi:**
- ✅ Membuat semua tabel dengan kolom yang sudah diperbaiki
- ✅ Membuat indexes dan constraints
- ✅ Insert data master: judges, rubrics, keywords, variants, configuration
- ❌ **TIDAK** ada insert songs (sudah dipindah ke file terpisah)
- ❌ **TIDAK** ada insert evaluations (sudah dipindah ke file terpisah)

### **2️⃣ KEDUA: `songs_data_complete.sql`**
```bash
# Di Supabase SQL Editor
# Copy-paste dan run file ini setelah step 1 selesai
```

**Isi:**
- ✅ Insert **SEMUA 11 SONGS** dengan data lengkap
- ✅ Menggunakan kolom yang sudah diperbaiki
- ✅ ON CONFLICT handling untuk safety

### **3️⃣ KETIGA (OPSIONAL): `evaluations_data.sql`**
```bash
# Generate dulu:
python3 generate_evaluations_sql.py > evaluations_data.sql

# Lalu di Supabase SQL Editor:
# Copy-paste dan run file evaluations_data.sql
```

**Isi:**
- ✅ Insert **SEMUA 77 EVALUATIONS** dari sheet Penilaian
- ✅ Data sebenarnya dari Excel
- ⚠️ **HARUS** dijalankan setelah songs sudah ada (step 2)

## ⚠️ **PENTING!**

### **Jangan Skip Urutan:**
- ❌ **JANGAN** jalankan `songs_data_complete.sql` sebelum `setup_database.sql`
- ❌ **JANGAN** jalankan `evaluations_data.sql` sebelum step 1 & 2

### **Kolom Sudah Diperbaiki:**
- ✅ `active` → `is_active`
- ✅ `key` → `rubric_key`
- ✅ `alias` → `song_code`
- ✅ `notasi_path` → `notation_file_path`
- ✅ `syair_path` → `lyrics_file_path`
- ✅ Dan semua kolom lainnya

### **Error yang Sudah Diperbaiki:**
- ✅ `column "active" does not exist` → Fixed
- ✅ `column "key" does not exist` → Fixed
- ✅ Semua indexes menggunakan kolom yang benar
- ✅ Semua INSERT statements menggunakan kolom yang benar

## 🎯 **Pilihan Setup:**

### **Setup Minimal (untuk testing):**
```bash
1. setup_database.sql
2. songs_data_complete.sql
```
**Result:** 11 songs + 0 evaluations (tabel kosong)

### **Setup Lengkap (untuk production):**
```bash
1. setup_database.sql
2. songs_data_complete.sql
3. evaluations_data.sql
```
**Result:** 11 songs + 77 real evaluations

## ✅ **Verification:**

Setelah menjalankan semua SQL, cek di Supabase:

```sql
-- Cek jumlah data
SELECT 'judges' as table_name, COUNT(*) as count FROM judges
UNION ALL
SELECT 'songs', COUNT(*) FROM songs
UNION ALL
SELECT 'evaluations', COUNT(*) FROM evaluations
UNION ALL
SELECT 'rubrics', COUNT(*) FROM rubrics;

-- Expected results:
-- judges: 7
-- songs: 11 (setelah step 2)
-- evaluations: 0 (minimal) atau 77 (lengkap setelah step 3)
-- rubrics: 5
```

## 🚀 **Ready to Go!**

Setelah semua SQL berhasil dijalankan:
1. Update `.streamlit/secrets.toml` dengan credentials Supabase
2. Upload files ke Storage bucket `song-contest-files/files/`
3. Run aplikasi: `streamlit run app_new.py`
