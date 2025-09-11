"""
Authentication Service for Lomba Cipta Lagu
Handles Google OAuth, Magic Links, Email/Password, and Admin Impersonation
"""

import streamlit as st
import pandas as pd
from supabase import create_client, Client
from typing import Optional, Dict, Any
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        """Initialize auth service with Supabase client"""
        self.client: Client = create_client(
            st.secrets["supabase_url"],
            st.secrets["supabase_anon_key"]
        )
    
    # ==================== SESSION MANAGEMENT ====================
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user with enhanced session persistence"""
        try:
            # First check browser storage for persistent session
            self._restore_session_from_browser()

            # Check if user is logged in via Supabase Auth
            user = self.client.auth.get_user()
            if user and user.user:
                # Get user profile with judge info using UUID
                profile = self._get_user_profile_by_uuid(user.user.id)
                if profile:
                    # Store in session for persistence with timestamp
                    from datetime import datetime
                    st.session_state.user_profile = profile
                    st.session_state.session_timestamp = datetime.now().isoformat()
                    # Store in browser for tab reload persistence
                    self._store_session_in_browser(profile)
                return profile

            # Check for admin impersonation session
            if "admin_session_token" in st.session_state:
                return self._get_impersonated_user()

            # Check for cached session with timestamp validation
            if "user_profile" in st.session_state and "session_timestamp" in st.session_state:
                cached_profile = st.session_state.user_profile
                session_timestamp = st.session_state.session_timestamp

                # Check if session is less than 24 hours old (extended for better UX)
                from datetime import datetime, timedelta
                if datetime.now() - datetime.fromisoformat(session_timestamp) < timedelta(hours=24):
                    return cached_profile
                else:
                    # Session expired, verify with auth server
                    try:
                        auth_user = self.client.auth.get_user()
                        if auth_user and auth_user.user:
                            # Refresh session timestamp
                            st.session_state.session_timestamp = datetime.now().isoformat()
                            return cached_profile
                        else:
                            # Clear invalid session
                            self._clear_session()
                    except:
                        # Clear invalid session
                        self._clear_session()

            return None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None

    def _store_session_in_browser(self, profile: Dict[str, Any]):
        """Store session in browser localStorage for tab reload persistence"""
        try:
            import json
            from datetime import datetime

            session_data = {
                'profile': profile,
                'timestamp': datetime.now().isoformat(),
                'app_version': '2.0'  # For cache invalidation if needed
            }

            # Use JavaScript to store in localStorage
            st.markdown(f"""
            <script>
                localStorage.setItem('lomba_session', '{json.dumps(session_data)}');
            </script>
            """, unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error storing session in browser: {e}")

    def _restore_session_from_browser(self):
        """Restore session from browser localStorage"""
        try:
            # Use JavaScript to get from localStorage
            st.markdown("""
            <script>
                const sessionData = localStorage.getItem('lomba_session');
                if (sessionData) {
                    // Send to Streamlit via query params (temporary method)
                    const data = JSON.parse(sessionData);
                    if (data.timestamp) {
                        const sessionTime = new Date(data.timestamp);
                        const now = new Date();
                        const hoursDiff = (now - sessionTime) / (1000 * 60 * 60);

                        // Only restore if less than 24 hours old
                        if (hoursDiff < 24 && data.profile) {
                            // Store in session state via hidden input
                            const hiddenInput = document.createElement('input');
                            hiddenInput.type = 'hidden';
                            hiddenInput.id = 'restored_session';
                            hiddenInput.value = JSON.stringify(data.profile);
                            document.body.appendChild(hiddenInput);
                        } else {
                            // Clear expired session
                            localStorage.removeItem('lomba_session');
                        }
                    }
                }
            </script>
            """, unsafe_allow_html=True)

            # Check if session was restored (this is a simplified approach)
            # In a real implementation, you'd use a more robust method

        except Exception as e:
            logger.error(f"Error restoring session from browser: {e}")

    def _clear_session(self):
        """Clear all session data"""
        try:
            # Clear Streamlit session
            if "user_profile" in st.session_state:
                del st.session_state.user_profile
            if "session_timestamp" in st.session_state:
                del st.session_state.session_timestamp

            # Clear browser storage
            st.markdown("""
            <script>
                localStorage.removeItem('lomba_session');
            </script>
            """, unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
    
    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile - simplified without auth_profiles table"""
        try:
            # Since auth_profiles table doesn't exist, return None
            # Authentication is handled directly through judges table by email
            logger.info(f"User profile lookup skipped - auth_profiles table not available")
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    def _get_user_profile_by_uuid(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile using UUID from judges table"""
        try:
            # First try to find judge by auth_user_id
            judge_response = self.client.table('judges').select('*').eq('auth_user_id', user_id).execute()

            if judge_response.data:
                judge = judge_response.data[0]
                role = judge.get('role', 'judge')

                return {
                    'id': user_id,
                    'judge_id': judge['id'],
                    'email': judge['email'],
                    'full_name': judge['name'],
                    'judge_name': judge['name'],
                    'role': role,
                    'provider': 'supabase',
                    # DUAL ROLE: Admin can also judge
                    'can_judge': True,  # All judges can judge
                    'can_admin': role == 'admin',  # Only admin can admin
                    'is_admin': role == 'admin'
                }

            # No fallback needed - judges table is the source of truth
            return None

        except Exception as e:
            logger.error(f"Error getting user profile by UUID: {e}")
            return None

    def _get_impersonated_user(self) -> Optional[Dict[str, Any]]:
        """Get impersonated user from session state (simplified approach)"""
        try:
            # Check if admin is impersonating using session state only
            impersonation_data = st.session_state.get("admin_impersonation")
            if not impersonation_data:
                return None

            # Check if session is still valid (24 hours)
            session_start = impersonation_data.get('session_start')
            if session_start:
                from datetime import datetime, timedelta
                start_time = datetime.fromisoformat(session_start)
                if datetime.now() - start_time > timedelta(hours=24):
                    # Session expired, clear it
                    del st.session_state.admin_impersonation
                    return None

            # Get judge data from database
            judge_id = impersonation_data.get('judge_id')
            if judge_id:
                response = self.client.table('judges').select('*').eq('id', judge_id).single().execute()
                if response.data:
                    return {
                        'id': f"admin_impersonation_{judge_id}",
                        'judge_id': judge_id,
                        'judges': response.data,
                        'role': 'judge',  # Impersonated as judge
                        'is_impersonated': True,
                        'admin_user': impersonation_data.get('admin_user')
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting impersonated user: {e}")
            return None
    
    # ==================== EMAIL AUTHORIZATION ====================

    def is_email_authorized(self, email: str) -> tuple[bool, str]:
        """Check if email exists in judges table"""
        try:
            response = self.client.table('judges').select('*').eq(
                'email', email.lower()
            ).eq('is_active', True).execute()

            if response.data:
                judge = response.data[0]
                return True, judge.get('role', 'judge')
            else:
                return False, None
        except Exception as e:
            logger.error(f"Error checking email authorization: {e}")
            return False, None

    def add_authorized_judge(self, name: str, email: str, role: str = 'judge') -> bool:
        """Add new judge with email (admin only)"""
        try:
            # Check if email already exists
            existing = self.client.table('judges').select('*').eq('email', email.lower()).execute()
            if existing.data:
                logger.warning(f"Judge with email {email} already exists")
                return False

            response = self.client.table('judges').insert({
                'name': name,
                'email': email.lower(),
                'role': role,
                'is_active': True
            }).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f"Error adding authorized judge: {e}")
            return False

    def remove_judge_authorization(self, email: str) -> bool:
        """Remove judge authorization by setting email to null (admin only)"""
        try:
            response = self.client.table('judges').update({
                'email': None,
                'is_active': False
            }).eq('email', email.lower()).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f"Error removing judge authorization: {e}")
            return False

    def update_judge_email(self, judge_id: int, email: str) -> bool:
        """Update judge email (admin only)"""
        try:
            response = self.client.table('judges').update({
                'email': email.lower(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', judge_id).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating judge email: {e}")
            return False

    def update_judge_name(self, judge_id: int, name: str) -> bool:
        """Update judge name (admin only)"""
        try:
            response = self.client.table('judges').update({
                'name': name,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', judge_id).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating judge name: {e}")
            return False

    def update_judge_role(self, judge_id: int, role: str) -> bool:
        """Update judge role (admin only)"""
        try:
            response = self.client.table('judges').update({
                'role': role,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', judge_id).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating judge role: {e}")
            return False

    def update_judge_status(self, judge_id: int, is_active: bool) -> bool:
        """Update judge status (admin only)"""
        try:
            response = self.client.table('judges').update({
                'is_active': is_active,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', judge_id).execute()

            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating judge status: {e}")
            return False

    def delete_judge(self, judge_id: int) -> bool:
        """Delete judge (admin only)"""
        try:
            response = self.client.table('judges').delete().eq('id', judge_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error deleting judge: {e}")
            return False

    # ==================== AUTHENTICATION METHODS ====================

    def login_with_google(self) -> bool:
        """Login with Google OAuth"""
        try:
            # Get current URL dynamically
            redirect_url = self._get_current_url()

            # Debug: Log the redirect URL
            logger.info(f"🔍 Google OAuth redirect URL: {redirect_url}")

            # For Streamlit Cloud, force HTTPS
            if 'streamlit.app' in redirect_url and redirect_url.startswith('http://'):
                redirect_url = redirect_url.replace('http://', 'https://')
                logger.info(f"🔧 Fixed to HTTPS: {redirect_url}")

            # Redirect to Google OAuth
            response = self.client.auth.sign_in_with_oauth({
                'provider': 'google',
                'options': {
                    'redirect_to': redirect_url
                }
            })

            if response.url:
                # Store the OAuth URL in session state for UI to use
                st.session_state['google_oauth_url'] = response.url
                logger.info(f"✅ Google OAuth URL generated: {response.url[:50]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Google login error: {e}")
            st.error(f"Google login failed: {e}")
            return False

    def handle_oauth_callback(self, code: str) -> bool:
        """Handle OAuth callback with authorization code"""
        try:
            # Exchange code for session with proper parameters
            logger.info(f"Exchanging code for session: {code[:10]}...")

            # Use the correct method signature
            response = self.client.auth.exchange_code_for_session({
                'auth_code': code
            })

            # Debug response structure
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response: {response}")

            # Handle different response formats
            user = None
            if hasattr(response, 'user') and response.user:
                user = response.user
                logger.info(f"User from response.user: {user}")
            elif hasattr(response, 'data') and response.data and hasattr(response.data, 'user'):
                user = response.data.user
                logger.info(f"User from response.data.user: {user}")
            elif hasattr(response, 'session') and response.session and hasattr(response.session, 'user'):
                user = response.session.user
                logger.info(f"User from response.session.user: {user}")
            else:
                logger.error(f"No user found in response: {response}")
                return False

            if user:
                user_email = getattr(user, 'email', None)

                # Check if email is authorized BEFORE creating profile
                if user_email:
                    is_authorized, role = self.is_email_authorized(user_email)
                    if not is_authorized:
                        logger.warning(f"❌ Unauthorized login attempt: {user_email}")
                        # Sign out the user immediately
                        try:
                            self.client.auth.sign_out()
                        except:
                            pass

                        # Show error message and redirect
                        import streamlit as st
                        st.error(f"❌ Email {user_email} tidak memiliki akses ke sistem ini.")
                        st.error("🔒 Silahkan hubungi administrator untuk mendapatkan akses sebagai juri.")
                        st.info("🔄 Anda akan diarahkan kembali ke halaman login...")

                        # Auto redirect after 3 seconds
                        st.markdown("""
                        <script>
                        setTimeout(function() {
                            window.location.href = window.location.origin;
                        }, 3000);
                        </script>
                        """, unsafe_allow_html=True)

                        return False

                # If authorized, proceed with profile creation
                self._create_or_update_profile(user)
                logger.info(f"✅ OAuth callback successful for authorized user: {user_email}")
                return True
            return False
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Try alternative method
            try:
                logger.info("Trying alternative auth method...")
                # Just check if user is now authenticated
                current_user = self.client.auth.get_user()
                if current_user and current_user.user:
                    user_email = getattr(current_user.user, 'email', None)

                    # Check authorization for alternative method too
                    if user_email:
                        is_authorized, role = self.is_email_authorized(user_email)
                        if not is_authorized:
                            logger.warning(f"❌ Unauthorized alternative login attempt: {user_email}")
                            try:
                                self.client.auth.sign_out()
                            except:
                                pass
                            return False

                    self._create_or_update_profile(current_user.user)
                    logger.info("✅ Alternative auth method successful")
                    return True
            except Exception as e2:
                logger.error(f"Alternative auth method failed: {e2}")

            return False

    def send_magic_link(self, email: str) -> bool:
        """Send magic link to email"""
        try:
            # Check if email is authorized
            is_authorized, role = self.is_email_authorized(email)
            if not is_authorized:
                st.error(f"❌ Email {email} is not authorized to access this system. Please contact administrator.")
                return False

            # Get current URL for redirect
            current_url = self._get_current_url()

            response = self.client.auth.sign_in_with_otp({
                'email': email,
                'options': {
                    'email_redirect_to': current_url
                }
            })

            if response:
                st.success(f"Magic link sent to {email}! Check your email.")
                return True
            return False
        except Exception as e:
            logger.error(f"Magic link error: {e}")
            st.error(f"Failed to send magic link: {e}")
            return False
    
    def login_with_email(self, email: str, password: str) -> bool:
        """Login with email and password"""
        try:
            # Check if email is authorized
            is_authorized, role = self.is_email_authorized(email)
            if not is_authorized:
                st.error(f"❌ Email {email} is not authorized to access this system. Please contact administrator.")
                return False

            response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })

            if response.user:
                st.success("Login successful!")
                st.rerun()
                return True
            return False
        except Exception as e:
            logger.error(f"Email login error: {e}")
            st.error(f"Login failed: {e}")
            return False
    
    def signup_with_email(self, email: str, password: str, full_name: str) -> bool:
        """Sign up with email and password"""
        try:
            # Check if email is authorized
            is_authorized, role = self.is_email_authorized(email)
            if not is_authorized:
                st.error(f"❌ Email {email} is not authorized to access this system. Please contact administrator to get access.")
                return False

            response = self.client.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'full_name': full_name,
                        'role': role  # Set role from whitelist
                    }
                }
            })

            if response.user:
                st.success("Account created! Please check your email for verification.")
                return True
            return False
        except Exception as e:
            logger.error(f"Signup error: {e}")
            st.error(f"Signup failed: {e}")
            return False
    
    def logout(self):
        """Logout current user"""
        try:
            # Clear admin session if exists
            if "admin_session_token" in st.session_state:
                self._end_admin_session()
            
            # Logout from Supabase Auth
            self.client.auth.sign_out()
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("Logged out successfully!")
            st.rerun()
        except Exception as e:
            logger.error(f"Logout error: {e}")
            st.error(f"Logout failed: {e}")
    
    # ==================== ADMIN IMPERSONATION ====================
    
    def start_admin_session(self, admin_user: Dict, target_judge_id: int) -> bool:
        """Start admin impersonation session (simplified approach)"""
        try:
            if admin_user.get('role') != 'admin':
                st.error("Only admins can impersonate other users")
                return False

            # Verify target judge exists
            response = self.client.table('judges').select('*').eq('id', target_judge_id).single().execute()
            if not response.data:
                st.error("Target judge not found")
                return False

            # Store impersonation data in session state only
            st.session_state.admin_impersonation = {
                'judge_id': target_judge_id,
                'admin_user': admin_user,
                'session_start': datetime.now().isoformat()
            }

            judge_name = response.data.get('name', f'Judge {target_judge_id}')
            st.success(f"Now impersonating: {judge_name}")
            st.rerun()
            return True

        except Exception as e:
            logger.error(f"Admin session error: {e}")
            st.error(f"Failed to start admin session: {e}")
            return False

    def _end_admin_session(self):
        """End admin impersonation session"""
        try:
            # Simply clear session state
            if "admin_impersonation" in st.session_state:
                del st.session_state.admin_impersonation
        except Exception as e:
            logger.error(f"Error ending admin session: {e}")

    def end_impersonation(self):
        """End admin impersonation and return to admin"""
        try:
            self._end_admin_session()
            st.success("Returned to admin account")
            st.rerun()
        except Exception as e:
            logger.error(f"Error ending impersonation: {e}")
            st.error(f"Failed to end impersonation: {e}")
    
    # ==================== UTILITY METHODS ====================
    
    def get_all_judges(self) -> pd.DataFrame:
        """Get all judges for admin dropdown"""
        try:
            response = self.client.table('judges').select('*').eq('is_active', True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error getting judges: {e}")
            return pd.DataFrame()
    
    def is_admin(self, user: Dict) -> bool:
        """Check if user is admin"""
        return user and user.get('role') == 'admin'
    
    def is_impersonating(self) -> bool:
        """Check if currently impersonating"""
        return "admin_impersonation" in st.session_state

    def _create_or_update_profile(self, user) -> None:
        """Create or update user profile in auth_profiles table"""
        try:
            # Debug user object
            logger.info(f"Creating profile for user: {user}")
            logger.info(f"User type: {type(user)}")

            # Handle different user object formats
            user_id = getattr(user, 'id', None)
            user_email = getattr(user, 'email', None)

            logger.info(f"Extracted user_id: {user_id}, user_email: {user_email}")

            if not user_id or not user_email:
                logger.error(f"Invalid user object: {user}")
                return

            # Skip auth_profiles table operations (table doesn't exist)
            logger.info("Skipping auth_profiles operations - table not available")

            # ALWAYS try to link with judge record by email (this is critical)
            self._link_judge_by_email(user_email, user_id)

        except Exception as e:
            logger.error(f"Error in profile creation process: {e}")

            # Even if profile creation fails completely, still try auto-linking
            try:
                user_email = getattr(user, 'email', None)
                user_id = getattr(user, 'id', None)
                if user_email and user_id:
                    logger.info("Attempting emergency auto-linking...")
                    self._link_judge_by_email(user_email, user_id)
            except Exception as link_error:
                logger.error(f"Emergency auto-linking also failed: {link_error}")

    def _link_judge_by_email(self, email: str, user_id: str) -> bool:
        """Link user with judge record by email and UUID - AUTOMATIC"""
        try:
            logger.info(f"🔗 Attempting auto-link for email: {email} with user_id: {user_id}")

            # Find judge by email (case insensitive)
            judge_response = self.client.table('judges').select('*').eq('email', email.lower()).execute()

            if judge_response.data:
                judge = judge_response.data[0]

                # Check if already linked
                if judge.get('auth_user_id') == user_id:
                    logger.info(f"✅ Judge {judge['name']} already linked with user {user_id}")
                    return True

                # AUTOMATIC: Update judge record with auth_user_id
                update_response = self.client.table('judges').update({
                    'auth_user_id': user_id,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', judge['id']).execute()

                if update_response.data:
                    logger.info(f"✅ AUTO-LINKED: Judge {judge['name']} (ID: {judge['id']}) with auth user {user_id}")

                    # Skip auth_profiles update (table doesn't exist)
                    logger.info("✅ Judge linked successfully - auth_profiles update skipped")

                    return True
                else:
                    logger.error(f"❌ Failed to update judge record for {email}")
                    return False

            else:
                logger.warning(f"❌ No judge found with email {email} - user cannot access system")
                return False

        except Exception as e:
            logger.error(f"❌ Auto-linking failed for {email}: {e}")
            return False

        except Exception as e:
            logger.error(f"Error linking judge by email: {e}")

    def _get_current_url(self) -> str:
        """Get current URL with dynamic port detection"""

        # Method 0: Check if we're on Streamlit Cloud first
        try:
            import os
            # Multiple ways to detect Streamlit Cloud
            streamlit_cloud_indicators = [
                'STREAMLIT_SHARING_MODE' in os.environ,
                'STREAMLIT_CLOUD' in os.environ,
                any('streamlit' in str(v).lower() for v in os.environ.values()),
                hasattr(st, 'secrets') and 'supabase_url' in st.secrets and 'localhost' not in st.secrets.get('supabase_url', '')
            ]

            if any(streamlit_cloud_indicators):
                logger.info("🌐 Detected Streamlit Cloud deployment")
                return 'https://lomba-cipta-lagu-bulkel-2025.streamlit.app'
        except Exception as e:
            logger.warning(f"Error detecting Streamlit Cloud: {e}")

        try:
            # Method 1: Try to get from Streamlit config (local development)
            import streamlit as st
            from streamlit.web.server import server

            # Get server config
            config = st.get_option("server.port")
            if config:
                return f"http://localhost:{config}"
        except:
            pass

        try:
            # Method 2: Try to get from browser URL (if available)
            import streamlit.components.v1 as components

            # Use JavaScript to get current URL
            current_url = components.html("""
                <script>
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: window.location.origin
                    }, '*');
                </script>
            """, height=0)

            if current_url and current_url.startswith('http'):
                return current_url
        except:
            pass

        try:
            # Method 3: Check environment variables
            import os
            port = os.environ.get('STREAMLIT_SERVER_PORT')
            if port:
                return f"http://localhost:{port}"
        except:
            pass

        try:
            # Method 4: Parse from command line args
            import sys
            for i, arg in enumerate(sys.argv):
                if arg == '--server.port' and i + 1 < len(sys.argv):
                    port = sys.argv[i + 1]
                    return f"http://localhost:{port}"
                elif arg.startswith('--server.port='):
                    port = arg.split('=')[1]
                    return f"http://localhost:{port}"
        except:
            pass

        # Method 5: Auto-detect Streamlit Cloud URL
        try:
            import os
            # Check if running on Streamlit Cloud
            if 'STREAMLIT_SHARING_MODE' in os.environ or 'STREAMLIT_CLOUD' in os.environ:
                # Try to get from hostname
                hostname = os.environ.get('HOSTNAME', '')
                if hostname and 'streamlit' in hostname:
                    return f"https://{hostname}"

                # Fallback: construct from app name
                app_name = os.environ.get('STREAMLIT_APP_NAME', 'lomba-cipta-lagu-bulkel-2025')
                return f"https://{app_name}.streamlit.app"
        except:
            pass

        # Final fallback: check if we're on Streamlit Cloud by checking secrets
        try:
            # If we have supabase_url in secrets, we're likely deployed
            if hasattr(st, 'secrets') and 'supabase_url' in st.secrets:
                # Check if localhost is in supabase_url (local dev) or not (deployed)
                supabase_url = st.secrets.get('supabase_url', '')
                if 'localhost' not in supabase_url and supabase_url:
                    # We're deployed, use the known Streamlit Cloud URL
                    return 'https://lomba-cipta-lagu-bulkel-2025.streamlit.app'
        except:
            pass

        # Ultimate fallback to secrets or default
        return st.secrets.get('app_url', 'http://localhost:8501')

# Global instance
auth_service = AuthService()
