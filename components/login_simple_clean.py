"""
Simple Login UI - Clean Version
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
        if st.button("Google Login", width=True):
            st.session_state.active_tab = "google"
            st.rerun()
    
    with col2:
        if st.button("Email Login", width=True):
            st.session_state.active_tab = "email"
            st.rerun()
    
    st.markdown("---")
    
    # Tab content
    if st.session_state.active_tab == "google":
        st.markdown("### Google Login")
        
        # Simple Google login button
        if st.button("Login with Google", width=True, type="primary"):
            with st.spinner("Preparing Google login..."):
                try:
                    success = auth_service.login_with_google()
                    if success and 'google_oauth_url' in st.session_state:
                        st.success("Redirecting to Google...")
                        st.markdown(f"""
                        <script>
                        window.open('{st.session_state['google_oauth_url']}', '_self');
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Failed to initiate Google login")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif st.session_state.active_tab == "email":
        st.markdown("### Email Login")
        
        # Email input
        email = st.text_input("Email", placeholder="nama@email.com")
        
        # Password input
        password = st.text_input("Password", type="password", placeholder="Password")
        
        # Login button
        if st.button("Login with Email", width=True, type="primary"):
            if email and password:
                if validate_email(email):
                    with st.spinner("Logging in..."):
                        auth_service.login_with_email(email, password)
                else:
                    st.error("Please enter a valid email address")
            else:
                st.error("Please fill in all fields")
        
        # Forgot password
        if st.button("Forgot Password?", width=True):
            if email:
                if validate_email(email):
                    with st.spinner("Sending reset email..."):
                        try:
                            auth_service.reset_password(email)
                            st.success("Password reset email sent! Check your inbox.")
                        except Exception as e:
                            st.error(f"Error sending reset email: {str(e)}")
                else:
                    st.error("Please enter a valid email address")
            else:
                st.error("Please enter your email address first")
    
    # Close container
    st.markdown('</div>', unsafe_allow_html=True)
