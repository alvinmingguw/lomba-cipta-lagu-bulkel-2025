"""
Quick Fix: Update auth_user_id for Alvin
"""

import streamlit as st
from services.database_service import db_service

def main():
    st.title("🔧 Fix Auth UUID")
    
    # The UUID from logs
    alvin_uuid = "3079a653-46fe-40d1-834b-05b1ec1ea03b"
    alvin_email = "alvin.mingguw@gmail.com"
    
    st.info(f"Linking UUID: {alvin_uuid}")
    st.info(f"Email: {alvin_email}")
    
    if st.button("🔗 Link Alvin's UUID"):
        try:
            # Update judges table with auth_user_id
            response = db_service.client.table('judges').update({
                'auth_user_id': alvin_uuid
            }).eq('email', alvin_email).execute()
            
            st.success("✅ UUID linked successfully!")
            st.json(response.data)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # Check current status
    st.subheader("Current Status:")
    
    judges_df = db_service.get_judges()
    alvin_row = judges_df[judges_df['email'] == alvin_email]
    
    if not alvin_row.empty:
        st.dataframe(alvin_row)
        
        current_uuid = alvin_row['auth_user_id'].iloc[0]
        if current_uuid == alvin_uuid:
            st.success("✅ UUID is correctly linked!")
        else:
            st.warning(f"⚠️ UUID mismatch: {current_uuid}")
    else:
        st.error("❌ Alvin not found in judges table")

if __name__ == "__main__":
    main()
