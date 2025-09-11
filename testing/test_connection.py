#!/usr/bin/env python3
"""
Test script to verify database connection and data retrieval
Run this to debug connection issues
"""

import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_connection():
    """Test direct connection to Supabase without cache"""
    print("🔍 Testing direct Supabase connection...")
    
    try:
        # Load secrets
        if os.path.exists('.streamlit/secrets.toml'):
            print("✅ Found secrets.toml file")
        else:
            print("❌ No secrets.toml file found")
            return
        
        # Initialize Streamlit to load secrets
        import streamlit as st
        
        # Get credentials
        supabase_url = st.secrets.get("supabase_url")
        supabase_key = st.secrets.get("supabase_anon_key")
        
        print(f"📡 Supabase URL: {supabase_url}")
        print(f"🔑 Supabase Key: {supabase_key[:20]}..." if supabase_key else "❌ No key")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return
        
        # Create client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")
        
        # Test judges query
        print("\n🧑‍⚖️ Testing judges query...")
        response = supabase.table('judges').select('*').execute()
        print(f"📊 Judges response: {response}")
        print(f"📊 Judges data: {response.data}")
        
        if response.data:
            df = pd.DataFrame(response.data)
            print(f"📊 Judges DataFrame: {df.shape} rows, columns: {list(df.columns)}")
            print(f"📊 Judges data preview:\n{df}")
        else:
            print("❌ No judges data returned")
        
        # Test with is_active filter
        print("\n🔍 Testing judges with is_active filter...")
        response_active = supabase.table('judges').select('*').eq('is_active', True).execute()
        print(f"📊 Active judges response: {response_active}")
        print(f"📊 Active judges data: {response_active.data}")
        
        # Test other tables
        print("\n📋 Testing rubrics query...")
        response_rubrics = supabase.table('rubrics').select('*').eq('is_active', True).execute()
        print(f"📊 Rubrics data count: {len(response_rubrics.data) if response_rubrics.data else 0}")
        
        print("\n🎵 Testing songs query...")
        response_songs = supabase.table('songs').select('*').eq('is_active', True).execute()
        print(f"📊 Songs data count: {len(response_songs.data) if response_songs.data else 0}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_direct_connection()
