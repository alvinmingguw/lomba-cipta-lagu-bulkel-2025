# 📁 Project Structure

## 🎯 **Clean & Organized Structure**

```
gki-perumnas-song-contest-2025/
├── 🎵 app.py                  # Main Streamlit application
├── 📦 requirements.txt        # Python dependencies
├── 📖 README.md               # Main documentation
├── 🗃️ sql/                   # Database setup scripts
│   ├── 01_initial_setup.sql   # Tables, indexes, initial data
│   ├── 02_songs_data.sql      # Complete song database
│   ├── 03_judges_and_auth.sql # Judges and authentication
│   ├── add_certificate_config.sql # Certificate configuration
│   ├── add_winner_display_config.sql # Winner display config
│   └── run_all_setup.sql      # Complete setup script
├── ⚙️ services/              # Application services
│   ├── __init__.py
│   ├── analytics_service.py   # Analytics & insights
│   ├── auth_service.py        # Authentication & sessions
│   ├── cache_service.py       # Performance caching
│   ├── database_service.py    # Database operations (main)
│   ├── export_service.py      # Reports & certificates
│   ├── file_service.py        # Supabase Storage integration
│   └── scoring_service.py     # AI scoring algorithms
├── 🎨 components/            # UI components
│   ├── admin_panel.py         # Admin interface with tabs
│   └── login_simple.py        # Authentication UI
├── 🎼 song-contest-files/    # Local file storage (mirrors Supabase)
│   ├── files/                # Audio, notation, lyrics files
│   └── certificates/         # Generated certificates
│   ├── Song01_Audio_*.mp3
│   ├── Song01_Notasi_*.pdf
│   ├── Song01_Syair_*.pdf
│   └── ... (11 songs total)
├── 🖼️ assets/               # Static assets & images
│   ├── banner.png
│   ├── logo.png
│   ├── logo_landscape.png
│   └── FLYER_*.png
├── 🏆 CERTIFICATE/           # Generated certificates
│   └── Participant_*.pdf
├── 📊 PENILAIAN_LOMBA_CIPTA_LAGU.xlsx # Evaluation data
├── 📚 docs/                  # Documentation
│   ├── FEATURES.md           # Feature documentation
│   ├── SETUP_GUIDE.md        # Setup instructions
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── README_NEW_SYSTEM.md  # New system overview
│   └── ... (other docs)
├── 🧪 testing/              # Testing & debugging files
│   ├── README.md
│   ├── test_*.py
│   ├── debug_*.sql
│   └── ... (testing files)
└── 📦 archive/              # Archived files
    ├── README.md
    ├── legacy_sql/           # Old SQL scripts
    ├── not_used/            # Unused files
    ├── not_used2/           # More unused files
    └── ... (archived files)
```

## 📋 **File Categories**

### 🎯 **Core Application**
- `app_new.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `README.md` - Main documentation

### 🗃️ **Database**
- `sql/` - Production database scripts
- All scripts are consolidated and ready for production use

### ⚙️ **Services**
- `services/` - Modular application services
- Each service handles specific functionality
- Clean separation of concerns

### 🎨 **UI Components**
- `components/` - Reusable UI components
- Admin panel and login interfaces

### 📁 **Data & Assets**
- `files/` - Song files (audio, notation, lyrics)
- `assets/` - Static images and branding
- `CERTIFICATE/` - Generated certificates

### 📚 **Documentation**
- `docs/` - Complete documentation
- Setup guides, features, and technical docs

### 🧪 **Development**
- `testing/` - Testing and debugging files
- Safe to ignore in production

### 📦 **Archive**
- `archive/` - Old files kept for reference
- Can be deleted after confirming new system works

## 🚀 **Quick Start**

1. **Database Setup**
   ```bash
   psql -d your_database -f sql/run_all_setup.sql
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**
   ```bash
   streamlit run app_new.py
   ```

## 🔧 **Development Workflow**

1. **Main App**: Edit `app_new.py`
2. **Services**: Modify files in `services/`
3. **UI Components**: Update `components/`
4. **Database**: Add scripts to `sql/`
5. **Testing**: Use files in `testing/`

## 📊 **File Counts**

- **Core Files**: 3 (app, requirements, README)
- **SQL Scripts**: 5 (complete database setup)
- **Services**: 7 (modular backend services)
- **Components**: 4 (UI components)
- **Song Files**: 33 (11 songs × 3 files each)
- **Assets**: 6 (logos, banners, flyers)
- **Documentation**: 9 (comprehensive docs)
- **Testing**: 14 (development files)
- **Archive**: 50+ (legacy files)

## 🎯 **Benefits of New Structure**

### ✅ **Organization**
- Clear separation of concerns
- Easy to find specific functionality
- Logical grouping of related files

### ✅ **Maintainability**
- Modular services architecture
- Clean code organization
- Easy to update and extend

### ✅ **Documentation**
- Comprehensive documentation
- Clear setup instructions
- Feature explanations

### ✅ **Development**
- Separate testing environment
- Archive for reference
- Clean production files

### ✅ **Deployment**
- Ready-to-use SQL scripts
- Consolidated dependencies
- Clear deployment path

## 🔄 **Migration Notes**

All functionality from legacy files has been:
1. **Consolidated** into `app_new.py`
2. **Modularized** into `services/`
3. **Documented** in `docs/`
4. **Tested** with files in `testing/`
5. **Archived** for reference

## 🗑️ **Safe to Delete**

After confirming the new system works:
- `archive/` folder (except for reference)
- `testing/` folder (in production)
- Old README files in `docs/`

## 📈 **Future Improvements**

1. **Docker Support**: Add Dockerfile for containerization
2. **CI/CD**: Add GitHub Actions for automated testing
3. **Monitoring**: Add logging and monitoring
4. **Backup**: Automated backup scripts
5. **Security**: Enhanced security measures
