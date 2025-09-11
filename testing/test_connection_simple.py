#!/usr/bin/env python3
"""
Simple test script to verify database connection
Run this with: python3 test_connection_simple.py
"""

import pandas as pd
from supabase import create_client, Client
import toml

def test_connection():
    """Test connection without streamlit dependency"""
    print("🔍 Testing Supabase connection...")
    
    try:
        # Load secrets from toml file
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)
        
        supabase_url = secrets.get("supabase_url")
        supabase_key = secrets.get("supabase_anon_key")
        
        print(f"📡 URL: {supabase_url}")
        print(f"🔑 Key: {supabase_key[:20]}..." if supabase_key else "❌ No key")
        
        # Create client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Client created")
        
        # Test queries
        print("\n🧑‍⚖️ Testing judges...")
        judges = supabase.table('judges').select('*').execute()
        print(f"Judges count: {len(judges.data)}")
        if judges.data:
            print(f"First judge: {judges.data[0]}")
        
        print("\n🧑‍⚖️ Testing active judges...")
        active_judges = supabase.table('judges').select('*').eq('is_active', True).execute()
        print(f"Active judges count: {len(active_judges.data)}")
        if active_judges.data:
            print(f"Active judges: {[j['name'] for j in active_judges.data]}")
        
        print("\n📋 Testing rubrics...")
        rubrics = supabase.table('rubrics').select('*').eq('is_active', True).execute()
        print(f"Active rubrics count: {len(rubrics.data)}")
        
        print("\n🎵 Testing songs...")
        songs = supabase.table('songs').select('*').eq('is_active', True).execute()
        print(f"Active songs count: {len(songs.data)}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
