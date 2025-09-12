#!/usr/bin/env python3
"""
Comprehensive test script to verify database connection and data retrieval
Run this to debug connection issues

Usage:
  python3 testing/test_connection.py           # Test with streamlit secrets
  python3 testing/test_connection.py --simple  # Test without streamlit dependency
"""

import pandas as pd
from supabase import create_client, Client
import os
import sys
import argparse

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_simple_connection():
    """Test connection without streamlit dependency"""
    print("🔍 Testing Supabase connection (simple mode)...")

    try:
        # Try to load secrets from toml file
        try:
            import toml
            with open('.streamlit/secrets.toml', 'r') as f:
                secrets = toml.load(f)
            supabase_url = secrets.get("supabase_url")
            supabase_key = secrets.get("supabase_anon_key")
        except Exception as e:
            print(f"❌ Could not load secrets.toml: {e}")
            print("💡 Make sure .streamlit/secrets.toml exists with supabase_url and supabase_anon_key")
            return

        print(f"📡 Supabase URL: {supabase_url}")
        print(f"🔑 Supabase Key: {supabase_key[:20]}..." if supabase_key else "❌ No key")

        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return

        # Create client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")

        # Test basic connection
        test_tables(supabase)

    except Exception as e:
        print(f"❌ Error in simple connection test: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

def test_streamlit_connection():
    """Test connection using streamlit secrets"""
    print("🔍 Testing Supabase connection (streamlit mode)...")

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

        # Test tables
        test_tables(supabase)

    except Exception as e:
        print(f"❌ Error in streamlit connection test: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

def test_tables(supabase):
    """Test all main tables"""
    try:
        # Test judges query
        print("\n🧑‍⚖️ Testing judges query...")
        response = supabase.table('judges').select('*').execute()
        print(f"📊 Judges response: {response}")
        print(f"📊 Judges data: {response.data}")

        if response.data:
            df = pd.DataFrame(response.data)
            print(f"📊 Judges DataFrame: {df.shape} rows, columns: {list(df.columns)}")
            print(f"📊 Judges data preview:\n{df.head()}")
        else:
            print("❌ No judges data returned")

        # Test with is_active filter
        print("\n🔍 Testing judges with is_active filter...")
        response_active = supabase.table('judges').select('*').eq('is_active', True).execute()
        print(f"📊 Active judges data count: {len(response_active.data) if response_active.data else 0}")

        # Test other tables
        print("\n📋 Testing rubrics query...")
        response_rubrics = supabase.table('rubrics').select('*').eq('is_active', True).execute()
        print(f"📊 Rubrics data count: {len(response_rubrics.data) if response_rubrics.data else 0}")

        print("\n🎵 Testing songs query...")
        response_songs = supabase.table('songs').select('*').eq('is_active', True).execute()
        print(f"📊 Songs data count: {len(response_songs.data) if response_songs.data else 0}")

        print("\n⚙️ Testing configuration query...")
        response_config = supabase.table('configuration').select('*').execute()
        print(f"📊 Configuration data count: {len(response_config.data) if response_config.data else 0}")

        print("\n✅ All table tests completed!")

    except Exception as e:
        print(f"❌ Error testing tables: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Supabase database connection')
    parser.add_argument('--simple', action='store_true', help='Use simple mode without streamlit dependency')
    args = parser.parse_args()

    if args.simple:
        test_simple_connection()
    else:
        test_streamlit_connection()
