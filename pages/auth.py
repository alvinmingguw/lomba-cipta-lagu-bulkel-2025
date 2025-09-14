import streamlit as st
import sys
import os

# Add the parent directory to the path so we can import from services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import auth_service

st.set_page_config(
    page_title="Login - Lomba Cipta Lagu Bulkel 2025",
    page_icon="🔐",
    layout="wide"
)

def render_auth_sidebar():
    """Render auth page sidebar with navigation"""
    with st.sidebar:
        # Custom CSS for better button styling
        st.markdown("""
        <style>
        .nav-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .nav-header {
            font-size: 1.4rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 1rem;
            text-align: center;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Navigation Section
        st.markdown("""
        <div class="nav-section">
            <div class="nav-header">🧭 Navigation</div>
        </div>
        """, unsafe_allow_html=True)

        # Home button
        if st.button("🏠 Home", type="secondary", width='stretch', key="nav_home"):
            st.switch_page("app.py")

        # Info lomba button
        if st.button("📋 Info Lomba", type="secondary", width='stretch', key="nav_info"):
            st.switch_page("app.py")

        # Certificate download button
        if st.button("🏆 Download Sertifikat", type="secondary", width='stretch', key="nav_cert"):
            st.switch_page("app.py")

        # Login button (highlighted since we're on login page)
        if st.button("🔐 Login", type="primary", width='stretch', key="nav_login"):
            # Already on login page
            st.rerun()

def main():
    """Main authentication page"""

    # Add "Kembali ke Beranda" button at top left
    st.markdown("""
    <style>
    .back-to-home {
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 999;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .back-to-home a {
        color: #495057;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .back-to-home a:hover {
        color: #007bff;
    }
    </style>
    <div class="back-to-home">
        <a href="/" target="_self">← Kembali ke Beranda</a>
    </div>
    """, unsafe_allow_html=True)

    # Hide Streamlit's built-in navigation (more specific)
    st.markdown("""
    <style>
    /* Hide only the built-in page navigation, not the entire sidebar */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Hide navigation links specifically */
    .css-1d391kg {
        display: none !important;
    }

    /* Hide the page selector */
    .css-17lntkn {
        display: none !important;
    }

    /* More specific selectors for page navigation */
    section[data-testid="stSidebar"] nav {
        display: none !important;
    }

    /* Hide page navigation list */
    section[data-testid="stSidebar"] ul[role="list"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Add sidebar navigation
    render_auth_sidebar()

    # Custom CSS for beautiful login page
    st.markdown("""
    <style>
    .login-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
        color: #333;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        border: 1px solid #dee2e6;
    }
    .login-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #495057;
    }
    .login-subtitle {
        font-size: 1.2rem;
        margin-bottom: 2rem;
        color: #6c757d;
        line-height: 1.4;
    }
    .success-container {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        padding: 3rem;
        border-radius: 20px;
        margin: 2rem 0;
        text-align: center;
        color: white;
        box-shadow: 0 15px 40px rgba(0,0,0,0.3);
    }
    .info-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        border-left: 6px solid #667eea;
    }
    .info-card h3 {
        font-size: 1.5rem;
        color: #333;
        margin-bottom: 1rem;
    }
    .info-card ul li {
        font-size: 1.1rem;
        margin: 0.8rem 0;
        color: #555;
    }
    .stButton > button {
        font-size: 1.3rem !important;
        padding: 1rem 2rem !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        height: auto !important;
        min-height: 60px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Handle OAuth callback first (before checking authentication)
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        st.info("🔐 Processing Google login...")

        try:
            # Exchange code for session
            success = auth_service.handle_oauth_callback(code)

            if success:
                # Check if user is authorized
                current_user = auth_service.get_current_user()

                if current_user and current_user.get('judge_id'):
                    st.success("✅ Google login successful!")
                    st.info("🔄 Redirecting to main app...")

                    # Clear URL parameters and session state
                    st.query_params.clear()
                    if 'google_oauth_url' in st.session_state:
                        del st.session_state['google_oauth_url']

                    # Auto redirect to dashboard using URL parameter
                    st.markdown("""
                    <meta http-equiv="refresh" content="2; url=/?dashboard=true">
                    <script>
                        // Clear any oauth processing flags
                        sessionStorage.removeItem('oauth_processing');
                        localStorage.removeItem('oauth_processing');

                        // Immediate redirect to dashboard
                        setTimeout(function() {
                            window.location.replace(window.location.origin + '/?dashboard=true');
                        }, 500);

                        // Fallback redirect if first attempt fails
                        setTimeout(function() {
                            if (window.location.search.includes('code=')) {
                                window.location.href = window.location.origin + '/?dashboard=true';
                            }
                        }, 2000);
                    </script>
                    """, unsafe_allow_html=True)

                    # Provide fallback button if JavaScript redirect fails
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("📊 Lanjutkan ke Dashboard", type="primary", key="manual_redirect_auth"):
                            st.session_state.show_dashboard = True
                            st.switch_page("app.py")

                    # Stop execution
                    st.stop()
                else:
                    # User authenticated but not authorized
                    st.error("❌ Akses ditolak: Email Anda tidak terdaftar sebagai juri")
                    st.info("💡 Silahkan hubungi admin untuk mendapatkan akses ke sistem")

                    # Logout unauthorized user and clear session
                    auth_service.logout()
                    st.query_params.clear()
                    if 'google_oauth_url' in st.session_state:
                        del st.session_state['google_oauth_url']
            else:
                st.error("❌ Google login failed")
                st.query_params.clear()
                if 'google_oauth_url' in st.session_state:
                    del st.session_state['google_oauth_url']

        except Exception as e:
            st.error(f"❌ Google login failed: {str(e)}")
            st.query_params.clear()
            if 'google_oauth_url' in st.session_state:
                del st.session_state['google_oauth_url']

    # Check if already authenticated
    current_user = auth_service.get_current_user()
    if current_user:
        st.markdown("""
        <div class="success-container">
            <div class="login-title">✅ Login Berhasil!</div>
            <div class="login-subtitle">Selamat datang kembali, {}</div>
        </div>
        """.format(current_user.get('name', 'User')), unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🏠 Kembali ke Beranda", type="primary", width='stretch'):
                st.switch_page("app.py")
        return

    # Login page header
    st.markdown("""
    <div class="login-container">
        <div class="login-title">🎵 Selamat Datang, Juri!</div>
        <div class="login-subtitle">Mari masuk untuk mulai menilai karya lagu peserta</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have OAuth URL ready
    if 'google_oauth_url' in st.session_state:
        oauth_url = st.session_state['google_oauth_url']

        # st.info("🔗 Klik tombol di bawah untuk login dengan Google:")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.link_button(
                "🚀 Login dengan Google",
                oauth_url,
                use_container_width=True
            )

            # st.markdown("---")
            # if st.button("🔄 Buat Link Baru", type="secondary", use_container_width=True):
            #     del st.session_state['google_oauth_url']
            #     st.rerun()
    else:
        # Login button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔐 Login dengan Google", type="primary", width='stretch'):
                with st.spinner("Menyiapkan login Google..."):
                    try:
                        success = auth_service.login_with_google()
                        if success and 'google_oauth_url' in st.session_state:
                            oauth_url = st.session_state['google_oauth_url']
                            st.success("✅ Google OAuth URL generated!")
                            st.info("🔗 Click button below to continue:")

                            # Simple link button for new tab
                            st.link_button(
                                "🚀 Lanjutkan ke Google",
                                oauth_url,
                                use_container_width=True
                            )

                            # Debug: Show the URL for testing
                            # with st.expander("🔍 Debug Info (klik untuk lihat URL)"):
                            #     st.code(oauth_url)

                            st.info("💡 Setelah login berhasil, kembali ke tab ini dan refresh halaman.")
                        else:
                            st.error("❌ Gagal membuat link login Google. Silakan coba lagi.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # Information card
    st.markdown("""
    <div class="info-card">
        <h3>ℹ️ Informasi Login</h3>
        <ul style="text-align: left; margin: 1rem 0;">
            <li>Hanya juri yang terdaftar yang dapat mengakses sistem penilaian</li>
            <li>Gunakan akun Google yang sama dengan yang didaftarkan sebagai juri</li>
            <li>Jika mengalami masalah login, hubungi administrator</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Back to landing page
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Kembali ke Beranda", type="secondary", width='stretch'):
            st.switch_page("app.py")

if __name__ == "__main__":
    main()
