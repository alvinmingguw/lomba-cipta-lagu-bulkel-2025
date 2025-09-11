# Setup Supabase Authentication

## 🔧 **Step 1: Run Database Schema**

1. **Go to Supabase Dashboard** → SQL Editor
2. **Run `setup_auth_schema.sql`** (already created)
3. **Verify tables created:**
   - `auth_profiles`
   - `admin_sessions`
   - Updated `judges` table with auth columns

## 🔐 **Step 2: Configure Supabase Auth Settings**

### **A. Enable Authentication Providers**

1. **Go to Supabase Dashboard** → Authentication → Providers

2. **Enable Email/Password:**
   - ✅ Enable email provider
   - ✅ Enable email confirmations
   - ✅ Set redirect URL: `http://localhost:8501` (for development)

3. **Enable Google OAuth:**
   - ✅ Enable Google provider
   - **Client ID:** Get from Google Cloud Console
   - **Client Secret:** Get from Google Cloud Console
   - **Redirect URL:** `https://[your-project].supabase.co/auth/v1/callback`

### **B. Configure Auth Settings**

1. **Go to Authentication → Settings**

2. **Site URL:** `http://localhost:8501` (for development)

3. **Redirect URLs:** Add these URLs:
   ```
   http://localhost:8501
   http://localhost:8501/**
   https://your-production-domain.com
   https://your-production-domain.com/**
   ```

4. **Email Templates:** Customize if needed
   - Confirm signup
   - Magic link
   - Password recovery

### **C. Configure RLS Policies**

The `setup_auth_schema.sql` already includes RLS policies for `auth_profiles` table.

## 🎯 **Step 3: Google OAuth Setup**

### **A. Create Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Google+ API

### **B. Create OAuth Credentials**

1. **Go to APIs & Services** → Credentials
2. **Create OAuth 2.0 Client ID**
3. **Application type:** Web application
4. **Authorized redirect URIs:**
   ```
   https://gxhtdwmjjgwrqlrvxgel.supabase.co/auth/v1/callback
   ```
5. **Copy Client ID and Client Secret**

### **C. Add to Supabase**

1. **Go to Supabase** → Authentication → Providers → Google
2. **Paste Client ID and Client Secret**
3. **Save**

## 🔑 **Step 4: Update Secrets**

Update `.streamlit/secrets.toml`:

```toml
# Existing Supabase config
supabase_url = "https://gxhtdwmjjgwrqlrvxgel.supabase.co"
supabase_anon_key = "your-anon-key"

# Add app URL for redirects
app_url = "http://localhost:8501"  # Change for production

# Optional: Add Google OAuth credentials for reference
[google_oauth]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"
```

## 🧪 **Step 5: Test Authentication**

### **A. Run the Application**

```bash
streamlit run app_new.py
```

### **B. Test Login Flows**

1. **Email/Password:**
   - Try signup with new email
   - Check email for verification
   - Try login after verification

2. **Magic Link:**
   - Enter email
   - Check email for magic link
   - Click link to login

3. **Google OAuth:**
   - Click Google login
   - Should redirect to Google
   - Should redirect back to app after auth

### **C. Test Admin Features**

1. **Login as admin** (Alvin Giovanni Mingguw)
2. **Check admin panel appears**
3. **Test "Login as Juri" feature**
4. **Test return to admin**

## 🐛 **Troubleshooting**

### **Common Issues:**

1. **"Invalid redirect URL"**
   - Check redirect URLs in Supabase settings
   - Make sure app_url in secrets matches

2. **"Email not confirmed"**
   - Check email for confirmation link
   - Check spam folder
   - Disable email confirmation in Supabase for testing

3. **Google OAuth not working**
   - Check Google Cloud Console settings
   - Verify redirect URI matches exactly
   - Check client ID/secret in Supabase

4. **Judge not found after login**
   - Check if email exists in judges table
   - Check auth_profiles table for user mapping
   - Run the trigger function manually if needed

### **Debug Commands:**

```sql
-- Check auth_profiles
SELECT * FROM auth_profiles;

-- Check judges with emails
SELECT id, name, email, role FROM judges WHERE email IS NOT NULL;

-- Check admin sessions
SELECT * FROM admin_sessions WHERE is_active = true;
```

## 🚀 **Production Deployment**

1. **Update redirect URLs** to production domain
2. **Update app_url** in secrets
3. **Configure custom domain** in Supabase if needed
4. **Test all auth flows** in production
5. **Monitor auth logs** in Supabase dashboard

## 📋 **Checklist**

- [ ] Database schema updated
- [ ] Email/password auth enabled
- [ ] Google OAuth configured
- [ ] Magic links enabled
- [ ] Redirect URLs configured
- [ ] Secrets updated
- [ ] Application tested
- [ ] Admin features tested
- [ ] Production ready
