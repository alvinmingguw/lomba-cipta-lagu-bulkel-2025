# -*- coding: utf-8 -*-
"""
Database Service - Handles all database operations with Supabase
Replaces Google Sheets functionality with optimized database queries
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """Centralized database service for all data operations"""
    
    def __init__(self):
        """Initialize database connection"""
        self.supabase_url = st.secrets.get("supabase_url")
        self.supabase_key = st.secrets.get("supabase_anon_key")
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of Supabase client"""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                st.error("Database connection failed. Please check configuration.")
                return None
        return self._client
    
    # ==================== JUDGES ====================
    
    @st.cache_data(ttl=3600)
    def get_judges(_self) -> pd.DataFrame:
        """Get all active judges"""
        try:
            response = _self.client.table('judges').select('*').eq('is_active', True).execute()
            logger.info(f"Judges query response: {response.data}")
            df = pd.DataFrame(response.data)
            logger.info(f"Judges DataFrame shape: {df.shape}, columns: {list(df.columns) if not df.empty else 'No columns'}")
            return df
        except Exception as e:
            logger.error(f"Error fetching judges: {e}")
            return pd.DataFrame()
    
    def add_judge(self, name: str, email: str = None) -> bool:
        """Add a new judge"""
        try:
            data = {"name": name, "email": email, "active": True}
            response = self.client.table('judges').insert(data).execute()
            st.cache_data.clear()  # Clear cache
            return True
        except Exception as e:
            logger.error(f"Error adding judge: {e}")
            return False

    def update_judge_email(self, judge_id: int, email: str) -> bool:
        """Update judge email"""
        try:
            data = {"email": email, "updated_at": datetime.now().isoformat()}
            response = self.client.table('judges').update(data).eq('id', judge_id).execute()
            st.cache_data.clear()  # Clear cache
            return True
        except Exception as e:
            logger.error(f"Error updating judge email: {e}")
            return False

    def update_judge_role(self, judge_id: int, role: str) -> bool:
        """Update judge role"""
        try:
            data = {"role": role, "updated_at": datetime.now().isoformat()}
            response = self.client.table('judges').update(data).eq('id', judge_id).execute()
            st.cache_data.clear()  # Clear cache
            return True
        except Exception as e:
            logger.error(f"Error updating judge role: {e}")
            return False

    # Email whitelist removed - using judges table for authorization
    
    # ==================== SONGS ====================
    
    @st.cache_data(ttl=1800)  # 30 minutes
    def get_songs(_self) -> pd.DataFrame:
        """Get all active songs with file metadata"""
        try:
            # Simplified query without foreign key joins for now
            response = _self.client.table('songs').select('*').eq('is_active', True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching songs: {e}")
            return pd.DataFrame()
    
    def add_song(self, title: str, composer: str, **kwargs) -> Optional[int]:
        """Add a new song"""
        try:
            data = {
                "title": title,
                "composer": composer,
                "active": True,
                **kwargs
            }
            response = self.client.table('songs').insert(data).execute()
            st.cache_data.clear()
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"Error adding song: {e}")
            return None
    
    # ==================== RUBRICS ====================
    
    @st.cache_data(ttl=3600)
    def get_rubrics(_self) -> pd.DataFrame:
        """Get all active rubrics"""
        try:
            response = _self.client.table('rubrics').select('*').eq('is_active', True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching rubrics: {e}")
            return pd.DataFrame()
    
    # ==================== EVALUATIONS ====================
    
    @st.cache_data(ttl=300)  # 5 minutes for fresh evaluation data
    def get_evaluations(_self, judge_id: int = None, song_id: int = None) -> pd.DataFrame:
        """Get evaluations with optional filtering"""
        try:
            query = _self.client.table('evaluations').select('''
                *,
                judge:judges(*),
                song:songs(*)
            ''')
            
            if judge_id:
                query = query.eq('judge_id', judge_id)
            if song_id:
                query = query.eq('song_id', song_id)
                
            response = query.execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching evaluations: {e}")
            return pd.DataFrame()

    def get_evaluations_by_song(self, song_id: int) -> pd.DataFrame:
        """Get all evaluations for a specific song"""
        return self.get_evaluations(song_id=song_id)

    def save_evaluation(self, judge_id: int, song_id: int, rubric_scores: Dict,
                       total_score: float, notes: str = None) -> bool:
        """Save or update an evaluation"""
        try:
            data = {
                "judge_id": judge_id,
                "song_id": song_id,
                "rubric_scores": json.dumps(rubric_scores),
                "total_score": total_score,
                "notes": notes,
                "updated_at": datetime.now().isoformat()
            }
            
            # Use upsert to handle both insert and update
            response = self.client.table('evaluations').upsert(
                data, 
                on_conflict='judge_id,song_id'
            ).execute()
            
            st.cache_data.clear()  # Clear evaluation cache
            return True
        except Exception as e:
            logger.error(f"Error saving evaluation: {e}")
            return False

    def update_evaluation(self, evaluation_id: int, rubric_scores: Dict,
                         total_score: float, notes: str = None) -> bool:
        """Update an existing evaluation"""
        try:
            data = {
                "rubric_scores": json.dumps(rubric_scores),
                "total_score": total_score,
                "notes": notes,
                "updated_at": datetime.now().isoformat()
            }

            response = self.client.table('evaluations').update(data).eq('id', evaluation_id).execute()

            st.cache_data.clear()  # Clear evaluation cache
            return True
        except Exception as e:
            logger.error(f"Error updating evaluation: {e}")
            return False

    def create_evaluation(self, judge_id: int, song_id: int, rubric_scores: Dict,
                         total_score: float, notes: str = None) -> bool:
        """Create a new evaluation"""
        try:
            data = {
                "judge_id": judge_id,
                "song_id": song_id,
                "rubric_scores": json.dumps(rubric_scores),
                "total_score": total_score,
                "notes": notes,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            response = self.client.table('evaluations').insert(data).execute()

            st.cache_data.clear()  # Clear evaluation cache
            return True
        except Exception as e:
            logger.error(f"Error creating evaluation: {e}")
            return False

    def final_submit_evaluation(self, evaluation_id: int) -> bool:
        """Mark evaluation as final submitted (locked)"""
        try:
            data = {
                "is_final_submitted": True,
                "final_submitted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            response = self.client.table('evaluations').update(data).eq('id', evaluation_id).execute()

            st.cache_data.clear()  # Clear evaluation cache
            return True
        except Exception as e:
            logger.error(f"Error final submitting evaluation: {e}")
            return False

    def unlock_evaluation(self, evaluation_id: int) -> bool:
        """Unlock evaluation (admin only)"""
        try:
            data = {
                "is_final_submitted": False,
                "final_submitted_at": None,
                "updated_at": datetime.now().isoformat()
            }

            response = self.client.table('evaluations').update(data).eq('id', evaluation_id).execute()

            st.cache_data.clear()  # Clear evaluation cache
            return True
        except Exception as e:
            logger.error(f"Error unlocking evaluation: {e}")
            return False

    # ==================== CONFIGURATION ====================
    
    @st.cache_data(ttl=3600)
    def get_config(_self) -> Dict[str, str]:
        """Get all configuration as dictionary"""
        try:
            response = _self.client.table('configuration').select('*').execute()
            # Database uses 'key' and 'value' columns directly
            return {item['key']: item['value'] for item in response.data}
        except Exception as e:
            logger.error(f"Error fetching configuration: {e}")
            return {}

    @st.cache_data(ttl=3600)
    def get_configuration(_self) -> pd.DataFrame:
        """Get all configuration settings as DataFrame"""
        try:
            response = _self.client.table('configuration').select('*').execute()
            # Database already uses 'key' and 'value' columns
            df = pd.DataFrame(response.data)
            return df
        except Exception as e:
            logger.error(f"Error fetching configuration: {e}")
            return pd.DataFrame()

    def update_config(self, key: str, value: str) -> bool:
        """Update configuration value"""
        try:
            data = {"key": key, "value": value, "updated_at": datetime.now().isoformat()}
            response = self.client.table('configuration').upsert(
                data,
                on_conflict='key'
            ).execute()
            st.cache_data.clear()
            return True
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

    def update_configuration(self, config_key: str, config_value: str) -> bool:
        """Update configuration setting (alias for update_config)"""
        return self.update_config(config_key, config_value)
    
    # ==================== KEYWORDS ====================
    
    @st.cache_data(ttl=3600)
    def get_keywords(_self) -> pd.DataFrame:
        """Get all active keywords"""
        try:
            response = _self.client.table('keywords').select('*').eq('is_active', True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching keywords: {e}")
            return pd.DataFrame()
    
    # ==================== ANALYTICS ====================
    
    def get_leaderboard(self) -> pd.DataFrame:
        """Get current leaderboard with rankings"""
        try:
            # Complex query for leaderboard - might need raw SQL
            query = """
            SELECT 
                s.title,
                s.composer,
                AVG(e.total_score) as avg_score,
                COUNT(e.id) as judge_count,
                STDDEV(e.total_score) as score_std
            FROM songs s
            LEFT JOIN evaluations e ON s.id = e.song_id
            WHERE s.is_active = true
            GROUP BY s.id, s.title, s.composer
            ORDER BY avg_score DESC NULLS LAST
            """
            
            response = self.client.rpc('execute_sql', {'query': query}).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {e}")
            # Fallback to simple query
            return self._get_simple_leaderboard()
    
    def _get_simple_leaderboard(self) -> pd.DataFrame:
        """Fallback leaderboard calculation"""
        evaluations = self.get_evaluations()
        if evaluations.empty:
            return pd.DataFrame()
        
        # Group by song and calculate averages
        leaderboard = evaluations.groupby(['song_id']).agg({
            'total_score': ['mean', 'std', 'count']
        }).round(2)
        
        leaderboard.columns = ['avg_score', 'score_std', 'judge_count']
        leaderboard = leaderboard.reset_index()
        
        # Add song details
        songs = self.get_songs()
        leaderboard = leaderboard.merge(
            songs[['id', 'title', 'composer']], 
            left_on='song_id', 
            right_on='id', 
            how='left'
        )
        
        return leaderboard.sort_values('avg_score', ascending=False)

# Global instance
db_service = DatabaseService()
