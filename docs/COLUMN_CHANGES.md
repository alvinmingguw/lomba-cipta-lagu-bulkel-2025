# Database Column Name Changes

This document outlines the column name changes made to follow international standards (snake_case, English, descriptive names).

## 📋 **Summary of Changes**

### **1. Table: `judges`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `active` | `is_active` | More descriptive boolean naming |

### **2. Table: `rubrics`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `key` | `rubric_key` | More specific, avoids SQL reserved word |
| `aspect` | `aspect_name` | More descriptive |
| `active` | `is_active` | More descriptive boolean naming |

### **3. Table: `keywords`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `type` | `keyword_type` | More specific, avoids SQL reserved word |
| `text` | `keyword_text` | More descriptive |
| `active` | `is_active` | More descriptive boolean naming |

### **4. Table: `variants`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `from_name` | `source_name` | More standard naming |
| `to_key` | `target_key` | More standard naming |

### **5. Table: `songs`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `alias` | `song_code` | More descriptive |
| `alias_merge` | `display_name` | More descriptive |
| `audio_path` | `audio_file_path` | More specific |
| `notasi_path` | `notation_file_path` | English + more specific |
| `syair_path` | `lyrics_file_path` | English + more specific |
| `lirik_text` | `lyrics_text` | English (already correct) |
| `syair_chord` | `lyrics_with_chords` | English + more descriptive |
| `active` | `is_active` | More descriptive boolean naming |
| (constraint) | `song_code UNIQUE` | Added for ON CONFLICT support |
| (constraint) | `title UNIQUE` | Added for ON CONFLICT support |

### **6. Table: `file_metadata`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `original_name` | `original_filename` | More specific |
| `file_size` | `file_size_bytes` | More descriptive unit |

### **7. Table: `winners`**
| Old Column | New Column | Reason |
|------------|------------|---------|
| `rank` | `position` | More standard naming |
| `notes` | `prize_description` | More descriptive |
| (new) | `is_active` | Added for consistency |

## 🔧 **Files Updated**

### **Database Schema:**
- ✅ `setup_database.sql` - All table definitions and sample data
- ✅ `songs_data_complete.sql` - Songs insert statements

### **Application Code:**
- ✅ `services/database_service.py` - Query updates
- ✅ `services/file_service.py` - File metadata updates
- ✅ `migrate_data.py` - Migration script updates
- ✅ `app_new.py` - Already using correct column names

### **Scripts:**
- ✅ `generate_evaluations_sql.py` - Uses Excel data (no changes needed)

## 📝 **Migration Notes**

1. **Backward Compatibility**: These changes are breaking changes. Old column names will not work.

2. **Data Migration**: When migrating from old schema:
   ```sql
   -- Example migration for songs table
   ALTER TABLE songs RENAME COLUMN alias TO song_code;
   ALTER TABLE songs RENAME COLUMN alias_merge TO display_name;
   -- ... etc
   ```

3. **Application Updates**: All application code has been updated to use new column names.

## ✅ **Benefits**

1. **Consistency**: All boolean columns use `is_*` prefix
2. **Clarity**: Column names are more descriptive and self-documenting
3. **Standards**: Follows international naming conventions
4. **SQL Safety**: Avoids reserved words like `key`, `type`, `rank`
5. **English**: All column names in English for international compatibility

## 🚀 **Next Steps**

1. Run the updated `setup_database.sql` to create schema with new column names
2. Use `songs_data_complete.sql` to insert all song data
3. Test application with new schema
4. Deploy to production when ready
