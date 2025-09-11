"""
Simple Login UI - Minimal Version for Testing
"""

import streamlit as st
from services.auth_service import auth_service
import re

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def render_login_page():
    """Render simple login page"""
    
    # Minimal CSS - just hide header
    st.markdown("""
    <style>
    .stApp > header {display: none;}
    .stDeployButton {display: none;}
    
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .login-title {
        text-align: center;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    
    .login-subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="login-title">GKI Perumnas</h1>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Lomba Cipta Lagu Bulkel 2025</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "google"
    
    # Simple tabs
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Google Login", width=True):
            st.session_state.active_tab = "google"
            st.rerun()
    
    with col2:
        if st.button("📧 Email Login", width=True):
            st.session_state.active_tab = "email"
            st.rerun()
    
    st.markdown("---")
    
    # Tab content
    if st.session_state.active_tab == "google":
        st.markdown("### Google Login")
        if st.button("🔐 Masuk dengan Google", width=True):
            with st.spinner("Redirecting to Google..."):
                success = auth_service.login_with_google()
                if success:
                    st.success("🔗 Redirecting to Google login...")
                else:
                    st.error("❌ Failed to initiate Google login")
    
    elif st.session_state.active_tab == "email":
        st.markdown("### Email Login")
        
        # Email input
        email = st.text_input("Email", placeholder="nama@email.com")
        
        # Password input
        password = st.text_input("Password", type="password", placeholder="Password")
        
        # Login button
        if st.button("📧 Masuk dengan Email", width=True):
            if email and password:
                if validate_email(email):
                    with st.spinner("Logging in..."):
                        auth_service.login_with_email(email, password)
                else:
                    st.error("Please enter a valid email address")
            else:
                st.error("Please fill in all fields")
        
        # Forgot password
        if st.button("🔑 Lupa Password?", width=True):
            if email:
                if validate_email(email):
                    with st.spinner("Mengirim reset password..."):
                        try:
                            auth_service.reset_password(email)
                            st.success("Link reset password telah dikirim!")
                        except Exception:
                            st.error("Gagal mengirim reset password. Hubungi admin.")
                else:
                    st.error("Masukkan email yang valid terlebih dahulu")
            else:
                st.error("Masukkan email terlebih dahulu")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.8rem;">
        🎼 Sistem Penilaian Juri | 🔒 Secure Login<br>
        Akun juri dikelola oleh admin
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
