# 🎵 GKI Perumnas Song Contest 2025

> **Advanced Digital Judging System** for GKI Perumnas Song Contest
> Theme: **"Waktu Bersama Harta Berharga"** (Time Together, Precious Treasure)
> Biblical Reference: **Ephesians 5:15-16**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)

## 🚀 Quick Start

```bash
# 1. Setup Environment
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit with your Supabase credentials

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Run Application
streamlit run app.py

# 4. Access Application
# Public: http://localhost:8501 (Winners & All Songs)
# Judges: Login via Google OAuth
# Admin: Use admin panel for management
```

## 📁 Project Architecture

```
gki-perumnas-song-contest-2025/
├── 🎯 app.py                       # Main Streamlit application
├── 📋 requirements.txt             # Python dependencies
├── 📖 README.md                    # Project documentation
├── ⚙️ .streamlit/
│   ├── secrets.toml               # Supabase configuration (create from example)
│   └── secrets.toml.example       # Configuration template
├── 🔧 services/                   # Core application services
│   ├── analytics_service.py       # 📊 Scoring and analytics
│   ├── auth_service.py            # 🔐 Authentication & user management
│   ├── cache_service.py           # ⚡ Performance caching
│   ├── database_service.py        # 🗄️ Database operations (main)
│   ├── export_service.py          # 📤 Data export functionality
│   ├── file_service.py            # 📁 Supabase Storage integration
│   └── scoring_service.py         # 🤖 AI-assisted evaluation
├── 🎨 components/                 # UI components
│   ├── admin_panel.py             # 👨‍💼 Admin interface with tabs
│   └── login_simple.py            # 🔑 Authentication UI
├── 🎵 song-contest-files/         # Local file storage (mirrors Supabase)
│   ├── files/                     # Audio, notation, lyrics files
│   └── certificates/              # Generated certificates
├── 🖼️ assets/                     # Static assets (images, banners)
├── 🗃️ sql/                        # Database setup scripts
├── 📚 docs/                       # Detailed documentation
├── 🧪 testing/                    # Development and testing files
├── 📦 archive/                    # Legacy code and migration tools
└── 🚫 unused/                     # Deprecated components
```

## 📊 Performance & Architecture

### **🚀 Performance Improvements**
| Feature | Old (Google Sheets) | New (Supabase) | Improvement |
|---------|-------------------|----------------|-------------|
| **Page Load Time** | 8-15 seconds | 1-3 seconds | **5x faster** |
| **File Access** | 3-10 seconds | <1 second | **10x faster** |
| **Data Updates** | 2-5 seconds | <0.5 seconds | **10x faster** |
| **Analytics** | Judge-specific only | Global + Judge-specific | **Much better** |
| **Caching** | Inconsistent | Smart & unified | **Reliable** |
| **Error Rate** | High (API limits) | Very low | **Much more stable** |

### **🏗️ Modular Architecture**
- ⚡ **10x faster performance** with Supabase backend
- 🏗️ **Modular architecture** (split from 3,630 lines into organized services)
- 🌐 **Global analytics** (data from ALL judges, not just active judge)
- 📊 **Optimized file storage** with Supabase Storage
- 🔄 **Smart caching** for better user experience
- 📱 **Better mobile responsiveness**

## ✨ Major Features & Improvements

### 🎯 **Enhanced User Experience**
- **📊 Progress Dashboard**: Visual completion tracking with incomplete song highlights
- **🔐 Streamlined Final Submission**: Moved to History tab with global validation
- **💯 Standardized Scoring**: Consistent 100-point scale display throughout
- **🔄 Persistent Sessions**: Survives tab reloads with 24-hour duration
- **🎨 Clean Interface**: Removed redundant tabs, focused on essentials

### 🤖 **AI-Powered Analysis**
- **🎯 Theme Relevance**: Smart analysis against contest theme
- **📝 Lyrical Quality**: Poetic structure and meaning evaluation
- **🎵 Musical Richness**: Harmonic complexity and chord progression analysis
- **🔍 Keyword Detection**: Contest-specific vocabulary matching
- **📊 Visual Analytics**: Interactive charts and insights

### 🏆 **Professional Judging System**
- **5 Criteria Evaluation**: Comprehensive rubric-based scoring
- **Real-time Auto-save**: Never lose evaluation progress
- **Judge Analytics**: Individual performance tracking
- **Export Capabilities**: PDF and Excel reports
- **Certificate Management**: Automated or pre-generated options

### 📊 **Advanced Analytics & Reporting** *(Latest Updates)*
- **🏆 Winner Analysis**: Comprehensive winner analytics with score breakdowns
- **🧠 Judge Insights**: Judge performance patterns and consistency analysis
- **📈 Global Leaderboard**: Real-time rankings with detailed statistics
- **🎵 Song Profile Analysis**: Individual song performance with full-width detailed views
- **📄 Enhanced PDF Reports**: Complete winner reports with all rankings and judge notes
- **🎯 Detailed Rubric Breakdown**: Per-aspect analysis with strengths/weaknesses identification

### 🌐 **Public Features**
- **Winners Showcase**: Display contest winners with audio players
- **All Songs Browser**: Search and listen to all contest entries
- **Responsive Design**: Works on desktop and mobile
- **Audio Streaming**: Direct audio playback from Supabase Storage

## 🔧 Configuration & Setup

### **🗄️ Database Setup**
```bash
# 1. Create Supabase project
# 2. Run database migrations
psql -d your_database -f sql/run_all_setup.sql

# 3. Setup Storage bucket: 'song-contest-files'
# 4. Configure RLS policies for security
```

### **⚙️ Application Configuration**
Key configuration options in the `config` table:

| Config Key | Description | Values |
|------------|-------------|---------|
| `THEME` | Contest theme display | String |
| `FORM_OPEN` | Enable/disable evaluation form | true/false |
| `FORM_OPEN_DATETIME` | When evaluation opens | DateTime |
| `FORM_CLOSE_DATETIME` | When evaluation closes | DateTime |
| `WINNER_ANNOUNCE_DATETIME` | When winners are announced | DateTime |
| `WINNERS_TOP_N` | Number of winners to display | Integer (1-10) |
| `SHOW_AUTHOR` | Show/hide composer names | true/false |
| `CERTIFICATE_MODE` | Certificate generation mode | STORAGE/GENERATE |
| `WINNER_DISPLAY_LAYOUT` | Winner display layout | TABS/COLUMNS |
| `SHOW_PDF_DOCUMENTS` | Show PDF document links | true/false |
| `TIMEZONE` | Application timezone | String (e.g., Asia/Jakarta) |

### **🔐 Authentication Setup**
- **Google OAuth**: Configure in Supabase Auth settings
- **Magic Links**: Email-based authentication
- **Admin Access**: Service role for admin functions

## 🗄️ Database Schema

| Table | Description | Key Fields |
|-------|-------------|------------|
| `songs` | Contest songs with metadata | title, composer, audio_file_path |
| `judges` | Judge information | name, email, auth_user_id |
| `rubrics` | Evaluation criteria | name, weight, ai_assisted |
| `evaluations` | Judge evaluations | judge_id, song_id, scores |
| `keywords` | Theme analysis keywords | keyword, weight, category |
| `config` | Application configuration | key, value |
| `auth_profiles` | User authentication | user_id, email, role |

## 🏆 Contest Information

**🎯 Theme**: "Waktu Bersama Harta Berharga" (Time Together, Precious Treasure)
**📖 Biblical Reference**: Ephesians 5:15-16
**🎪 Target Audience**: GKI Perumnas congregation (all ages)
**🏅 Evaluation**: 5-criteria rubric with AI assistance

## 📝 Evaluation Criteria

| Criteria | Weight | AI Assisted | Description |
|----------|--------|-------------|-------------|
| **🎯 Theme Relevance** | 20% | ✅ Yes | Alignment with contest theme |
| **📝 Lyrical Quality** | 20% | ✅ Yes | Poetic structure and meaning |
| **🎵 Musical Richness** | 20% | ✅ Yes | Harmonic complexity and progression |
| **🎨 Creativity & Originality** | 20% | ❌ Manual | Innovation and uniqueness |
| **👥 Congregational Suitability** | 20% | ❌ Manual | Appropriateness for worship |

## 📱 Application Usage

### **🌐 Public Access** (No Login Required)
- **🏆 Winners Showcase**: View contest winners with audio players
- **🎵 All Songs Browser**: Search and listen to all contest entries
- **🔍 Smart Search**: Filter songs by title or composer
- **📱 Mobile Optimized**: Responsive design for all devices

### **👨‍⚖️ Judge Access** (Authentication Required)
- **🔐 Secure Login**: Google OAuth authentication
- **📊 Digital Evaluation**: Score songs using comprehensive rubric
- **🤖 AI Assistance**: Get intelligent suggestions for evaluation
- **📈 Progress Tracking**: Monitor completion status in real-time
- **✅ Final Submission**: Lock evaluations when complete

### **👨‍💼 Admin Access** (Service Role)
- **📊 Dashboard Overview**: System metrics and judge impersonation
- **📈 Recent Activity**: Monitor evaluation progress in real-time
- **👨‍⚖️ Judge Management**: Add, edit, and manage judge accounts
- **⚙️ Configuration Management**: Organized tabs for all system settings
- **🧹 Configuration Cleanup**: Identify and remove unused configurations
- **🏆 Certificate Management**: Generate and manage certificates
- **📊 Data Export**: Export evaluation data for analysis
- **🏆 Winner Analysis**: Comprehensive analytics with score comparisons and insights
- **🧠 Judge Analytics**: Separate judge insights and performance patterns
- **🎵 Song Analysis**: Detailed per-song analysis with full-width layouts

## 🆕 Recent Updates (Latest Version)

### **🎯 Analytics & Reporting Enhancements**
- **🏆 Winner Analysis Improvements**:
  - Fixed layout issues with full-width display
  - Enhanced score analysis with proper 100-point scale
  - Comprehensive winner breakdown with all rankings
  - Judge insights moved to separate analytics section

- **📊 Song Profile Analysis**:
  - **Full-width layout**: Removed cramped column layouts for better visibility
  - **Enhanced button placement**: Download Report and Detail Analysis now use full-width buttons
  - **Improved UX**: Detail Analysis appears directly within the same expander
  - **Better metrics display**: 5-6 metrics displayed horizontally for better readability

- **📄 PDF Report Enhancements**:
  - **Complete rankings**: Winner reports now show ALL songs, not just top winners
  - **All judge notes**: Display all judge comments instead of just the latest
  - **Comprehensive analysis**: Enhanced song reports with detailed breakdowns

- **🧠 Judge Analytics**:
  - **Separated from Winner Analysis**: Now has its own dedicated section
  - **Improved UX**: Direct display without requiring additional button clicks
  - **Enhanced insights**: Better judge performance patterns and consistency analysis

### **🔧 Technical Improvements**
- **Layout Optimization**: Removed nested expanders that caused display issues
- **Session State Management**: Better handling of detailed analysis display
- **Error Handling**: Fixed column reference errors in analytics
- **Performance**: Optimized data retrieval for analytics and reporting

## 🛠️ Development Guide

### **🚀 Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
streamlit run app.py --server.runOnSave true

# Access application
open http://localhost:8501
```

### **🧪 Testing & Debugging**
```bash
# Run tests
python -m pytest testing/

# Check database connection
python testing/test_connection.py

# Debug authentication
python testing/test_magic_link.py
```

### **📚 Documentation Structure**
- **`docs/`**: Detailed technical documentation
- **`testing/`**: Development and testing files
- **`sql/`**: Database setup and migration scripts

## 🚀 Deployment

### **☁️ Streamlit Cloud**
```bash
# 1. Push to GitHub repository
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main

# 2. Connect to Streamlit Cloud
# 3. Add secrets in Streamlit Cloud dashboard
# 4. Deploy from GitHub repository
```

### **🐳 Docker Deployment**
```dockerfile
# Dockerfile included for containerized deployment
docker build -t lomba-lagu .
docker run -p 8501:8501 lomba-lagu
```

### **🔧 Environment Variables**
Required secrets for deployment:
- `supabase_url`
- `supabase_anon_key`
- `supabase_service_role_key`
- `google_client_id` (optional)
- `google_client_secret` (optional)

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License & Credits

**Created for**: GKI Perumnas Lomba Cipta Lagu 2025
**Theme**: "Waktu Bersama Harta Berharga"
**Technology Stack**: Streamlit + Supabase + PostgreSQL
**AI Integration**: OpenAI GPT for evaluation assistance

---

<div align="center">

**🎵 Made with ❤️ for GKI Perumnas Community**

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)

</div>
