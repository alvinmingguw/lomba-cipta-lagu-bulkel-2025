#!/usr/bin/env python3
"""
Debug OAuth Configuration
Check Google OAuth and Supabase configuration
"""

import streamlit as st
import os
from supabase import create_client, Client

def main():
    st.title("🔍 OAuth Debug Tool")
    
    # Check environment
    st.header("🌐 Environment Detection")
    
    # Check if Streamlit Cloud
    streamlit_cloud_indicators = [
        ('STREAMLIT_SHARING_MODE', 'STREAMLIT_SHARING_MODE' in os.environ),
        ('STREAMLIT_CLOUD', 'STREAMLIT_CLOUD' in os.environ),
        ('Has streamlit in env vars', any('streamlit' in str(v).lower() for v in os.environ.values())),
        ('Has supabase_url in secrets', hasattr(st, 'secrets') and 'supabase_url' in st.secrets)
    ]
    
    for indicator, status in streamlit_cloud_indicators:
        st.write(f"- {indicator}: {'✅' if status else '❌'}")
    
    # Show current URL detection
    st.header("🔗 URL Detection")
    
    try:
        # Try to get current URL
        import streamlit.components.v1 as components
        
        current_url = components.html("""
            <script>
                const url = window.location.href;
                const origin = window.location.origin;
                
                // Send to parent
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: {
                        href: url,
                        origin: origin,
                        protocol: window.location.protocol,
                        hostname: window.location.hostname,
                        port: window.location.port
                    }
                }, '*');
            </script>
            <div>Detecting URL...</div>
        """, height=50)
        
        if current_url:
            st.json(current_url)
        else:
            st.info("URL detection in progress...")
            
    except Exception as e:
        st.error(f"URL detection error: {e}")
    
    # Manual URL input for testing
    st.header("🧪 Manual OAuth Test")
    
    test_url = st.text_input(
        "Test URL:", 
        value="https://lomba-cipta-lagu-bulkel-2025.streamlit.app",
        help="Enter the URL to test OAuth with"
    )
    
    if st.button("🔐 Test Google OAuth"):
        try:
            # Initialize Supabase client
            supabase_url = st.secrets.get('supabase_url')
            supabase_key = st.secrets.get('supabase_anon_key')
            
            if not supabase_url or not supabase_key:
                st.error("❌ Supabase credentials not found in secrets")
                return
                
            client = create_client(supabase_url, supabase_key)
            
            st.info(f"🔍 Testing OAuth with redirect URL: {test_url}")
            
            # Try OAuth
            response = client.auth.sign_in_with_oauth({
                'provider': 'google',
                'options': {
                    'redirect_to': test_url
                }
            })
            
            if response.url:
                st.success("✅ OAuth URL generated successfully!")
                st.code(response.url)
                
                # Show the OAuth URL for manual testing
                st.markdown(f"[🔗 Click here to test OAuth]({response.url})")
                
                # Show what should be configured in Google Cloud Console
                st.header("📋 Google Cloud Console Configuration")
                
                st.subheader("Authorized JavaScript origins:")
                st.code(f"""
{supabase_url}
{test_url}
http://localhost:8501
http://localhost:8503
                """)
                
                st.subheader("Authorized redirect URIs:")
                st.code(f"{supabase_url}/auth/v1/callback")
                
            else:
                st.error("❌ Failed to generate OAuth URL")
                
        except Exception as e:
            st.error(f"❌ OAuth test failed: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    # Show current secrets (redacted)
    st.header("🔐 Secrets Check")
    
    if hasattr(st, 'secrets'):
        secrets_status = {
            'supabase_url': 'supabase_url' in st.secrets,
            'supabase_anon_key': 'supabase_anon_key' in st.secrets,
            'app_url': 'app_url' in st.secrets
        }
        
        for key, exists in secrets_status.items():
            status = "✅" if exists else "❌"
            st.write(f"- {key}: {status}")
            
        # Show redacted values
        if 'supabase_url' in st.secrets:
            url = st.secrets['supabase_url']
            redacted_url = url[:20] + "..." + url[-10:] if len(url) > 30 else url
            st.write(f"  - supabase_url: `{redacted_url}`")
            
    else:
        st.error("❌ No secrets found")

if __name__ == "__main__":
    main()
