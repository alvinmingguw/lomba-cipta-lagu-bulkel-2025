# 🎶 Penjurian Lomba Cipta Lagu — GKI Perumnas 2025

Aplikasi **penjurian online** berbasis **Streamlit + Google Sheets** untuk lomba cipta lagu bertema *“Waktu Bersama Harta Berharga”* di GKI Perumnas.

Aplikasi ini memudahkan **juri** untuk:
- Memberikan nilai berbasis **rubrik** (multi-aspek, berbobot, configurable dari Google Sheet).
- Mendengarkan audio, membaca syair, melihat notasi—semua di satu halaman.
- Menyimpan nilai langsung ke Google Sheets (cloud-first, tanpa DB lokal).
- Melihat **analisis otomatis** dari lirik & musik (tema, kekuatan lirik, chord richness, genre, key).
- Mengekspor hasil ke Excel/PDF, serta menghasilkan laporan pemenang & sertifikat.

---

## ✨ Fitur Utama

### 📝 Form Penilaian Interaktif
- Rubrik configurable dari Google Sheet `Rubrik`.
- Nilai tersimpan ke sheet `Penilaian` (update jika juri menilai ulang).
- Preview **audio** (MP3/M4A), **syair** (PDF), **notasi** (PDF).
- **Konfirmasi sebelum simpan** agar aman duplikasi.

### 🔍 Analisis Syair
- Skor **Tema** (kecocokan dengan frasa/keyword dari sheet `Keywords`).
- Skor **Kekuatan Lirik** (hybrid & lebih “manusiawi”):
  - Relevansi keluarga/kebersamaan
  - Emosi rohani (kasih, syukur, doa)
  - Imagery/metafora (ungkapan segar)
  - Struktur (verse/chorus/bridge)
  - Penalti klise & repetisi berlebih
- Highlight frasa/keyword di teks syair.
- Visualisasi: distribusi & scatter Tema vs Lirik.

### 🎼 Analisis Musik (Chord)
- Ekstraksi chord dari berbagai sumber (prioritas: `chords_list`, `syair_chord`, `full_score`, `extract_notasi`, `extract_syair`).
- Skor **Kekayaan Akor (1–5)** berdasarkan sebaran fitur.
- Deteksi **Nada Dasar (Key)** + confidence sederhana.
- Estimasi **Genre** (Worship/CCM, Pop, Jazz—heuristik ringan).
- Statistik: **Extensions%**, **Slash%**, **NonDiatonik%**, **Transisi unik**, **Jumlah akor unik**.
- Multi-chart: radar per lagu, distribusi key/genre, korelasi fitur.

### 📊 Hasil & Analitik
- Leaderboard (rata-rata total + **jarak ke posisi berikutnya**).
- Konsistensi antar juri (standar deviasi).
- Kontribusi aspek per lagu vs baseline (strengths & weaknesses).
- Korelasi aspek → total (fitur paling menentukan).
- **Insight Cepat** otomatis (juara sementara, aspek terkuat/terlemah, pertarungan ketat).

### 📤 Ekspor
- **Excel lengkap** (raw penilaian + ranking + rata2 aspek).
- **PDF Rekap + Insight**.
- **PDF Pemenang (analisis per lagu)**.
- **ZIP Sertifikat** (peserta & pemenang).

---

## 🏗️ Arsitektur Singkat

- **Frontend**: Streamlit
- **Penyimpanan**: Google Sheets (tanpa DB lokal)
- **Auth**: Google Service Account
- **Parsing PDF**: PyMuPDF (fitz)
- **Ekspor**: ReportLab (PDF), XlsxWriter (Excel)
- **Analitik**: Pandas, NumPy, Plotly (opsional)

---

## 📂 Struktur Repo (direkomendasikan)

```
penjurianLomba-webapp/
├─ assets/                 # logo/banner (≤ ~1–2 MB)
│  ├─ banner.png
│  └─ logo.png
├─ app.py                  # Streamlit app utama
├─ core/                   # Modul-modul logika utama
├─ tools_redact_pdfs.py    # util opsional untuk meredaksi PDF
├─ requirements.txt        # dependensi
├─ README.md               # dokumentasi (file ini)
└─ .gitignore              # abaikan cache, secrets, file besar lokal
```

> Folder **files/**, **files_backup/**, **files_anon/** tidak disarankan masuk repo. Simpan media di Google Drive dan referensikan via URL/ID di sheet `Songs`.

---

## 🔐 Konfigurasi Secrets Streamlit

Buat file `.streamlit/secrets.toml` (jangan commit ke Git): 

```toml
gsheet_id = "SPREADSHEET_ID"

[gcp_service_account]
type = "service_account"
project_id = "your-project"
private_key_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "1234567890"
token_uri = "https://oauth2.googleapis.com/token"
```

- Share spreadsheet ke `client_email` sebagai **Editor**.
- `gsheet_id` = ID Google Sheet (bagian di URL setelah `/d/` dan sebelum `/edit`).

---

## 📑 Struktur Google Sheet

**1) Tab `Rubrik`**  
Kolom yang dipakai:
- `key` — nama singkat kolom penilaian (mis. `tema`, `musik`, `lirik`)
- `aspek` — nama yang tampil
- `bobot` — bobot kontribusi ke total (0–100, dijumlahkan antar aspek)
- `min_score` — minimal skor per aspek (default 1)
- `max_score` — maksimal skor per aspek (default 5)
- `desc_5` … `desc_1` — deskripsi kriteria untuk masing-masing skor

**2) Tab `Songs`**  
Kolom yang dipakai (boleh kosong sebagian):
- `judul`, `pengarang`
- `audio_path` — URL/ID Google Drive atau path lokal (untuk uji lokal)
- `syair_path` — URL/ID PDF syair
- `notasi_path` — URL/ID PDF notasi
- `lirik_text` — teks lirik (opsional, alternatif ekstraksi dari PDF)
- `chords_list` — daftar chord (opsional, “C, Em, F, G…”)
- `full_score` / `syair_chord` — teks campuran lirik+chord (opsional)

**3) Tab `Keywords`**  
- `type` — `phrase` atau `keyword`
- `text` — frasa/kata kunci tema
- `weight` — bobot (default 1)

**4) Tab `Penilaian`**  
- Otomatis dibuat/diupdate oleh aplikasi:
  - `timestamp`, `juri`, `judul`, `author`, setiap `key` rubrik, `total`

**5) (Opsional) Tab `Config`**  
K/V untuk menyesuaikan perilaku aplikasi, contoh:
- `FORM_OPEN` = `true|false` (menutup form publik saat finalisasi)
- `THEME` = judul tema yang ditampilkan
- `SHOW_AUTHOR` = `true|false`
- `WINNERS_TOP_N` = `3` (jumlah pemenang di rekap)

**6) (Opsional) Tab `Variants`**  
- `from_name`, `to_key` — pemetaan nama lama → key rubrik baru (migrasi)

---

## 🧪 Jalankan Lokal

1) Install dependencies
```bash
pip install -r requirements.txt
```

2) Jalankan
```bash
streamlit run app.py
```

Aplikasi akan terbuka di browser (default http://localhost:8501).

---

## 🚀 Deploy ke Streamlit Community Cloud

1. Push repo ini ke GitHub.
2. Buka https://share.streamlit.io → **New app**.
3. Pilih repo + branch `main` + file `app.py`.
4. Masukkan **secrets** (salin dari `.streamlit/secrets.toml`).  
5. **Deploy**.

Tips:
- Pastikan file media (audio/PDF) disimpan di Google Drive dengan akses “Anyone with the link” **Viewer**, atau pastikan Service Account punya akses (shared).  
- Gunakan **ID Drive** atau link `https://drive.google.com/file/d/<ID>/view` / `.../preview`. Aplikasi akan membentuk URL embed otomatis.

---

## 🧰 Git Quick Start

```bash
# masuk folder proyek
cd /Users/<kamu>/Downloads/penjurianLomba-webapp

# inisialisasi repo
git init
git checkout -b main

# buat .gitignore ringkas
cat > .gitignore <<'EOF'
__pycache__/
*.pyc
.env
.streamlit/secrets.toml
files/
files_backup/
files_anon/
not_used/
*.mp3
*.m4a
*.pdf
*.xlsx
*.zip
.DS_Store
EOF

# add & commit
git add .gitignore README.md requirements.txt app.py core/ tools_redact_pdfs.py assets/
git commit -m "Initial commit: Streamlit GSheet Judging App"

# hubungkan ke GitHub
git remote add origin https://github.com/<username>/gki-perumnas-lomba-lagu-2025.git

# push
git push -u origin main
```

**Nama repo disarankan**: `gki-perumnas-lomba-lagu-2025`

---

## 🛠️ Troubleshooting (ringkas)

- **Audio tidak bisa diputar**  
  → Cek izin file di Drive. Pastikan SA atau “Anyone with link (Viewer)”.

- **Syair/Notasi tidak tampil**  
  → Pastikan link adalah ID/URL Drive yang valid dan file bertipe PDF.

- **Nilai tidak tersimpan**  
  → Pastikan `gsheet_id` benar dan Service Account punya akses **Editor**.

- **Error AuthorizedSession / _auth_request**  
  → Biasanya terjadi jika kredensial kadaluwarsa/format `private_key` salah (harus tetap ada `\n` baris baru dalam secrets). Pastikan `private_key` di secrets **mempertahankan newline** `\\n` → akan dipatch otomatis di app.

---

## 📜 Lisensi

Internal use GKI Perumnas; non-komersial.
