# -*- coding: utf-8 -*-
"""
Analytics Service - Handles all analytics and reporting functionality
Provides global analytics across all judges and comprehensive insights
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsService:
    """Centralized analytics service for comprehensive reporting"""
    
    def __init__(self):
        """Initialize analytics service"""
        pass
    
    # ==================== GLOBAL ANALYTICS ====================
    
    def get_global_leaderboard(self) -> pd.DataFrame:
        """Get global leaderboard across ALL judges (not just active judge)"""
        try:
            from services.database_service import db_service

            # Get all evaluations regardless of judge
            evaluations_df = db_service.get_evaluations()

            if evaluations_df.empty:
                return pd.DataFrame()

            # Calculate comprehensive statistics
            leaderboard = evaluations_df.groupby(['song_id']).agg({
                'total_score': ['mean', 'std', 'count', 'min', 'max'],
                'judge_id': 'nunique'
            }).round(2)

            # Flatten column names
            leaderboard.columns = ['avg_score', 'score_std', 'total_evaluations',
                                 'min_score', 'max_score', 'unique_judges']
            leaderboard = leaderboard.reset_index()

            # Convert scores from scale 5 to scale 100 (multiply by 4 since max is 25 -> 100)
            score_columns = ['avg_score', 'score_std', 'min_score', 'max_score']
            for col in score_columns:
                leaderboard[col] = leaderboard[col] * 4  # Convert 25-point scale to 100-point scale

            # Add song details with all fields needed
            songs_df = db_service.get_songs()
            leaderboard = leaderboard.merge(
                songs_df[['id', 'title', 'composer', 'audio_file_path', 'lyrics_text',
                         'full_score', 'chords_list', 'lyrics_with_chords', 'key_signature',
                         'notation_file_path', 'lyrics_file_path']],
                left_on='song_id',
                right_on='id',
                how='left'
            )

            # Calculate additional metrics (after conversion)
            leaderboard['score_range'] = leaderboard['max_score'] - leaderboard['min_score']
            leaderboard['consistency'] = 1 / (1 + leaderboard['score_std'].fillna(0))

            # Sort by average score
            leaderboard = leaderboard.sort_values('avg_score', ascending=False)

            # Add ranking
            leaderboard['rank'] = range(1, len(leaderboard) + 1)

            return leaderboard
            
        except Exception as e:
            logger.error(f"Error generating global leaderboard: {e}")
            return pd.DataFrame()
    
    def get_judge_analytics(self) -> pd.DataFrame:
        """Get analytics for all judges"""
        try:
            from services.database_service import db_service

            evaluations_df = db_service.get_evaluations()

            if evaluations_df.empty:
                return pd.DataFrame()

            # Judge statistics
            judge_stats = evaluations_df.groupby('judge_id').agg({
                'total_score': ['mean', 'std', 'count', 'min', 'max'],
                'created_at': ['min', 'max']
            }).round(2)

            # Flatten columns
            judge_stats.columns = ['avg_score', 'score_std', 'evaluations_count',
                                 'min_score', 'max_score', 'first_evaluation', 'last_evaluation']
            judge_stats = judge_stats.reset_index()

            # Convert scores from scale 5 to scale 100 (multiply by 4)
            score_columns = ['avg_score', 'score_std', 'min_score', 'max_score']
            for col in score_columns:
                judge_stats[col] = judge_stats[col] * 4  # Convert 25-point scale to 100-point scale

            # Add judge details
            judges_df = db_service.get_judges()
            judge_stats = judge_stats.merge(
                judges_df[['id', 'name']],
                left_on='judge_id',
                right_on='id',
                how='left'
            )

            # Calculate judge characteristics (after conversion to 100-point scale)
            judge_stats['scoring_tendency'] = judge_stats['avg_score'].apply(
                lambda x: 'Lenient' if x > 75 else 'Strict' if x < 60 else 'Moderate'
            )

            judge_stats['consistency'] = judge_stats['score_std'].apply(
                lambda x: 'Very Consistent' if x < 20 else 'Consistent' if x < 40 else 'Variable'  # Adjusted for 100-point scale
            )

            return judge_stats
            
        except Exception as e:
            logger.error(f"Error generating judge analytics: {e}")
            return pd.DataFrame()
    
    def get_rubric_analytics(self) -> pd.DataFrame:
        """Get analytics for each rubric criterion"""
        try:
            from services.database_service import db_service
            
            evaluations_df = db_service.get_evaluations()
            rubrics_df = db_service.get_rubrics()
            
            if evaluations_df.empty or rubrics_df.empty:
                return pd.DataFrame()
            
            rubric_stats = []
            
            for _, evaluation in evaluations_df.iterrows():
                if evaluation['rubric_scores']:
                    import json
                    # Handle both dict and string formats
                    scores = evaluation['rubric_scores']
                    if isinstance(scores, str):
                        scores = json.loads(scores)
                    elif not isinstance(scores, dict):
                        continue  # Skip invalid data
                    
                    for rubric_key, score in scores.items():
                        rubric_stats.append({
                            'rubric_key': rubric_key,
                            'score': score,
                            'song_id': evaluation['song_id'],
                            'judge_id': evaluation['judge_id']
                        })
            
            if not rubric_stats:
                return pd.DataFrame()
            
            rubric_df = pd.DataFrame(rubric_stats)
            
            # Calculate statistics per rubric
            analytics = rubric_df.groupby('rubric_key').agg({
                'score': ['mean', 'std', 'count', 'min', 'max']
            }).round(2)
            
            analytics.columns = ['avg_score', 'score_std', 'total_scores', 'min_score', 'max_score']
            analytics = analytics.reset_index()
            
            # Add rubric details
            analytics = analytics.merge(
                rubrics_df[['rubric_key', 'aspect_name', 'weight']],
                left_on='rubric_key',
                right_on='rubric_key',
                how='left'
            )
            
            # Calculate impact on total score
            analytics['weighted_contribution'] = analytics['avg_score'] * analytics['weight']
            
            return analytics.sort_values('weighted_contribution', ascending=False)
            
        except Exception as e:
            logger.error(f"Error generating rubric analytics: {e}")
            return pd.DataFrame()
    
    # ==================== VISUALIZATION FUNCTIONS ====================
    
    def create_leaderboard_chart(self, leaderboard_df: pd.DataFrame) -> go.Figure:
        """Create interactive leaderboard chart"""
        if leaderboard_df.empty:
            return go.Figure()
        
        fig = px.bar(
            leaderboard_df.head(10),
            x='title',
            y='avg_score',
            error_y='score_std',
            color='unique_judges',
            title='Top 10 Songs - Global Leaderboard (Scale 100)',
            labels={
                'title': 'Song Title',
                'avg_score': 'Average Score (/100)',
                'unique_judges': 'Number of Judges'
            }
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            yaxis=dict(
                title="Average Score (/100)",
                range=[0, 100]
            )
        )
        
        return fig
    
    def create_judge_comparison_chart(self, judge_stats_df: pd.DataFrame) -> go.Figure:
        """Create judge comparison chart"""
        if judge_stats_df.empty:
            return go.Figure()
        
        fig = px.scatter(
            judge_stats_df,
            x='avg_score',
            y='score_std',
            size='evaluations_count',
            color='scoring_tendency',
            hover_name='name',
            title='Judge Scoring Patterns (Scale 100)',
            labels={
                'avg_score': 'Average Score Given (/100)',
                'score_std': 'Score Standard Deviation',
                'evaluations_count': 'Number of Evaluations'
            }
        )

        fig.update_layout(
            height=500,
            xaxis=dict(
                title="Average Score Given (/100)",
                range=[0, 100]
            )
        )
        
        return fig
    
    def create_rubric_impact_chart(self, rubric_analytics_df: pd.DataFrame) -> go.Figure:
        """Create rubric impact visualization"""
        if rubric_analytics_df.empty:
            return go.Figure()
        
        fig = px.bar(
            rubric_analytics_df,
            x='aspect_name',
            y='weighted_contribution',
            color='avg_score',
            title='Rubric Criteria Impact on Total Scores',
            labels={
                'aspect_name': 'Evaluation Aspect',
                'weighted_contribution': 'Weighted Contribution to Total',
                'avg_score': 'Average Score'
            }
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig
    
    def create_score_distribution_chart(self) -> go.Figure:
        """Create score distribution chart"""
        try:
            from services.database_service import db_service

            evaluations_df = db_service.get_evaluations()

            if evaluations_df.empty:
                return go.Figure()

            # Convert scores to 100-point scale for display
            evaluations_df_display = evaluations_df.copy()
            evaluations_df_display['total_score'] = evaluations_df_display['total_score'] * 4

            fig = px.histogram(
                evaluations_df_display,
                x='total_score',
                nbins=20,
                title='Score Distribution Across All Evaluations (Scale 100)',
                labels={
                    'total_score': 'Total Score (/100)',
                    'count': 'Number of Evaluations'
                }
            )

            # Add mean line (converted to 100-point scale)
            mean_score = evaluations_df_display['total_score'].mean()
            fig.add_vline(
                x=mean_score,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {mean_score:.1f}/100"
            )

            fig.update_layout(
                height=400,
                xaxis=dict(
                    title="Total Score (/100)",
                    range=[0, 100]
                )
            )

            return fig
            
        except Exception as e:
            logger.error(f"Error creating score distribution chart: {e}")
            return go.Figure()
    
    # ==================== INSIGHTS GENERATION ====================
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generate comprehensive insights from all data"""
        try:
            insights = {}
            
            # Get data
            leaderboard = self.get_global_leaderboard()
            judge_stats = self.get_judge_analytics()
            rubric_analytics = self.get_rubric_analytics()
            
            # Competition insights
            if not leaderboard.empty:
                insights['competition'] = {
                    'total_songs': len(leaderboard),
                    'leader': leaderboard.iloc[0]['title'] if len(leaderboard) > 0 else None,
                    'leader_score': leaderboard.iloc[0]['avg_score'] if len(leaderboard) > 0 else None,
                    'closest_competition': self._find_closest_competition(leaderboard),
                    'most_consistent': self._find_most_consistent_song(leaderboard),
                    'most_controversial': self._find_most_controversial_song(leaderboard)
                }
            
            # Judge insights
            if not judge_stats.empty:
                # Check if all judges have same evaluation count (all complete)
                eval_counts = judge_stats['evaluations_count'].unique()

                insights['judges'] = {
                    'total_judges': len(judge_stats),
                    'most_lenient': judge_stats.loc[judge_stats['avg_score'].idxmax(), 'name'],
                    'most_strict': judge_stats.loc[judge_stats['avg_score'].idxmin(), 'name'],
                    'most_consistent': judge_stats.loc[judge_stats['score_std'].idxmin(), 'name']
                }

                # Only show "most active" if there's actually a difference in evaluation counts
                if len(eval_counts) > 1:
                    insights['judges']['most_active'] = judge_stats.loc[judge_stats['evaluations_count'].idxmax(), 'name']
            
            # Rubric insights
            if not rubric_analytics.empty:
                insights['rubrics'] = {
                    'most_impactful': rubric_analytics.iloc[0]['aspect_name'],
                    'highest_scoring': rubric_analytics.loc[rubric_analytics['avg_score'].idxmax(), 'aspect_name'],
                    'most_variable': rubric_analytics.loc[rubric_analytics['score_std'].idxmax(), 'aspect_name']
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {}
    
    def _find_closest_competition(self, leaderboard: pd.DataFrame) -> Optional[Dict]:
        """Find the closest competition between top songs"""
        if len(leaderboard) < 2:
            return None
        
        leaderboard['score_diff'] = leaderboard['avg_score'].diff().abs()
        closest_idx = leaderboard['score_diff'].idxmin()
        
        if pd.isna(leaderboard.loc[closest_idx, 'score_diff']):
            return None
        
        return {
            'song1': leaderboard.loc[closest_idx-1, 'title'],
            'song2': leaderboard.loc[closest_idx, 'title'],
            'difference': leaderboard.loc[closest_idx, 'score_diff']
        }
    
    def _find_most_consistent_song(self, leaderboard: pd.DataFrame) -> Optional[str]:
        """Find song with most consistent scoring"""
        if leaderboard.empty:
            return None
        
        # Filter songs with multiple evaluations
        multi_eval = leaderboard[leaderboard['total_evaluations'] > 1]
        if multi_eval.empty:
            return None
        
        return multi_eval.loc[multi_eval['score_std'].idxmin(), 'title']
    
    def _find_most_controversial_song(self, leaderboard: pd.DataFrame) -> Optional[str]:
        """Find song with most controversial scoring"""
        if leaderboard.empty:
            return None
        
        # Filter songs with multiple evaluations
        multi_eval = leaderboard[leaderboard['total_evaluations'] > 1]
        if multi_eval.empty:
            return None
        
        return multi_eval.loc[multi_eval['score_std'].idxmax(), 'title']

# Global instance
analytics_service = AnalyticsService()
