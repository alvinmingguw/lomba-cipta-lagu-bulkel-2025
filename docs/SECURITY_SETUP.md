# 🔒 Security Setup - Simple Judge-Based Authentication

## 🎯 **Overview**

Sistem ini memastikan **HANYA juri yang punya email yang bisa login/signup**. Simple dan clean - pakai table `judges` yang sudah ada.

## 🔐 **How It Works**

### **1. Judges Table Authorization**
- Judge punya email = bisa login ✅
- Judge tidak punya email = tidak bisa login ❌
- Simple rule: email di judges table = authorized

### **2. Authentication Flow**
```
User tries to login/signup → Check judges table →
  ├─ If email exists in judges: Allow access
  └─ If email not in judges: Block with error message
```

### **3. Admin Management**
- Super admin bisa add/edit/remove judge emails
- Real-time management melalui admin panel
- No separate whitelist table needed!

---

## 🚀 **Setup Instructions**

### **Step 1: Run Simple Setup**
```sql
-- Run setup_simple_auth.sql di Supabase SQL Editor
-- This updates existing judges table with emails
```

### **Step 2: Add Judge Emails**

#### **Option A: Via SQL (Recommended for initial setup)**
1. **Edit `setup_simple_auth.sql`**
2. **Replace placeholder emails dengan email real:**
   ```sql
   UPDATE judges SET
       email = CASE
           WHEN name = 'Alvin Giovanni Mingguw' THEN 'real-admin@gmail.com'
           WHEN name = 'Judge Name' THEN 'real-judge@gmail.com'
           -- Add more real emails here
       END
   ```
3. **Run di Supabase SQL Editor**

#### **Option B: Via Admin Panel (After app is running)**
1. **Login sebagai admin**
2. **Go to "👨‍⚖️ Judge Management"**
3. **Add/edit judge emails**

### **Step 3: Test Security**
1. **Try login dengan email yang TIDAK di whitelist** → Should be blocked
2. **Try login dengan email yang di whitelist** → Should work
3. **Test all authentication methods** (Google, Magic Link, Email/Password)

---

## 👨‍⚖️ **Managing Judge Access**

### **Add New Judge (Admin Panel)**
1. Login as admin
2. Go to "👨‍⚖️ Judge Management"
3. Click "➕ Add New Judge"
4. Enter name, email, select role
5. Click "➕ Add Judge"

### **Edit Judge Email (Admin Panel)**
1. Find judge in the list
2. Click ✏️ button next to judge
3. Enter new email
4. Click 💾 to save

### **Add Judge (SQL)**
```sql
INSERT INTO judges (name, email, role, is_active) VALUES
('New Judge Name', 'new-judge@example.com', 'judge', true);
```

### **Remove Access (SQL)**
```sql
-- Remove login access (keep judge data)
UPDATE judges SET email = NULL WHERE name = 'Judge Name';

-- Or deactivate completely
UPDATE judges SET is_active = false WHERE name = 'Judge Name';
```

---

## 🛡️ **Security Features**

### **✅ What's Protected:**
- ❌ No signup without authorized email
- ❌ No login without authorized email  
- ❌ No Google OAuth without authorized email
- ❌ No magic link without authorized email
- ✅ Only whitelisted emails can access
- ✅ Role-based access (admin vs judge)
- ✅ Admin can manage whitelist real-time

### **🔒 Security Levels:**

#### **Level 1: Email Whitelist (Current)**
- Only specific emails can access
- Perfect for controlled access
- Easy to manage

#### **Level 2: Domain Restriction (Optional)**
```sql
-- Only emails from specific domains
WHERE email LIKE '%@yourdomain.com' OR email LIKE '%@partnerdomain.com'
```

#### **Level 3: Invite-Only (Future)**
- Admin sends invitations
- Users click invite link to signup
- More formal process

---

## 🧪 **Testing Scenarios**

### **Test 1: Unauthorized Email**
1. Try signup with `unauthorized@test.com`
2. **Expected:** ❌ "Email is not authorized to access this system"

### **Test 2: Authorized Email**
1. Try signup with email from whitelist
2. **Expected:** ✅ Account created successfully

### **Test 3: Google OAuth**
1. Try Google login with unauthorized email
2. **Expected:** ❌ Blocked after OAuth redirect

### **Test 4: Magic Link**
1. Try magic link with unauthorized email
2. **Expected:** ❌ "Email is not authorized"

### **Test 5: Admin Management**
1. Login as admin
2. Add new email to whitelist
3. Try login with that email
4. **Expected:** ✅ Should work immediately

---

## 📋 **Current Authorized Emails**

**Update this list with real emails:**

### **Admins:**
- `alvinmingguw@gmail.com` - Alvin Giovanni Mingguw (Super Admin)
- `your-admin-email@gmail.com` - Replace with real admin email

### **Judges:**
- `judge1@gmail.com` - Replace with real judge email
- `judge2@gmail.com` - Replace with real judge email
- `judge3@gmail.com` - Replace with real judge email
- `judge4@gmail.com` - Replace with real judge email
- `judge5@gmail.com` - Replace with real judge email
- `judge6@gmail.com` - Replace with real judge email
- `judge7@gmail.com` - Replace with real judge email

---

## 🔧 **Troubleshooting**

### **"Email not authorized" error:**
1. Check if email is in whitelist: `SELECT * FROM email_whitelist WHERE email = 'user@example.com'`
2. Check if email is active: `WHERE is_active = true`
3. Add email to whitelist if needed

### **Admin can't add emails:**
1. Check admin role: `SELECT role FROM auth_profiles WHERE email = 'admin@example.com'`
2. Make sure admin is logged in properly

### **Google OAuth not checking whitelist:**
1. Check auth service implementation
2. Verify `is_email_authorized()` function is called

---

## 🚨 **Important Notes**

### **⚠️ Before Production:**
1. **Replace ALL placeholder emails** with real emails
2. **Test thoroughly** with real email addresses
3. **Document all authorized users**
4. **Set up backup admin access**

### **🔒 Security Best Practices:**
1. **Use work emails** when possible (more professional)
2. **Regularly review** authorized emails
3. **Remove inactive judges** from whitelist
4. **Keep admin list minimal** (only 1-2 people)
5. **Document who has access** and why

### **📱 For Mobile/WhatsApp Integration:**
- Email whitelist works with any email address
- Can use Gmail, Yahoo, Outlook, etc.
- No phone number restriction needed
- Focus on email-based authentication

---

## 🎯 **Next Steps**

1. **Update `update_email_whitelist.sql`** dengan email real
2. **Run SQL script** di Supabase
3. **Test dengan email real**
4. **Document final authorized list**
5. **Train admin** cara manage whitelist

**Sistem sekarang AMAN - hanya email yang diauthorize yang bisa akses!** 🔒
