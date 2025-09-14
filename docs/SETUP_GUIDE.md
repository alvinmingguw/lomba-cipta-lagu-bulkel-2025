# 🚀 Complete Setup Guide - Theme Song GKI Perumnas

## 📋 Prerequisites

- Python 3.8+
- Supabase account (free tier is sufficient)
- Git
- Google Cloud Console account (for OAuth - optional)

## 🔧 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/alvinmingguw/themesong-gki-perumnas.git
cd themesong-gki-perumnas
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 🗄️ **Step 3: Supabase Project Setup**

### **Create New Supabase Project**

1. **Go to [supabase.com](https://supabase.com)**
2. **Click "New Project"**
3. **Fill in:**
   - **Name**: `themesong-gki-perumnas`
   - **Database Password**: Create a strong password
   - **Region**: `Southeast Asia (Singapore)` (recommended)
4. **Click "Create new project"**
5. **Wait 2-3 minutes** for setup to complete

### **Setup Database Schema**

1. **Go to SQL Editor** in your new Supabase project
2. **Run SQL files in order:**

#### Option A: Complete Fresh Setup
```bash
# Run all setup scripts in order
# Copy contents of sql/01_initial_setup.sql to Supabase SQL Editor and run
# Then copy contents of sql/02_songs_data.sql and run
# Then copy contents of sql/03_judges_and_auth.sql and run
```

#### Option B: Use run_all_setup.sql
```bash
# Copy entire contents of sql/run_all_setup.sql to Supabase SQL Editor
# Click "Run" - this will create all tables, data, and configurations
```

**This will create:**
- ✅ **All tables** with complete data
- ✅ **All indexes** for performance
- ✅ **Row Level Security** on all tables
- ✅ **Complete data** (judges, songs, rubrics, configurations)

## 📁 **Step 4: Storage Setup**

### **Create Storage Bucket & Folders**

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

### **Upload Files**

#### Option A: Manual Upload (Quick)
1. **Go to Storage** → `song-contest-files`
2. **Upload to `files/` folder:**
   - All `.mp3` and `.m4a` files
   - All `.pdf` files (notation and lyrics)

#### Option B: Automated Migration (Recommended)
```bash
python migrate_data.py  # If you have migration script
```

## 🔐 **Step 5: Authentication Setup**

### **Configure Supabase Auth Settings**

1. **Go to Supabase Dashboard** → Authentication → Providers

2. **Enable Email/Password:**
   - ✅ Enable email provider
   - ✅ Enable email confirmations
   - ✅ Set redirect URL: `http://localhost:8501` (for development)

3. **Enable Magic Links:**
   - ✅ Enable magic link authentication
   - ✅ Configure email templates

### **Google OAuth Setup (Optional)**

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create OAuth 2.0 credentials**
3. **Application type:** Web application
4. **Authorized redirect URIs:**
   ```
   https://[your-project-id].supabase.co/auth/v1/callback
   ```
5. **Copy Client ID and Client Secret**
6. **Add to Supabase** → Authentication → Providers → Google

### **Configure Auth Settings**

1. **Go to Authentication → Settings**
2. **Site URL:** `http://localhost:8501` (for development)
3. **Redirect URLs:** Add these URLs:
   ```
   http://localhost:8501
   http://localhost:8501/**
   https://your-production-domain.com
   https://your-production-domain.com/**
   ```

## ⚙️ **Step 6: Environment Configuration**

### **Create Secrets File**

Create `.streamlit/secrets.toml`:

```toml
# Supabase Configuration
supabase_url = "https://your-project-id.supabase.co"
supabase_anon_key = "your-anon-key-here"

# App Configuration
app_url = "http://localhost:8501"  # Change for production

# Google OAuth (Optional)
[google_oauth]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"
```

### **Get Your Credentials**

1. **Go to Supabase Dashboard** → Settings → API
2. **Copy:**
   - **Project URL** → `supabase_url`
   - **Anon/Public Key** → `supabase_anon_key`

## 🚀 **Step 7: Run Application**

### **Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Start Application**
```bash
streamlit run app.py
```

### **Access Application**
- **Local:** `http://localhost:8501`
- **Network:** Check terminal for network URL

## 🧪 **Step 8: Test the Setup**

### **Verify Basic Functionality**
1. ✅ Application loads without errors
2. ✅ Songs list displays correctly
3. ✅ Audio files play properly
4. ✅ PDF files open correctly

### **Test Authentication**
1. ✅ Login page appears
2. ✅ Magic link authentication works
3. ✅ Google OAuth works (if configured)
4. ✅ Admin access works

### **Test Core Features**
1. ✅ Song evaluation form works
2. ✅ Scoring system functions
3. ✅ Analytics display correctly
4. ✅ Certificate download works

## 🔐 Authentication Setup

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URIs
4. Update secrets.toml with credentials

### Magic Link Setup

1. Configure email templates in Supabase
2. Set up custom SMTP (optional)
3. Test email delivery

### Admin Setup

1. Create admin user in `auth_profiles` table
2. Set role to 'admin'
3. Test admin access

## 📊 Configuration Options

### Database Configuration

Key settings in `config` table:

```sql
-- Contest settings
UPDATE config SET config_value = 'Your Contest Title' WHERE config_key = 'CONTEST_TITLE';
UPDATE config SET config_value = 'Your Theme' WHERE config_key = 'CONTEST_THEME';

-- Form scheduling
UPDATE config SET config_value = '2025-01-01 00:00:00' WHERE config_key = 'FORM_OPEN_TIME';
UPDATE config SET config_value = '2025-12-31 23:59:59' WHERE config_key = 'FORM_CLOSE_TIME';

-- Feature toggles
UPDATE config SET config_value = 'True' WHERE config_key = 'SHOW_AUTHOR';
UPDATE config SET config_value = 'True' WHERE config_key = 'FINAL_SUBMIT_ENABLED';
UPDATE config SET config_value = 'False' WHERE config_key = 'USE_PREGENERATED_CERTIFICATES';
```

### Application Settings

Modify in Streamlit interface or directly in database.

## 🧪 Testing

### Run Tests

```bash
# Database connection test
python testing/test_connection.py

# Authentication test
python testing/test_magic_link.py

# Dashboard test
python testing/test_dashboard.py
```

### Verify Setup

1. Access application at `http://localhost:8501`
2. Test authentication
3. Verify song data loading
4. Test evaluation workflow
5. Check admin functions

## 🔧 Troubleshooting

### Common Issues

#### Database Connection

```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test connection
psql -d your_database -c "SELECT 1;"
```

#### Supabase Issues

- Verify URL and keys in secrets.toml
- Check storage bucket permissions
- Verify authentication settings

#### File Upload Issues

- Check Supabase storage permissions
- Verify file paths in database
- Test file access URLs

#### Authentication Problems

- Verify OAuth credentials
- Check email configuration
- Test Magic Link delivery

### Debug Mode

Enable debug mode by adding to secrets.toml:

```toml
[debug]
enabled = true
log_level = "DEBUG"
```

## 📱 Production Deployment

### Streamlit Cloud

1. Connect GitHub repository
2. Add secrets in Streamlit Cloud dashboard
3. Deploy application

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app_new.py"]
```

### Environment Variables

Set in production environment:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## 🔄 Maintenance

### Regular Tasks

- Monitor database performance
- Check storage usage
- Review authentication logs
- Update dependencies

### Backup Strategy

- Database: Regular PostgreSQL backups
- Files: Supabase storage backups
- Configuration: Export config table

### Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run any new migrations
psql -d your_database -f sql/migrations/latest.sql
```

## 🔒 **Security & Authentication**

### **Judge-Based Authentication System**

The system ensures **ONLY judges with emails can login/signup**:

- ✅ Judge has email in `judges` table = can login
- ❌ Judge has no email = cannot login
- ✅ Admin can manage judge emails through admin panel

### **Authentication Flow**
```
User tries to login/signup → Check judges table →
  ├─ If email exists in judges: Allow access
  └─ If email not in judges: Block with error message
```

### **Admin Management**
- Super admin can add/edit/remove judge emails
- Real-time management through admin panel
- No separate whitelist table needed

### **Security Features**
- Row Level Security (RLS) on all tables
- Email-based authorization
- Session management
- OAuth integration (Google)
- Magic link authentication

## 📞 Support

For issues and questions:

1. Check troubleshooting section
2. Review logs in Streamlit interface
3. Check Supabase dashboard for errors
4. Contact system administrator

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Project Features](FEATURES.md)
- [Project Structure](PROJECT_STRUCTURE.md)
