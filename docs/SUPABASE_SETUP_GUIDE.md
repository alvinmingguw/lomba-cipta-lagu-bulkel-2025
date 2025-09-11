# 🚀 Complete Supabase Setup Guide

## 📋 **Step 1: Create New Supabase Project**

1. **Go to [supabase.com](https://supabase.com)**
2. **Click "New Project"**
3. **Fill in:**
   - **Name**: `lomba-cipta-lagu-gki-perumnas-2025`
   - **Database Password**: Use your password: `0Ydt0xJQzGAMnDZc`
   - **Region**: `Southeast Asia (Singapore)`
4. **Click "Create new project"**
5. **Wait 2-3 minutes** for setup to complete

## 🗄️ **Step 2: Setup Database Schema**

1. **Go to SQL Editor** in your new Supabase project
2. **Copy and paste** the entire contents of `setup_database.sql`
3. **Click "Run"**
4. **Verify success** - you should see: "Database schema setup completed successfully!"

**This will create:**
- ✅ **9 tables** with all real data from your Excel
- ✅ **All indexes** for performance
- ✅ **Row Level Security** on all tables
- ✅ **Complete data** (judges, songs, rubrics, keywords, variants, config, meta)

## 📁 **Step 3: Create Storage Bucket & Folders**

### **Create Bucket:**
1. **Go to Storage** in Supabase dashboard
2. **Click "New bucket"**
3. **Name**: `song-contest-files`
4. **Make it Public**: ✅ (for easier access)
5. **Click "Create bucket"**

### **Create Folder Structure:**
In the `song-contest-files` bucket, create these folders:

```
song-contest-files/
├── files/           # All song files (MP3, M4A, PDF notasi, PDF syair)
└── certificates/    # Generated certificates
```

**How to create folders:**
1. Click on the bucket
2. Click "Upload" → "Create folder"
3. Create folder: `files`
4. Create folder: `certificates`

## 📤 **Step 4: Upload Files**

### **Option A: Manual Upload (Quick)**

1. **Go to Storage** → `song-contest-files`
2. **Upload to `files/` folder:**
   - All `.mp3` and `.m4a` files from `files_backup/`
   - All `.pdf` files from `files_backup/`
   - All `.pdf` files from `files_anon/`

### **Option B: Automated Migration (Recommended)**

Run the migration script:
```bash
python migrate_data.py
```

This will:
- ✅ Upload all files automatically
- ✅ Update database with file IDs
- ✅ Map old paths to new Supabase Storage paths

## ⚙️ **Step 5: Configure App**

1. **Copy secrets template:**
   ```bash
   cp .streamlit/secrets_template.toml .streamlit/secrets.toml
   ```

2. **Update with your Supabase credentials:**
   ```toml
   # .streamlit/secrets.toml
   supabase_url = "https://your-new-project-id.supabase.co"
   supabase_anon_key = "your-anon-key-here"
   ```

3. **Get your credentials:**
   - **URL**: From Supabase dashboard → Settings → API
   - **Anon Key**: From Supabase dashboard → Settings → API

## 🔐 **Step 6: Storage Policies (Optional)**

If you want more security, create these policies in SQL Editor:

```sql
-- Allow public read access to files
CREATE POLICY "Public read access" ON storage.objects 
FOR SELECT USING (bucket_id = 'song-contest-files');

-- Allow authenticated users to upload
CREATE POLICY "Authenticated upload" ON storage.objects 
FOR INSERT WITH CHECK (bucket_id = 'song-contest-files' AND auth.role() = 'authenticated');

-- Allow authenticated users to update their uploads
CREATE POLICY "Authenticated update" ON storage.objects 
FOR UPDATE USING (bucket_id = 'song-contest-files' AND auth.role() = 'authenticated');
```

## 🧪 **Step 7: Test the Setup**

1. **Install dependencies:**
   ```bash
   pip install -r requirements_new.txt
   ```

2. **Run migration (if not done):**
   ```bash
   python migrate_data.py
   ```

3. **Test new app:**
   ```bash
   streamlit run app_new.py
   ```

4. **Verify:**
   - ✅ Judges list loads
   - ✅ Songs list loads with audio/PDF links
   - ✅ Evaluation form works
   - ✅ Analytics shows data

## 📊 **What You Get:**

### **Complete Database with ALL Excel Data:**
- **5 Judges**: Pnt. Yudith, Alvin, Inkristo, Febe, Bpk Rinto
- **11 Songs**: All with correct paths and file references
- **5 Rubrics**: With exact descriptions from Excel (1-5 scale)
- **16 Keywords**: With correct weights
- **18 Variants**: All name mappings
- **8 Config items**: All settings from Excel
- **2 Meta items**: Event name and year

### **Fast File Access:**
- **Audio files**: Direct streaming from Supabase Storage
- **PDF files**: Instant viewing
- **No more Google Drive delays!**

### **Global Analytics:**
- **All judges data** combined
- **Comprehensive reports**
- **Fast PDF/Excel exports**

## 🚨 **Troubleshooting:**

### **"Database connection failed"**
- Check Supabase URL and key in `secrets.toml`
- Verify project is active

### **"File not found"**
- Check bucket name is `song-contest-files`
- Verify folders exist: `audios/`, `pdfs/`, `images/`
- Run migration script

### **"Permission denied"**
- Check bucket is public OR
- Add storage policies (Step 6)

### **Migration fails**
- Check Excel file path: `not_used/PENILAIAN_LOMBA_CIPTA_LAGU.xlsx`
- Verify all sheets exist
- Check file permissions

## ✅ **Success Checklist:**

- [ ] Supabase project created
- [ ] Database schema setup (run `setup_database.sql`)
- [ ] Storage bucket `song-contest-files` created
- [ ] Folders created: `audios/`, `pdfs/`, `images/`, `certificates/`
- [ ] Files uploaded (manual or migration script)
- [ ] `secrets.toml` configured with Supabase credentials
- [ ] Migration script run successfully
- [ ] New app tested: `streamlit run app_new.py`

**🎉 You're ready to go!**
