"""
Test Dashboard - Bypass authentication for testing
"""

import streamlit as st
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import db_service
from services.cache_service import cache_service
from services.auth_service import auth_service

def mock_user():
    """Create mock user for testing"""
    return {
        'id': '1',
        'email': 'alvin.mingguw@gmail.com',
        'full_name': 'Alvin Giovanni Mingguw',
        'role': 'admin',
        'judge_id': 1,
        'provider': 'test'
    }

def main():
    st.title("🧪 Test Dashboard")
    st.markdown("Testing dashboard without authentication")
    
    # Mock authentication
    st.session_state['mock_user'] = mock_user()
    
    # Test user selection
    st.subheader("👤 Test as:")
    
    judges_df = db_service.get_judges()
    
    if not judges_df.empty:
        judge_options = ["Admin"] + judges_df['name'].tolist()
        selected_role = st.selectbox("Select role:", judge_options)
        
        if selected_role == "Admin":
            test_user = mock_user()
        else:
            judge_row = judges_df[judges_df['name'] == selected_role].iloc[0]
            test_user = {
                'id': str(judge_row['id']),
                'email': judge_row['email'],
                'full_name': judge_row['name'],
                'role': judge_row.get('role', 'judge'),
                'judge_id': judge_row['id'],
                'provider': 'test'
            }
        
        st.json(test_user)
        
        if st.button("🚀 Test Dashboard"):
            # Import and run main app components
            from app_new import render_main_app, render_admin_panel
            
            if test_user['role'] == 'admin':
                st.markdown("---")
                st.header("👨‍💼 Admin Panel")
                render_admin_panel(test_user)
            else:
                st.markdown("---")
                st.header("🎵 Judge Dashboard")
                render_main_app(test_user)
    
    # Database status
    st.markdown("---")
    st.subheader("📊 Database Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        judges_count = len(db_service.get_judges())
        st.metric("Judges", judges_count)
    
    with col2:
        songs_count = len(db_service.get_songs())
        st.metric("Songs", songs_count)
    
    with col3:
        rubrics_count = len(db_service.get_rubrics())
        st.metric("Rubrics", rubrics_count)
    
    # Show data
    if st.checkbox("Show Judges Data"):
        st.dataframe(db_service.get_judges())
    
    if st.checkbox("Show Songs Data"):
        st.dataframe(db_service.get_songs())
    
    if st.checkbox("Show Rubrics Data"):
        st.dataframe(db_service.get_rubrics())

if __name__ == "__main__":
    main()
