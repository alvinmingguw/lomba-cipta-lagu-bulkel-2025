"""
Test Magic Link Generation
"""

import streamlit as st
from services.auth_service import auth_service

def main():
    st.title("🔗 Test Magic Link")
    
    st.subheader("Generate Fresh Magic Link:")
    
    email = st.text_input("Email:", value="alvin.mingguw@gmail.com")
    
    if st.button("🚀 Send Magic Link"):
        if email:
            try:
                success = auth_service.send_magic_link(email)
                if success:
                    st.success("✅ Magic link sent! Check your email.")
                    st.info("📧 Click the link in your email to login.")
                else:
                    st.error("❌ Failed to send magic link")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.error("Please enter an email")
    
    st.markdown("---")
    st.subheader("📋 Instructions:")
    st.markdown("""
    1. **Enter your email** above
    2. **Click "Send Magic Link"**
    3. **Check your email** for the magic link
    4. **Click the link** in your email
    5. **You should be redirected** to the dashboard
    
    **Note:** Magic links expire in 1 hour.
    """)
    
    # Show current auth status
    st.markdown("---")
    st.subheader("🔐 Current Auth Status:")
    
    try:
        user = auth_service.client.auth.get_user()
        if user and user.user:
            st.success("✅ User is authenticated!")
            st.json({
                'id': user.user.id,
                'email': user.user.email,
                'provider': user.user.app_metadata.get('provider', 'unknown')
            })
        else:
            st.warning("⚠️ No authenticated user")
    except Exception as e:
        st.error(f"❌ Auth check failed: {e}")

if __name__ == "__main__":
    main()
