# 🚀 Setup Guide

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Supabase account
- Git

## 🔧 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/alvinmingguw/lomba-cipta-lagu-bulkel-2025.git
cd lomba-cipta-lagu-bulkel-2025
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

#### Option A: Complete Fresh Setup

```bash
# Run all setup scripts in order
psql -d your_database -f sql/run_all_setup.sql
```

#### Option B: Step by Step

```bash
# 1. Initial setup (tables, indexes, basic data)
psql -d your_database -f sql/01_initial_setup.sql

# 2. Songs data
psql -d your_database -f sql/02_songs_data.sql

# 3. Judges and authentication
psql -d your_database -f sql/03_judges_and_auth.sql

# 4. Certificate configuration
psql -d your_database -f add_certificate_config.sql
```

### 4. Supabase Configuration

#### Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Note your project URL and anon key

#### Setup Storage

1. Create bucket named `song-contest-files`
2. Upload song files to appropriate folders:
   ```
   contest-files/
   ├── audio/
   ├── notation/
   ├── lyrics/
   └── certificates/
   ```

#### Configure Authentication

1. Enable Google OAuth (optional)
2. Configure email templates for Magic Links
3. Set up custom SMTP (optional)

### 5. Environment Configuration

Create `.streamlit/secrets.toml`:

```toml
[supabase]
supabase_url = "your-supabase-url"
supabase_anon_key = "your-anon-key"
supabase_service_key = "your-service-key"

[app]
app_url = "http://localhost:8501"

[google_oauth]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"
redirect_uri = "your-redirect-uri"
```

### 6. File Upload

Upload song files to Supabase Storage:

```bash
# Use Supabase CLI or web interface
supabase storage cp files/ supabase://song-contest-files/
```

### 7. Run Application

```bash
streamlit run app_new.py
```

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
