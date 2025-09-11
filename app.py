# -*- coding: utf-8 -*-
"""
New Streamlit App - Refactored with Modular Services
High-performance song contest judging application
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
import time
import json
import io
import base64
from datetime import datetime

# Import modular services
from services.database_service import db_service
from services.file_service import file_service
from services.cache_service import cache_service
from services.scoring_service import ScoringService
from services.analytics_service import analytics_service
from services.export_service import export_service
from services.auth_service import auth_service

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    st.warning("⚠️ ReportLab not installed. PDF generation will be disabled.")

# Import components
from components.login_simple import render_login_page
from components.admin_panel import render_admin_panel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="LOMBA CIPTA LAGU THEME SONG BULAN KELUARGA GKI PERUMNAS 2025",
    page_icon="🎵",
    layout="wide",
)

# ==================== BEAUTIFUL NAVIGATION CSS ====================

st.markdown("""
<style>
/* Beautiful Navigation Styling */
.stSidebar .stSelectbox > div > div {
    display: none !important;
}

/* Custom Navigation Buttons */
.nav-button {
    display: block !important;
    width: 100% !important;
    padding: 1rem 1.5rem !important;
    margin: 0.5rem 0 !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

.nav-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
}

.nav-button.active {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4) !important;
}

/* Page Navigation Enhancement */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 1rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stTabs [data-baseweb="tab"] {
    height: 60px;
    padding: 0 2rem;
    background: white;
    border-radius: 10px;
    border: 2px solid transparent;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stTabs [data-baseweb="tab"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    border-color: #667eea;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-color: #667eea !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3) !important;
}

/* Navigation Section Headers */
.nav-section-header {
    font-size: 1.3rem;
    font-weight: bold;
    color: #333;
    margin: 2rem 0 1rem 0;
    padding: 0.8rem 1rem;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 10px;
    border-left: 4px solid #667eea;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Sidebar Enhancement */
.stSidebar > div {
    background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
}

/* Button Enhancements */
.stButton > button {
    font-size: 1.1rem !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: 2px solid transparent !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-color: #667eea !important;
}

.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
    color: white !important;
    border-color: #6c757d !important;
}
</style>
""", unsafe_allow_html=True)

# ==================== GLOBAL CSS ====================

st.markdown("""
<style>
  .rubrik-cell{
    border:1px solid #E6E9F0;
    border-radius:10px;
    padding:.7rem .8rem;
    min-height:78px;
    background:#fff;
  }
  .rubrik-col-aspek{ font-weight:600; }
  .rubrik-col-bobot{ text-align:center; font-weight:600; }

  .r5{ background:#E9F8EF; }
  .r4{ background:#F1FAF0; }
  .r3{ background:#FFF5DA; }
  .r2{ background:#FFECE0; }
  .r1{ background:#FFE5E7; }

  .rubrik-head{
    font-weight:700;
    background:#F8FAFF;
    border:1px solid #E3E6EC;
    border-radius:10px;
    padding:.6rem .75rem;
    text-align:center;
  }
  .block-container{ max-width:1300px; }
  
  .stAudio { width: 100% !important; }

  @media (max-width: 640px) {
    .block-container { padding-top: 0.5rem; padding-bottom: 3.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: .25rem; }
    .stTabs [data-baseweb="tab"] { padding: .35rem .6rem; font-size: 0.92rem; }
  }
</style>
""", unsafe_allow_html=True)

# ==================== INITIALIZATION ====================

def initialize_app():
    """Initialize application with cache warming"""
    try:
        # Warm cache for better performance
        cache_service.warm_cache()
        
        # Initialize session state
        if "active_judge" not in st.session_state:
            st.session_state.active_judge = None
        
        if "selected_song" not in st.session_state:
            st.session_state.selected_song = None
        
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        st.error("Failed to initialize application. Please check your configuration.")
        st.stop()

# ==================== HELPER FUNCTIONS ====================

def should_show_balloons() -> bool:
    """Control balloon animations - show less frequently"""
    import random
    import time

    # Get current time
    current_time = time.time()

    # Check if we've shown balloons recently (within last 5 minutes)
    last_balloon_time = st.session_state.get('last_balloon_time', 0)
    time_since_last = current_time - last_balloon_time

    # Only show balloons if:
    # 1. It's been more than 5 minutes since last balloon
    # 2. Random chance (30% probability)
    if time_since_last > 300 and random.random() < 0.3:
        st.session_state['last_balloon_time'] = current_time
        return True

    return False

def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value with caching"""
    config = cache_service.get_cached_config()
    return config.get(key, default)

def display_banner():
    """Display application banner"""
    try:
        st.image("assets/banner.png", width='stretch')
    except Exception:
        # Get theme from config - escape HTML to prevent HTML injection
        config = cache_service.get_cached_config()
        theme = config.get('THEME', 'LOMBA CIPTA LAGU THEME SONG BULAN KELUARGA GKI PERUMNAS 2025')
        # Escape HTML tags to prevent HTML injection
        import html
        safe_theme = html.escape(str(theme))
        st.markdown(f"### 🎵 {safe_theme}")

# ==================== SIDEBAR ====================

def render_user_sidebar(current_user):
    """Render sidebar with user info and logout"""
    with st.sidebar:
        st.markdown("### 👤 User Info")

        # User details
        user_name = current_user.get('judge_name') or current_user.get('full_name', 'Unknown User')
        user_role = current_user.get('role', 'judge')

        st.markdown(f"**Name:** {user_name}")
        st.markdown(f"**Role:** {user_role.title()}")

        # Show impersonation status
        if auth_service.is_impersonating():
            st.warning("🎭 **Impersonating as Judge**")
            impersonation_data = st.session_state.get('admin_impersonation', {})
            admin_user = impersonation_data.get('admin_user', {})
            admin_name = admin_user.get('judges', {}).get('name', 'Unknown Admin')
            st.info(f"👑 Original Admin: {admin_name}")

            if st.button("🔙 Return to Admin", key="sidebar_return_admin"):
                auth_service.end_impersonation()

        st.markdown("---")

        # Navigation section
        st.markdown("### 🧭 Navigation")

        # Landing page button
        if st.button("🏠 Landing Page", key="sidebar_landing", type="secondary", width='stretch'):
            # Set flag to show landing page
            st.session_state.show_landing = True
            st.rerun()

        st.markdown("---")

        # Logout button - ALWAYS visible for authenticated users
        if st.button("🚪 Logout", key="sidebar_logout", type="secondary", width='stretch'):
            auth_service.logout()
            st.rerun()

        # Store current judge info in session state for compatibility
        st.session_state.active_judge = user_name
        st.session_state.current_user = current_user

        # Display cache statistics (for debugging)
        if st.checkbox("Show Cache Stats", value=False):
            stats = cache_service.get_cache_stats()
            st.json(stats)

        return user_name

# ==================== MAIN TABS ====================

def get_effective_user(current_user):
    """Get effective user (handles admin impersonation)"""
    # Check if admin is impersonating
    if current_user.get('role') == 'admin' and 'impersonate_judge' in st.session_state:
        selected_judge = st.session_state.impersonate_judge
        if selected_judge != "[Login as Admin]":
            judges_df = cache_service.get_cached_judges()
            judge_row = judges_df[judges_df['name'] == selected_judge].iloc[0]
            return {
                'judge_id': judge_row['id'],
                'judge_name': judge_row['name'],
                'role': 'judge',
                'email': judge_row['email']
            }
    return current_user

def render_audio_player(song_data, player_id=None):
    """Render SIMPLE audio player that actually works"""

    # Get audio path
    audio_path = song_data.get('audio_file_path', '')

    if not audio_path:
        st.info("🎵 Audio belum tersedia")
        return

    # Construct URL
    try:
        import urllib.parse
        if not audio_path.startswith('files/'):
            clean_path = f"files/{audio_path}"
        else:
            clean_path = audio_path

        supabase_project_url = st.secrets["supabase_url"]
        bucket_name = "song-contest-files"
        encoded_path = urllib.parse.quote(clean_path)
        audio_url = f"{supabase_project_url}/storage/v1/object/public/{bucket_name}/{encoded_path}"

        # SIMPLE Streamlit audio widget
        st.audio(audio_url)

    except Exception as e:
        st.error(f"❌ Error loading audio: {e}")


def render_comprehensive_rubric_analysis(rubric, song_data, ai_suggestions, ai_explanations):
    """Render comprehensive analysis for a specific rubric with rich content"""
    rubric_key = rubric['rubric_key']
    aspect_name = rubric['aspect_name']

    # 1. SPIDER CHART VISUALIZATION
    st.markdown("#### 🕸️ Analisis Visual")
    try:
        import plotly.graph_objects as go

        # Create mini spider chart for this rubric
        categories = ['Kualitas', 'Kompleksitas', 'Kesesuaian', 'Orisinalitas', 'Daya Tarik']

        if rubric_key in ai_suggestions:
            ai_score = ai_suggestions[rubric_key]
            # Generate scores based on rubric type
            if rubric_key == 'tema':
                values = [ai_score, ai_score-0.5, ai_score+0.2, ai_score-0.3, ai_score+0.1]
            elif rubric_key == 'lirik':
                values = [ai_score, ai_score+0.3, ai_score-0.1, ai_score+0.2, ai_score-0.2]
            elif rubric_key == 'musik':
                values = [ai_score, ai_score+0.5, ai_score-0.2, ai_score+0.1, ai_score+0.3]
            else:
                values = [3, 3, 3, 3, 3]  # Default for manual rubrics
        else:
            values = [3, 3, 3, 3, 3]

        # Normalize values to 1-5 range
        values = [max(1, min(5, v)) for v in values]

        # Close the radar chart
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name=aspect_name,
            line_color='#667eea'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            showlegend=False,
            height=250,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.info("📊 Visualisasi memerlukan plotly")
    except Exception as e:
        st.warning(f"⚠️ Error rendering chart: {str(e)}")
        # Fallback visualization
        st.markdown("📊 **Analisis Visual (Text Mode)**")
        if rubric_key in ai_suggestions:
            score = ai_suggestions[rubric_key]
            st.progress(score/5)
            st.caption(f"Skor: {score}/5")

    # 2. KEY INSIGHTS SECTION
    st.markdown("#### 💡 Key Insights")

    if rubric_key in ai_suggestions:
        ai_score = ai_suggestions[rubric_key]
        ai_explanation = ai_explanations.get(rubric_key, 'Analisis tersedia')

        # Generate comprehensive insights
        try:
            insights = generate_comprehensive_insights(rubric_key, song_data, ai_score)
            for insight in insights:
                st.markdown(f"""
                <div style="background: #e8f4fd; border-left: 4px solid #2196f3; padding: 12px; margin: 8px 0; border-radius: 6px;">
                    <strong>🔍 {insight['title']}</strong><br>
                    <span style="color: #555;">{insight['content']}</span>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Error generating insights: {str(e)}")
            # Fallback insights
            st.info(f"🔍 **Analisis {aspect_name}**: Skor AI menunjukkan nilai {ai_score}/5 untuk aspek ini.")

        # AI Analysis with detailed explanation
        st.markdown("#### 🤖 Analisis Mendalam")
        st.info(f"**Skor: {ai_score}/5** - {ai_explanation}")

        # Detailed breakdown
        try:
            breakdown = generate_score_breakdown(rubric_key, song_data, ai_score)
            for item in breakdown:
                st.markdown(f"• **{item['aspect']}**: {item['score']}/5 - {item['reason']}")
        except Exception as e:
            st.warning(f"⚠️ Error generating breakdown: {str(e)}")
            # Fallback breakdown
            st.markdown(f"• **Penilaian Umum**: {ai_score}/5 - Berdasarkan analisis AI")

    else:
        # Manual assessment with rich guidelines
        st.markdown("#### 📋 Panduan Penilaian Manual")
        try:
            guidelines = get_comprehensive_manual_guidelines(rubric_key)
            for guideline in guidelines:
                st.markdown(f"""
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 6px 0; border-radius: 6px;">
                    <strong>{guideline['title']}</strong><br>
                    <span style="color: #666;">{guideline['content']}</span>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Error loading guidelines: {str(e)}")
            # Fallback guidelines
            st.info(f"📋 **Panduan {aspect_name}**: Silakan nilai berdasarkan kualitas, kesesuaian, dan daya tarik aspek ini.")

    # 3. DETAILED ANALYSIS POINTS
    st.markdown("#### 📊 Analisis Detail")
    try:
        analysis_points = generate_detailed_analysis(rubric_key, song_data)
        for point in analysis_points:
            st.markdown(f"""
            <div style="background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 6px 0; border-radius: 6px;">
                <strong style="color: #495057;">📈 {point['metric']}</strong><br>
                <span style="color: #6c757d;">{point['value']} - {point['interpretation']}</span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"⚠️ Error generating analysis: {str(e)}")
        # Fallback analysis
        st.info(f"📊 **Analisis Detail {aspect_name}**: Evaluasi komprehensif sedang dimuat...")

    # 4. RECOMMENDATIONS
    st.markdown("#### 🎯 Rekomendasi & Saran")
    try:
        recommendations = generate_comprehensive_recommendations(rubric_key, song_data)
        for rec in recommendations:
            st.markdown(f"""
            <div style="background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 12px; margin: 8px 0; border-radius: 6px;">
                <strong>💡 {rec['title']}</strong><br>
                <span style="color: #555;">{rec['content']}</span>
                {f'<br><small style="color: #666;"><em>Prioritas: {rec["priority"]}</em></small>' if 'priority' in rec else ''}
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"⚠️ Error generating recommendations: {str(e)}")
        # Fallback recommendations
        st.info(f"🎯 **Rekomendasi {aspect_name}**: Saran perbaikan sedang dimuat...")

    # 5. FINAL RECOMMENDATIONS SUMMARY
    if rubric_key in ai_suggestions:
        ai_score = ai_suggestions[rubric_key]
        score_color = "#28a745" if ai_score >= 4 else "#ffc107" if ai_score >= 3 else "#dc3545"
        score_text = "Excellent" if ai_score >= 4 else "Good" if ai_score >= 3 else "Needs Improvement"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {score_color}20, {score_color}10);
                    border: 2px solid {score_color}; padding: 15px; margin: 10px 0;
                    border-radius: 10px; text-align: center;">
            <h4 style="margin: 0; color: {score_color};">🎯 Rekomendasi Akhir</h4>
            <h2 style="margin: 5px 0; color: {score_color};">{ai_score}/5</h2>
            <p style="margin: 0; color: #666; font-weight: 600;">{score_text}</p>
        </div>
        """, unsafe_allow_html=True)

def render_rubric_scoring_radio(rubric, song_data, current_score, judge_id, editing_locked, ai_suggestions):
    """Render scoring controls for a specific rubric using radio buttons"""
    rubric_key = rubric['rubric_key']

    # Define scoring descriptions based on database structure
    scoring_descriptions = {
        'tema': {
            1: 'Tidak sesuai tema / pesan tidak tersampaikan',
            2: 'Sedikit berkaitan; pesan kurang jelas',
            3: 'Cukup relevan, masih sesuai tema',
            4: 'Relevan & pesan tersampaikan jelas',
            5: 'Lirik sangat relevan, menginspirasi, menyentuh hati jemaat'
        },
        'lirik': {
            1: 'Lemah/sulit dipahami/tidak bermakna',
            2: 'Kurang kuat, beberapa bagian janggal',
            3: 'Sederhana tapi masih dimengerti',
            4: 'Menarik, mudah diingat, pesan jelas',
            5: 'Sangat puitis, rima indah, pesan mendalam & kuat'
        },
        'musik': {
            1: 'Tidak enak didengar/aransemen kacau',
            2: 'Monoton, aransemen kurang rapi',
            3: 'Melodi sederhana, harmoni oke',
            4: 'Melodi menarik, harmoni baik, aransemen rapi',
            5: 'Melodi sangat indah, harmoni & aransemen profesional'
        },
        'kreativ': {
            1: 'Tidak kreatif, terkesan meniru',
            2: 'Kurang kreatif, mirip lagu lain',
            3: 'Standar, masih ada ciri khas',
            4: 'Cukup kreatif, terasa segar & berbeda',
            5: 'Sangat kreatif, inovatif, benar-benar unik'
        },
        'jemaat': {
            1: 'Sangat sulit/terlalu teknis',
            2: 'Cenderung sulit dinyanyikan bersama',
            3: 'Cukup mudah; ada bagian agak sulit',
            4: 'Mudah dinyanyikan; range wajar',
            5: 'Sangat mudah dinyanyikan bersama; nada nyaman & ramah jemaat'
        }
    }

    # Get descriptions for this rubric
    descriptions = scoring_descriptions.get(rubric_key, {
        1: 'Sangat Kurang',
        2: 'Kurang',
        3: 'Cukup',
        4: 'Baik',
        5: 'Sangat Baik'
    })

    # Create radio button options
    options = []
    for score in range(1, 6):
        options.append(f"{score} - {descriptions[score]}")

    # AI suggestion display
    if rubric_key in ai_suggestions:
        ai_score = ai_suggestions[rubric_key]
        st.caption(f"🤖 Saran: {ai_score}/{rubric['max_score']}")

        # Quick apply AI suggestion button
        if st.button(f"✨ Terapkan Saran", key=f"apply_ai_{rubric_key}_{song_data['id']}",
                    disabled=editing_locked, help="Terapkan skor yang disarankan"):
            auto_save_score(judge_id, song_data['id'], rubric_key, ai_score)

    # Radio button for scoring
    selected_option = st.radio(
        "Pilih nilai:",
        options=options,
        index=int(current_score) - 1,  # Convert to 0-based index
        key=f"score_{rubric_key}_{song_data['id']}",
        disabled=editing_locked,
        label_visibility="collapsed"
    )

    # Extract score from selected option
    score = int(selected_option.split(' - ')[0])

    # Auto-save when score changes
    if not editing_locked and score != current_score:
        auto_save_score(judge_id, song_data['id'], rubric_key, score)

    # Score visualization
    score_percentage = (score / rubric['max_score']) * 100
    st.progress(score_percentage / 100)
    st.caption(f"Skor: {score}/{rubric['max_score']} ({score_percentage:.0f}%)")

    return score

def generate_comprehensive_insights(rubric_key, song_data, ai_score):
    """Generate comprehensive insights for each rubric type"""
    insights = []
    title = song_data.get('title', 'Lagu')
    lyrics = song_data.get('lyrics_text', '')
    chords = song_data.get('chords_list', '')

    if rubric_key == 'tema':
        insights = [
            {
                'title': 'Kesesuaian Tema Utama',
                'content': f'Lagu "{title}" menunjukkan tingkat kesesuaian tema {"sangat tinggi" if ai_score >= 4 else "baik" if ai_score >= 3 else "cukup" if ai_score >= 2 else "rendah"} dengan "Waktu Bersama Harta Berharga". Pesan utama {"tersampaikan dengan jelas" if ai_score >= 4 else "cukup tersampaikan" if ai_score >= 3 else "perlu diperkuat"}.'
            },
            {
                'title': 'Relevansi Alkitabiah',
                'content': f'Konten lirik {"sangat selaras" if ai_score >= 4 else "selaras" if ai_score >= 3 else "cukup selaras" if ai_score >= 2 else "kurang selaras"} dengan nilai-nilai Efesus 5:15-16 tentang hikmat dalam menggunakan waktu.'
            },
            {
                'title': 'Dampak Spiritual',
                'content': f'Potensi lagu untuk menginspirasi jemaat dalam menghargai waktu keluarga dinilai {"sangat tinggi" if ai_score >= 4 else "tinggi" if ai_score >= 3 else "sedang"}.'
            }
        ]
    elif rubric_key == 'lirik':
        word_count = len(lyrics.split()) if lyrics else 0
        insights = [
            {
                'title': 'Kualitas Puitis',
                'content': f'Lirik menunjukkan kualitas puitis yang {"excellent" if ai_score >= 4 else "baik" if ai_score >= 3 else "standar"}. Penggunaan bahasa {"sangat efektif" if ai_score >= 4 else "efektif" if ai_score >= 3 else "cukup efektif"} dengan {word_count} kata yang tersusun {"harmonis" if ai_score >= 3 else "sederhana"}.'
            },
            {
                'title': 'Struktur & Rima',
                'content': f'Pola rima dan struktur bait {"sangat teratur dan menarik" if ai_score >= 4 else "teratur" if ai_score >= 3 else "cukup teratur"}. Flow lirik {"sangat mudah diikuti" if ai_score >= 4 else "mudah diikuti" if ai_score >= 3 else "dapat diikuti"}.'
            },
            {
                'title': 'Kedalaman Makna',
                'content': f'Pesan dalam lirik memiliki kedalaman {"sangat mendalam" if ai_score >= 4 else "mendalam" if ai_score >= 3 else "cukup"} dan {"sangat relevan" if ai_score >= 4 else "relevan" if ai_score >= 3 else "cukup relevan"} dengan kehidupan sehari-hari.'
            }
        ]
    elif rubric_key == 'musik':
        chord_count = len(chords.split()) if chords else 0
        insights = [
            {
                'title': 'Kekayaan Harmoni',
                'content': f'Struktur harmoni menggunakan {chord_count} chord dengan tingkat kompleksitas {"tinggi" if ai_score >= 4 else "sedang" if ai_score >= 3 else "dasar"}. Progressi chord {"sangat menarik" if ai_score >= 4 else "menarik" if ai_score >= 3 else "standar"}.'
            },
            {
                'title': 'Kualitas Melodi',
                'content': f'Melodi memiliki karakteristik {"sangat indah dan memorable" if ai_score >= 4 else "indah" if ai_score >= 3 else "pleasant"}. Range vokal {"sangat sesuai" if ai_score >= 4 else "sesuai" if ai_score >= 3 else "cukup sesuai"} untuk jemaat.'
            },
            {
                'title': 'Aransemen & Tekstur',
                'content': f'Kualitas aransemen dinilai {"profesional" if ai_score >= 4 else "baik" if ai_score >= 3 else "standar"} dengan tekstur musik yang {"kaya dan seimbang" if ai_score >= 4 else "seimbang" if ai_score >= 3 else "sederhana"}.'
            }
        ]
    elif rubric_key == 'kreativ':
        insights = [
            {
                'title': 'Tingkat Orisinalitas',
                'content': f'Lagu menunjukkan tingkat orisinalitas yang {"sangat tinggi" if ai_score >= 4 else "tinggi" if ai_score >= 3 else "sedang"}. Elemen-elemen kreatif {"sangat menonjol" if ai_score >= 4 else "menonjol" if ai_score >= 3 else "cukup terlihat"}.'
            },
            {
                'title': 'Inovasi Musikal',
                'content': f'Pendekatan musikal {"sangat inovatif" if ai_score >= 4 else "inovatif" if ai_score >= 3 else "cukup fresh"} dengan elemen-elemen yang {"benar-benar unik" if ai_score >= 4 else "cukup unik" if ai_score >= 3 else "familiar namun menarik"}.'
            },
            {
                'title': 'Keunikan Konsep',
                'content': f'Konsep keseluruhan lagu {"sangat original" if ai_score >= 4 else "original" if ai_score >= 3 else "cukup berbeda"} dibanding karya-karya sejenis.'
            }
        ]
    elif rubric_key == 'jemaat':
        insights = [
            {
                'title': 'Kemudahan Vokal',
                'content': f'Range vokal dan melodi {"sangat mudah" if ai_score >= 4 else "mudah" if ai_score >= 3 else "cukup mudah"} untuk dinyanyikan jemaat semua usia. Interval-interval {"sangat natural" if ai_score >= 4 else "natural" if ai_score >= 3 else "dapat dijangkau"}.'
            },
            {
                'title': 'Aksesibilitas Musikal',
                'content': f'Struktur musik {"sangat ramah" if ai_score >= 4 else "ramah" if ai_score >= 3 else "cukup ramah"} untuk jemaat awam. Tingkat kesulitan teknis {"minimal" if ai_score >= 4 else "rendah" if ai_score >= 3 else "sedang"}.'
            },
            {
                'title': 'Daya Ingat & Partisipasi',
                'content': f'Potensi lagu untuk mudah diingat dan dinyanyikan bersama dinilai {"sangat tinggi" if ai_score >= 4 else "tinggi" if ai_score >= 3 else "sedang"}.'
            }
        ]

    return insights

def generate_score_breakdown(rubric_key, song_data, ai_score):
    """Generate detailed score breakdown"""
    breakdown = []

    if rubric_key == 'tema':
        breakdown = [
            {'aspect': 'Relevansi Tema', 'score': min(5, ai_score + 0.2), 'reason': 'Kesesuaian dengan tema utama'},
            {'aspect': 'Nilai Alkitabiah', 'score': ai_score, 'reason': 'Selaras dengan Efesus 5:15-16'},
            {'aspect': 'Pesan Keluarga', 'score': min(5, ai_score - 0.1), 'reason': 'Penekanan pada waktu bersama keluarga'},
            {'aspect': 'Inspirasi Spiritual', 'score': ai_score, 'reason': 'Kemampuan menginspirasi jemaat'}
        ]
    elif rubric_key == 'lirik':
        breakdown = [
            {'aspect': 'Kualitas Bahasa', 'score': ai_score, 'reason': 'Penggunaan bahasa yang efektif'},
            {'aspect': 'Struktur Puitis', 'score': min(5, ai_score + 0.3), 'reason': 'Rima dan irama yang baik'},
            {'aspect': 'Kedalaman Makna', 'score': min(5, ai_score - 0.2), 'reason': 'Substansi pesan yang disampaikan'},
            {'aspect': 'Kemudahan Pemahaman', 'score': ai_score, 'reason': 'Clarity dan accessibility'}
        ]
    elif rubric_key == 'musik':
        breakdown = [
            {'aspect': 'Kualitas Melodi', 'score': ai_score, 'reason': 'Keindahan dan flow melodis'},
            {'aspect': 'Kekayaan Harmoni', 'score': min(5, ai_score + 0.4), 'reason': 'Kompleksitas dan variasi chord'},
            {'aspect': 'Aransemen', 'score': min(5, ai_score - 0.1), 'reason': 'Kualitas pengaturan musik'},
            {'aspect': 'Produksi', 'score': ai_score, 'reason': 'Kualitas recording dan mixing'}
        ]
    else:
        breakdown = [
            {'aspect': 'Aspek Utama', 'score': 3, 'reason': 'Penilaian manual diperlukan'},
            {'aspect': 'Kualitas Keseluruhan', 'score': 3, 'reason': 'Evaluasi subjektif juri'},
            {'aspect': 'Kesesuaian Kriteria', 'score': 3, 'reason': 'Sesuai standar penilaian'}
        ]

    return breakdown

def generate_detailed_analysis(rubric_key, song_data):
    """Generate detailed analysis metrics"""
    analysis = []

    lyrics = song_data.get('lyrics_text', '')
    chords = song_data.get('chords_list', '')
    title = song_data.get('title', '')

    if rubric_key == 'tema':
        theme_keywords = ['waktu', 'bersama', 'keluarga', 'harta', 'berharga', 'kasih', 'sayang']
        keyword_count = sum(1 for word in theme_keywords if word.lower() in lyrics.lower())

        analysis = [
            {'metric': 'Kata Kunci Tema', 'value': f'{keyword_count}/7', 'interpretation': 'Frekuensi kata-kata tema utama'},
            {'metric': 'Panjang Lirik', 'value': f'{len(lyrics.split())} kata', 'interpretation': 'Substansi konten lirik'},
            {'metric': 'Fokus Tema', 'value': f'{(keyword_count/max(1, len(lyrics.split()))*100):.1f}%', 'interpretation': 'Persentase fokus pada tema'},
            {'metric': 'Relevansi Judul', 'value': 'Tinggi' if any(word in title.lower() for word in theme_keywords) else 'Sedang', 'interpretation': 'Kesesuaian judul dengan tema'}
        ]
    elif rubric_key == 'lirik':
        word_count = len(lyrics.split()) if lyrics else 0
        sentence_count = lyrics.count('.') + lyrics.count('!') + lyrics.count('?') if lyrics else 0

        analysis = [
            {'metric': 'Jumlah Kata', 'value': f'{word_count} kata', 'interpretation': 'Panjang dan substansi lirik'},
            {'metric': 'Struktur Kalimat', 'value': f'{sentence_count} kalimat', 'interpretation': 'Kompleksitas struktur bahasa'},
            {'metric': 'Rata-rata Kata/Kalimat', 'value': f'{word_count/max(1,sentence_count):.1f}', 'interpretation': 'Kompleksitas kalimat'},
            {'metric': 'Variasi Kosakata', 'value': f'{len(set(lyrics.lower().split()))} unik', 'interpretation': 'Kekayaan pilihan kata'}
        ]
    elif rubric_key == 'musik':
        chord_list = chords.split() if chords else []
        unique_chords = len(set(chord_list))

        analysis = [
            {'metric': 'Jumlah Chord', 'value': f'{len(chord_list)} chord', 'interpretation': 'Panjang progressi harmoni'},
            {'metric': 'Variasi Chord', 'value': f'{unique_chords} unik', 'interpretation': 'Kekayaan harmoni'},
            {'metric': 'Kompleksitas', 'value': f'{(unique_chords/max(1,len(chord_list))*100):.1f}%', 'interpretation': 'Tingkat variasi harmoni'},
            {'metric': 'Struktur Musik', 'value': 'Terstruktur' if len(chord_list) > 8 else 'Sederhana', 'interpretation': 'Kompleksitas aransemen'}
        ]
    else:
        analysis = [
            {'metric': 'Penilaian Manual', 'value': 'Diperlukan', 'interpretation': 'Evaluasi subjektif oleh juri'},
            {'metric': 'Kriteria Khusus', 'value': 'Sesuai Rubrik', 'interpretation': 'Mengikuti panduan penilaian'},
            {'metric': 'Standar Kualitas', 'value': 'Kompetitif', 'interpretation': 'Memenuhi standar lomba'}
        ]

    return analysis

def get_comprehensive_manual_guidelines(rubric_key):
    """Get comprehensive manual assessment guidelines"""
    guidelines = []

    if rubric_key == 'kreativ':
        guidelines = [
            {'title': 'Orisinalitas Konsep', 'content': 'Evaluasi keunikan ide dan pendekatan yang tidak mainstream'},
            {'title': 'Inovasi Musikal', 'content': 'Penggunaan elemen musik yang fresh dan tidak klise'},
            {'title': 'Kreativitas Lirik', 'content': 'Cara penyampaian pesan yang unik dan menarik'},
            {'title': 'Keberanian Artistik', 'content': 'Pengambilan risiko kreatif yang calculated dan efektif'}
        ]
    elif rubric_key == 'jemaat':
        guidelines = [
            {'title': 'Range Vokal', 'content': 'Pastikan nada tertinggi dan terendah dapat dijangkau jemaat umum'},
            {'title': 'Kemudahan Melodi', 'content': 'Interval dan pola melodi yang natural dan mudah diingat'},
            {'title': 'Tempo & Ritme', 'content': 'Kecepatan dan pola ritme yang nyaman untuk bernyanyi bersama'},
            {'title': 'Struktur Lagu', 'content': 'Bagian-bagian lagu yang mudah dipelajari dan diikuti'}
        ]
    else:
        guidelines = [
            {'title': 'Standar Kualitas', 'content': 'Evaluasi berdasarkan standar industri musik rohani'},
            {'title': 'Kesesuaian Konteks', 'content': 'Relevansi dengan setting ibadah dan komunitas'},
            {'title': 'Dampak Spiritual', 'content': 'Potensi untuk menginspirasi dan memberkati jemaat'}
        ]

    return guidelines

def generate_comprehensive_recommendations(rubric_key, song_data):
    """Generate comprehensive recommendations"""
    recommendations = []

    if rubric_key == 'tema':
        recommendations = [
            {'title': 'Penguatan Pesan Tema', 'content': 'Pertimbangkan penambahan lirik yang lebih eksplisit tentang nilai waktu keluarga', 'priority': 'Tinggi'},
            {'title': 'Referensi Alkitabiah', 'content': 'Integrasikan lebih banyak nilai-nilai dari Efesus 5:15-16', 'priority': 'Sedang'},
            {'title': 'Aplikasi Praktis', 'content': 'Tambahkan contoh konkret bagaimana menghargai waktu bersama', 'priority': 'Sedang'}
        ]
    elif rubric_key == 'lirik':
        recommendations = [
            {'title': 'Pengembangan Puitis', 'content': 'Eksplorasi metafora dan imagery yang lebih kaya untuk memperdalam makna', 'priority': 'Tinggi'},
            {'title': 'Struktur Rima', 'content': 'Konsistensi pola rima untuk meningkatkan flow dan memorability', 'priority': 'Sedang'},
            {'title': 'Variasi Kosakata', 'content': 'Gunakan sinonim dan variasi kata untuk menghindari repetisi', 'priority': 'Rendah'}
        ]
    elif rubric_key == 'musik':
        recommendations = [
            {'title': 'Pengayaan Harmoni', 'content': 'Eksplorasi chord extensions dan substitusi untuk memperkaya warna harmoni', 'priority': 'Tinggi'},
            {'title': 'Dinamika Musik', 'content': 'Variasi volume dan intensitas untuk menciptakan emotional journey', 'priority': 'Sedang'},
            {'title': 'Aransemen Instrumen', 'content': 'Pertimbangkan penambahan instrumen untuk memperkaya tekstur', 'priority': 'Sedang'}
        ]
    elif rubric_key == 'kreativ':
        recommendations = [
            {'title': 'Eksplorasi Genre', 'content': 'Pertimbangkan fusion dengan genre musik yang tidak mainstream', 'priority': 'Tinggi'},
            {'title': 'Elemen Surprise', 'content': 'Tambahkan unexpected elements yang tetap selaras dengan tema', 'priority': 'Sedang'},
            {'title': 'Pendekatan Unik', 'content': 'Cari angle atau perspektif yang belum banyak dieksplor', 'priority': 'Tinggi'}
        ]
    elif rubric_key == 'jemaat':
        recommendations = [
            {'title': 'Simplifikasi Melodi', 'content': 'Pertimbangkan penyederhanaan bagian-bagian yang terlalu kompleks', 'priority': 'Tinggi'},
            {'title': 'Key Adjustment', 'content': 'Sesuaikan kunci nada dengan range vokal jemaat umum', 'priority': 'Sedang'},
            {'title': 'Struktur Repetitif', 'content': 'Gunakan pola yang mudah diingat dan diulang', 'priority': 'Sedang'}
        ]

    return recommendations

# Sticky mode removed - using accordion only

def render_accordion_mode(rubric, song_data, ai_suggestions, ai_explanations, existing_scores, judge_id, editing_locked):
    """Render accordion mode - collapsible sections with score in header"""
    rubric_key = rubric['rubric_key']
    current_score = existing_scores.get(rubric_key, 0)

    # Get icon
    rubric_icons = {
        'tema': '🎯',
        'lirik': '📝',
        'musik': '🎼',
        'kreativ': '✨',
        'jemaat': '👥'
    }
    icon = rubric_icons.get(rubric_key, '📋')

    # Score display
    if current_score > 0:
        score_display = f"📝 {current_score}/5"
        score_color = "#28a745" if current_score >= 4 else "#ffc107" if current_score >= 3 else "#dc3545"
    else:
        score_display = "📝 Belum dinilai"
        score_color = "#6c757d"

    # Use expander for accordion behavior
    with st.expander(f"{icon} {rubric['aspect_name']} (Bobot: {rubric['weight']}%) - {score_display}", expanded=current_score == 0):
        # Create 2-column layout within expander
        col_analysis, col_scoring = st.columns([2, 1])

        with col_analysis:
            # Analysis content
            st.markdown(f"#### 📊 Analisis {rubric['aspect_name']}")

            try:
                render_comprehensive_rubric_analysis(rubric, song_data, ai_suggestions, ai_explanations)
            except Exception as e:
                st.error(f"Error rendering analysis: {str(e)}")
                # Fallback content
                st.info("📋 Analisis komprehensif sedang dimuat...")
                if rubric_key in ai_suggestions:
                    st.success(f"🤖 **Skor AI**: {ai_suggestions[rubric_key]}/5")

        with col_scoring:
            # Scoring controls
            st.markdown("#### 📝 Penilaian")
            score = render_rubric_scoring_radio(rubric, song_data, current_score, judge_id, editing_locked, ai_suggestions)

def render_rubric_chart(rubric_key, song_data, ai_score, max_score):
    """Render visual chart for specific rubric"""
    try:
        import plotly.graph_objects as go
        import plotly.express as px

        if rubric_key == 'melodi':
            # Simple score visualization
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = ai_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Skor Melodi"},
                gauge = {
                    'axis': {'range': [None, max_score]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 2], 'color': "lightgray"},
                        {'range': [2, 3], 'color': "yellow"},
                        {'range': [3, 4], 'color': "orange"},
                        {'range': [4, max_score], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': max_score
                    }
                }
            ))
            fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

        elif rubric_key == 'harmoni':
            # Harmony complexity chart
            categories = ['Progressi Dasar', 'Modulasi', 'Variasi Akor', 'Resolusi']
            values = [ai_score] * 4  # Simplified for demo

            fig = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Analisis Harmoni'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max_score]
                    )),
                showlegend=False,
                height=250,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

        elif rubric_key == 'syair':
            # Word analysis chart
            lyrics = song_data.get('lyrics_text', '')
            if lyrics:
                words = lyrics.lower().split()
                # Count theme-related words
                theme_words = ['waktu', 'bersama', 'keluarga', 'harta', 'berharga', 'kasih', 'cinta', 'tuhan', 'berkat']
                theme_count = sum(1 for word in words if any(theme in word for theme in theme_words))
                total_words = len(words)

                fig = go.Figure(data=[
                    go.Bar(name='Kata Tema', x=['Analisis Syair'], y=[theme_count]),
                    go.Bar(name='Total Kata', x=['Analisis Syair'], y=[total_words])
                ])
                fig.update_layout(
                    title="Analisis Kata dalam Syair",
                    height=200,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        # Fallback to simple text display if plotly not available
        st.info(f"📊 Skor: {ai_score}/{max_score}")

def generate_recommendations(rubric_key, song_data):
    """Generate recommendations for each rubric"""
    recommendations = []

    if rubric_key == 'melodi':
        recommendations = [
            {
                'title': 'Pengembangan Melodi',
                'content': 'Pertimbangkan variasi ritme dan interval untuk meningkatkan daya tarik melodis.'
            },
            {
                'title': 'Keterbacaan',
                'content': 'Pastikan melodi mudah diingat dan dapat dinyanyikan oleh jemaat.'
            }
        ]
    elif rubric_key == 'harmoni':
        recommendations = [
            {
                'title': 'Progressi Harmoni',
                'content': 'Eksplorasi penggunaan akor substitusi untuk memperkaya harmoni.'
            },
            {
                'title': 'Modulasi',
                'content': 'Pertimbangkan modulasi sederhana untuk menambah dinamika lagu.'
            }
        ]
    elif rubric_key == 'syair':
        recommendations = [
            {
                'title': 'Kedalaman Makna',
                'content': 'Perkuat pesan spiritual dan nilai keluarga dalam syair.'
            },
            {
                'title': 'Struktur Syair',
                'content': 'Pastikan alur cerita dalam syair koheren dan mudah dipahami.'
            }
        ]
    elif rubric_key == 'kreativ':
        recommendations = [
            {
                'title': 'Orisinalitas',
                'content': 'Nilai keunikan pendekatan komposisi dan ide-ide segar dalam karya.'
            },
            {
                'title': 'Inovasi',
                'content': 'Pertimbangkan elemen-elemen yang membuat lagu berbeda dari yang lain.'
            }
        ]
    elif rubric_key == 'jemaat':
        recommendations = [
            {
                'title': 'Kemudahan Bernyanyi',
                'content': 'Pastikan rentang nada sesuai untuk jemaat umum (tidak terlalu tinggi/rendah).'
            },
            {
                'title': 'Penggunaan Liturgis',
                'content': 'Evaluasi kesesuaian untuk berbagai momen dalam ibadah.'
            }
        ]

    return recommendations

def get_manual_guidelines(rubric_key):
    """Get manual assessment guidelines for each rubric"""
    guidelines = {
        'melodi': [
            'Evaluasi keindahan dan daya tarik melodi',
            'Pertimbangkan kemudahan untuk diingat dan dinyanyikan',
            'Nilai kesesuaian melodi dengan karakter lagu rohani',
            'Perhatikan variasi dan pengembangan motif melodis'
        ],
        'harmoni': [
            'Analisis kekayaan dan kesesuaian progressi harmoni',
            'Nilai penggunaan akor yang mendukung melodi',
            'Pertimbangkan kompleksitas yang sesuai untuk jemaat',
            'Evaluasi resolusi harmoni yang memuaskan'
        ],
        'syair': [
            'Nilai kedalaman makna dan pesan spiritual',
            'Evaluasi kesesuaian dengan tema lomba',
            'Pertimbangkan kualitas sastra dan puitis',
            'Perhatikan kemudahan pemahaman oleh jemaat'
        ],
        'kreativ': [
            'Nilai orisinalitas dan keunikan karya',
            'Evaluasi kreativitas dalam pendekatan komposisi',
            'Pertimbangkan inovasi dalam penggunaan elemen musik',
            'Nilai keberanian dalam eksplorasi musikal'
        ],
        'jemaat': [
            'Evaluasi kemudahan untuk dinyanyikan jemaat',
            'Pertimbangkan rentang nada yang sesuai',
            'Nilai kesesuaian untuk penggunaan dalam ibadah',
            'Perhatikan aspek partisipasi jemaat'
        ]
    }

    return guidelines.get(rubric_key, ['Penilaian manual diperlukan untuk kriteria ini'])

def get_available_content(song_data):
    """Get all available content for a song"""
    content = {
        'id': song_data.get('id'),
        'title': song_data.get('title', ''),
        'composer': song_data.get('composer', ''),
        'lyrics_text': song_data.get('lyrics_text', ''),
        'lyrics_file_id': song_data.get('lyrics_file_id'),
        'lyrics_file_path': song_data.get('lyrics_file_path'),
        'chords_list': song_data.get('chords_list', ''),
        'chords_text': song_data.get('chords_text', ''),  # Alternative field
        'notation_file_id': song_data.get('notation_file_id'),
        'notation_file_path': song_data.get('notation_file_path'),
        'notation_text': song_data.get('notation_text', ''),  # Manual notation
        'full_score': song_data.get('full_score', ''),
        'lyrics_with_chords': song_data.get('lyrics_with_chords', ''),
        'key_signature': song_data.get('key_signature', ''),
        'audio_file_id': song_data.get('audio_file_id'),
        'audio_file_path': song_data.get('audio_file_path'),
        'lyrics_pdf_url': song_data.get('lyrics_pdf_url'),
        'notation_pdf_url': song_data.get('notation_pdf_url')
    }
    return content

def render_comprehensive_content(song_data, tab_type="lyrics"):
    """Render comprehensive content based on tab type with all available data"""
    content = get_available_content(song_data)

    if tab_type == "lyrics":
        # Tab Syair & Tema: Prioritas syair, tapi tampilkan semua yang ada
        st.markdown("#### 📝 **Konten Lagu**")

        # Show content selection if multiple sources available
        available_sources = []
        if content['lyrics_text']: available_sources.append("📝 Syair (Teks)")
        if content['lyrics_file_id'] or content['lyrics_file_path']: available_sources.append("📄 Syair (PDF)")
        if content['chords_list'] or content['chords_text']: available_sources.append("🎼 Chord")
        if content['notation_text']: available_sources.append("🎵 Notasi (Teks)")

        if len(available_sources) > 1:
            selected_source = st.selectbox(
                "Pilih konten yang ingin ditampilkan:",
                available_sources,
                key=f"content_selector_lyrics_{song_data['id']}"
            )
        else:
            selected_source = available_sources[0] if available_sources else None

        # Display selected content
        if selected_source == "📝 Syair (Teks)" and content['lyrics_text']:
            render_lyrics_text(content['lyrics_text'])
        elif selected_source == "📄 Syair (PDF)":
            render_lyrics_viewer(song_data)
        elif selected_source == "🎼 Chord" and (content['chords_list'] or content['chords_text']):
            render_chords_text(content['chords_list'] or content['chords_text'])
        elif selected_source == "🎵 Notasi (Teks)" and content['notation_text']:
            render_notation_text(content['notation_text'])
        else:
            # Fallback: show whatever is available
            if content['lyrics_text']:
                render_lyrics_text(content['lyrics_text'])
            elif content['lyrics_file_id'] or content['lyrics_file_path']:
                render_lyrics_viewer(song_data)
            else:
                st.warning("⚠️ Konten syair tidak tersedia")

    elif tab_type == "notation":
        # Tab Notasi & Musik: Prioritas notasi/chord, tampilkan selengkap mungkin
        st.markdown("#### 🎼 **Konten Musik**")

        # Show all available music content
        music_content_shown = False

        # 1. Chord progression (highest priority for music tab)
        if content['chords_list'] or content['chords_text']:
            st.markdown("##### 🎸 **Chord Progression**")
            render_chords_text(content['chords_list'] or content['chords_text'])
            music_content_shown = True

        # 2. Manual notation text
        if content['notation_text']:
            if music_content_shown:
                st.markdown("---")
            st.markdown("##### 🎵 **Notasi (Teks)**")
            render_notation_text(content['notation_text'])
            music_content_shown = True

        # 3. PDF notation
        if content['notation_file_id'] or content['notation_file_path']:
            if music_content_shown:
                st.markdown("---")
            st.markdown("##### 📄 **Notasi (PDF)**")
            render_notation_viewer(song_data)
            music_content_shown = True

        # 4. Fallback: show lyrics if no music content
        if not music_content_shown:
            if content['lyrics_text']:
                st.markdown("##### 📝 **Syair (Fallback)**")
                st.info("💡 Konten musik tidak tersedia, menampilkan syair sebagai referensi")
                render_lyrics_text(content['lyrics_text'])
            else:
                st.warning("⚠️ Konten musik dan syair tidak tersedia")

def render_lyrics_text(lyrics_text):
    """Render lyrics text with proper styling"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #007bff;
            font-family: 'Georgia', serif;
            line-height: 1.8;
            white-space: pre-wrap;
            overflow-wrap: break-word;
            max-height: 500px;
            overflow-y: auto;
        ">
            {lyrics_text}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_chords_text(chords_text):
    """Render chords text with proper styling"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            white-space: pre-wrap;
            overflow-wrap: break-word;
            max-height: 500px;
            overflow-y: auto;
        ">
            {chords_text}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_notation_text(notation_text):
    """Render notation text with proper styling"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            white-space: pre-wrap;
            overflow-wrap: break-word;
            max-height: 500px;
            overflow-y: auto;
        ">
            {notation_text}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_notation_viewer(song_data):
    """Render notation viewer for a song"""
    pdf_url = None

    # Try to get PDF URL
    if song_data.get('notation_file_id'):
        pdf_url = file_service.get_file_url(song_data['notation_file_id'])
    elif song_data.get('notation_file_path'):
        notation_path = song_data['notation_file_path']
        if notation_path:
            try:
                # Files are in bucket/files/ folder structure
                if notation_path.startswith('files/'):
                    clean_path = notation_path  # Keep files/ prefix
                else:
                    clean_path = f"files/{notation_path}"  # Add files/ prefix
                pdf_url = file_service.get_public_url(clean_path)
                if not pdf_url:
                    import urllib.parse
                    supabase_project_url = st.secrets["supabase_url"]
                    bucket_name = "song-contest-files"
                    encoded_path = urllib.parse.quote(clean_path)
                    pdf_url = f"{supabase_project_url}/storage/v1/object/public/{bucket_name}/{encoded_path}"
            except Exception as e:
                st.warning(f"Error loading notation: {e}")

    # Always display PDF prominently if available
    if pdf_url:
        # Prominent PDF display section
        st.markdown("### 🎼 **Notasi Musik (PDF Original)**")

        # Download/open button at top for easy access
        st.markdown(f"""
        <div style="text-align: center; margin: 15px 0;">
            <a href="{pdf_url}" target="_blank" style="text-decoration: none;">
                <div style="background: linear-gradient(90deg, #4CAF50, #45a049); color: white; padding: 15px 30px; border-radius: 10px; text-align: center; display: inline-block; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.3); font-size: 1.1rem;">
                    📄 Buka PDF Notasi di Tab Baru
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

        # Embed PDF viewer with larger size
        st.markdown(f"""
        <div style="border: 3px solid #4CAF50; border-radius: 15px; overflow: hidden; margin: 20px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.2);">
            <iframe src="{pdf_url}" width="100%" height="700" type="application/pdf" style="border: none;">
                <p>Browser Anda tidak mendukung PDF viewer. <a href="{pdf_url}" target="_blank">Klik di sini untuk membuka PDF</a></p>
            </iframe>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 **Tip**: Gunakan PDF original di atas sebagai referensi utama untuk penilaian")

        return

    # Fallback messages
    if song_data.get('notation_file_path'):
        st.warning(f"📄 Notasi tersedia tapi belum di-upload: `{song_data['notation_file_path']}`")
        st.info("💡 **Admin**: Upload file ke Supabase Storage untuk mengaktifkan PDF viewer")
    else:
        st.info("📄 Notasi belum tersedia")

def render_lyrics_viewer(song_data):
    """Render lyrics viewer for a song"""
    pdf_url = None

    # Try to get PDF URL first
    if song_data.get('lyrics_file_id'):
        pdf_url = file_service.get_file_url(song_data['lyrics_file_id'])
    elif song_data.get('lyrics_file_path'):
        lyrics_path = song_data['lyrics_file_path']
        if lyrics_path:
            try:
                # Files are in bucket/files/ folder structure
                if lyrics_path.startswith('files/'):
                    clean_path = lyrics_path  # Keep files/ prefix
                else:
                    clean_path = f"files/{lyrics_path}"  # Add files/ prefix
                pdf_url = file_service.get_public_url(clean_path)
                if not pdf_url:
                    import urllib.parse
                    supabase_project_url = st.secrets["supabase_url"]
                    bucket_name = "song-contest-files"
                    encoded_path = urllib.parse.quote(clean_path)
                    pdf_url = f"{supabase_project_url}/storage/v1/object/public/{bucket_name}/{encoded_path}"
            except Exception as e:
                st.warning(f"Error loading lyrics PDF: {e}")

    # Always display PDF prominently if available
    if pdf_url:
        # Prominent PDF display section
        st.markdown("### 📄 **Syair Lagu (PDF Original)**")

        # Download/open button at top for easy access
        st.markdown(f"""
        <div style="text-align: center; margin: 15px 0;">
            <a href="{pdf_url}" target="_blank" style="text-decoration: none;">
                <div style="background: linear-gradient(90deg, #2196F3, #1976D2); color: white; padding: 15px 30px; border-radius: 10px; text-align: center; display: inline-block; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.3); font-size: 1.1rem;">
                    📝 Buka PDF Syair di Tab Baru
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

        # Embed PDF viewer with larger size
        st.markdown(f"""
        <div style="border: 3px solid #2196F3; border-radius: 15px; overflow: hidden; margin: 20px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.2);">
            <iframe src="{pdf_url}" width="100%" height="700" type="application/pdf" style="border: none;">
                <p>Browser Anda tidak mendukung PDF viewer. <a href="{pdf_url}" target="_blank">Klik di sini untuk membuka PDF</a></p>
            </iframe>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 **Tip**: Gunakan PDF original di atas sebagai referensi utama untuk penilaian")

    # Show text content if available (fallback or additional)
    if song_data.get('lyrics_text'):
        st.markdown("---")
        st.markdown("**📝 Syair Lagu (Teks):**")
        st.text_area("Syair Lagu", value=song_data['lyrics_text'], height=200, disabled=True, key=f"lyrics_text_{song_data['id']}", label_visibility="collapsed")
    elif not pdf_url:
        # Only show warning if no PDF and no text
        if song_data.get('lyrics_file_path'):
            st.warning(f"📝 Syair tersedia tapi belum di-upload: `{song_data['lyrics_file_path']}`")
            st.info("💡 **Admin**: Upload file ke Supabase Storage untuk mengaktifkan PDF viewer")
        else:
            st.info("📝 Syair belum tersedia")

# Removed render_song_analysis and related functions - analysis is now integrated in evaluation tab

# Removed analysis functions - functionality integrated in evaluation tab

# Analysis functions removed - content moved to evaluation tab

# Analysis functions removed - content moved to evaluation tab

def auto_save_score(judge_id: int, song_id: int, rubric_key: str, score: int):
    """Auto-save individual score when changed - optimized for performance"""
    try:
        # Get existing evaluation (use cached data to avoid DB calls)
        existing_evaluations = cache_service.get_cached_evaluations(judge_id=judge_id, song_id=song_id)

        if not existing_evaluations.empty:
            # Update existing evaluation
            existing_eval = existing_evaluations.iloc[0]
            existing_scores = existing_eval['rubric_scores'] or {}

            # Handle string format
            if isinstance(existing_scores, str):
                import json
                existing_scores = json.loads(existing_scores)
            elif not isinstance(existing_scores, dict):
                existing_scores = {}

            # Update the specific rubric score
            existing_scores[rubric_key] = score

            # Calculate total weighted score in 25-point scale for database storage
            rubrics_df = cache_service.get_cached_rubrics()
            total_weighted_score = 0
            for _, rubric in rubrics_df.iterrows():
                if rubric['rubric_key'] in existing_scores:
                    rubric_score = existing_scores[rubric['rubric_key']]
                    # Calculate weighted score in 25-point scale (not 100-point)
                    total_weighted_score += (rubric_score / rubric['max_score']) * (rubric['weight'] / 100) * 25

            # Update evaluation (async to avoid blocking UI)
            success = db_service.update_evaluation(
                existing_eval['id'],
                rubric_scores=existing_scores,
                total_score=total_weighted_score
            )

            # Only clear cache if update was successful (reduce unnecessary cache clears)
            if success:
                # Use selective cache invalidation instead of clearing all
                cache_service.invalidate_cache('evaluations')

                # Show success message without blocking
                st.success(f"✅ Nilai {rubric_key} tersimpan: {score}", icon="💾")
            else:
                st.error(f"❌ Gagal menyimpan nilai {rubric_key}")

        else:
            # Create new evaluation
            rubrics_df = cache_service.get_cached_rubrics()
            initial_scores = {rubric_key: score}

            # Calculate initial total score in 25-point scale for database storage
            total_weighted_score = 0
            for _, rubric in rubrics_df.iterrows():
                if rubric['rubric_key'] == rubric_key:
                    total_weighted_score = (score / rubric['max_score']) * (rubric['weight'] / 100) * 25
                    break

            # Create evaluation
            success = db_service.create_evaluation(
                judge_id=judge_id,
                song_id=song_id,
                rubric_scores=initial_scores,
                total_score=total_weighted_score,
                notes=""
            )

            # Only clear cache if creation was successful
            if success:
                cache_service.invalidate_cache('evaluations')
                st.success(f"✅ Evaluasi baru dibuat dengan nilai {rubric_key}: {score}", icon="💾")
            else:
                st.error(f"❌ Gagal membuat evaluasi baru")

    except Exception as e:
        st.error(f"❌ Error auto-saving score: {str(e)}")
        # Reduced logging to improve performance
        logger.error(f"Auto-save error: {e}")

def auto_save_notes(judge_id: int, song_id: int, notes: str):
    """Auto-save notes when changed"""
    try:
        # Get existing evaluation
        existing_evaluations = cache_service.get_cached_evaluations(judge_id=judge_id, song_id=song_id)

        if not existing_evaluations.empty:
            # Update existing evaluation
            existing_eval = existing_evaluations.iloc[0]

            # Update evaluation with new notes
            db_service.update_evaluation(
                existing_eval['id'],
                notes=notes
            )

            # Clear cache
            cache_service.clear_evaluations_cache()

    except Exception as e:
        st.error(f"Error auto-saving notes: {e}")

def build_suggestions(song_data):
    """Build AI suggestions for scoring based on song analysis"""
    try:
        # Get song content for analysis
        title = song_data.get('title', '')
        lyrics_text = song_data.get('lyrics_text', '')
        chords_text = song_data.get('chords_list', '')
        composer = song_data.get('composer', '')

        # Initialize scoring service for advanced analysis
        scoring_service = ScoringService()

        # Contest theme and verse for reference
        contest_theme = "WAKTU BERSAMA HARTA BERHARGA"
        contest_verse = "Efesus 5:15-16 - Karena itu, perhatikanlah dengan saksama, bagaimana kamu hidup, janganlah seperti orang bebal, tetapi seperti orang arif, dan pergunakanlah waktu yang ada, karena hari-hari ini adalah jahat."

        # 1. TEMA - Kesesuaian Tema (Advanced analysis)
        tema_score = 3  # Default
        if lyrics_text:
            # Use scoring service for theme analysis
            keywords_df = cache_service.get_cached_keywords()
            if not keywords_df.empty:
                phrases = [(row['keyword_text'], row['weight']) for _, row in keywords_df.iterrows() if row['keyword_type'] == 'phrase']
                keywords = [(row['keyword_text'], row['weight']) for _, row in keywords_df.iterrows() if row['keyword_type'] == 'keyword']
                theme_relevance = scoring_service.score_theme_relevance(lyrics_text, keywords, phrases)
                tema_score = max(1, min(5, int(theme_relevance / 20) + 1))  # Convert 0-100 to 1-5
            else:
                # Fallback to simple keyword matching
                theme_keywords = ['waktu', 'bersama', 'harta', 'berharga', 'keluarga', 'kasih', 'berkat']
                matches = sum(1 for keyword in theme_keywords if keyword.lower() in lyrics_text.lower())
                tema_score = min(5, max(1, matches + 1))
        else:
            # Analyze title only
            theme_keywords = ['waktu', 'bersama', 'harta', 'berharga', 'keluarga']
            matches = sum(1 for keyword in theme_keywords if keyword.lower() in title.lower())
            tema_score = min(5, max(2, matches + 2))

        # 2. LIRIK - Kekuatan Lirik (Advanced analysis)
        lirik_score = 3  # Default
        if lyrics_text:
            # Use scoring service for lyrical quality
            lirik_quality = scoring_service.score_lyrical_quality(lyrics_text)
            lirik_score = max(1, min(5, int(lirik_quality / 20) + 1))  # Convert 0-100 to 1-5
        else:
            # Analyze title structure and length
            if len(title) > 15 and any(word in title.lower() for word in ['kasih', 'berkat', 'bersama']):
                lirik_score = 4
            elif len(title) > 10:
                lirik_score = 3
            else:
                lirik_score = 2

        # 3. MUSIK - Kekayaan Musik (Advanced analysis)
        musik_score = 3  # Default
        if chords_text:
            # Parse chords and analyze
            chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
            if chord_list:
                musik_quality = scoring_service.score_harmonic_richness(chord_list)
                musik_score = musik_quality  # Already 1-5 scale
            else:
                musik_score = 3
        else:
            # Default based on composer info
            musik_score = 4 if composer else 3

        # Return only the 3 AI-analyzable rubrics
        # kreativ and jemaat require manual assessment
        suggestions = {
            'tema': tema_score,
            'lirik': lirik_score,
            'musik': musik_score
        }

        return suggestions

    except Exception as e:
        # Return safe defaults if analysis fails
        return {
            'tema': 3,
            'lirik': 3,
            'musik': 3
        }

    except Exception as e:
        # Return safe defaults if analysis fails
        return {
            'tema': 3,
            'lirik': 3,
            'musik': 3
        }

def render_music_analysis(chords_text, title):
    """Render detailed music analysis"""
    if not chords_text:
        st.warning("Tidak ada data chord untuk dianalisis")
        return

    # Parse chords
    chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
    unique_chords = list(dict.fromkeys(chord_list))

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 🎼 Analisis Harmoni")

        # Basic metrics
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Total Chord", len(chord_list))
            st.metric("Chord Unik", len(unique_chords))

        with metric_col2:
            # Chord variety ratio
            variety_ratio = len(unique_chords) / max(1, len(chord_list))
            st.metric("Rasio Variasi", f"{variety_ratio:.2f}")

            # Repetition analysis
            if variety_ratio > 0.7:
                st.success("✅ Sangat variatif")
            elif variety_ratio > 0.5:
                st.info("⚠️ Cukup variatif")
            else:
                st.warning("❌ Banyak pengulangan")

        # Key detection (enhanced)
        st.markdown("**🔑 Deteksi Nada Dasar:**")
        key_analysis = analyze_key_signature(unique_chords)
        st.info(f"🎵 **Nada Dasar**: {key_analysis['key']}")
        st.caption(f"Confidence: {key_analysis['confidence']:.1%}")

        # Genre detection (enhanced)
        st.markdown("**🎭 Deteksi Genre:**")
        genre_analysis = analyze_genre(unique_chords, chord_list)
        st.info(f"🎪 **Genre**: {genre_analysis['genre']}")
        st.caption(f"Karakteristik: {genre_analysis['characteristics']}")

    with col2:
        st.markdown("#### 📈 Kompleksitas Musik")

        # Advanced complexity analysis
        extensions = sum(1 for chord in chord_list if any(ext in chord for ext in ['7', '9', '11', '13', 'sus', 'add']))
        slash_chords = sum(1 for chord in chord_list if '/' in chord)
        diminished = sum(1 for chord in chord_list if 'dim' in chord.lower())
        augmented = sum(1 for chord in chord_list if 'aug' in chord.lower())

        complexity_col1, complexity_col2 = st.columns(2)
        with complexity_col1:
            st.metric("Extended Chord", extensions)
            st.metric("Slash Chord", slash_chords)
        with complexity_col2:
            st.metric("Diminished", diminished)
            st.metric("Augmented", augmented)

        # Complexity score
        total_complex = extensions + slash_chords + diminished + augmented
        complexity_ratio = total_complex / max(1, len(chord_list))

        st.markdown("**🎯 Skor Kompleksitas:**")
        if complexity_ratio > 0.3:
            st.error(f"❌ Sangat Kompleks ({complexity_ratio:.1%})")
            st.caption("Mungkin sulit untuk jemaat")
        elif complexity_ratio > 0.15:
            st.warning(f"⚠️ Cukup Kompleks ({complexity_ratio:.1%})")
            st.caption("Perlu latihan untuk jemaat")
        else:
            st.success(f"✅ Sederhana ({complexity_ratio:.1%})")
            st.caption("Mudah dimainkan jemaat")

        # Chord progression display
        st.markdown("**🎹 Progesi Chord:**")
        if len(unique_chords) <= 8:
            st.code(" → ".join(unique_chords))
        else:
            st.code(" → ".join(unique_chords[:8]) + " → ...")

        # Chord frequency
        chord_freq = {}
        for chord in chord_list:
            chord_freq[chord] = chord_freq.get(chord, 0) + 1

        most_used = sorted(chord_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        st.markdown("**📊 Chord Paling Sering:**")
        for chord, freq in most_used:
            st.markdown(f"• **{chord}**: {freq}x")

def analyze_key_signature(unique_chords):
    """Analyze key signature from chord progression"""
    # Simplified key detection
    major_keys = {
        'C': ['C', 'Dm', 'Em', 'F', 'G', 'Am'],
        'G': ['G', 'Am', 'Bm', 'C', 'D', 'Em'],
        'D': ['D', 'Em', 'F#m', 'G', 'A', 'Bm'],
        'A': ['A', 'Bm', 'C#m', 'D', 'E', 'F#m'],
        'E': ['E', 'F#m', 'G#m', 'A', 'B', 'C#m'],
        'F': ['F', 'Gm', 'Am', 'Bb', 'C', 'Dm']
    }

    key_scores = {}
    for key, expected_chords in major_keys.items():
        score = 0
        for chord in unique_chords:
            # Simple matching (ignoring extensions)
            base_chord = chord.split('/')[0].replace('7', '').replace('sus', '').replace('add', '')
            if base_chord in expected_chords:
                score += 1
        key_scores[key] = score / max(1, len(unique_chords))

    best_key = max(key_scores, key=key_scores.get)
    confidence = key_scores[best_key]

    return {
        'key': best_key,
        'confidence': confidence
    }

def analyze_genre(unique_chords, chord_list):
    """Analyze musical genre from chord characteristics"""
    # Count characteristics
    has_7th = any('7' in chord for chord in chord_list)
    has_sus = any('sus' in chord for chord in chord_list)
    has_slash = any('/' in chord for chord in chord_list)
    has_extended = any(ext in chord for chord in chord_list for ext in ['9', '11', '13', 'add'])

    chord_count = len(unique_chords)

    # Genre classification
    if has_extended and has_7th and chord_count > 6:
        return {
            'genre': 'Jazz/Contemporary Gospel',
            'characteristics': 'Extended chords, complex harmony'
        }
    elif has_7th and has_sus:
        return {
            'genre': 'Contemporary Christian',
            'characteristics': 'Modern harmony, worship style'
        }
    elif chord_count <= 4 and not has_7th:
        return {
            'genre': 'Folk/Traditional',
            'characteristics': 'Simple, easy to sing'
        }
    elif has_slash or has_sus:
        return {
            'genre': 'Pop/Contemporary',
            'characteristics': 'Modern progression, accessible'
        }
    else:
        return {
            'genre': 'Contemporary',
            'characteristics': 'Balanced complexity'
        }

def render_analysis_visualizations(song_data):
    """Render analysis visualizations"""
    st.markdown("#### 📊 Visualisasi Analisis")

    # Get AI suggestions and manual guidelines
    ai_suggestions, ai_explanations = build_suggestions_with_explanations(song_data)
    manual_guidelines = build_manual_assessment_guidelines(song_data)

    # Create comprehensive scoring data
    rubrics_df = cache_service.get_cached_rubrics()

    viz_col1, viz_col2 = st.columns([1, 1])

    with viz_col1:
        # Spider Chart (using plotly if available, otherwise bar chart)
        st.markdown("**🕸️ Spider Chart Analisis**")

        try:
            import plotly.graph_objects as go

            categories = []
            ai_scores = []
            max_scores = []

            for _, rubric in rubrics_df.iterrows():
                categories.append(rubric['aspect_name'])
                score = ai_suggestions.get(rubric['rubric_key'], 3)  # Default 3 for manual rubrics
                ai_scores.append(score)
                max_scores.append(int(rubric['max_score']))

            # Close the radar chart
            categories.append(categories[0])
            ai_scores.append(ai_scores[0])
            max_scores.append(max_scores[0])

            fig = go.Figure()

            fig.add_trace(go.Scatterpolar(
                r=ai_scores,
                theta=categories,
                fill='toself',
                name='Skor AI',
                line_color='blue'
            ))

            fig.add_trace(go.Scatterpolar(
                r=max_scores,
                theta=categories,
                fill='toself',
                name='Skor Maksimal',
                line_color='red',
                opacity=0.3
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5]
                    )),
                showlegend=True,
                title="Spider Chart Analisis Rubrik"
            )

            st.plotly_chart(fig, width=True)

        except ImportError:
            # Fallback to bar chart
            import pandas as pd

            chart_data = []
            for _, rubric in rubrics_df.iterrows():
                score = ai_suggestions.get(rubric['rubric_key'], 3)
                chart_data.append({
                    'Kriteria': rubric['aspect_name'],
                    'Skor AI': score,
                    'Skor Maksimal': int(rubric['max_score'])
                })

            df = pd.DataFrame(chart_data)
            st.bar_chart(df.set_index('Kriteria'))
            st.caption("📊 Analisis AI untuk setiap kriteria penilaian")

    with viz_col2:
        # Stacked analysis
        st.markdown("**📈 Analisis Bertingkat**")

        # Theme analysis breakdown
        lyrics_text = song_data.get('lyrics_text', '')
        if lyrics_text:
            theme_breakdown = {
                'Tema Utama': 0,
                'Tema Pendukung': 0,
                'Kata Kunci': 0,
                'Relevansi': 0
            }

            # Simple theme scoring
            main_keywords = ['waktu', 'bersama', 'harta', 'berharga']
            support_keywords = ['keluarga', 'kasih', 'berkat', 'rumah']
            key_phrases = ['waktu bersama', 'harta berharga']

            for keyword in main_keywords:
                if keyword in lyrics_text.lower():
                    theme_breakdown['Tema Utama'] += 1

            for keyword in support_keywords:
                if keyword in lyrics_text.lower():
                    theme_breakdown['Tema Pendukung'] += 1

            for phrase in key_phrases:
                if phrase in lyrics_text.lower():
                    theme_breakdown['Kata Kunci'] += 2

            # Calculate relevance
            total_words = len(lyrics_text.split())
            total_theme_words = sum(theme_breakdown.values())
            theme_breakdown['Relevansi'] = min(10, (total_theme_words / total_words) * 100)

            # Display as metrics
            for category, score in theme_breakdown.items():
                if category == 'Relevansi':
                    st.metric(category, f"{score:.1f}%")
                else:
                    st.metric(category, score)

        # Music complexity breakdown
        chords_text = song_data.get('chords_list', '')
        if chords_text:
            st.markdown("**🎵 Breakdown Kompleksitas Musik**")

            chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]

            complexity_breakdown = {
                'Basic Chords': 0,
                'Extended Chords': 0,
                'Slash Chords': 0,
                'Complex Chords': 0
            }

            for chord in chord_list:
                if any(ext in chord for ext in ['7', '9', '11', '13']):
                    complexity_breakdown['Extended Chords'] += 1
                elif '/' in chord:
                    complexity_breakdown['Slash Chords'] += 1
                elif any(comp in chord.lower() for comp in ['dim', 'aug', 'sus']):
                    complexity_breakdown['Complex Chords'] += 1
                else:
                    complexity_breakdown['Basic Chords'] += 1

            for category, count in complexity_breakdown.items():
                st.metric(category, count)

def render_key_insights(song_data):
    """Render key insights and recommendations"""
    st.markdown("#### 🔍 Insight Kunci & Rekomendasi")

    # Get comprehensive analysis
    ai_suggestions, ai_explanations = build_suggestions_with_explanations(song_data)
    manual_guidelines = build_manual_assessment_guidelines(song_data)

    # Generate insights
    insights = []
    recommendations = []

    # Analyze AI suggestions
    if ai_suggestions:
        avg_ai_score = sum(ai_suggestions.values()) / len(ai_suggestions)

        if avg_ai_score >= 4:
            insights.append("🌟 **Kualitas Tinggi**: Lagu menunjukkan kualitas yang sangat baik dalam aspek yang dapat dianalisis AI")
        elif avg_ai_score >= 3:
            insights.append("✅ **Kualitas Baik**: Lagu memiliki kualitas yang solid dalam aspek tema, lirik, dan musik")
        else:
            insights.append("⚠️ **Perlu Perbaikan**: Beberapa aspek memerlukan perhatian lebih")

        # Specific insights per rubric
        for rubric_key, score in ai_suggestions.items():
            if score >= 4:
                if rubric_key == 'tema':
                    insights.append("🎯 **Tema Kuat**: Sangat relevan dengan tema 'Waktu Bersama Harta Berharga'")
                elif rubric_key == 'lirik':
                    insights.append("📝 **Lirik Berkualitas**: Struktur dan kualitas lirik sangat baik")
                elif rubric_key == 'musik':
                    insights.append("🎵 **Musik Kaya**: Harmoni dan progesi chord sangat menarik")
            elif score <= 2:
                if rubric_key == 'tema':
                    recommendations.append("🎯 Perkuat relevansi dengan tema utama lomba")
                elif rubric_key == 'lirik':
                    recommendations.append("📝 Tingkatkan kualitas puitis dan struktur lirik")
                elif rubric_key == 'musik':
                    recommendations.append("🎵 Variasikan progesi chord untuk kekayaan musik")

    # Analyze manual guidelines
    lyrics_text = song_data.get('lyrics_text', '')
    chords_text = song_data.get('chords_list', '')

    if lyrics_text:
        word_count = len(lyrics_text.split())
        if word_count < 50:
            recommendations.append("📏 Pertimbangkan untuk memperpanjang lirik agar lebih ekspresif")
        elif word_count > 200:
            recommendations.append("✂️ Pertimbangkan untuk mempersingkat lirik agar mudah diingat")

    if chords_text:
        chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
        unique_chords = list(dict.fromkeys(chord_list))

        if len(unique_chords) > 8:
            recommendations.append("🎼 Banyak chord unik - pastikan tidak terlalu sulit untuk jemaat")
        elif len(unique_chords) < 4:
            recommendations.append("🎹 Pertimbangkan menambah variasi chord untuk kekayaan musik")

    # Display insights
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**💡 Insight Utama:**")
        if insights:
            for insight in insights:
                st.markdown(f"• {insight}")
        else:
            st.info("Tidak ada insight khusus yang terdeteksi")

        # Contest-specific insights
        st.markdown("**🏆 Insight Khusus Lomba:**")
        st.markdown("• 🎯 **Tema**: 'Waktu Bersama Harta Berharga' - fokus pada kebersamaan keluarga")
        st.markdown("• 📖 **Ayat**: Efesus 5:15-16 - tentang kebijaksanaan menggunakan waktu")
        st.markdown("• 👨‍👩‍👧‍👦 **Target**: Semua usia dalam jemaat GKI Perumnas")

    with col2:
        st.markdown("**🚀 Rekomendasi Perbaikan:**")
        if recommendations:
            for rec in recommendations:
                st.markdown(f"• {rec}")
        else:
            st.success("✅ Tidak ada rekomendasi khusus - lagu sudah baik!")

        # General recommendations
        st.markdown("**📋 Checklist Umum:**")
        st.markdown("• ✅ Apakah mudah dinyanyikan jemaat?")
        st.markdown("• ✅ Apakah pesan tersampaikan jelas?")
        st.markdown("• ✅ Apakah musik mendukung lirik?")
        st.markdown("• ✅ Apakah sesuai dengan tema lomba?")

        # Originality check suggestion
        st.markdown("**🔍 Cek Orisinalitas:**")
        if lyrics_text:
            search_query = f'"{song_data.get("title", "")}" lyrics'
            google_search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            st.markdown(f"[🔍 Cek di Google]({google_search_url})")

        if chords_text:
            chord_search = " ".join(chords_text.split()[:4])  # First 4 chords
            chord_search_url = f"https://www.google.com/search?q={chord_search.replace(' ', '+')}+chord+progression"
            st.markdown(f"[🎼 Cek Progesi Chord]({chord_search_url})")

# Duplicate function removed - using the one above

def auto_save_notes(judge_id: int, song_id: int, notes: str):
    """Auto-save notes when changed"""
    try:
        # Get existing evaluation
        existing_evaluations = cache_service.get_cached_evaluations(judge_id=judge_id, song_id=song_id)

        if not existing_evaluations.empty:
            # Update existing evaluation
            existing_eval = existing_evaluations.iloc[0]

            # Update evaluation with new notes
            db_service.update_evaluation(
                existing_eval['id'],
                rubric_scores=existing_eval['rubric_scores'],
                total_score=existing_eval['total_score'],
                notes=notes
            )
        else:
            # Create new evaluation with notes only
            db_service.create_evaluation(
                judge_id=judge_id,
                song_id=song_id,
                rubric_scores={},
                total_score=0,
                notes=notes
            )

        # Clear cache to refresh data
        cache_service.clear_evaluations_cache()

    except Exception as e:
        st.error(f"Error auto-saving notes: {e}")

def build_suggestions_with_explanations(song_data):
    """Build AI suggestions with explanations for each rubric"""
    try:
        # Get basic suggestions (only tema, lirik, musik)
        suggestions = build_suggestions(song_data)

        # Generate detailed explanations
        explanations = {}
        title = song_data.get('title', '')
        lyrics_text = song_data.get('lyrics_text', '')
        chords_text = song_data.get('chords_list', '')

        # Tema explanation
        if 'tema' in suggestions:
            if lyrics_text:
                theme_keywords = ['waktu', 'bersama', 'harta', 'berharga', 'keluarga']
                found_keywords = [kw for kw in theme_keywords if kw.lower() in lyrics_text.lower()]
                if found_keywords:
                    explanations['tema'] = f"Skor {suggestions['tema']}: Ditemukan kata kunci tema: {', '.join(found_keywords)}"
                else:
                    explanations['tema'] = f"Skor {suggestions['tema']}: Analisis semantik dari teks lirik"
            else:
                explanations['tema'] = f"Skor {suggestions['tema']}: Analisis dari judul '{title}'"

        # Lirik explanation
        if 'lirik' in suggestions:
            if lyrics_text:
                word_count = len(lyrics_text.split())
                explanations['lirik'] = f"Skor {suggestions['lirik']}: Analisis kualitas lirik ({word_count} kata)"
            else:
                explanations['lirik'] = f"Skor {suggestions['lirik']}: Analisis dari judul dan struktur"

        # Musik explanation
        if 'musik' in suggestions:
            if chords_text:
                chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
                unique_chords = len(set(chord_list))
                explanations['musik'] = f"Skor {suggestions['musik']}: Analisis harmoni ({unique_chords} chord unik)"
            else:
                explanations['musik'] = f"Skor {suggestions['musik']}: Estimasi berdasarkan informasi lagu"

        return suggestions, explanations

    except Exception as e:
        # Return safe defaults if analysis fails
        return {
            'tema': 3,
            'lirik': 3,
            'musik': 3
        }, {
            'tema': 'Skor default: Analisis tidak tersedia',
            'lirik': 'Skor default: Analisis tidak tersedia',
            'musik': 'Skor default: Analisis tidak tersedia'
        }

def build_suggestions_with_explanations(song_data):
    """Build AI suggestions with explanations for each rubric"""
    try:
        # Get basic suggestions (only tema, lirik, musik)
        suggestions = build_suggestions(song_data)

        # Generate detailed explanations
        explanations = {}
        title = song_data.get('title', '')
        lyrics_text = song_data.get('lyrics_text', '')
        chords_text = song_data.get('chords_list', '')

        # Tema explanation
        if 'tema' in suggestions:
            if lyrics_text:
                theme_keywords = ['waktu', 'bersama', 'harta', 'berharga', 'keluarga']
                found_keywords = [kw for kw in theme_keywords if kw.lower() in lyrics_text.lower()]
                if found_keywords:
                    explanations['tema'] = f"Skor {suggestions['tema']}: Ditemukan kata kunci tema: {', '.join(found_keywords)}"
                else:
                    explanations['tema'] = f"Skor {suggestions['tema']}: Analisis semantik dari teks lirik"
            else:
                explanations['tema'] = f"Skor {suggestions['tema']}: Analisis dari judul '{title}'"

        # Lirik explanation
        if 'lirik' in suggestions:
            if lyrics_text:
                word_count = len(lyrics_text.split())
                line_count = len(lyrics_text.split('\n'))
                explanations['lirik'] = f"Skor {suggestions['lirik']}: Analisis {word_count} kata, {line_count} baris, struktur puitis"
            else:
                explanations['lirik'] = f"Skor {suggestions['lirik']}: Analisis dari struktur judul"

        # Musik explanation
        if 'musik' in suggestions:
            if chords_text:
                chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
                unique_chords = list(dict.fromkeys(chord_list))
                extensions = sum(1 for chord in chord_list if any(ext in chord for ext in ['7', '9', 'sus', 'add']))
                explanations['musik'] = f"Skor {suggestions['musik']}: {len(unique_chords)} chord unik, {extensions} extended chord"
            else:
                explanations['musik'] = f"Skor {suggestions['musik']}: Estimasi berdasarkan informasi lagu"

        # Add manual assessment notes for non-AI rubrics
        rubrics_df = cache_service.get_cached_rubrics()
        for _, rubric in rubrics_df.iterrows():
            rubric_key = rubric['rubric_key']
            if rubric_key not in suggestions:
                if rubric_key == 'kreativ':
                    explanations[rubric_key] = "⚠️ Kreativitas & Orisinalitas memerlukan penilaian manual juri"
                elif rubric_key == 'jemaat':
                    explanations[rubric_key] = "⚠️ Kesesuaian untuk Jemaat memerlukan penilaian manual juri"
                else:
                    explanations[rubric_key] = "⚠️ Kriteria ini memerlukan penilaian manual juri"

        return suggestions, explanations

    except Exception as e:
        # Return safe defaults for AI-analyzable rubrics only
        default_suggestions = {
            'tema': 3,
            'lirik': 3,
            'musik': 3
        }
        default_explanations = {
            'tema': 'Skor default (analisis gagal)',
            'lirik': 'Skor default (analisis gagal)',
            'musik': 'Skor default (analisis gagal)',
            'kreativ': '⚠️ Kreativitas & Orisinalitas memerlukan penilaian manual juri',
            'jemaat': '⚠️ Kesesuaian untuk Jemaat memerlukan penilaian manual juri'
        }
        return default_suggestions, default_explanations

def check_form_schedule():
    """Check if form is open based on schedule configuration"""
    try:
        config = cache_service.get_cached_config()

        # Get current time
        from datetime import datetime
        import pytz

        timezone_str = config.get('TIMEZONE', 'Asia/Jakarta')
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)

        # Get schedule configuration
        form_open_str = config.get('FORM_OPEN_DATETIME', '2024-01-01 00:00:00')
        form_close_str = config.get('FORM_CLOSE_DATETIME', '2024-12-31 23:59:59')
        winner_announce_str = config.get('WINNER_ANNOUNCE_DATETIME', '2025-01-01 00:00:00')

        # Parse datetime strings
        form_open = tz.localize(datetime.strptime(form_open_str, '%Y-%m-%d %H:%M:%S'))
        form_close = tz.localize(datetime.strptime(form_close_str, '%Y-%m-%d %H:%M:%S'))
        winner_announce = tz.localize(datetime.strptime(winner_announce_str, '%Y-%m-%d %H:%M:%S'))

        # Check status
        is_before_open = current_time < form_open
        is_after_close = current_time > form_close
        is_winner_time = current_time >= winner_announce
        is_form_open = config.get('FORM_OPEN', 'True').lower() == 'true'

        return {
            'is_before_open': is_before_open,
            'is_after_close': is_after_close,
            'is_winner_time': is_winner_time,
            'is_form_open': is_form_open,
            'form_open': form_open,
            'form_close': form_close,
            'winner_announce': winner_announce,
            'current_time': current_time,
            'can_evaluate': is_form_open and not is_before_open and not is_after_close,
            'can_show_winners': is_winner_time or is_form_open  # Show winners if time or manual override
        }

    except Exception as e:
        # Fallback to basic FORM_OPEN check
        config = cache_service.get_cached_config()
        is_form_open = config.get('FORM_OPEN', 'True').lower() == 'true'

        return {
            'is_before_open': False,
            'is_after_close': False,
            'is_winner_time': True,
            'is_form_open': is_form_open,
            'can_evaluate': is_form_open,
            'can_show_winners': is_form_open,
            'error': str(e)
        }

def build_manual_assessment_guidelines(song_data):
    """Build manual assessment guidelines for Kreativitas & Jemaat"""
    guidelines = {}

    title = song_data.get('title', '')
    lyrics_text = song_data.get('lyrics_text', '')
    chords_text = song_data.get('chords_list', '')
    composer = song_data.get('composer', '')

    # Contest theme and verse for reference
    contest_theme = "WAKTU BERSAMA HARTA BERHARGA"
    contest_verse = "Efesus 5:15-16"

    # KREATIVITAS & ORISINALITAS Guidelines
    creativity_factors = []

    # 1. Unique title/concept
    common_words = ['kasih', 'cinta', 'Tuhan', 'Allah', 'berkat', 'syukur']
    if not any(word in title.lower() for word in common_words):
        creativity_factors.append("✅ Judul unik, tidak menggunakan kata-kata umum")
    else:
        creativity_factors.append("⚠️ Judul menggunakan kata-kata yang umum")

    # 2. Musical complexity
    if chords_text:
        chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
        unique_chords = list(dict.fromkeys(chord_list))
        extensions = sum(1 for chord in chord_list if any(ext in chord for ext in ['7', '9', 'sus', 'add']))

        if len(unique_chords) > 6:
            creativity_factors.append(f"✅ Variasi chord kaya ({len(unique_chords)} chord unik)")
        elif len(unique_chords) > 4:
            creativity_factors.append(f"⚠️ Variasi chord cukup ({len(unique_chords)} chord unik)")
        else:
            creativity_factors.append(f"❌ Variasi chord terbatas ({len(unique_chords)} chord unik)")

        if extensions > 0:
            creativity_factors.append(f"✅ Menggunakan extended chord ({extensions} chord)")
        else:
            creativity_factors.append("⚠️ Tidak menggunakan extended chord")
    else:
        creativity_factors.append("❓ Data chord tidak tersedia untuk analisis")

    # 3. Lyrical creativity
    if lyrics_text:
        # Check for metaphors, imagery
        imagery_words = ['cahaya', 'terang', 'jalan', 'rumah', 'hati', 'jiwa', 'mata', 'tangan']
        imagery_count = sum(1 for word in imagery_words if word in lyrics_text.lower())

        if imagery_count > 3:
            creativity_factors.append(f"✅ Kaya akan imagery dan metafora ({imagery_count} kata)")
        elif imagery_count > 1:
            creativity_factors.append(f"⚠️ Cukup menggunakan imagery ({imagery_count} kata)")
        else:
            creativity_factors.append("❌ Kurang menggunakan imagery dan metafora")

        # Check for repetition patterns
        lines = lyrics_text.split('\n')
        unique_lines = len(set(line.strip().lower() for line in lines if line.strip()))
        total_lines = len([line for line in lines if line.strip()])

        if total_lines > 0:
            repetition_ratio = unique_lines / total_lines
            if repetition_ratio > 0.8:
                creativity_factors.append("✅ Struktur lirik variatif, minim pengulangan")
            elif repetition_ratio > 0.6:
                creativity_factors.append("⚠️ Struktur lirik cukup variatif")
            else:
                creativity_factors.append("❌ Banyak pengulangan dalam lirik")
    else:
        creativity_factors.append("❓ Teks lirik tidak tersedia untuk analisis")

    guidelines['kreativ'] = {
        'title': 'Kreativitas & Orisinalitas',
        'factors': creativity_factors,
        'suggestion': "Pertimbangkan: keunikan konsep, kompleksitas musik, kreativitas lirik, dan orisinalitas keseluruhan"
    }

    # KESESUAIAN UNTUK JEMAAT Guidelines
    congregation_factors = []

    # 1. Vocal range analysis (simplified)
    congregation_factors.append("🎵 Periksa range vokal: apakah mudah dijangkau jemaat?")
    congregation_factors.append("🎵 Periksa interval melodi: apakah ada lompatan yang sulit?")

    # 2. Chord complexity for congregation
    if chords_text:
        chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
        difficult_chords = sum(1 for chord in chord_list if any(ext in chord for ext in ['7', '9', 'sus', 'add', 'dim', 'aug']))

        if difficult_chords == 0:
            congregation_factors.append("✅ Semua chord dasar, mudah dimainkan")
        elif difficult_chords < len(chord_list) * 0.3:
            congregation_factors.append(f"⚠️ Beberapa chord kompleks ({difficult_chords} dari {len(chord_list)})")
        else:
            congregation_factors.append(f"❌ Banyak chord kompleks ({difficult_chords} dari {len(chord_list)})")
    else:
        congregation_factors.append("❓ Data chord tidak tersedia untuk analisis")

    # 3. Lyrical accessibility
    if lyrics_text:
        # Check for difficult words
        difficult_words = ['epistemologi', 'hermeneutik', 'eksegesis', 'pneumatologi']
        has_difficult = any(word in lyrics_text.lower() for word in difficult_words)

        if not has_difficult:
            congregation_factors.append("✅ Bahasa mudah dipahami jemaat")
        else:
            congregation_factors.append("⚠️ Menggunakan istilah teologi yang mungkin sulit")

        # Check sentence length
        sentences = lyrics_text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

        if avg_sentence_length < 8:
            congregation_factors.append("✅ Kalimat pendek, mudah diingat")
        elif avg_sentence_length < 12:
            congregation_factors.append("⚠️ Panjang kalimat sedang")
        else:
            congregation_factors.append("❌ Kalimat panjang, mungkin sulit diingat")
    else:
        congregation_factors.append("❓ Teks lirik tidak tersedia untuk analisis")

    # 4. Theme accessibility
    congregation_factors.append("👨‍👩‍👧‍👦 Apakah tema 'Waktu Bersama Harta Berharga' mudah dipahami semua usia?")
    congregation_factors.append("🎯 Apakah pesan dapat diterapkan dalam kehidupan sehari-hari jemaat?")

    guidelines['jemaat'] = {
        'title': 'Kesesuaian untuk Jemaat',
        'factors': congregation_factors,
        'suggestion': "Pertimbangkan: kemudahan vokal, kompleksitas musik, aksesibilitas bahasa, dan relevansi untuk semua usia"
    }

    return guidelines

def fix_corrupted_scores():
    """Fix corrupted scores in database (admin only)"""
    try:
        with st.spinner("🔍 Checking for corrupted scores..."):
            # Get all evaluations
            evaluations_df = db_service.get_evaluations()

            if evaluations_df.empty:
                st.success("✅ No evaluations found")
                return

            corrupted_count = 0
            fixed_count = 0

            # Check for corrupted scores (> 25 means scale was incorrectly calculated)
            # But actually, let's check if there are any real issues
            # Max score should be 5 rubrics × 5 points = 25
            corrupted_evals = evaluations_df[evaluations_df['total_score'] > 25]
            corrupted_count = len(corrupted_evals)

            if corrupted_count == 0:
                st.success("🎉 No corrupted scores found! Database is clean.")
                st.info("💡 All scores are within the expected range (0-25)")
                return

            st.warning(f"🚨 Found {corrupted_count} scores above maximum (25)")
            st.info("💡 These scores might be from old calculation logic")

            # Show details
            for _, eval_row in corrupted_evals.iterrows():
                eval_id = eval_row['id']
                total_score = eval_row['total_score']
                # Don't divide by 4 - the scores are already correct!
                # The issue was in display, not in storage
                corrected_score = total_score

                st.write(f"- ID {eval_id}: {total_score} (already correct)")

            if st.button("🔧 Refresh Cache", type="primary"):
                # Just refresh cache instead of "fixing" scores
                cache_service.clear_evaluations_cache()
                st.success("✅ Cache refreshed!")
                st.rerun()

                # Update the evaluation
                success = db_service.update_evaluation(
                    eval_id=eval_id,
                    rubric_scores=eval_row.get('rubric_scores', {}),
                    total_score=corrected_score,
                    notes=eval_row.get('notes', '')
                )

                if success:
                    fixed_count += 1

                progress_bar.progress((i + 1) / len(corrupted_evals))

                # Clear cache
                cache_service.clear_evaluations_cache()

                st.success(f"✅ Fixed {fixed_count}/{corrupted_count} corrupted scores!")
                st.rerun()

    except Exception as e:
        st.error(f"❌ Error fixing scores: {e}")

def setup_missing_config():
    """Setup missing configuration keys (admin only)"""
    try:
        with st.spinner("⚙️ Setting up missing configuration..."):
            # Get current config
            current_config = db_service.get_config()

            # Define required configurations with defaults
            required_configs = {
                'SUBMISSION_START_DATETIME': '2025-08-01 00:00:00',  # Periode submission peserta
                'SUBMISSION_END_DATETIME': '2025-08-31 23:59:59',    # Periode submission peserta
                'FORM_OPEN_DATETIME': '2025-09-01 00:00:00',         # Periode penilaian juri
                'FORM_CLOSE_DATETIME': '2025-09-30 23:59:59',        # Periode penilaian juri
                'WINNER_ANNOUNCE_DATETIME': '2025-10-15 00:00:00',   # Pengumuman pemenang
                'FORM_OPEN': 'True',
                'TIMEZONE': 'Asia/Jakarta',
                'CERTIFICATE_MODE': 'STORAGE',  # STORAGE or GENERATE
                'CERTIFICATE_BUCKET': 'song-contest-files',
                'CERTIFICATE_FOLDER': 'certificates'
            }

            added_count = 0

            for key, default_value in required_configs.items():
                if key not in current_config:
                    # Add missing config
                    success = db_service.update_config(key, default_value)
                    if success:
                        st.write(f"✅ Added: {key} = {default_value}")
                        added_count += 1
                    else:
                        st.write(f"❌ Failed to add: {key}")
                else:
                    st.write(f"ℹ️ Exists: {key} = {current_config[key]}")

            if added_count > 0:
                # Clear cache
                st.cache_data.clear()
                st.success(f"✅ Added {added_count} missing configurations!")
                st.rerun()
            else:
                st.info("ℹ️ All required configurations already exist")

    except Exception as e:
        st.error(f"❌ Error setting up config: {e}")

def render_admin_impersonation_sidebar(current_user):
    """Render judge selection controls in sidebar for both admin and judge"""
    st.sidebar.markdown("---")

    user_role = current_user.get('role', 'judge')

    if user_role == 'admin':
        # Admin can impersonate any judge
        st.sidebar.markdown("### 🎭 Admin: Login as Judge")

        # Get all judges for dropdown
        try:
            judges_df = cache_service.get_cached_judges()
        except Exception as e:
            st.error(f"❌ Error loading judges: {e}")
            judges_df = pd.DataFrame()

        # Filter only judges (exclude admin role)
        judge_only_df = judges_df[judges_df['role'] == 'judge'] if not judges_df.empty else pd.DataFrame()

        # Sort judges alphabetically by name
        if not judge_only_df.empty:
            judge_only_df = judge_only_df.sort_values('name')
            judge_names = judge_only_df['name'].tolist()
            judge_options = ["[Login as Admin]"] + judge_names
        else:
            judge_options = ["[Login as Admin]"]

        # Default to "[Login as Admin]" for admin
        default_index = 0

        # Force refresh if needed
        if st.sidebar.button("🔄 Refresh Judges List", help="Click if dropdown is empty"):
            st.rerun()

        # Admin impersonation dropdown in main content
        st.markdown("### 🎭 ADMIN: Pilih Juri untuk Impersonation")
        selected_judge = st.selectbox(
            "Pilih juri:",
            options=judge_options,
            index=default_index,
            key=f"main_judge_select_{len(judge_options)}"
        )

        # Save to session state for impersonation to work
        if selected_judge != st.session_state.get('impersonate_judge'):
            st.session_state.impersonate_judge = selected_judge
            st.rerun()  # Force refresh to apply impersonation

        # Show current mode with simple styling
        if selected_judge != "[Login as Admin]" and not judge_only_df.empty:
            judge_row = judge_only_df[judge_only_df['name'] == selected_judge].iloc[0]
            st.sidebar.success(f"🎭 **Selected:** {judge_row['name']}")
        else:
            st.sidebar.info("🔧 **Mode:** Admin")

    else:
        # Judge - show current judge info (no dropdown needed)
        st.sidebar.markdown("### 👨‍⚖️ Juri Login")
        judge_name = current_user.get('judge_name', current_user.get('full_name', 'Unknown'))
        st.sidebar.markdown(f"""
        <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745; margin: 10px 0;">
            <strong>🎭 Login as: {judge_name}</strong>
        </div>
        """, unsafe_allow_html=True)

        # Set session state for consistency with admin impersonation
        st.session_state.impersonate_judge = judge_name

def render_progress_dashboard(judge_id):
    """Render progress dashboard showing evaluation completion status"""
    st.markdown("### 📊 Progress Penilaian")

    # Get all songs and evaluations
    songs_df = cache_service.get_cached_songs()
    rubrics_df = cache_service.get_cached_rubrics()
    total_rubrics = len(rubrics_df)

    # Sort songs by ID as integer for proper numerical ordering
    songs_df['id_int'] = pd.to_numeric(songs_df['id'], errors='coerce')
    songs_df = songs_df.sort_values('id_int')

    # Calculate progress for each song
    progress_data = []
    total_songs = len(songs_df)
    completed_songs = 0

    for _, song in songs_df.iterrows():
        evaluations = cache_service.get_cached_evaluations(judge_id=judge_id, song_id=song['id'])

        if not evaluations.empty:
            evaluation = evaluations.iloc[0]
            rubric_scores = evaluation['rubric_scores']

            if isinstance(rubric_scores, str):
                import json
                rubric_scores = json.loads(rubric_scores)
            elif not isinstance(rubric_scores, dict):
                rubric_scores = {}

            # Count completed rubrics
            completed_rubrics = len([score for score in rubric_scores.values() if score and score > 0])
            completion_percentage = (completed_rubrics / total_rubrics) * 100
            total_score = evaluation['total_score']

            if completed_rubrics == total_rubrics:
                status = "✅ Lengkap"
                status_color = "success"
                completed_songs += 1
            elif completed_rubrics > 0:
                status = f"🔄 Parsial ({completed_rubrics}/{total_rubrics})"
                status_color = "warning"
            else:
                status = "⏳ Belum dinilai"
                status_color = "error"
                completion_percentage = 0
                total_score = 0
        else:
            completed_rubrics = 0
            completion_percentage = 0
            total_score = 0
            status = "⏳ Belum dinilai"
            status_color = "error"

        progress_data.append({
            'song': song,
            'completed_rubrics': completed_rubrics,
            'total_rubrics': total_rubrics,
            'completion_percentage': completion_percentage,
            'total_score': total_score,
            'status': status,
            'status_color': status_color
        })

    # Overall progress
    overall_progress = (completed_songs / total_songs) * 100

    # Display overall progress
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Lagu", total_songs)
    with col2:
        st.metric("Sudah Lengkap", completed_songs, f"{completed_songs - (total_songs - completed_songs)}")
    with col3:
        st.metric("Belum Lengkap", total_songs - completed_songs)
    with col4:
        st.metric("Progress Keseluruhan", f"{overall_progress:.1f}%")

    # Progress bar
    st.progress(overall_progress / 100)

    # Show incomplete songs prominently
    incomplete_songs = [item for item in progress_data if item['completed_rubrics'] < item['total_rubrics']]

    if incomplete_songs:
        st.markdown("#### 🎯 Lagu yang Perlu Diselesaikan")

        for item in incomplete_songs:
            song = item['song']
            with st.expander(f"🎵 **{song['title']}** - {item['status']}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Pencipta:** {song.get('composer', 'Tidak diketahui')}")
                    if item['completed_rubrics'] > 0:
                        st.write(f"**Progress:** {item['completed_rubrics']}/{item['total_rubrics']} kriteria")
                        # Convert to 100-point scale for display
                        score_100 = (item['total_score'] / 25) * 100
                        st.write(f"**Skor Sementara:** {score_100:.1f}/100")
                    else:
                        st.write("**Status:** Belum ada penilaian")

                    # Progress bar for this song
                    st.progress(item['completion_percentage'] / 100)

                with col2:
                    if st.button(f"📝 Nilai Sekarang", key=f"eval_{song['id']}", type="primary"):
                        st.session_state.selected_song = song['title']
                        st.rerun()
    else:
        st.success("🎉 **Semua lagu sudah dinilai lengkap!**")
        # Controlled balloon animation - only show occasionally
        if should_show_balloons():
            st.balloons()

    st.markdown("---")

def render_evaluation_tab(current_user):
    """Render evaluation tab - focused on scoring only"""
    st.header("📝 Penilaian Lagu")

    # Check form schedule (allow admin to bypass)
    schedule_status = check_form_schedule()

    if not schedule_status['can_evaluate'] and current_user['role'] != 'admin':
        if schedule_status['is_before_open']:
            st.error("⏰ **Form belum dibuka**")
            st.info(f"Form akan dibuka pada: {schedule_status['form_open'].strftime('%d/%m/%Y %H:%M')}")
        elif schedule_status['is_after_close']:
            st.error("⏰ **Form sudah ditutup**")
            st.info(f"Form ditutup pada: {schedule_status['form_close'].strftime('%d/%m/%Y %H:%M')}")
        else:
            st.error("⏰ **Form penilaian tidak tersedia**")
            st.info("Silakan hubungi admin untuk informasi lebih lanjut")
        return

    # Get effective user (handles admin impersonation)
    effective_user = get_effective_user(current_user)

    # Get judge info from effective user
    judge_id = effective_user.get('judge_id')
    judge_name = effective_user.get('judge_name') or effective_user.get('full_name', 'Unknown Judge')

    if not judge_id:
        st.error("❌ Judge information not found. Please contact administrator.")
        st.json(effective_user)  # Debug info
        return

    # Render scoring interface directly
    render_penilaian_tab(judge_id, judge_name, effective_user)

def render_penilaian_tab(judge_id, judge_name, effective_user):
    """Render the evaluation/scoring tab"""

    # Create judge_info object for compatibility
    judge_info = {
        'id': judge_id,
        'name': judge_name
    }

    # Get songs and sort by song number/ID
    songs_df = cache_service.get_cached_songs()

    if songs_df.empty:
        st.warning("No songs found. Please add songs first.")
        return

    # Sort songs by ID as integer for proper numerical ordering
    songs_df['id_int'] = pd.to_numeric(songs_df['id'], errors='coerce')
    songs_df = songs_df.sort_values('id_int')

    # Show progress dashboard
    render_progress_dashboard(judge_id)

    # STEP 1: Song Selection with Status in Dropdown
    st.markdown("### 🎵 Langkah 1: Pilih Lagu")

    # Create song options with detailed status
    song_options = []
    song_mapping = {}

    # Get total rubrics count for completion check
    rubrics_df = cache_service.get_cached_rubrics()
    total_rubrics = len(rubrics_df)

    for _, song in songs_df.iterrows():
        # Check if song has been evaluated
        evaluations = cache_service.get_cached_evaluations(judge_id=judge_id, song_id=song['id'])

        if not evaluations.empty:
            # Song has been evaluated - check completion status
            evaluation = evaluations.iloc[0]
            total_score = evaluation['total_score']

            # Check how many rubrics have been scored
            rubric_scores = evaluation['rubric_scores']
            if isinstance(rubric_scores, str):
                import json
                rubric_scores = json.loads(rubric_scores)
            elif not isinstance(rubric_scores, dict):
                rubric_scores = {}

            # Count non-zero scores
            completed_rubrics = len([score for score in rubric_scores.values() if score and score > 0])

            # Determine status
            if completed_rubrics == total_rubrics:
                # Complete evaluation
                status_emoji = "✅"
                status_text = "Lengkap"
                # Convert to 100-point scale for display
                score_100 = (total_score / 25) * 100
                option_text = f"{status_emoji} {song['id']}. {song['title']} ({status_text} - Skor: {score_100:.1f}/100)"
            elif completed_rubrics > 0:
                # Partial evaluation
                status_emoji = "🔄"
                status_text = f"Parsial ({completed_rubrics}/{total_rubrics})"
                # Convert to 100-point scale for display
                score_100 = (total_score / 25) * 100
                option_text = f"{status_emoji} {song['id']}. {song['title']} ({status_text} - Skor: {score_100:.1f}/100)"
            else:
                # Has evaluation record but no scores
                status_emoji = "⏳"
                status_text = "Belum dinilai"
                option_text = f"{status_emoji} {song['id']}. {song['title']} ({status_text})"
        else:
            # Song not evaluated yet
            status_emoji = "⏳"
            status_text = "Belum dinilai"
            option_text = f"{status_emoji} {song['id']}. {song['title']} ({status_text})"

        # Add author if SHOW_AUTHOR is enabled
        config = cache_service.get_cached_config()
        show_author = config.get('SHOW_AUTHOR', 'False').lower() == 'true'
        if show_author and song.get('author'):
            option_text += f" - {song['author']}"

        song_options.append(option_text)
        song_mapping[option_text] = song['title']

    # Get default index
    default_index = 0
    if hasattr(st.session_state, 'selected_song') and st.session_state.selected_song:
        # Find the option that matches the selected song
        for i, option in enumerate(song_options):
            if song_mapping[option] == st.session_state.selected_song:
                default_index = i
                break

    selected_option = st.selectbox(
        "Pilih lagu untuk dinilai:",
        options=song_options,
        index=default_index,
        help="✅ = Lengkap, 🔄 = Parsial, ⏳ = Belum dinilai",
        key="judge_song_selector"
    )

    # Get actual song title from mapping
    selected_song = song_mapping[selected_option]

    # Force refresh if song changed
    if hasattr(st.session_state, 'selected_song') and st.session_state.selected_song != selected_song:
        # Clear any cached data when song changes
        if hasattr(st.session_state, 'audio_cache'):
            del st.session_state.audio_cache

    # Update session state
    st.session_state.selected_song = selected_song
    
    # Get song details
    song_data = songs_df[songs_df['title'] == selected_song].iloc[0]


    
    # STEP 2: Song Information & Media with Optimal Flow
    st.markdown("### 🎼 Langkah 2: Dengarkan & Pelajari Lagu")

    # Get configuration
    config = cache_service.get_cached_config()
    show_author = config.get('SHOW_AUTHOR', 'True').lower() == 'true'

    # Show song info prominently
    st.markdown(f"**🎵 {song_data['title']}**")
    if show_author:
        st.markdown(f"*Pencipta: {song_data['composer']}*")

    # Create tabs for better organization (removed redundant analysis tab)
    media_tab1, media_tab2, media_tab3 = st.tabs(["🎵 Audio", "📄 Notasi", "📝 Syair"])

    with media_tab1:
        st.markdown("**🎵 Dengarkan Lagu**")
        # Use simple render_audio_player with unique key
        render_audio_player(song_data, f"judge_{song_data['id']}")

    with media_tab2:
        st.markdown("**📄 Notasi Musik**")
        render_notation_viewer(song_data)

    with media_tab3:
        st.markdown("**📝 Syair Lagu**")
        render_lyrics_viewer(song_data)

    # Card-Based Rubric Evaluation Layout
    st.markdown("---")
    st.markdown("### 📊 Langkah 3: Penilaian & Analisis")

    # Use accordion mode only (simplified)
    ui_mode = "accordion"

    # Get existing evaluation data first
    existing_evaluations = cache_service.get_cached_evaluations(judge_id=judge_id, song_id=song_data['id'])
    existing_scores = {}
    is_final_submitted = False
    evaluation_id = None

    if not existing_evaluations.empty:
        existing_eval = existing_evaluations.iloc[0]
        evaluation_id = existing_eval['id']
        is_final_submitted = existing_eval.get('is_final_submitted', False)

        # Handle both dict and string formats
        scores_data = existing_eval['rubric_scores']
        if isinstance(scores_data, str):
            import json
            existing_scores = json.loads(scores_data)
        elif isinstance(scores_data, dict):
            existing_scores = scores_data

    # Check if evaluation is locked
    config = cache_service.get_cached_config()
    editing_locked = is_final_submitted and config.get('LOCK_FINAL_EVALUATIONS', 'True').lower() == 'true'

    # Get AI suggestions and explanations
    ai_suggestions, ai_explanations = build_suggestions_with_explanations(song_data)

    # Get manual assessment guidelines
    manual_guidelines = build_manual_assessment_guidelines(song_data)

    # Initialize scoring variables
    scores = {}
    total_weighted_score = 0

    # Custom CSS for card-based design
    st.markdown("""
    <style>
    .rubric-card {
        background: white;
        border: 1px solid #e1e5e9;
        border-radius: 12px;
        padding: 0;
        margin-bottom: 2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        transition: box-shadow 0.3s ease;
        overflow: hidden;
    }
    .rubric-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    .rubric-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem 1.5rem;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .rubric-header h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .rubric-icon {
        font-size: 1.3rem;
        margin-right: 0.5rem;
    }
    .rubric-weight {
        font-size: 0.85rem;
        opacity: 0.9;
        background: rgba(255,255,255,0.2);
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
    }
    .rubric-content {
        padding: 1.5rem;
    }
    .analysis-box {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
        height: 500px;
        overflow-y: auto;
        overflow-x: hidden;
    }
    .scoring-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #e9ecef;
    }
    .insight-highlight {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .card-separator {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e9ecef, transparent);
        margin: 2rem 0;
    }

    /* ACCORDION MODE STYLES */
    .accordion-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
        transition: all 0.3s ease;
        border-radius: 12px 12px 0 0;
    }

    .accordion-header:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }

    .accordion-header.collapsed {
        border-radius: 12px;
        margin-bottom: 1rem;
    }

    .accordion-score-badge {
        background: rgba(255,255,255,0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.9em;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .accordion-content {
        background: white;
        border: 1px solid #e1e5e9;
        border-top: none;
        border-radius: 0 0 12px 12px;
        overflow: hidden;
    }

    /* Sticky mode CSS removed - using accordion only */

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .floating-score-panel {
            bottom: 10px;
            left: 10px;
            right: 10px;
            min-width: auto;
            max-width: none;
        }

        .scoring-box-sticky {
            position: static;
            max-height: none;
        }

        .analysis-box {
            height: 300px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Render each rubric as a card
    rubrics_df = cache_service.get_cached_rubrics()

    # Define rubric icons
    rubric_icons = {
        'tema': '🎯',
        'lirik': '📝',
        'musik': '🎼',
        'kreativ': '✨',
        'jemaat': '👥'
    }

    # Store floating panel data for later rendering
    floating_panels = []

    for _, rubric in rubrics_df.iterrows():
        rubric_key = rubric['rubric_key']
        icon = rubric_icons.get(rubric_key, '📋')

        # Create card container with header (accordion mode only)
        st.markdown(f"""
        <div class="rubric-card">
            <div class="rubric-header">
                <div>
                    <span class="rubric-icon">{icon}</span>
                    <span>{rubric['aspect_name']}</span>
                </div>
                <span class="rubric-weight">Bobot: {rubric['weight']}%</span>
            </div>
            <div class="rubric-content">
        """, unsafe_allow_html=True)

        # Render using accordion mode only
        render_accordion_mode(rubric, song_data, ai_suggestions, ai_explanations, existing_scores, judge_id, editing_locked)

        # Close card container
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Add separator between cards
        st.markdown('<div class="card-separator"></div>', unsafe_allow_html=True)

    # No additional rendering needed for accordion mode

def render_analisis_tab(judge_id, judge_name):
    """Render analysis tab with comprehensive insights"""
    st.markdown("### 📈 Analisis & Insights")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        # Song filter
        songs_df = cache_service.get_cached_songs()
        song_options = ["Semua Lagu"] + [f"{row['id']}. {row['title']}" for _, row in songs_df.iterrows()]
        selected_song_filter = st.selectbox("🎵 Filter Lagu:", song_options)

    with col2:
        # Judge filter (for admin view)
        judges_df = cache_service.get_cached_judges()
        judge_options = ["Semua Juri"] + [row['name'] for _, row in judges_df.iterrows()]
        selected_judge_filter = st.selectbox("👥 Filter Juri:", judge_options)

    with col3:
        # Rubric filter
        rubrics_df = cache_service.get_cached_rubrics()
        rubric_options = ["Semua Kriteria"] + [row['aspect_name'] for _, row in rubrics_df.iterrows()]
        selected_rubric_filter = st.selectbox("📋 Filter Kriteria:", rubric_options)

    st.markdown("---")

    # Song Profiles Section
    st.markdown("#### 🎵 Profil Lagu")

    # Get evaluations data
    evaluations_df = cache_service.get_cached_evaluations()

    if not evaluations_df.empty:
        # Create song analysis cards
        for _, song in songs_df.iterrows():
            song_evals = evaluations_df[evaluations_df['song_id'] == song['id']]

            if not song_evals.empty:
                with st.expander(f"🎵 {song['id']}. {song['title']}", expanded=False):
                    # Use full width layout - no columns
                    # Calculate average scores
                    avg_scores = {}
                    for _, eval_row in song_evals.iterrows():
                        rubric_scores = eval_row['rubric_scores']
                        if isinstance(rubric_scores, str):
                            import json
                            rubric_scores = json.loads(rubric_scores)

                        for rubric_key, score in rubric_scores.items():
                            if rubric_key not in avg_scores:
                                avg_scores[rubric_key] = []
                            if score and score > 0:
                                avg_scores[rubric_key].append(score)

                    # Display metrics
                    metrics_cols = st.columns(len(avg_scores))
                    for i, (rubric_key, scores) in enumerate(avg_scores.items()):
                        if scores:
                            avg_score = sum(scores) / len(scores)
                            rubric_name = rubrics_df[rubrics_df['rubric_key'] == rubric_key]['aspect_name'].iloc[0]
                            metrics_cols[i].metric(
                                rubric_name,
                                f"{avg_score:.1f}/5",
                                f"{len(scores)} juri"
                            )

                    # Overall score
                    total_scores = [eval_row['total_score'] for _, eval_row in song_evals.iterrows() if eval_row['total_score'] > 0]
                    if total_scores:
                        avg_total = sum(total_scores) / len(total_scores)
                        score_100 = (avg_total / 25) * 100
                        st.success(f"📊 **Skor Rata-rata**: {score_100:.1f}/100 (dari {len(total_scores)} juri)")

                    # Action buttons below the score - full width
                    st.markdown("---")

                    # Download Report button - full width
                    if st.button(f"📄 Download Report", key=f"download_song_{song['id']}", use_container_width=True):
                        if PDF_AVAILABLE:
                            try:
                                with st.spinner(f"🔄 Generating report for {song['title']}..."):
                                    pdf_bytes = generate_song_report_pdf(song['id'])
                                    filename = f"laporan_{song['title'].replace(' ', '_')}.pdf"

                                    st.download_button(
                                        label="📥 Download PDF",
                                        data=pdf_bytes,
                                        file_name=filename,
                                        mime="application/pdf",
                                        key=f"dl_song_{song['id']}",
                                        use_container_width=True
                                    )
                                    st.success("✅ Report generated!")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                        else:
                            st.error("❌ PDF generation not available")

                    # Detail Analysis button - full width, separate
                    if st.button(f"👁️ Detail Analysis", key=f"detail_song_{song['id']}", use_container_width=True):
                        # Show detailed analysis directly in the same expander
                        st.markdown("---")
                        st.markdown("### 🔍 Detailed Analysis")
                        render_song_detailed_analysis(song, song_evals)
    else:
        st.info("📋 Belum ada data evaluasi untuk dianalisis")

    st.markdown("---")

    # Overall Insights Section
    st.markdown("#### 📊 Insight Keseluruhan")

    if not evaluations_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 🎯 Statistik Rubrik")
            # Calculate rubric statistics
            all_rubric_scores = {}
            for _, eval_row in evaluations_df.iterrows():
                rubric_scores = eval_row['rubric_scores']
                if isinstance(rubric_scores, str):
                    import json
                    rubric_scores = json.loads(rubric_scores)

                for rubric_key, score in rubric_scores.items():
                    if rubric_key not in all_rubric_scores:
                        all_rubric_scores[rubric_key] = []
                    if score and score > 0:
                        all_rubric_scores[rubric_key].append(score)

            for rubric_key, scores in all_rubric_scores.items():
                if scores:
                    rubric_name = rubrics_df[rubrics_df['rubric_key'] == rubric_key]['aspect_name'].iloc[0]
                    avg_score = sum(scores) / len(scores)
                    st.metric(
                        f"📋 {rubric_name}",
                        f"{avg_score:.2f}/5",
                        f"{len(scores)} penilaian"
                    )

        with col2:
            st.markdown("##### 👥 Konsistensi Juri")
            # Calculate judge consistency
            judge_scores = {}
            for _, eval_row in evaluations_df.iterrows():
                judge_id = eval_row['judge_id']
                total_score = eval_row['total_score']
                if total_score > 0:
                    if judge_id not in judge_scores:
                        judge_scores[judge_id] = []
                    judge_scores[judge_id].append(total_score)

            if len(judge_scores) > 1:
                # Calculate standard deviation across judges
                all_scores = [score for scores in judge_scores.values() for score in scores]
                if len(all_scores) > 1:
                    import statistics
                    std_dev = statistics.stdev(all_scores)
                    consistency_pct = max(0, 100 - (std_dev / statistics.mean(all_scores) * 100))
                    st.metric("🎯 Konsistensi Penilaian", f"{consistency_pct:.1f}%")

            st.metric("👥 Total Juri Aktif", len(judge_scores))
            st.metric("📊 Total Evaluasi", len(evaluations_df))
    else:
        st.info("📋 Belum ada data untuk analisis insight")

def render_song_detailed_analysis(song, song_evals):
    """Render comprehensive detailed analysis for a song"""
    try:
        # Get additional data
        rubrics_df = cache_service.get_cached_rubrics()
        judges_df = cache_service.get_cached_judges()

        # Basic song info
        st.markdown(f"### 🎵 {song['title']}")
        st.markdown(f"**Pencipta:** {song['composer']}")

        # Use full width layout instead of columns
        st.markdown("#### 📊 Overview Penilaian")

        if not song_evals.empty:
            # Calculate statistics
            total_scores = [eval_row['total_score'] for _, eval_row in song_evals.iterrows() if eval_row['total_score'] > 0]

            if total_scores:
                avg_score = sum(total_scores) / len(total_scores)
                score_100 = (avg_score / 25) * 100
                max_score = max(total_scores)
                min_score = min(total_scores)

                # Get position in leaderboard first
                song_position = None
                try:
                    from services.analytics_service import analytics_service
                    leaderboard_df = analytics_service.get_global_leaderboard()
                    if not leaderboard_df.empty:
                        for idx, (_, row) in enumerate(leaderboard_df.iterrows(), 1):
                            if row['song_id'] == song['id']:
                                song_position = idx
                                break
                except:
                    pass

                # Display metrics in a row (6 columns if position available)
                if song_position:
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    col6.metric("Posisi Leaderboard", f"#{song_position}")
                else:
                    col1, col2, col3, col4, col5 = st.columns(5)

                col1.metric("Rata-rata", f"{score_100:.1f}/100")
                col2.metric("Tertinggi", f"{(max_score/25)*100:.1f}/100")
                col3.metric("Terendah", f"{(min_score/25)*100:.1f}/100")
                col4.metric("Total Juri", len(song_evals))
                col5.metric("Evaluasi Lengkap", len([e for _, e in song_evals.iterrows() if e['total_score'] > 0]))

                # Consistency analysis
                if len(total_scores) > 1:
                    import numpy as np
                    std_dev = np.std([(score/25)*100 for score in total_scores])

                    if std_dev < 5:
                        consistency = "🟢 Sangat konsisten"
                    elif std_dev < 10:
                        consistency = "🟡 Cukup konsisten"
                    else:
                        consistency = "🔴 Beragam penilaian"

                    st.info(f"**Konsistensi Juri:** {consistency} (std: {std_dev:.1f})")

        # Detailed rubric analysis
        st.markdown("---")
        st.markdown("#### 📋 Analisis Rubrik Detail")

        if not song_evals.empty:
            # Create rubric breakdown table
            rubric_analysis = {}

            for _, eval_row in song_evals.iterrows():
                rubric_scores = eval_row['rubric_scores']
                if isinstance(rubric_scores, str):
                    import json
                    rubric_scores = json.loads(rubric_scores)

                for rubric_key, score in rubric_scores.items():
                    if score and score > 0:
                        if rubric_key not in rubric_analysis:
                            rubric_analysis[rubric_key] = []
                        rubric_analysis[rubric_key].append(score)

            # Display rubric analysis
            for rubric_key, scores in rubric_analysis.items():
                if scores:
                    # Get rubric name
                    rubric_name = rubric_key.title()
                    try:
                        rubric_row = rubrics_df[rubrics_df['rubric_key'] == rubric_key]
                        if not rubric_row.empty:
                            rubric_name = rubric_row.iloc[0]['aspect_name']
                    except:
                        pass

                    avg_score = sum(scores) / len(scores)
                    max_score = max(scores)
                    min_score = min(scores)

                    with st.expander(f"🎯 {rubric_name} - Rata-rata: {avg_score:.1f}/5"):
                        # Use full width layout instead of columns
                        st.markdown("**📊 Statistik:**")

                        # Display stats in a row
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        stat_col1.metric("Rata-rata", f"{avg_score:.1f}/5")
                        stat_col2.metric("Tertinggi", f"{max_score}/5")
                        stat_col3.metric("Terendah", f"{min_score}/5")
                        stat_col4.metric("Jumlah Penilaian", len(scores))

                        st.markdown("**🎯 Analisis:**")
                        if avg_score >= 4.0:
                            st.success("🌟 Kekuatan utama lagu ini - Aspek ini sangat baik dan menjadi keunggulan lagu.")
                        elif avg_score >= 3.0:
                            st.info("✅ Area yang cukup baik - Aspek ini sudah cukup baik dengan ruang untuk peningkatan.")
                        else:
                            st.warning("🔧 Area yang perlu diperbaiki - Aspek ini memerlukan perhatian dan perbaikan.")

        # Judge-by-judge breakdown
        st.markdown("---")
        st.markdown("#### 👨‍⚖️ Penilaian per Juri")

        judge_table_data = []
        header = ['Juri', 'Tema', 'Lirik', 'Musik', 'Kreativitas', 'Jemaat', 'Total', 'Catatan']
        judge_table_data.append(header)

        for _, eval_row in song_evals.iterrows():
            # Get judge name
            judge_name = "Unknown"
            try:
                judge_row = judges_df[judges_df['id'] == eval_row['judge_id']]
                if not judge_row.empty:
                    judge_name = judge_row.iloc[0]['name']
            except:
                pass

            # Parse rubric scores
            rubric_scores = eval_row['rubric_scores']
            if isinstance(rubric_scores, str):
                import json
                rubric_scores = json.loads(rubric_scores)

            row = [judge_name]
            for rubric_key in ['tema', 'lirik', 'musik', 'kreativ', 'jemaat']:
                score = rubric_scores.get(rubric_key, 0)
                row.append(f"{score}/5" if score > 0 else "-")

            # Total score
            total_score = eval_row['total_score']
            score_100 = (total_score / 25) * 100
            row.append(f"{score_100:.1f}/100")

            # Notes
            notes = eval_row.get('notes', '')
            row.append(notes[:50] + "..." if len(notes) > 50 else notes or "-")

            judge_table_data.append(row)

        # Display table
        import pandas as pd
        df_display = pd.DataFrame(judge_table_data[1:], columns=judge_table_data[0])
        st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"Error in detailed analysis: {str(e)}")

def render_hasil_tab(judge_id, judge_name):
    """Render results tab with winners and rankings"""
    st.markdown("### 🏆 Hasil Lomba")

    # Get data
    songs_df = cache_service.get_cached_songs()
    evaluations_df = cache_service.get_cached_evaluations()

    if evaluations_df.empty:
        st.info("📋 Belum ada hasil evaluasi")
        return

    # Calculate final scores for each song
    song_results = []

    for _, song in songs_df.iterrows():
        song_evals = evaluations_df[evaluations_df['song_id'] == song['id']]

        if not song_evals.empty:
            # Get scores from all judges
            total_scores = [eval_row['total_score'] for _, eval_row in song_evals.iterrows() if eval_row['total_score'] > 0]

            if total_scores:
                avg_score = sum(total_scores) / len(total_scores)
                score_100 = (avg_score / 25) * 100

                song_results.append({
                    'id': song['id'],
                    'title': song['title'],
                    'composer': song.get('composer', 'Unknown'),
                    'avg_score': avg_score,
                    'score_100': score_100,
                    'judge_count': len(total_scores)
                })

    if not song_results:
        st.info("📋 Belum ada lagu yang memiliki skor lengkap")
        return

    # Sort by score (descending)
    song_results.sort(key=lambda x: x['score_100'], reverse=True)

    # Display winners
    st.markdown("#### 🏆 Pemenang")

    if len(song_results) >= 1:
        # Winner 1
        winner1 = song_results[0]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FFD700, #FFA500); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: #8B4513;">🥇 JUARA 1</h3>
            <h2 style="margin: 0.5rem 0; color: #8B4513;">{winner1['title']}</h2>
            <p style="margin: 0; color: #8B4513; font-weight: 600;">Skor: {winner1['score_100']:.1f}/100</p>
            <p style="margin: 0; color: #8B4513;">Pencipta: {winner1['composer']}</p>
        </div>
        """, unsafe_allow_html=True)

    if len(song_results) >= 2:
        # Winner 2
        winner2 = song_results[1]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #C0C0C0, #A9A9A9); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: #2F4F4F;">🥈 JUARA 2</h3>
            <h2 style="margin: 0.5rem 0; color: #2F4F4F;">{winner2['title']}</h2>
            <p style="margin: 0; color: #2F4F4F; font-weight: 600;">Skor: {winner2['score_100']:.1f}/100</p>
            <p style="margin: 0; color: #2F4F4F;">Pencipta: {winner2['composer']}</p>
        </div>
        """, unsafe_allow_html=True)

    if len(song_results) >= 3:
        # Winner 3
        winner3 = song_results[2]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #CD7F32, #A0522D); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: white;">🥉 JUARA 3</h3>
            <h2 style="margin: 0.5rem 0; color: white;">{winner3['title']}</h2>
            <p style="margin: 0; color: white; font-weight: 600;">Skor: {winner3['score_100']:.1f}/100</p>
            <p style="margin: 0; color: white;">Pencipta: {winner3['composer']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Full leaderboard
    st.markdown("#### 📊 Leaderboard Lengkap")

    # Create DataFrame for display
    import pandas as pd
    results_df = pd.DataFrame(song_results)
    results_df['Ranking'] = range(1, len(results_df) + 1)
    results_df['Skor'] = results_df['score_100'].round(1)
    results_df['Juri'] = results_df['judge_count']

    # Display table
    display_df = results_df[['Ranking', 'title', 'composer', 'Skor', 'Juri']].copy()
    display_df.columns = ['Peringkat', 'Judul Lagu', 'Pencipta', 'Skor (/100)', 'Juri']

    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Download Hasil Lengkap", key="download_full_results"):
            if PDF_AVAILABLE:
                try:
                    with st.spinner("🔄 Generating complete results report..."):
                        pdf_bytes = generate_winner_report_pdf()
                        filename = f"hasil_lengkap_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

                        st.download_button(
                            label="📥 Download Results PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key="dl_full_results"
                        )
                        st.success("✅ Results report generated!")
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
            else:
                st.error("❌ PDF generation not available")

    with col2:
        if st.button("🎖️ Generate Sertifikat", key="generate_certificates_hasil"):
            st.info("🚧 Certificate generation akan diimplementasikan")

    with col3:
        if st.button("📊 Analisis Pemenang", key="analyze_winners"):
            st.info("🚧 Winner analysis akan diimplementasikan")

def render_export_tab(judge_id, judge_name):
    """Render export/download tab with working PDF generation"""
    st.markdown("### 📄 Download & Export")

    if not PDF_AVAILABLE:
        st.error("❌ **PDF generation tidak tersedia**")
        st.info("Untuk mengaktifkan PDF generation, install reportlab: `pip install reportlab`")
        return

    # Per Song Reports
    st.markdown("#### 🎵 Laporan Per Lagu")

    songs_df = cache_service.get_cached_songs()

    # Song selector for individual reports
    selected_song = st.selectbox(
        "Pilih lagu untuk generate laporan:",
        options=[f"{row['id']}. {row['title']}" for _, row in songs_df.iterrows()],
        key="export_song_selector"
    )

    if selected_song:
        song_id = int(selected_song.split('.')[0])
        song_title = songs_df[songs_df['id'] == song_id]['title'].iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"📄 Generate Report: {song_title}", key=f"generate_song_{song_id}"):
                try:
                    with st.spinner("🔄 Generating PDF report..."):
                        pdf_bytes = generate_song_report_pdf(song_id)
                        filename = f"laporan_lagu_{song_id}_{song_title.replace(' ', '_')}.pdf"

                        # Create download button
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_song_{song_id}"
                        )
                        st.success(f"✅ Report generated successfully!")

                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")

        with col2:
            if st.button(f"📄 Generate Report (Judge Only)", key=f"generate_song_judge_{song_id}"):
                try:
                    with st.spinner("🔄 Generating judge-specific PDF report..."):
                        pdf_bytes = generate_song_report_pdf(song_id, judge_id)
                        filename = f"laporan_lagu_{song_id}_{judge_name.replace(' ', '_')}.pdf"

                        # Create download button
                        st.download_button(
                            label="📥 Download Judge Report",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_song_judge_{song_id}"
                        )
                        st.success(f"✅ Judge report generated successfully!")

                except Exception as e:
                    st.error(f"❌ Error generating judge report: {str(e)}")

    st.markdown("---")

    # Winner Documents
    st.markdown("#### 🏆 Dokumen Pemenang")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Laporan Pemenang", key="generate_winner_report"):
            try:
                with st.spinner("🔄 Generating winner report..."):
                    pdf_bytes = generate_winner_report_pdf()
                    filename = f"laporan_pemenang_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

                    # Create download button
                    st.download_button(
                        label="📥 Download Winner Report",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        key="download_winner_report"
                    )
                    st.success("✅ Winner report generated successfully!")

            except Exception as e:
                st.error(f"❌ Error generating winner report: {str(e)}")

    with col2:
        if st.button("🎖️ Sertifikat Pemenang", key="generate_certificates"):
            st.info("🚧 Certificate generation akan diimplementasikan")

    with col3:
        if st.button("📊 Analisis Kemenangan", key="generate_winner_analysis"):
            st.info("🚧 Winner analysis akan diimplementasikan")

    st.markdown("---")

    # Analysis Reports
    st.markdown("#### 📊 Laporan Analisis")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👥 Analisis Juri", key="generate_judge_analysis"):
            st.info("🚧 Judge analysis akan diimplementasikan")

    with col2:
        if st.button("📈 Insight Keseluruhan", key="generate_overall_insights"):
            st.info("🚧 Overall insights akan diimplementasikan")

    with col3:
        if st.button("📊 Laporan Statistik", key="generate_statistical_report"):
            st.info("🚧 Statistical report akan diimplementasikan")

    st.markdown("---")

    # Raw Data Export
    st.markdown("#### 📋 Export Data Mentah")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Export Skor (CSV)", key="export_scores_csv"):
            try:
                # Get evaluations data
                evaluations_df = cache_service.get_cached_evaluations()
                songs_df = cache_service.get_cached_songs()
                judges_df = cache_service.get_cached_judges()

                if not evaluations_df.empty:
                    # Prepare CSV data
                    csv_data = []
                    for _, eval_row in evaluations_df.iterrows():
                        song_title = songs_df[songs_df['id'] == eval_row['song_id']]['title'].iloc[0]
                        judge_name = judges_df[judges_df['id'] == eval_row['judge_id']]['name'].iloc[0]

                        rubric_scores = eval_row['rubric_scores']
                        if isinstance(rubric_scores, str):
                            rubric_scores = json.loads(rubric_scores)
                        elif not isinstance(rubric_scores, dict):
                            rubric_scores = {}

                        csv_row = {
                            'song_id': eval_row['song_id'],
                            'song_title': song_title,
                            'judge_id': eval_row['judge_id'],
                            'judge_name': judge_name,
                            'tema': rubric_scores.get('tema', 0),
                            'lirik': rubric_scores.get('lirik', 0),
                            'musik': rubric_scores.get('musik', 0),
                            'kreativitas': rubric_scores.get('kreativ', 0),
                            'jemaat': rubric_scores.get('jemaat', 0),
                            'total_score': eval_row['total_score'],
                            'score_100': (eval_row['total_score'] / 25) * 100 if eval_row['total_score'] > 0 else 0,
                            'notes': eval_row.get('notes', ''),
                            'created_at': eval_row['created_at']
                        }
                        csv_data.append(csv_row)

                    # Convert to DataFrame and CSV
                    csv_df = pd.DataFrame(csv_data)
                    csv_string = csv_df.to_csv(index=False)

                    # Create download button
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_string,
                        file_name=f"evaluasi_scores_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="download_scores_csv"
                    )
                    st.success("✅ CSV data prepared for download!")
                else:
                    st.warning("⚠️ No evaluation data available")

            except Exception as e:
                st.error(f"❌ Error exporting CSV: {str(e)}")

    with col2:
        if st.button("📄 Export Evaluasi (JSON)", key="export_evaluations_json"):
            try:
                # Get evaluations data
                evaluations_df = cache_service.get_cached_evaluations()

                if not evaluations_df.empty:
                    # Convert to JSON
                    json_data = evaluations_df.to_json(orient='records', indent=2)

                    # Create download button
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        key="download_evaluations_json"
                    )
                    st.success("✅ JSON data prepared for download!")
                else:
                    st.warning("⚠️ No evaluation data available")

            except Exception as e:
                st.error(f"❌ Error exporting JSON: {str(e)}")

    with col3:
        if st.button("💾 Export Database Lengkap", key="export_full_database"):
            st.info("🚧 Full database export akan diimplementasikan")

# ==================== PDF GENERATION FUNCTIONS ====================

def generate_song_report_pdf(song_id: int, judge_id: int = None) -> bytes:
    """Generate PDF report for a specific song"""
    if not PDF_AVAILABLE:
        raise Exception("PDF generation not available. Please install reportlab.")

    # Get data
    songs_df = cache_service.get_cached_songs()
    song = songs_df[songs_df['id'] == song_id].iloc[0]

    evaluations_df = cache_service.get_cached_evaluations()
    song_evals = evaluations_df[evaluations_df['song_id'] == song_id]

    if judge_id:
        song_evals = song_evals[song_evals['judge_id'] == judge_id]

    rubrics_df = cache_service.get_cached_rubrics()
    judges_df = cache_service.get_cached_judges()

    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"Laporan Evaluasi Lagu", title_style))
    story.append(Paragraph(f"{song['title']}", title_style))
    story.append(Spacer(1, 20))

    # Song Information
    story.append(Paragraph("Informasi Lagu", styles['Heading2']))
    song_info = [
        ['Judul', song['title']],
        ['Pencipta', song.get('composer', 'Unknown')],
        ['ID Lagu', str(song['id'])],
        ['Tanggal Laporan', datetime.now().strftime('%d/%m/%Y %H:%M')]
    ]

    song_table = Table(song_info, colWidths=[2*inch, 4*inch])
    song_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(song_table)
    story.append(Spacer(1, 20))

    # Evaluation Results
    if not song_evals.empty:
        story.append(Paragraph("Hasil Penilaian", styles['Heading2']))

        # Calculate scores
        eval_data = []
        eval_data.append(['Juri', 'Tema', 'Lirik', 'Musik', 'Kreativitas', 'Jemaat', 'Total'])

        for _, eval_row in song_evals.iterrows():
            judge_name = judges_df[judges_df['id'] == eval_row['judge_id']]['name'].iloc[0]
            rubric_scores = eval_row['rubric_scores']

            if isinstance(rubric_scores, str):
                rubric_scores = json.loads(rubric_scores)

            row = [judge_name]
            for rubric_key in ['tema', 'lirik', 'musik', 'kreativ', 'jemaat']:
                score = rubric_scores.get(rubric_key, 0)
                row.append(str(score) if score > 0 else '-')

            total_score = eval_row['total_score']
            score_100 = (total_score / 25) * 100 if total_score > 0 else 0
            row.append(f"{score_100:.1f}/100")

            eval_data.append(row)

        # Add average row if multiple judges
        if len(song_evals) > 1:
            avg_row = ['RATA-RATA']
            for rubric_key in ['tema', 'lirik', 'musik', 'kreativ', 'jemaat']:
                scores = []
                for _, eval_row in song_evals.iterrows():
                    rubric_scores = eval_row['rubric_scores']
                    if isinstance(rubric_scores, str):
                        rubric_scores = json.loads(rubric_scores)
                    score = rubric_scores.get(rubric_key, 0)
                    if score > 0:
                        scores.append(score)

                if scores:
                    avg_score = sum(scores) / len(scores)
                    avg_row.append(f"{avg_score:.1f}")
                else:
                    avg_row.append('-')

            # Average total
            total_scores = [eval_row['total_score'] for _, eval_row in song_evals.iterrows() if eval_row['total_score'] > 0]
            if total_scores:
                avg_total = sum(total_scores) / len(total_scores)
                avg_total_100 = (avg_total / 25) * 100
                avg_row.append(f"{avg_total_100:.1f}/100")
            else:
                avg_row.append('-')

            eval_data.append(avg_row)

        eval_table = Table(eval_data)
        eval_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        # Highlight average row
        if len(song_evals) > 1:
            eval_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))

        story.append(eval_table)
        story.append(Spacer(1, 20))

        # Song Analysis section
        story.append(Paragraph("Analisis Lagu", styles['Heading2']))

        # Calculate average scores for analysis
        rubric_averages = {}
        rubric_names = {
            'tema': 'Kesesuaian Tema',
            'lirik': 'Kekuatan Lirik',
            'musik': 'Kekayaan Musik',
            'kreativ': 'Kreativitas & Orisinalitas',
            'jemaat': 'Kesesuaian untuk Jemaat'
        }

        for rubric_key in ['tema', 'lirik', 'musik', 'kreativ', 'jemaat']:
            scores = []
            for _, eval_row in song_evals.iterrows():
                rubric_scores = eval_row['rubric_scores']
                if isinstance(rubric_scores, str):
                    rubric_scores = json.loads(rubric_scores)
                score = rubric_scores.get(rubric_key, 0)
                if score > 0:
                    scores.append(score)

            if scores:
                rubric_averages[rubric_key] = sum(scores) / len(scores)
            else:
                rubric_averages[rubric_key] = 0

        # Identify strengths and weaknesses
        sorted_rubrics = sorted(rubric_averages.items(), key=lambda x: x[1], reverse=True)
        strengths = [item for item in sorted_rubrics if item[1] >= 4.0]
        good_areas = [item for item in sorted_rubrics if 3.0 <= item[1] < 4.0]
        weaknesses = [item for item in sorted_rubrics if item[1] < 3.0]

        # Strengths section
        if strengths:
            story.append(Paragraph("<b>🌟 Kekuatan Utama:</b>", styles['Normal']))
            for rubric_key, score in strengths:
                story.append(Paragraph(f"• <b>{rubric_names[rubric_key]}</b>: {score:.1f}/5 - Sangat baik", styles['Normal']))
            story.append(Spacer(1, 10))

        # Good areas section
        if good_areas:
            story.append(Paragraph("<b>✅ Area yang Baik:</b>", styles['Normal']))
            for rubric_key, score in good_areas:
                story.append(Paragraph(f"• <b>{rubric_names[rubric_key]}</b>: {score:.1f}/5 - Cukup baik", styles['Normal']))
            story.append(Spacer(1, 10))

        # Weaknesses section
        if weaknesses:
            story.append(Paragraph("<b>🔧 Area yang Perlu Diperbaiki:</b>", styles['Normal']))
            for rubric_key, score in weaknesses:
                story.append(Paragraph(f"• <b>{rubric_names[rubric_key]}</b>: {score:.1f}/5 - Perlu peningkatan", styles['Normal']))
            story.append(Spacer(1, 10))

        # Overall assessment
        total_scores = [eval_row['total_score'] for _, eval_row in song_evals.iterrows() if eval_row['total_score'] > 0]
        if total_scores:
            avg_total = sum(total_scores) / len(total_scores)
            avg_total_100 = (avg_total / 25) * 100

            story.append(Paragraph("<b>📊 Penilaian Keseluruhan:</b>", styles['Normal']))
            if avg_total_100 >= 80:
                assessment = "Lagu ini memiliki kualitas yang sangat baik dan siap untuk dipresentasikan."
            elif avg_total_100 >= 70:
                assessment = "Lagu ini memiliki kualitas yang baik dengan beberapa area yang bisa ditingkatkan."
            elif avg_total_100 >= 60:
                assessment = "Lagu ini memiliki potensi yang baik namun memerlukan perbaikan di beberapa aspek."
            else:
                assessment = "Lagu ini memerlukan perbaikan signifikan di berbagai aspek."

            story.append(Paragraph(f"Skor rata-rata: {avg_total_100:.1f}/100. {assessment}", styles['Normal']))
            story.append(Spacer(1, 15))

        # Add comprehensive song analysis
        story.append(PageBreak())
        _add_comprehensive_song_analysis(story, song, song_evals, styles)

        # Judge comments section (if any)
        has_comments = False
        for _, eval_row in song_evals.iterrows():
            notes = eval_row.get('notes', '')
            if notes and notes.strip():
                has_comments = True
                break

        if has_comments:
            story.append(Paragraph("📝 Catatan Juri", styles['Heading2']))
            for _, eval_row in song_evals.iterrows():
                judge_name = judges_df[judges_df['id'] == eval_row['judge_id']]['name'].iloc[0]
                notes = eval_row.get('notes', '')

                if notes and notes.strip():
                    story.append(Paragraph(f"<b>{judge_name}:</b>", styles['Normal']))
                    story.append(Paragraph(notes, styles['Normal']))
                    story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("Belum ada evaluasi untuk lagu ini.", styles['Normal']))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_winner_report_pdf() -> bytes:
    """Generate comprehensive PDF report for winners with detailed analysis"""
    if not PDF_AVAILABLE:
        raise Exception("PDF generation not available. Please install reportlab.")

    # Get data using analytics service for proper scoring
    from services.analytics_service import analytics_service
    leaderboard_df = analytics_service.get_global_leaderboard()
    evaluations_df = cache_service.get_cached_evaluations()
    judges_df = cache_service.get_cached_judges()
    rubrics_df = cache_service.get_cached_rubrics()
    config = cache_service.get_cached_config()

    if leaderboard_df.empty:
        raise Exception("No evaluation data available for winner report")

    # Get winners count from config
    winners_count = int(config.get('WINNERS_TOP_N', 3))
    winners_df = leaderboard_df.head(winners_count)

    # Convert to song_results format for compatibility
    song_results = []
    for _, row in winners_df.iterrows():
        song_results.append({
            'id': row['song_id'],
            'title': row['title'],
            'composer': row['composer'],
            'avg_score': row['avg_score'] / 4,  # Convert back to 25-point for internal calculations
            'score_100': row['avg_score'],  # Already in 100-point scale
            'judge_count': row['unique_judges']
        })

    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph("Hasil Lomba Cipta Lagu", title_style))
    story.append(Paragraph("Bulan Keluarga GKI Perumnas 2025", title_style))
    story.append(Spacer(1, 30))

    # Winners with detailed analysis
    if song_results:
        story.append(Paragraph("🏆 ANALISIS PEMENANG", styles['Heading1']))
        story.append(Spacer(1, 20))

        # Detailed analysis for ALL winners (based on config)
        for i, result in enumerate(song_results):
            if i == 0:
                medal = "🥇 JUARA 1"
                color = colors.gold
            elif i == 1:
                medal = "🥈 JUARA 2"
                color = colors.silver
            elif i == 2:
                medal = "🥉 JUARA 3"
                color = colors.orange
            else:
                medal = f"🏆 PERINGKAT {i+1}"
                color = colors.lightblue

            story.append(Paragraph(medal, styles['Heading2']))
            story.append(Paragraph(f"<b>{result['title']}</b> - {result['composer']}", styles['Heading3']))
            story.append(Spacer(1, 10))

            # Basic info
            winner_info = [
                ['Skor Total', f"{result['score_100']:.1f}/100"],
                ['Jumlah Juri', f"{result['judge_count']} juri"],
                ['Posisi', f"Peringkat {i+1} dari {len(leaderboard_df)} lagu"]
            ]

            winner_table = Table(winner_info, colWidths=[1.5*inch, 4*inch])
            winner_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(winner_table)
            story.append(Spacer(1, 15))

            # Add detailed rubric analysis
            _add_winner_rubric_analysis(story, result, evaluations_df, judges_df, rubrics_df, styles)

            # Add comparison with other winners
            if i < len(song_results) - 1:
                _add_winner_comparison(story, result, song_results[i+1:], styles)

            if i < 2:  # Add page break between winners
                story.append(PageBreak())

        # Full ranking - use ALL songs from leaderboard
        story.append(PageBreak())
        story.append(Paragraph("📊 PERINGKAT LENGKAP", styles['Heading1']))
        story.append(Spacer(1, 20))

        ranking_data = [['Peringkat', 'Judul Lagu', 'Pencipta', 'Skor', 'Juri']]

        # Use ALL songs from leaderboard_df, not just winners
        for i, (_, row) in enumerate(leaderboard_df.iterrows()):
            ranking_data.append([
                str(i + 1),
                row['title'],
                row['composer'],
                f"{row['avg_score']:.1f}/100",
                str(row['unique_judges'])
            ])

        ranking_table = Table(ranking_data, colWidths=[0.8*inch, 2.5*inch, 2*inch, 1*inch, 0.7*inch])
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        # Highlight top 3 (use leaderboard length, not song_results)
        for i in range(min(3, len(leaderboard_df))):
            if i == 0:
                bg_color = colors.gold
            elif i == 1:
                bg_color = colors.silver
            else:
                bg_color = colors.orange

            ranking_table.setStyle(TableStyle([
                ('BACKGROUND', (0, i+1), (-1, i+1), bg_color),
            ]))

        story.append(ranking_table)
    else:
        story.append(Paragraph("Belum ada hasil evaluasi.", styles['Normal']))

    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Laporan dibuat pada: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def _add_winner_rubric_analysis(story, result, evaluations_df, judges_df, rubrics_df, styles):
    """Add detailed rubric analysis for a winner"""
    song_id = result['id']
    song_evals = evaluations_df[evaluations_df['song_id'] == song_id]

    if song_evals.empty:
        return

    story.append(Paragraph("<b>📊 Analisis Rubrik Penilaian:</b>", styles['Heading3']))
    story.append(Spacer(1, 10))

    # Create rubric analysis table
    rubric_data = [['Aspek Penilaian', 'Rata-rata', 'Tertinggi', 'Terendah', 'Analisis']]

    # Calculate rubric scores
    rubric_scores = {}
    for _, eval_row in song_evals.iterrows():
        rubric_scores_json = eval_row['rubric_scores']
        if isinstance(rubric_scores_json, str):
            import json
            rubric_scores_json = json.loads(rubric_scores_json)

        for rubric_key, score in rubric_scores_json.items():
            if score and score > 0:
                if rubric_key not in rubric_scores:
                    rubric_scores[rubric_key] = []
                rubric_scores[rubric_key].append(score)

    # Analyze each rubric
    for rubric_key, scores in rubric_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            # Get rubric name
            rubric_name = rubric_key.title()
            try:
                rubric_row = rubrics_df[rubrics_df['rubric_key'] == rubric_key]
                if not rubric_row.empty:
                    rubric_name = rubric_row.iloc[0]['aspect_name']
            except:
                pass

            # Analysis based on score
            if avg_score >= 4.0:
                analysis = "Sangat Baik"
            elif avg_score >= 3.5:
                analysis = "Baik"
            elif avg_score >= 3.0:
                analysis = "Cukup"
            else:
                analysis = "Perlu Perbaikan"

            rubric_data.append([
                rubric_name,
                f"{avg_score:.1f}/5",
                f"{max_score:.1f}/5",
                f"{min_score:.1f}/5",
                analysis
            ])

    rubric_table = Table(rubric_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
    rubric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(rubric_table)
    story.append(Spacer(1, 15))

    # Add judge-by-judge breakdown
    story.append(Paragraph("<b>👨‍⚖️ Penilaian per Juri:</b>", styles['Heading3']))
    story.append(Spacer(1, 10))

    judge_data = [['Juri', 'Tema', 'Lirik', 'Musik', 'Kreativitas', 'Jemaat', 'Total']]

    for _, eval_row in song_evals.iterrows():
        judge_name = "Unknown"
        try:
            judge_row = judges_df[judges_df['id'] == eval_row['judge_id']]
            if not judge_row.empty:
                judge_name = judge_row.iloc[0]['name']
        except:
            pass

        rubric_scores_json = eval_row['rubric_scores']
        if isinstance(rubric_scores_json, str):
            import json
            rubric_scores_json = json.loads(rubric_scores_json)

        row = [judge_name]
        for rubric_key in ['tema', 'lirik', 'musik', 'kreativ', 'jemaat']:
            score = rubric_scores_json.get(rubric_key, 0)
            row.append(f"{score}/5" if score > 0 else "-")

        total_score = eval_row['total_score']
        score_100 = (total_score / 25) * 100
        row.append(f"{score_100:.1f}/100")

        judge_data.append(row)

    judge_table = Table(judge_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
    judge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(judge_table)
    story.append(Spacer(1, 15))

    # Add judge notes section - ALL NOTES
    story.append(Paragraph("<b>📝 Catatan dari Juri:</b>", styles['Heading3']))
    story.append(Spacer(1, 10))

    has_notes = False
    for _, eval_row in song_evals.iterrows():
        judge_name = "Unknown"
        try:
            judge_row = judges_df[judges_df['id'] == eval_row['judge_id']]
            if not judge_row.empty:
                judge_name = judge_row.iloc[0]['name']
        except:
            pass

        notes = eval_row.get('notes', '')
        if notes and notes.strip():
            has_notes = True
            story.append(Paragraph(f"<b>{judge_name}:</b>", styles['Normal']))
            story.append(Paragraph(notes, styles['Normal']))
            story.append(Spacer(1, 8))

    if not has_notes:
        story.append(Paragraph("Tidak ada catatan khusus dari juri.", styles['Normal']))

    story.append(Spacer(1, 20))

def _add_winner_comparison(story, current_winner, other_winners, styles):
    """Add comparison with other winners"""
    if not other_winners:
        return

    story.append(Paragraph("<b>🔍 Perbandingan dengan Pesaing:</b>", styles['Heading3']))
    story.append(Spacer(1, 10))

    # Compare with runner-up
    runner_up = other_winners[0]
    score_diff = current_winner['score_100'] - runner_up['score_100']

    comparison_text = f"""
    <b>Dibandingkan dengan Runner-up ({runner_up['title']}):</b><br/>
    • Selisih skor: {score_diff:.1f} poin<br/>
    • Keunggulan: {score_diff/current_winner['score_100']*100:.1f}% lebih tinggi<br/>
    • Status: {'Unggul signifikan' if score_diff > 5 else 'Unggul tipis' if score_diff > 2 else 'Sangat ketat'}
    """

    story.append(Paragraph(comparison_text, styles['Normal']))
    story.append(Spacer(1, 15))

def _add_comprehensive_song_analysis(story, song, song_evals, styles):
    """Add comprehensive analysis including AI analysis, charts, and detailed insights"""
    try:
        story.append(Paragraph("🎯 Analisis Komprehensif Lagu", styles['Heading1']))
        story.append(Spacer(1, 20))

        # Get AI analysis
        try:
            ai_suggestions, ai_explanations = build_suggestions_with_explanations(song)

            if ai_suggestions:
                story.append(Paragraph("🤖 Analisis AI", styles['Heading2']))
                story.append(Spacer(1, 10))

                # AI scores table
                ai_data = [['Aspek', 'Skor AI', 'Penjelasan']]

                rubric_names = {
                    'tema': 'Kesesuaian Tema',
                    'lirik': 'Kekuatan Lirik',
                    'musik': 'Kekayaan Musik'
                }

                for rubric_key, score in ai_suggestions.items():
                    rubric_name = rubric_names.get(rubric_key, rubric_key.title())
                    explanation = ai_explanations.get(rubric_key, 'Tidak ada penjelasan')
                    ai_data.append([rubric_name, f"{score}/5", explanation])

                ai_table = Table(ai_data, colWidths=[2*inch, 1*inch, 3.5*inch])
                ai_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))

                story.append(ai_table)
                story.append(Spacer(1, 20))
        except Exception as e:
            story.append(Paragraph(f"AI analysis tidak tersedia: {str(e)}", styles['Normal']))
            story.append(Spacer(1, 10))

        # Musical Analysis
        story.append(Paragraph("🎵 Analisis Musikal", styles['Heading2']))
        story.append(Spacer(1, 10))

        # Chord analysis
        chords_text = song.get('chords_list', '')
        if chords_text:
            story.append(Paragraph("<b>Analisis Chord:</b>", styles['Heading3']))

            # Parse chords
            chord_list = [chord.strip() for chord in chords_text.split() if chord.strip()]
            unique_chords = list(dict.fromkeys(chord_list))

            # Chord statistics
            chord_stats = [
                ['Total Chord', str(len(chord_list))],
                ['Chord Unik', str(len(unique_chords))],
                ['Kompleksitas', f"{len(unique_chords)/max(1, len(chord_list))*100:.1f}%"],
                ['Progesi', ' → '.join(unique_chords[:8]) + (' → ...' if len(unique_chords) > 8 else '')]
            ]

            chord_table = Table(chord_stats, colWidths=[1.5*inch, 4.5*inch])
            chord_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(chord_table)
            story.append(Spacer(1, 15))

            # Chord complexity analysis
            try:
                from services.scoring_service import scoring_service
                complexity_score = scoring_service.score_harmonic_richness(chord_list)

                complexity_text = f"""
                <b>Tingkat Kompleksitas Harmoni:</b> {complexity_score}/5<br/>
                """

                if complexity_score >= 4:
                    complexity_text += "• Harmoni sangat kaya dengan variasi chord yang kompleks<br/>"
                elif complexity_score >= 3:
                    complexity_text += "• Harmoni cukup kaya dengan beberapa variasi menarik<br/>"
                else:
                    complexity_text += "• Harmoni sederhana, mudah dimainkan jemaat<br/>"

                story.append(Paragraph(complexity_text, styles['Normal']))
                story.append(Spacer(1, 10))
            except:
                pass
        else:
            story.append(Paragraph("Data chord tidak tersedia untuk analisis.", styles['Normal']))
            story.append(Spacer(1, 10))

        # Lyrics Analysis
        lyrics_text = song.get('lyrics_text', '')
        if lyrics_text:
            story.append(Paragraph("📝 Analisis Lirik", styles['Heading2']))
            story.append(Spacer(1, 10))

            # Basic lyrics statistics
            words = lyrics_text.split()
            lines = lyrics_text.split('\n')

            lyrics_stats = [
                ['Total Kata', str(len(words))],
                ['Total Baris', str(len(lines))],
                ['Rata-rata Kata per Baris', f"{len(words)/max(1, len(lines)):.1f}"],
                ['Panjang Rata-rata Kata', f"{sum(len(word) for word in words)/max(1, len(words)):.1f} huruf"]
            ]

            lyrics_table = Table(lyrics_stats, colWidths=[2*inch, 2*inch])
            lyrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(lyrics_table)
            story.append(Spacer(1, 15))

            # Theme analysis
            theme_words = ['waktu', 'bersama', 'keluarga', 'harta', 'berharga', 'kasih', 'cinta', 'tuhan', 'berkat', 'syukur']
            theme_count = sum(1 for word in words if any(theme in word.lower() for theme in theme_words))
            theme_percentage = (theme_count / max(1, len(words))) * 100

            theme_analysis = f"""
            <b>Analisis Tema "Waktu Bersama Keluarga":</b><br/>
            • Kata-kata terkait tema: {theme_count} dari {len(words)} kata ({theme_percentage:.1f}%)<br/>
            • Relevansi tema: {'Sangat tinggi' if theme_percentage > 10 else 'Tinggi' if theme_percentage > 5 else 'Sedang' if theme_percentage > 2 else 'Rendah'}<br/>
            """

            story.append(Paragraph(theme_analysis, styles['Normal']))
            story.append(Spacer(1, 15))

            # Show lyrics with theme words highlighted (first 200 words)
            story.append(Paragraph("<b>Cuplikan Lirik (dengan highlight kata tema):</b>", styles['Heading3']))

            # Highlight theme words in lyrics
            highlighted_lyrics = lyrics_text
            for theme_word in theme_words:
                highlighted_lyrics = highlighted_lyrics.replace(
                    theme_word, f"<b><u>{theme_word}</u></b>"
                )
                highlighted_lyrics = highlighted_lyrics.replace(
                    theme_word.title(), f"<b><u>{theme_word.title()}</u></b>"
                )

            # Truncate if too long
            if len(highlighted_lyrics) > 800:
                highlighted_lyrics = highlighted_lyrics[:800] + "..."

            story.append(Paragraph(highlighted_lyrics, styles['Normal']))
            story.append(Spacer(1, 15))
        else:
            story.append(Paragraph("📝 Analisis Lirik", styles['Heading2']))
            story.append(Paragraph("Teks lirik tidak tersedia untuk analisis.", styles['Normal']))
            story.append(Spacer(1, 10))

    except Exception as e:
        story.append(Paragraph(f"Error dalam analisis komprehensif: {str(e)}", styles['Normal']))

def create_download_link(pdf_bytes: bytes, filename: str) -> str:
    """Create download link for PDF"""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Download {filename}</a>'

def render_evaluation_history_tab(current_user):
    """Render evaluation history tab"""
    st.header("📋 History Penilaian Saya")

    # Get effective user (handles admin impersonation)
    effective_user = get_effective_user(current_user)
    judge_id = effective_user.get('judge_id')
    judge_name = effective_user.get('judge_name') or effective_user.get('full_name', 'Unknown Judge')

    if not judge_id:
        st.error("Judge ID not found. Please contact administrator.")
        return

    # Get all evaluations by this judge
    evaluations_df = cache_service.get_cached_evaluations(judge_id=judge_id)

    if evaluations_df.empty:
        st.info("Anda belum melakukan penilaian apapun.")
        return

    st.success(f"📊 Total penilaian: **{len(evaluations_df)}** lagu")

    # Calculate overall completion status
    songs_df = cache_service.get_cached_songs()
    rubrics_df = cache_service.get_cached_rubrics()
    total_songs = len(songs_df)
    total_rubrics = len(rubrics_df)

    completed_songs = 0
    all_evaluations_final = True

    for _, evaluation in evaluations_df.iterrows():
        rubric_scores = evaluation['rubric_scores']
        if isinstance(rubric_scores, str):
            import json
            rubric_scores = json.loads(rubric_scores)
        elif not isinstance(rubric_scores, dict):
            rubric_scores = {}

        completed_rubrics = len([score for score in rubric_scores.values() if score and score > 0])
        if completed_rubrics == total_rubrics:
            completed_songs += 1

        # Check if this evaluation is final
        if not evaluation.get('is_final_submitted', False):
            all_evaluations_final = False

    # Show Final Submit section if all songs are complete
    if completed_songs == total_songs and not all_evaluations_final:
        st.markdown("---")
        st.markdown("### 🔐 Submit Final - Finalisasi Semua Penilaian")

        st.success(f"🎯 **Semua {total_songs} lagu sudah dinilai lengkap!**")
        st.warning("⚠️ **Perhatian**: Setelah submit final, SEMUA penilaian tidak dapat diedit lagi!")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔐 Submit Final & Lock Semua",
                       type="primary",
                       width='stretch',
                       help="Submit final dan kunci SEMUA penilaian - tidak dapat diedit lagi"):

                # Final submit all evaluations
                success_count = 0
                for _, evaluation in evaluations_df.iterrows():
                    if db_service.final_submit_evaluation(evaluation['id']):
                        success_count += 1

                if success_count == len(evaluations_df):
                    st.success(f"✅ Berhasil submit final {success_count} penilaian!")
                    # Controlled balloon animation - only show occasionally
                    if should_show_balloons():
                        st.balloons()
                    st.info("🔒 Semua penilaian sekarang terkunci dan tidak dapat diedit")

                    # Add timestamp
                    from datetime import datetime
                    import pytz
                    jakarta_tz = pytz.timezone('Asia/Jakarta')
                    now = datetime.now(jakarta_tz)
                    st.info(f"📅 Waktu finalisasi: {now.strftime('%d/%m/%Y %H:%M:%S')} WIB")

                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Hanya berhasil submit {success_count}/{len(evaluations_df)} penilaian")

        with col2:
            st.markdown("**📋 Checklist Final:**")
            st.markdown(f"• ✅ Semua {total_songs} lagu dinilai")
            st.markdown(f"• ✅ Semua {total_rubrics} kriteria terisi")
            st.markdown("• ✅ Skor sudah sesuai")
            st.markdown("• ⚠️ Tidak dapat diedit lagi")

    elif all_evaluations_final:
        st.markdown("---")
        st.success("🔒 **Semua Penilaian Sudah Final** - Terima kasih atas partisipasi Anda!")

        # Show final submission timestamp if available
        final_evaluations = [eval for _, eval in evaluations_df.iterrows() if eval.get('final_submitted_at')]
        if final_evaluations:
            latest_final = max(final_evaluations, key=lambda x: x.get('final_submitted_at', ''))
            final_time = latest_final.get('final_submitted_at')
            if final_time:
                from datetime import datetime
                if isinstance(final_time, str):
                    final_time = datetime.fromisoformat(final_time.replace('Z', '+00:00'))
                st.info(f"📅 Waktu finalisasi: {final_time.strftime('%d/%m/%Y %H:%M:%S')} WIB")

    elif completed_songs < total_songs:
        st.markdown("---")
        st.info(f"⏳ **Progress**: {completed_songs}/{total_songs} lagu sudah dinilai lengkap")
        st.info("💡 Lengkapi semua penilaian untuk dapat melakukan submit final")

    # Show evaluations in a nice format
    for _, evaluation in evaluations_df.iterrows():
        # Convert to 100-point scale for display
        score_100 = (evaluation['total_score'] / 25) * 100
        with st.expander(f"🎵 {evaluation['song']['title']} - Skor: {score_100:.1f}/100"):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Show rubric scores
                st.markdown("**📋 Detail Penilaian:**")
                rubric_scores = evaluation['rubric_scores']

                if isinstance(rubric_scores, str):
                    import json
                    rubric_scores = json.loads(rubric_scores)

                # Get rubrics for display names
                rubrics_df = cache_service.get_cached_rubrics()

                for _, rubric in rubrics_df.iterrows():
                    if rubric['rubric_key'] in rubric_scores:
                        score = rubric_scores[rubric['rubric_key']]
                        st.markdown(f"• **{rubric['aspect_name']}**: {score}/{rubric['max_score']}")

                # Show notes if any
                if evaluation.get('notes'):
                    st.markdown("**📝 Catatan:**")
                    st.text(evaluation['notes'])

            with col2:
                # Convert to 100-point scale for display
                score_100 = (evaluation['total_score'] / 25) * 100
                st.metric("Total Skor", f"{score_100:.1f}/100")

                # Show timestamp
                created_at = evaluation.get('created_at')
                if created_at:
                    from datetime import datetime
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    st.caption(f"Dinilai: {created_at.strftime('%d/%m/%Y %H:%M')}")

                # Add edit button
                st.markdown("---")
                if st.button(f"✏️ Edit Penilaian",
                           key=f"edit_{evaluation['song']['id']}",
                           help="Kembali ke tab penilaian untuk mengedit",
                           width='stretch'):
                    # Set selected song in session state
                    st.session_state.selected_song = evaluation['song']['title']
                    st.session_state.active_tab = "📝 Penilaian"
                    st.rerun()

                # Check completion status
                rubric_scores = evaluation['rubric_scores']
                if isinstance(rubric_scores, str):
                    import json
                    rubric_scores = json.loads(rubric_scores)
                elif not isinstance(rubric_scores, dict):
                    rubric_scores = {}

                rubrics_df = cache_service.get_cached_rubrics()
                total_rubrics = len(rubrics_df)
                completed_rubrics = len([score for score in rubric_scores.values() if score and score > 0])

                if completed_rubrics == total_rubrics:
                    st.success(f"✅ Lengkap ({completed_rubrics}/{total_rubrics})")
                elif completed_rubrics > 0:
                    st.warning(f"🔄 Parsial ({completed_rubrics}/{total_rubrics})")
                else:
                    st.info(f"⏳ Belum lengkap ({completed_rubrics}/{total_rubrics})")

def render_analytics_tab():
    """Render analytics tab with comprehensive analysis features"""
    st.header("📊 Hasil & Analitik")

    # Get current user for judge context
    current_user = st.session_state.get('current_user')
    if current_user:
        effective_user = get_effective_user(current_user)
        judge_id = effective_user.get('judge_id')
        judge_name = effective_user.get('judge_name') or effective_user.get('full_name', 'Unknown Judge')
    else:
        judge_id = None
        judge_name = "Guest"

    # Create streamlined tabs - CENTRALIZED EXPORT
    tab_analisis, tab_hasil, tab_global = st.tabs([
        "📈 Analisis & Export",
        "🏆 Hasil Lomba",
        "🌐 Global Analytics"
    ])

    with tab_analisis:
        if judge_id:
            # Combined analysis and export in one tab
            render_combined_analysis_export_tab(judge_id, judge_name)
        else:
            st.warning("⚠️ Login sebagai juri untuk melihat analisis detail")

    with tab_hasil:
        if judge_id:
            render_hasil_tab(judge_id, judge_name)
        else:
            st.warning("⚠️ Login sebagai juri untuk melihat hasil detail")

    with tab_global:
        render_global_analytics_tab()

def render_combined_analysis_export_tab(judge_id, judge_name):
    """Render combined analysis and export tab with centralized download options"""

    # ==================== ANALYSIS SECTION ====================
    st.markdown("### 📈 Analisis Komprehensif")

    # Quick analysis overview
    render_analisis_tab(judge_id, judge_name)

    st.markdown("---")

    # ==================== CENTRALIZED EXPORT SECTION ====================
    st.markdown("### 📥 **Download & Export Center**")
    st.markdown("*Semua opsi download tersedia di satu tempat*")

    # Create beautiful export sections
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 2rem; border-radius: 15px; margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h4 style="color: #333; margin-bottom: 1.5rem;">🎯 Export Options</h4>
    </div>
    """, unsafe_allow_html=True)

    # ==================== QUICK EXPORTS ====================
    st.markdown("#### 🚀 Quick Downloads")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Excel comprehensive export
        if st.button("📊 Excel Lengkap", type="primary", width='stretch', key="quick_excel"):
            try:
                excel_data = export_service.export_comprehensive_excel()
                st.download_button(
                    "📥 Download Excel",
                    data=excel_data,
                    file_name=f"lomba_lengkap_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_quick_excel"
                )
                st.success("✅ Excel ready!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    with col2:
        # PDF leaderboard
        if st.button("📄 PDF Hasil", type="primary", width='stretch', key="quick_pdf"):
            if PDF_AVAILABLE:
                try:
                    leaderboard_df = analytics_service.get_global_leaderboard()
                    pdf_data = export_service.export_leaderboard_pdf(leaderboard_df)
                    st.download_button(
                        "📥 Download PDF",
                        data=pdf_data,
                        file_name=f"hasil_lomba_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="dl_quick_pdf"
                    )
                    st.success("✅ PDF ready!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("❌ PDF not available")

    with col3:
        # CSV scores export
        if st.button("📊 CSV Skor", type="secondary", width='stretch', key="quick_csv"):
            try:
                evaluations_df = cache_service.get_cached_evaluations()
                if not evaluations_df.empty:
                    csv_data = evaluations_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_data,
                        file_name=f"skor_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="dl_quick_csv"
                    )
                    st.success("✅ CSV ready!")
                else:
                    st.warning("⚠️ No data available")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    with col4:
        # JSON export
        if st.button("📄 JSON Data", type="secondary", width='stretch', key="quick_json"):
            try:
                evaluations_df = cache_service.get_cached_evaluations()
                if not evaluations_df.empty:
                    json_data = evaluations_df.to_json(orient='records', indent=2)
                    st.download_button(
                        "📥 Download JSON",
                        data=json_data,
                        file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        key="dl_quick_json"
                    )
                    st.success("✅ JSON ready!")
                else:
                    st.warning("⚠️ No data available")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # ==================== DETAILED EXPORTS ====================
    st.markdown("#### 📋 Detailed Reports")

    # Per song reports
    with st.expander("🎵 **Per Song Reports**", expanded=False):
        songs_df = cache_service.get_cached_songs()

        col1, col2 = st.columns([2, 1])

        with col1:
            selected_song = st.selectbox(
                "Pilih lagu untuk generate laporan:",
                options=[f"{row['id']}. {row['title']}" for _, row in songs_df.iterrows()],
                key="detailed_song_selector"
            )

        with col2:
            if st.button("📄 Generate Report", type="primary", width='stretch', key="generate_song_report"):
                if PDF_AVAILABLE:
                    try:
                        song_id = int(selected_song.split('.')[0])
                        with st.spinner(f"🔄 Generating report..."):
                            pdf_bytes = generate_song_report_pdf(song_id)
                            song_title = selected_song.split('. ')[1]
                            filename = f"laporan_{song_title.replace(' ', '_')}.pdf"

                            st.download_button(
                                label="📥 Download Song Report",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                key="dl_song_report"
                            )
                            st.success("✅ Song report generated!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("❌ PDF generation not available")

    # Winner reports
    with st.expander("🏆 **Winner Reports**", expanded=False):
        # First row: Winner Report and Certificates in columns
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🥇 Winner Report", type="primary", use_container_width=True, key="winner_report"):
                if PDF_AVAILABLE:
                    try:
                        with st.spinner("🔄 Generating winner report..."):
                            pdf_bytes = generate_winner_report_pdf()
                            filename = f"pemenang_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

                            st.download_button(
                                label="📥 Download Winner Report",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                key="dl_winner_report"
                            )
                            st.success("✅ Winner report generated!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("❌ PDF generation not available")

        with col2:
            if st.button("🎖️ Certificates", type="secondary", use_container_width=True, key="certificates"):
                render_certificate_generation()

        # Second row: Winner Analysis full width
        st.markdown("---")
        if st.button("📊 Winner Analysis", type="secondary", use_container_width=True, key="winner_analysis"):
            render_winner_analysis()

    # Judge Analytics - separate section
    with st.expander("🧠 **Judge Analytics**", expanded=False):
        render_judge_insights()

def render_judge_insights():
    """Render judge insights and patterns analysis"""
    st.markdown("### 🧠 Judge Insights & Patterns")

    try:
        # Get judge analytics
        from services.analytics_service import analytics_service
        judge_analytics_df = analytics_service.get_judge_analytics()
        evaluations_df = cache_service.get_cached_evaluations()

        if judge_analytics_df.empty:
            st.warning("Judge analytics data not available")
            return

        if evaluations_df.empty:
            st.warning("No evaluation data available")
            return

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**👨‍⚖️ Judge Scoring Patterns:**")

            # Analyze judge tendencies
            judge_insights = []
            for _, judge in judge_analytics_df.iterrows():
                avg_score = judge['avg_score']
                if avg_score > 75:
                    tendency = "🟢 Lenient (skor tinggi)"
                elif avg_score < 60:
                    tendency = "🔴 Strict (skor rendah)"
                else:
                    tendency = "🟡 Moderate (skor seimbang)"

                judge_insights.append({
                    'name': judge['name'],
                    'avg_score': avg_score,
                    'tendency': tendency,
                    'evaluations': judge['evaluations_count']
                })

            # Display judge patterns
            for insight in judge_insights:
                st.markdown(f"**{insight['name']}**")
                st.markdown(f"• Rata-rata skor: {insight['avg_score']:.1f}/100")
                st.markdown(f"• Pola: {insight['tendency']}")
                st.markdown(f"• Total evaluasi: {insight['evaluations']}")
                st.markdown("---")

        with col2:
            st.markdown("**📊 Overall Statistics:**")

            # Overall statistics
            total_evaluations = len(evaluations_df)
            unique_judges = len(evaluations_df['judge_id'].unique())
            unique_songs = len(evaluations_df['song_id'].unique())

            st.metric("Total Evaluations", total_evaluations)
            st.metric("Active Judges", unique_judges)
            st.metric("Songs Evaluated", unique_songs)

            # Average scores by judge
            avg_by_judge = judge_analytics_df['avg_score'].mean()
            st.metric("Average Judge Score", f"{avg_by_judge:.1f}/100")

    except Exception as e:
        st.error(f"❌ Error in judge insights: {e}")

def render_certificate_generation():
    """Generate certificates for participants"""
    st.markdown("### 🎖️ Certificate Generation")

    try:
        # Get songs data
        songs_df = cache_service.get_cached_songs()
        if songs_df.empty:
            st.warning("📋 No songs found")
            return

        # Sort songs by ID for proper ordering
        songs_df['id_int'] = pd.to_numeric(songs_df['id'], errors='coerce')
        songs_df = songs_df.sort_values('id_int')

        # Certificate generation options
        col1, col2 = st.columns([2, 1])

        with col1:
            cert_type = st.selectbox(
                "Certificate Type:",
                ["🏆 Winner Certificates", "🎵 Participation Certificates", "📜 All Certificates"],
                help="Choose what type of certificates to generate"
            )

        with col2:
            if st.button("🎖️ Generate All", type="primary"):
                with st.spinner("Generating certificates..."):
                    # Simulate certificate generation
                    progress_bar = st.progress(0)
                    for i, (_, song) in enumerate(songs_df.iterrows()):
                        progress_bar.progress((i + 1) / len(songs_df))
                        # Here you would implement actual certificate generation
                        # For now, just simulate the process
                        import time
                        time.sleep(0.1)

                    st.success(f"✅ Generated {len(songs_df)} certificates successfully!")

        # Display certificate preview/status
        st.markdown("#### 📋 Certificate Status")

        for _, song in songs_df.iterrows():
            with st.expander(f"🎵 {song['id']}. {song['title']} - {song['composer']}"):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Composer:** {song['composer']}")
                    st.write(f"**Title:** {song['title']}")

                with col2:
                    # Check if certificate exists (placeholder logic)
                    cert_exists = song.get('certificate_path') is not None
                    if cert_exists:
                        st.success("✅ Generated")
                    else:
                        st.warning("⏳ Pending")

                with col3:
                    if cert_exists:
                        st.button("📥 Download", key=f"cert_download_{song['id']}")
                    else:
                        if st.button("🎖️ Generate", key=f"cert_generate_{song['id']}"):
                            st.info("Certificate generation would happen here")

    except Exception as e:
        st.error(f"❌ Error in certificate generation: {e}")

def render_winner_analysis():
    """Detailed analysis of winners"""
    st.markdown("### 📊 Winner Analysis")

    try:
        # Get leaderboard data (use analytics service for proper 100-point scale)
        from services.analytics_service import analytics_service
        leaderboard_df = analytics_service.get_global_leaderboard()
        if leaderboard_df.empty:
            st.warning("📊 No evaluation data available for analysis")
            return

        # Get configuration
        config = cache_service.get_cached_config()
        winners_count = int(config.get('WINNERS_TOP_N', 3))

        # Get top winners
        winners_df = leaderboard_df.head(winners_count)

        # Analysis tabs - using 2 main tabs for better layout
        tab1, tab2 = st.tabs(["📊 Score Analysis", "🎯 Detailed Breakdown"])

        with tab1:
            st.markdown("#### 🏆 Top Winners")

            for i, (_, winner) in enumerate(winners_df.iterrows(), 1):
                rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏆"

                with st.container():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                                padding: 1rem; border-radius: 10px; margin-bottom: 1rem;
                                border-left: 4px solid {'#FFD700' if i == 1 else '#C0C0C0' if i == 2 else '#CD7F32'};">
                        <h4 style="margin: 0;">{rank_emoji} Rank {i}: {winner['title']}</h4>
                        <p style="margin: 0.5rem 0;"><strong>Composer:</strong> {winner['composer']}</p>
                        <p style="margin: 0;"><strong>Score:</strong> {winner['avg_score']:.2f}/100
                           ({winner['unique_judges']} judges)</p>
                    </div>
                    """, unsafe_allow_html=True)

        with tab2:
            st.markdown("#### 📈 Score Distribution Analysis")

            # Score comparison chart
            import plotly.express as px

            fig = px.bar(
                winners_df,
                x='title',
                y='avg_score',
                title="Winner Scores Comparison",
                labels={'avg_score': 'Average Score', 'title': 'Song Title'},
                color='avg_score',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            st.markdown("#### 📊 Statistical Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Highest Score", f"{winners_df['avg_score'].max():.2f}")
            with col2:
                st.metric("Average Score", f"{winners_df['avg_score'].mean():.2f}")
            with col3:
                st.metric("Score Range", f"{winners_df['avg_score'].max() - winners_df['avg_score'].min():.2f}")

            st.markdown("---")

            # Detailed Winner Analysis
            st.markdown("#### 🎯 Detailed Winner Analysis")

            # Get detailed evaluations for winners
            evaluations_df = cache_service.get_cached_evaluations()
            rubrics_df = cache_service.get_cached_rubrics()
            judges_df = cache_service.get_cached_judges()

            if not evaluations_df.empty and not rubrics_df.empty:
                for i, (_, winner) in enumerate(winners_df.iterrows(), 1):
                    rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏆"

                    with st.expander(f"{rank_emoji} {winner['title']} - Comprehensive Analysis", expanded=(i==1)):
                        # Get evaluations for this song
                        song_evals = evaluations_df[evaluations_df['song_id'] == winner['song_id']]

                        if not song_evals.empty:
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.markdown("**📊 Rubrik Scores dari Setiap Juri:**")

                                # Create detailed rubric table
                                rubric_table_data = []
                                header = ['Juri', 'Tema', 'Lirik', 'Musik', 'Kreativitas', 'Jemaat', 'Total']
                                rubric_table_data.append(header)

                                # Collect rubric averages for analysis
                                rubric_totals = {'tema': [], 'lirik': [], 'musik': [], 'kreativ': [], 'jemaat': []}

                                for _, eval_row in song_evals.iterrows():
                                    # Get judge name
                                    judge_name = "Unknown"
                                    try:
                                        judge_row = judges_df[judges_df['id'] == eval_row['judge_id']]
                                        if not judge_row.empty:
                                            judge_name = judge_row.iloc[0]['name']
                                    except:
                                        pass

                                    # Parse rubric scores
                                    rubric_scores = eval_row['rubric_scores']
                                    if isinstance(rubric_scores, str):
                                        import json
                                        rubric_scores = json.loads(rubric_scores)

                                    row = [judge_name]
                                    for rubric_key in ['tema', 'lirik', 'musik', 'kreativ', 'jemaat']:
                                        score = rubric_scores.get(rubric_key, 0)
                                        row.append(f"{score}/5" if score > 0 else "-")
                                        if score > 0:
                                            rubric_totals[rubric_key].append(score)

                                    # Total score
                                    total_score = eval_row['total_score']
                                    score_100 = (total_score / 25) * 100
                                    row.append(f"{score_100:.1f}/100")

                                    rubric_table_data.append(row)

                                # Display table
                                import pandas as pd
                                df_display = pd.DataFrame(rubric_table_data[1:], columns=rubric_table_data[0])
                                st.dataframe(df_display, use_container_width=True)

                            with col2:
                                st.markdown("**🎯 Analisis Kekuatan & Kelemahan:**")

                                # Analyze strengths and weaknesses
                                strengths = []
                                good_areas = []
                                weaknesses = []

                                for rubric_key, scores in rubric_totals.items():
                                    if scores:
                                        avg_score = sum(scores) / len(scores)

                                        # Get rubric name
                                        rubric_name = rubric_key.title()
                                        try:
                                            rubric_row = rubrics_df[rubrics_df['rubric_key'] == rubric_key]
                                            if not rubric_row.empty:
                                                rubric_name = rubric_row.iloc[0]['aspect_name']
                                        except:
                                            pass

                                        if avg_score >= 4.0:
                                            strengths.append(f"• **{rubric_name}**: {avg_score:.1f}/5 - Sangat baik")
                                        elif avg_score >= 3.0:
                                            good_areas.append(f"• **{rubric_name}**: {avg_score:.1f}/5 - Cukup baik")
                                        else:
                                            weaknesses.append(f"• **{rubric_name}**: {avg_score:.1f}/5 - Perlu perbaikan")

                                if strengths:
                                    st.markdown("**🌟 Kekuatan Utama:**")
                                    for strength in strengths:
                                        st.markdown(strength)
                                    st.markdown("")

                                if good_areas:
                                    st.markdown("**✅ Area yang Baik:**")
                                    for area in good_areas:
                                        st.markdown(area)
                                    st.markdown("")

                                if weaknesses:
                                    st.markdown("**🔧 Area yang Perlu Diperbaiki:**")
                                    for weakness in weaknesses:
                                        st.markdown(weakness)
                                    st.markdown("")

                                # Overall assessment
                                overall_score = winner['avg_score']
                                st.markdown("**📊 Penilaian Keseluruhan:**")
                                if overall_score >= 80:
                                    assessment = "Lagu berkualitas sangat tinggi dengan eksekusi yang excellent."
                                elif overall_score >= 70:
                                    assessment = "Lagu berkualitas baik dengan beberapa aspek yang menonjol."
                                elif overall_score >= 60:
                                    assessment = "Lagu cukup baik dengan potensi pengembangan."
                                else:
                                    assessment = "Lagu perlu peningkatan di beberapa aspek."

                                st.info(f"Skor: {overall_score:.1f}/100. {assessment}")

                            # Comparison with other winners
                            if i < len(winners_df):
                                st.markdown("---")
                                st.markdown("**🔍 Perbandingan dengan Pesaing:**")

                                if i < len(winners_df):
                                    # Compare with next winner
                                    next_winners = winners_df.iloc[i:].reset_index(drop=True)
                                    if len(next_winners) > 0:
                                        runner_up = next_winners.iloc[0]
                                        score_diff = winner['avg_score'] - runner_up['avg_score']

                                        col_comp1, col_comp2 = st.columns(2)
                                        with col_comp1:
                                            st.metric(
                                                f"Selisih dengan #{i+1}",
                                                f"{score_diff:.1f} poin",
                                                f"{score_diff/winner['avg_score']*100:.1f}% lebih tinggi"
                                            )

                                        with col_comp2:
                                            if score_diff > 5:
                                                status = "🔥 Unggul signifikan"
                                            elif score_diff > 2:
                                                status = "✅ Unggul jelas"
                                            else:
                                                status = "⚡ Persaingan ketat"
                                            st.info(f"Status: {status}")
                        else:
                            st.warning("No detailed evaluation data found for this song")
            else:
                st.warning("Detailed evaluation data not available")



    except Exception as e:
        st.error(f"❌ Error in winner analysis: {e}")

def render_global_analytics_tab():
    """Render global analytics tab with GLOBAL data (all judges)"""
    st.markdown("### 🌐 Analitik Global")
    st.info("📈 Analitik ini menampilkan data dari SEMUA juri, bukan hanya juri aktif")

    # Get configuration
    config = cache_service.get_cached_config()
    show_author = config.get('SHOW_AUTHOR', 'True').lower() == 'true'

    # Get global analytics
    leaderboard_df = analytics_service.get_global_leaderboard()
    judge_analytics_df = analytics_service.get_judge_analytics()
    rubric_analytics_df = analytics_service.get_rubric_analytics()
    insights = analytics_service.generate_insights()

    # Get winners count from config
    winners_count = int(config.get('WINNERS_TOP_N', 3))
    show_winners_auto = config.get('SHOW_WINNERS_AUTOMATIC', 'False').lower() == 'true'

    if leaderboard_df.empty:
        st.warning("Belum ada data penilaian untuk dianalisis.")
        return

    # Display leaderboard
    st.subheader("🏆 Leaderboard Global")

    # Show winners section if enabled
    if show_winners_auto and len(leaderboard_df) >= winners_count:
        st.markdown(f"### 🎉 TOP {winners_count} PEMENANG")

        winners_df = leaderboard_df.head(winners_count)

        for i, (_, row) in enumerate(winners_df.iterrows(), 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"🏆"

            with st.container():
                st.markdown(f"""
                <div style='background: linear-gradient(90deg, #ffd700, #ffed4e); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 5px solid #ff6b35;'>
                    <h4 style='margin: 0; color: #333;'>{rank_emoji} JUARA {i}: {row['title']}</h4>
                    <p style='margin: 5px 0; color: #666;'>Skor: {row['avg_score']:.2f}/100 ({row['unique_judges']} juri)</p>
                    {f"<p style='margin: 0; color: #666; font-style: italic;'>Pencipta: {row['composer']}</p>" if show_author else ""}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    # Select columns based on SHOW_AUTHOR config
    if show_author:
        display_columns = ['rank', 'title', 'composer', 'avg_score', 'score_std', 'unique_judges']
    else:
        display_columns = ['rank', 'title', 'avg_score', 'score_std', 'unique_judges']

    st.dataframe(
        leaderboard_df[display_columns],
        width='stretch',
        hide_index=True
    )
    
    # Leaderboard chart
    chart = analytics_service.create_leaderboard_chart(leaderboard_df)
    st.plotly_chart(chart, width='stretch')
    
    # Judge comparison
    if not judge_analytics_df.empty:
        st.subheader("🧑‍⚖️ Perbandingan Juri")
        judge_chart = analytics_service.create_judge_comparison_chart(judge_analytics_df)
        st.plotly_chart(judge_chart, width='stretch')
    
    # Rubric analysis
    if not rubric_analytics_df.empty:
        st.subheader("📋 Analisis Rubrik")
        rubric_chart = analytics_service.create_rubric_impact_chart(rubric_analytics_df)
        st.plotly_chart(rubric_chart, width='stretch')
    
    # Score distribution
    st.subheader("📈 Distribusi Skor")
    dist_chart = analytics_service.create_score_distribution_chart()
    st.plotly_chart(dist_chart, width='stretch')
    
    # Insights
    if insights:
        st.subheader("🔍 Insights")
        
        if 'competition' in insights:
            comp = insights['competition']
            st.markdown(f"**🏆 Pemimpin:** {comp.get('leader', 'N/A')} ({comp.get('leader_score', 0):.2f}/100)")

            if comp.get('closest_competition'):
                cc = comp['closest_competition']
                st.markdown(f"**⚔️ Persaingan Terketat:** {cc['song1']} vs {cc['song2']} (selisih {cc['difference']:.2f}/100)")
        
        if 'judges' in insights:
            judges = insights['judges']
            # Only show "most active" if there's actually a difference
            if 'most_active' in judges:
                st.markdown(f"**👨‍⚖️ Juri Paling Aktif:** {judges['most_active']} (berdasarkan jumlah evaluasi)")
            st.markdown(f"**😊 Juri Paling Longgar:** {judges.get('most_lenient', 'N/A')} (rata-rata skor tertinggi)")
            st.markdown(f"**😤 Juri Paling Ketat:** {judges.get('most_strict', 'N/A')} (rata-rata skor terendah)")
            st.markdown(f"**🎯 Juri Paling Konsisten:** {judges.get('most_consistent', 'N/A')} (standar deviasi terendah)")
    
    # Note about exports
    st.info("💡 **Export options tersedia di tab 'Analisis & Export'**")

    # Certificate download section
    st.subheader("🏆 Download Sertifikat")

    # Check certificate mode from configuration
    config = cache_service.get_cached_config()
    certificate_mode = config.get('CERTIFICATE_MODE', 'GENERATE').upper()

    if certificate_mode == 'STORAGE':
        # Use pre-generated certificates from Supabase storage
        st.info("📁 Menggunakan sertifikat dari storage")

        # Get bucket and folder from config
        bucket_name = config.get('CERTIFICATE_BUCKET', 'song-contest-files')
        folder_name = config.get('CERTIFICATE_FOLDER', 'certificates')

        # Since we can't list files with anon key, we'll use known filenames from songs data
        try:
            from services.database_service import db_service
            songs_df = db_service.get_songs()

            if not songs_df.empty:
                st.success(f"📁 Menggunakan sertifikat pre-generated dari storage")
                st.write(f"📄 **Sertifikat tersedia untuk {len(songs_df)} peserta**")

                # Show sample participants
                for i, song in songs_df.head(3).iterrows():
                    composer = song.get('composer', 'Unknown')
                    st.write(f"   • Participant_{composer}.pdf")
                if len(songs_df) > 3:
                    st.write(f"   • ... dan {len(songs_df) - 3} sertifikat lainnya")

                # Download all as ZIP button
                # Download all as ZIP button
                if st.button("🏆 Download Semua Sertifikat (ZIP)", key="download_all_storage"):
                    with st.spinner("📦 Membuat ZIP dari storage..."):
                        try:
                            import zipfile
                            import io
                            import urllib.parse
                            import requests

                            # Create ZIP file in memory
                            zip_buffer = io.BytesIO()

                            with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
                                success_count = 0

                                for _, song in songs_df.iterrows():
                                    composer = song.get('composer', 'Unknown')
                                    title = song.get('title', 'Unknown')
                                    certificate_path = song.get('certificate_path')

                                    if not certificate_path:
                                        st.warning(f"⚠️ Sertifikat tidak tersedia untuk: {composer} - {title}")
                                        continue

                                    filename = certificate_path

                                    try:
                                        # Construct direct public URL
                                        supabase_project_url = st.secrets["supabase_url"]
                                        encoded_path = urllib.parse.quote(f"{folder_name}/{filename}")
                                        direct_url = f"{supabase_project_url}/storage/v1/object/public/{bucket_name}/{encoded_path}"

                                        # Download PDF using direct URL
                                        response = requests.get(direct_url, timeout=10)

                                        if response.status_code == 200:
                                            # Add to ZIP
                                            zip_file.writestr(filename, response.content)
                                            success_count += 1
                                        else:
                                            st.warning(f"⚠️ File tidak ditemukan: {filename}")

                                    except Exception as file_error:
                                        st.warning(f"⚠️ Gagal download {filename}: {file_error}")

                            zip_buffer.seek(0)

                            if success_count > 0:
                                # Provide download button
                                timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M')
                                st.download_button(
                                    f"📥 Download ZIP Sertifikat ({success_count} files)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"certificates_storage_{timestamp}.zip",
                                    mime="application/zip"
                                )
                                st.success(f"✅ Berhasil mengunduh {success_count} sertifikat")
                            else:
                                st.error("❌ Tidak ada sertifikat yang berhasil diunduh")

                        except Exception as zip_error:
                            st.error(f"❌ Error creating ZIP: {zip_error}")
            else:
                st.warning("⚠️ Tidak ada data peserta ditemukan")
                st.info("💡 Pastikan data songs sudah ada di database")

        except Exception as e:
            st.error(f"❌ Error mengakses storage: {e}")
            st.warning("🔄 Storage tidak accessible dengan anon key")
            st.info("💡 Solusi: Buat RLS policy untuk public read access ke bucket certificates")
            st.code("""
-- Di Supabase SQL Editor, jalankan:
CREATE POLICY "Public read certificates" ON storage.objects
FOR SELECT USING (bucket_id = 'song-contest-files' AND (storage.foldername(name))[1] = 'certificates');
            """)

            st.info("🔄 Fallback ke generate otomatis...")
            cert_data = export_service.generate_all_certificates()
            st.download_button(
                "🏆 Download Semua Sertifikat (Generated)",
                data=cert_data,
                file_name=f"certificates_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip"
            )
    else:
        # Generate certificates on-the-fly (original behavior)
        cert_data = export_service.generate_all_certificates()
        st.download_button(
            "🏆 Download Semua Sertifikat",
            data=cert_data,
            file_name=f"certificates_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip"
        )

# ==================== AUTHENTICATION CALLBACKS ====================

def render_unauthorized_page():
    """Render unauthorized access page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🚫 Akses Tidak Diizinkan</h1>
        <p style="color: #ff6b6b; font-size: 1.2rem; margin-bottom: 2rem;">
            Email Anda tidak terdaftar sebagai juri dalam sistem ini.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Get current user info for display
    try:
        user = auth_service.client.auth.get_user()
        if user and user.user:
            user_email = user.user.email
            st.info(f"📧 Email yang login: **{user_email}**")
    except:
        pass

    st.markdown("### 📋 Langkah Selanjutnya:")
    st.markdown("""
    1. **Hubungi Administrator** untuk mendaftarkan email Anda sebagai juri
    2. **Pastikan menggunakan email yang benar** sesuai dengan yang didaftarkan
    3. **Logout dan login kembali** setelah email didaftarkan
    """)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("🔄 Logout & Login Ulang", type="primary", width='stretch'):
            auth_service.logout()
            st.rerun()

    with col2:
        if st.button("📧 Hubungi Admin", width='stretch'):
            st.info("📞 Hubungi administrator lomba untuk bantuan pendaftaran")

    with col3:
        if st.button("🏠 Kembali ke Login", width='stretch'):
            auth_service.logout()
            st.rerun()

def handle_auth_callbacks():
    """Handle authentication callbacks from Google OAuth and Magic Link"""

    # Add JavaScript to handle URL hash for magic links
    st.markdown("""
    <script>
    // Check for magic link tokens in URL hash
    if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);

        if (params.get('access_token') && params.get('type') === 'magiclink') {
            // Redirect to clean URL with magic link indicator
            const cleanUrl = window.location.origin + window.location.pathname + '?type=magiclink';
            window.location.replace(cleanUrl);
        }
    }
    </script>
    """, unsafe_allow_html=True)

    # Get URL parameters
    query_params = st.query_params

    # Handle Google OAuth callback
    if "code" in query_params:
        code = query_params["code"]
        st.info("🔐 Processing Google login...")

        try:
            # Exchange code for session
            success = auth_service.handle_oauth_callback(code)

            if success:
                # Check if user is authorized (exists in judges table)
                current_user = auth_service.get_current_user()

                if current_user and current_user.get('judge_id'):
                    st.success("✅ Google login successful!")
                    # Clear URL parameters and refresh
                    st.query_params.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    # User authenticated but not authorized
                    st.error("❌ Akses ditolak: Email Anda tidak terdaftar sebagai juri")
                    st.info("💡 Silahkan hubungi admin untuk mendapatkan akses ke sistem")

                    # Logout the unauthorized user
                    auth_service.logout()

                    # Clear URL parameters and show back to landing page button
                    st.query_params.clear()

                    if st.button("🏠 Kembali ke Beranda", type="primary"):
                        st.rerun()

                    time.sleep(3)
                    st.rerun()
            else:
                st.error("❌ Google login failed: Authentication unsuccessful")
                st.query_params.clear()
                time.sleep(2)
                st.rerun()

        except Exception as e:
            st.error(f"❌ Google login failed: {str(e)}")
            st.query_params.clear()
            time.sleep(2)
            st.rerun()

    # Handle Magic Link callback
    if "type" in query_params and query_params["type"] == "magiclink":
        st.info("🔗 Processing magic link login...")

        try:
            # Check if user is now authenticated
            current_user = auth_service.get_current_user()

            if current_user and current_user.get('judge_id'):
                st.success("✅ Magic link login successful!")
                st.query_params.clear()
                time.sleep(1)
                st.rerun()
            elif current_user:
                # User authenticated but not authorized
                st.error("❌ Akses ditolak: Email Anda tidak terdaftar sebagai juri")
                st.info("💡 Silahkan hubungi admin untuk mendapatkan akses ke sistem")

                # Logout the unauthorized user
                auth_service.logout()

                # Clear URL parameters and show back to landing page button
                st.query_params.clear()

                if st.button("🏠 Kembali ke Beranda", type="primary", key="magic_back"):
                    st.rerun()

                time.sleep(3)
                st.rerun()
            else:
                st.error("❌ Magic link login failed - no session found")
                st.query_params.clear()
                time.sleep(2)
                st.rerun()

        except Exception as e:
            st.error(f"❌ Magic link login failed: {str(e)}")
            st.query_params.clear()
            time.sleep(2)
            st.rerun()

# ==================== LANDING PAGE ====================

def get_contest_status(config):
    """Get contest status based on configuration"""
    from datetime import datetime
    import logging

    # Default values
    status = {
        'is_closed': False,
        'show_winners': False,
        'announcement_date': '31 Desember 2025'
    }

    # Handle both dict and DataFrame formats
    if isinstance(config, dict):
        config_dict = config
    elif hasattr(config, 'empty') and config.empty:
        return status
    elif hasattr(config, 'iterrows'):
        # DataFrame format
        config_dict = {row['key']: row['value'] for _, row in config.iterrows()}
    else:
        return status



    # Check if contest is closed
    form_close = config_dict.get('FORM_CLOSE_DATETIME')
    if form_close:
        try:
            # Parse datetime string - try different formats
            close_time = None

            # Try parsing as simple datetime string first (most common format)
            try:
                close_time = datetime.strptime(form_close, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try ISO format
                if 'T' not in form_close:
                    form_close += ' 23:59:59'
                close_time = datetime.fromisoformat(form_close.replace('Z', '+00:00'))

            if close_time:
                status['is_closed'] = datetime.now() > close_time

                # Format tanggal Indonesia cantik dengan hari
                hari_indonesia = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                bulan_indonesia = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                                 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

                hari = hari_indonesia[close_time.weekday()]
                tanggal = close_time.day
                bulan = bulan_indonesia[close_time.month]
                tahun = close_time.year
                jam = close_time.strftime('%H:%M')

                status['form_close_date'] = f"{hari}, {tanggal} {bulan} {tahun} pukul {jam}"
            else:
                status['form_close_date'] = form_close

        except Exception as e:
            logging.error(f"Error parsing form_close_date: {e}")
            status['form_close_date'] = form_close

    # Check if winners should be shown
    winner_announcement = config_dict.get('WINNER_ANNOUNCE_DATETIME')
    if winner_announcement:
        try:
            # Parse datetime string - try different formats
            announcement_time = None

            # Try parsing as simple datetime string first (most common format)
            try:
                announcement_time = datetime.strptime(winner_announcement, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try ISO format
                if 'T' not in winner_announcement:
                    winner_announcement += ' 00:00:00'
                announcement_time = datetime.fromisoformat(winner_announcement.replace('Z', '+00:00'))

            if announcement_time:
                status['show_winners'] = datetime.now() >= announcement_time

                # Format tanggal Indonesia cantik dengan hari
                hari_indonesia = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                bulan_indonesia = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                                 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

                hari = hari_indonesia[announcement_time.weekday()]
                tanggal = announcement_time.day
                bulan = bulan_indonesia[announcement_time.month]
                tahun = announcement_time.year
                jam = announcement_time.strftime('%H:%M')

                status['announcement_date'] = f"{hari}, {tanggal} {bulan} {tahun} pukul {jam}"
            else:
                status['announcement_date'] = winner_announcement

        except Exception as e:
            logging.error(f"Error parsing winner_announcement_date: {e}")
            status['announcement_date'] = winner_announcement

    # Get form open time for display
    form_open = config_dict.get('FORM_OPEN_DATETIME')
    if form_open:
        try:
            # Parse datetime string - try different formats
            open_time = None

            # Try parsing as simple datetime string first (most common format)
            try:
                open_time = datetime.strptime(form_open, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try ISO format
                if 'T' not in form_open:
                    form_open += ' 00:00:00'
                open_time = datetime.fromisoformat(form_open.replace('Z', '+00:00'))

            if open_time:
                # Format tanggal Indonesia cantik dengan hari
                hari_indonesia = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                bulan_indonesia = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                                 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

                hari = hari_indonesia[open_time.weekday()]
                tanggal = open_time.day
                bulan = bulan_indonesia[open_time.month]
                tahun = open_time.year
                jam = open_time.strftime('%H:%M')

                status['form_open_date'] = f"{hari}, {tanggal} {bulan} {tahun} pukul {jam}"
            else:
                status['form_open_date'] = form_open

        except Exception as e:
            logging.error(f"Error parsing form_open_date: {e}")
            status['form_open_date'] = form_open

    return status

def render_winners_section():
    """Render winners section with actual winners data"""
    st.markdown("""
    <div class="winners-card">
        <h2>🏆 Pemenang Lomba Cipta Lagu Bulkel 2025</h2>
        <p style="font-size: 1.2rem; margin: 1rem 0;">
            Selamat kepada pemenang!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Get configuration for winner display layout
    try:
        config = db_service.get_config()
        winner_layout = config.get('WINNER_DISPLAY_LAYOUT', 'COLUMNS')  # TABS or COLUMNS
        show_pdf = config.get('SHOW_PDF_DOCUMENTS', 'FALSE').upper() == 'TRUE'
        show_scores = config.get('SHOW_WINNER_SCORES', 'TRUE').upper() == 'TRUE'
    except:
        # Fallback to default values if config not available
        winner_layout = 'COLUMNS'  # Default to COLUMNS layout (side-by-side with full score)
        show_pdf = False  # Default to hide PDF since text versions are available
        show_scores = True  # Default to show scores

    try:
        # Get winners data from analytics
        from services.analytics_service import analytics_service
        from services.database_service import db_service

        leaderboard_df = analytics_service.get_global_leaderboard()

        if leaderboard_df.empty:
            st.warning("Belum ada data penilaian untuk menentukan pemenang.")
            return

        # Get configuration for winners count
        config = cache_service.get_cached_config()
        winners_count = int(config.get('WINNERS_TOP_N', 3))

        # Get top winners
        winners_df = leaderboard_df.head(winners_count)

        # Get songs data for audio and lyrics
        songs_df = db_service.get_songs()

        # Group winners by composer and base title to handle multiple versions
        grouped_winners = {}
        for _, row in winners_df.iterrows():
            composer = row['composer']
            title = row['title']

            # Simple regex to remove v1, v2, etc for grouping
            import re
            base_title = re.sub(r'\s+v\d+$', '', title, flags=re.IGNORECASE).strip()

            key = (composer, base_title)
            if key not in grouped_winners:
                grouped_winners[key] = []
            grouped_winners[key].append(row)

        # Sort groups by highest score in each group
        sorted_groups = []
        for key, versions in grouped_winners.items():
            max_score = max(v['avg_score'] for v in versions)
            sorted_groups.append((max_score, key, versions))

        sorted_groups.sort(key=lambda x: x[0], reverse=True)

        # Display winners with audio and lyrics
        for i, (max_score, composer_title, versions) in enumerate(sorted_groups, 1):
            composer, base_title = composer_title
            main_version = versions[0]  # Use first version for main display

            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"🏆"

            # Create gradient background based on rank
            if i == 1:
                gradient = "linear-gradient(135deg, #ffd700, #ffed4e)"
                border_color = "#ffd700"
            elif i == 2:
                gradient = "linear-gradient(135deg, #c0c0c0, #e8e8e8)"
                border_color = "#c0c0c0"
            elif i == 3:
                gradient = "linear-gradient(135deg, #cd7f32, #daa520)"
                border_color = "#cd7f32"
            else:
                gradient = "linear-gradient(135deg, #667eea, #764ba2)"
                border_color = "#667eea"

            # Winner header with version info
            version_info = f" ({len(versions)} versi)" if len(versions) > 1 else ""
            avg_score = sum(v['avg_score'] for v in versions) / len(versions)
            total_judges = sum(v['unique_judges'] for v in versions)

            st.markdown(f"""
            <div style='background: {gradient}; padding: 20px; border-radius: 15px; margin: 15px 0; border-left: 5px solid {border_color}; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                <h3 style='margin: 0 0 10px 0; color: #333; font-size: 1.5rem;'>{rank_emoji} JUARA {i}</h3>
                <h4 style='margin: 0 0 8px 0; color: #444; font-size: 1.3rem;'>{base_title}{version_info}</h4>
                <p style='margin: 5px 0; color: #666; font-size: 1.1rem;'>
                    <strong>Skor Rata-rata:</strong> {avg_score:.2f}/100
                    <span style='color: #888;'>({total_judges} total penilaian)</span>
                </p>
                <p style='margin: 0; color: #666; font-style: italic; font-size: 1rem;'>
                    <strong>Pencipta:</strong> {composer}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Get all song data for all versions
            all_song_data = []
            if not songs_df.empty:
                for version in versions:
                    matching_songs = songs_df[songs_df['title'] == version['title']]
                    if not matching_songs.empty:
                        all_song_data.append(matching_songs.iloc[0])

            if all_song_data:
                # Show multiple audio versions if available
                if len(all_song_data) > 1:
                    st.markdown("##### 🎵 Pilihan Audio (Voting Internal)")
                    st.info("💡 Silakan dengarkan kedua versi untuk membantu menentukan versi final yang akan diumumkan")

                    # Determine version names based on v1/v2
                    version_names = []
                    for version in versions:
                        version_title = version['title']
                        if 'v2' in version_title.lower():
                            version_names.append("Versi 2")
                        else:
                            version_names.append("Versi 1")

                    # Choose layout based on configuration
                    if winner_layout == 'COLUMNS':
                        # COLUMNS layout: Side-by-side with full score
                        col_a, col_b = st.columns(2)
                        columns = [col_a, col_b]

                        for idx, (col, song_data, version_name) in enumerate(zip(columns, all_song_data, version_names)):
                            with col:
                                # Version card
                                version_score = versions[idx]['avg_score']
                                full_title = versions[idx]['title']
                                key_signature = song_data.get('key_signature', 'N/A')

                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                                    padding: 1.5rem;
                                    border-radius: 10px;
                                    border-left: 4px solid {border_color};
                                    margin-bottom: 1rem;
                                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                ">
                                    <h4 style="margin: 0 0 10px 0; color: #333;">{version_name}</h4>
                                    <p style="margin: 5px 0; color: #666; font-size: 0.9rem;">
                                        <strong>📊 Skor:</strong> {version_score:.2f}/100
                                    </p>
                                    <p style="margin: 5px 0; color: #007bff; font-size: 0.9rem;">
                                        <strong>🎼 Nada Dasar:</strong> {key_signature}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)

                                # Audio player with unique ID
                                st.markdown("**🎵 Audio**")
                                render_audio_player(song_data, f"winner_{i}_{idx}")

                                # Full score directly below audio
                                st.markdown("---")
                                st.markdown("**🎼 Full Score**")

                                if song_data.get('full_score'):
                                    st.markdown(
                                        f"""
                                        <div style="
                                            background-color: #fff8e1;
                                            padding: 1rem;
                                            border-radius: 8px;
                                            border-left: 3px solid #ff9800;
                                            font-family: 'Courier New', monospace;
                                            white-space: pre-wrap;
                                            font-size: 0.75rem;
                                            line-height: 1.2;
                                            max-height: 400px;
                                            overflow-y: auto;
                                        ">
                                            {song_data['full_score']}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.info("Full score tidak tersedia")

                                # PDF buttons if enabled
                                if show_pdf:
                                    st.markdown("**📄 PDF**")
                                    if song_data.get('lyrics_pdf_url'):
                                        st.markdown(f"""
                                        <a href="{song_data['lyrics_pdf_url']}" target="_blank" style="text-decoration: none;">
                                            <button style="
                                                background-color: #007bff;
                                                color: white;
                                                padding: 6px 10px;
                                                border: none;
                                                border-radius: 4px;
                                                cursor: pointer;
                                                font-size: 0.8rem;
                                                margin: 2px;
                                                width: 48%;
                                            ">📝 Syair</button>
                                        </a>
                                        """, unsafe_allow_html=True)

                                    if song_data.get('notation_pdf_url'):
                                        st.markdown(f"""
                                        <a href="{song_data['notation_pdf_url']}" target="_blank" style="text-decoration: none;">
                                            <button style="
                                                background-color: #28a745;
                                                color: white;
                                                padding: 6px 10px;
                                                border: none;
                                                border-radius: 4px;
                                                cursor: pointer;
                                                font-size: 0.8rem;
                                                margin: 2px;
                                                width: 48%;
                                            ">🎼 Notasi</button>
                                        </a>
                                        """, unsafe_allow_html=True)

                    else:
                        # TABS layout: Current tabbed layout
                        # Create 2 columns for version comparison
                        col_a, col_b = st.columns(2)
                        columns = [col_a, col_b]

                        for idx, (col, song_data, version_name) in enumerate(zip(columns, all_song_data, version_names)):
                            with col:
                                # Version card
                                version_score = versions[idx]['avg_score']
                                full_title = versions[idx]['title']
                                key_signature = song_data.get('key_signature', 'N/A')

                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                                    padding: 1.5rem;
                                    border-radius: 10px;
                                    border-left: 4px solid {border_color};
                                    margin-bottom: 1rem;
                                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                ">
                                    <h4 style="margin: 0 0 10px 0; color: #333;">{version_name}</h4>
                                    <p style="margin: 5px 0; color: #666; font-size: 0.9rem;">
                                        <strong>📊 Skor:</strong> {version_score:.2f}/100
                                    </p>
                                    <p style="margin: 5px 0; color: #007bff; font-size: 0.9rem;">
                                        <strong>🎼 Nada Dasar:</strong> {key_signature}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)

                                # Audio player with unique ID
                                st.markdown("**🎵 Audio**")
                                render_audio_player(song_data, f"winner_{i}_{idx}")

                        # Show comprehensive score comparison for TABS layout
                        st.markdown("---")
                        st.markdown("### 🎼 Perbandingan Full Score")

                        # Create tabs based on PDF configuration
                        if show_pdf:
                            tab1, tab2, tab3, tab4 = st.tabs(["📝 Syair", "🎸 Chord Comparison", "🎵 Lyrics + Chords", "📄 PDF Documents"])
                        else:
                            tab1, tab2, tab3 = st.tabs(["📝 Syair", "🎸 Chord Comparison", "🎵 Lyrics + Chords"])

                        with tab1:
                            st.markdown("##### 📝 Syair (Sama untuk kedua versi)")
                            if all_song_data[0].get('lyrics_text'):
                                st.markdown(
                                    f"""
                                    <div style="
                                        background-color: #f8f9fa;
                                        padding: 1.5rem;
                                        border-radius: 8px;
                                        border-left: 3px solid {border_color};
                                        font-family: 'Georgia', serif;
                                        line-height: 1.6;
                                        white-space: pre-wrap;
                                        font-size: 0.95rem;
                                    ">
                                        {all_song_data[0]['lyrics_text']}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                        with tab2:
                            st.markdown("##### 🎸 Perbandingan Chord")
                            col_chord1, col_chord2 = st.columns(2)

                            with col_chord1:
                                st.markdown(f"**{version_names[0]} (Key {all_song_data[0].get('key_signature', 'N/A')})**")
                                if all_song_data[0].get('chords_list'):
                                    st.markdown(
                                        f"""
                                        <div style="
                                            background-color: #e8f4fd;
                                            padding: 1rem;
                                            border-radius: 8px;
                                            border-left: 3px solid #007bff;
                                            font-family: 'Courier New', monospace;
                                            white-space: pre-wrap;
                                            font-size: 0.9rem;
                                        ">
                                            {all_song_data[0]['chords_list']}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                            with col_chord2:
                                st.markdown(f"**{version_names[1]} (Key {all_song_data[1].get('key_signature', 'N/A')})**")
                                if all_song_data[1].get('chords_list'):
                                    st.markdown(
                                        f"""
                                        <div style="
                                            background-color: #f0f8e8;
                                            padding: 1rem;
                                            border-radius: 8px;
                                            border-left: 3px solid #28a745;
                                            font-family: 'Courier New', monospace;
                                            white-space: pre-wrap;
                                            font-size: 0.9rem;
                                        ">
                                            {all_song_data[1]['chords_list']}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                        with tab3:
                            st.markdown("##### 🎵 Syair + Chord")

                            # Show both versions with lyrics and chords
                            for idx, song_data in enumerate(all_song_data):
                                with st.expander(f"🎵 {version_names[idx]} - Syair + Chord (Key {song_data.get('key_signature', 'N/A')})"):
                                    if song_data.get('lyrics_with_chords'):
                                        st.markdown(
                                            f"""
                                            <div style="
                                                background-color: #f8f9fa;
                                                padding: 1.5rem;
                                                border-radius: 8px;
                                                font-family: 'Courier New', monospace;
                                                white-space: pre-wrap;
                                                font-size: 0.85rem;
                                                line-height: 1.4;
                                            ">
                                                {song_data['lyrics_with_chords']}
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                                    # Show full score if available
                                    if song_data.get('full_score'):
                                        st.markdown("**🎼 Full Score dengan Notasi Angka:**")
                                        st.markdown(
                                            f"""
                                            <div style="
                                                background-color: #fff8e1;
                                                padding: 1.5rem;
                                                border-radius: 8px;
                                                border-left: 3px solid #ff9800;
                                                font-family: 'Courier New', monospace;
                                                white-space: pre-wrap;
                                                font-size: 0.8rem;
                                                line-height: 1.3;
                                            ">
                                                {song_data['full_score']}
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                        # PDF tab only if enabled
                        if show_pdf:
                            with tab4:
                                st.markdown("##### 📄 Dokumen PDF Asli")

                                col_pdf1, col_pdf2 = st.columns(2)

                                for idx, (col, song_data, version_name) in enumerate(zip([col_pdf1, col_pdf2], all_song_data, version_names)):
                                    with col:
                                        st.markdown(f"**{version_name}**")

                                        # Lyrics PDF
                                        if song_data.get('lyrics_pdf_url'):
                                            st.markdown(f"""
                                            <a href="{song_data['lyrics_pdf_url']}" target="_blank" style="text-decoration: none;">
                                                <button style="
                                                    background-color: #007bff;
                                                    color: white;
                                                    padding: 8px 12px;
                                                    border: none;
                                                    border-radius: 5px;
                                                    cursor: pointer;
                                                    font-size: 0.85rem;
                                                    margin: 2px 0;
                                                    width: 100%;
                                                ">📝 Syair PDF</button>
                                            </a>
                                            """, unsafe_allow_html=True)

                                        # Notation PDF
                                        if song_data.get('notation_pdf_url'):
                                            st.markdown(f"""
                                            <a href="{song_data['notation_pdf_url']}" target="_blank" style="text-decoration: none;">
                                                <button style="
                                                    background-color: #28a745;
                                                    color: white;
                                                    padding: 8px 12px;
                                                    border: none;
                                                    border-radius: 5px;
                                                    cursor: pointer;
                                                    font-size: 0.85rem;
                                                    margin: 2px 0;
                                                    width: 100%;
                                                ">🎼 Notasi PDF</button>
                                            </a>
                                            """, unsafe_allow_html=True)
                else:
                    # Single version display
                    song_data = all_song_data[0]
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown("##### 🎵 Audio")
                        render_audio_player(song_data)

                    with col2:
                        st.markdown("##### 📝 Syair")
                        if song_data.get('lyrics_text'):
                            st.markdown(
                                f"""
                                <div style="
                                    background-color: #f8f9fa;
                                    padding: 1.5rem;
                                    border-radius: 8px;
                                    border-left: 3px solid {border_color};
                                    font-family: 'Georgia', serif;
                                    line-height: 1.6;
                                    white-space: pre-wrap;
                                    max-height: 300px;
                                    overflow-y: auto;
                                    font-size: 0.95rem;
                                ">
                                    {song_data['lyrics_text']}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.info("Syair tidak tersedia")

                st.markdown("---")  # Separator between winners
            else:
                st.warning(f"⚠️ Data lagu '{base_title}' tidak ditemukan")
                st.markdown("---")

        # Show congratulations message
        st.markdown("""
        <div style='background: rgba(46, 204, 113, 0.1); padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2ecc71;'>
            <p style='margin: 0; color: #27ae60; font-size: 1.1rem; text-align: center;'>
                🎉 <strong>Selamat kepada pemenang!</strong> 🎉<br>
                <span style='font-size: 1rem; color: #666;'>Terima kasih kepada semua peserta yang telah berpartisipasi dalam lomba ini.</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error menampilkan pemenang: {str(e)}")
        st.info("🏆 Pengumuman pemenang akan segera ditampilkan di sini")

def render_all_songs_section(view_mode="📋 Semua Lagu"):
    """Render section for all songs with winner emoji and improved audio player"""
    st.markdown("---")
    st.markdown("""
    <div class="winners-card">
        <h2>🎵 Semua Lagu Peserta</h2>
        <p style="font-size: 1.1rem; margin: 1rem 0;">
            Dengarkan semua karya peserta lomba (diurutkan berdasarkan skor)
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        # Get all songs data (sorted by score)
        from services.analytics_service import analytics_service
        all_songs_df = analytics_service.get_global_leaderboard()

        if all_songs_df.empty:
            st.info("Belum ada data lagu yang tersedia.")
            return

        # Get configuration for winners and scores
        try:
            config = db_service.get_config()
            winners_count = int(config.get('WINNERS_TOP_N', 3))
            show_scores = config.get('SHOW_ALL_SONGS_SCORES', 'FALSE').upper() == 'TRUE'
        except:
            winners_count = 3
            show_scores = False

        # Don't exclude winners - show ALL songs with winner emoji
        # Get top winners for emoji marking
        winner_titles = set()
        if len(all_songs_df) >= winners_count:
            winners_df = all_songs_df.head(winners_count)
            winner_titles = set(winners_df['title'].tolist())

        # Sort by score (highest first) - simple, no search needed
        filtered_df = all_songs_df.sort_values('avg_score', ascending=False)

        # Filter based on view mode
        if view_mode == "🏆 Hanya Pemenang":
            # Show only winners
            filtered_df = filtered_df.head(winners_count)
            expander_title = f"🏆 **Top {winners_count} Pemenang**"
            subtitle = f"*Menampilkan {winners_count} lagu terbaik*"
        elif view_mode == "🎵 Lagu Lainnya":
            # Show non-winners (exclude top winners)
            filtered_df = filtered_df.iloc[winners_count:]
            expander_title = "🎵 **Lagu Peserta Lainnya**"
            subtitle = f"*Menampilkan {len(filtered_df)} lagu peserta (selain pemenang)*"
        else:
            # Show all songs (default)
            expander_title = "🎵 **Semua Lagu Peserta**"
            subtitle = f"*Menampilkan semua {len(filtered_df)} lagu peserta*"

        # Song selection with expander - cleaner UI
        with st.expander(expander_title, expanded=True):
            st.markdown(subtitle)

            # Create song options with winner emoji
            song_options = []
            for _, song_row in filtered_df.iterrows():
                # Add winner emoji for top songs
                winner_emoji = ""
                if song_row['title'] in winner_titles:
                    # Find rank in original sorted leaderboard
                    original_df_sorted = all_songs_df.sort_values('avg_score', ascending=False).reset_index(drop=True)
                    try:
                        original_rank = original_df_sorted[original_df_sorted['title'] == song_row['title']].index[0] + 1
                        if original_rank == 1:
                            winner_emoji = "🥇 "
                        elif original_rank == 2:
                            winner_emoji = "🥈 "
                        elif original_rank == 3:
                            winner_emoji = "🥉 "
                        elif original_rank <= winners_count:
                            winner_emoji = "🏆 "
                    except:
                        # Fallback: if in winner_titles, at least show trophy
                        winner_emoji = "🏆 "

                score_text = f" - Skor: {song_row['avg_score']:.1f}/100" if show_scores else ""
                song_options.append(f"{winner_emoji}{song_row['title']} - {song_row['composer']}{score_text}")

            # Simple selectbox inside expander
            selected_idx = st.selectbox(
                "Pilih lagu:",
                range(len(song_options) + 1),
                format_func=lambda x: "Pilih lagu..." if x == 0 else song_options[x-1],
                key="song_selector",
                label_visibility="collapsed"
            )

        # Force refresh when selection changes
        if hasattr(st.session_state, 'last_landing_selection') and st.session_state.last_landing_selection != selected_idx:
            # Clear audio cache when song changes
            if hasattr(st.session_state, 'landing_audio_cache'):
                del st.session_state.landing_audio_cache
        st.session_state.last_landing_selection = selected_idx

        if selected_idx > 0:
            # Get selected song
            selected_song = filtered_df.iloc[selected_idx - 1]

            # Get song data from songs table (same as Winners section)
            songs_df = db_service.get_songs()
            matching_songs = songs_df[songs_df['title'] == selected_song['title']]

            if not matching_songs.empty:
                song_data = matching_songs.iloc[0]
            else:
                # Fallback to constructed data
                song_data = get_available_content({
                    'id': selected_song['song_id'],
                    'title': selected_song['title'],
                    'composer': selected_song['composer'],
                    'audio_file_path': selected_song.get('audio_file_path'),
                    'lyrics_text': selected_song.get('lyrics_text'),
                    'full_score': selected_song.get('full_score'),
                    'chords_list': selected_song.get('chords_list'),
                    'lyrics_with_chords': selected_song.get('lyrics_with_chords'),
                    'key_signature': selected_song.get('key_signature'),
                    'notation_file_path': selected_song.get('notation_file_path'),
                    'lyrics_file_path': selected_song.get('lyrics_file_path')
                })

            # Display selected song
            st.markdown("---")
            key_text = f" (Key {song_data.get('key_signature', 'N/A')})" if song_data.get('key_signature') else ""
            st.markdown(f"### 🎵 {selected_song['title']}{key_text}")
            st.markdown(f"**Pencipta:** {selected_song['composer']}")

            if show_scores:
                st.metric("📊 Skor Rata-rata", f"{selected_song['avg_score']:.1f}/100")

            # Two columns layout
            col_audio, col_score = st.columns([1, 1])

            with col_audio:
                st.markdown("**🎵 Audio**")



                # Use updated render_audio_player with force refresh
                render_audio_player(song_data, f"landing_{selected_song['song_id']}")

            with col_score:
                st.markdown("**🎼 Full Score**")

                # Priority: full_score > lyrics_with_chords > chords_list > lyrics_text
                content_to_show = None
                content_type = ""

                if song_data.get('full_score'):
                    content_to_show = song_data['full_score']
                    content_type = "Full Score"
                elif song_data.get('lyrics_with_chords'):
                    content_to_show = song_data['lyrics_with_chords']
                    content_type = "Syair + Chord"
                elif song_data.get('chords_list'):
                    content_to_show = song_data['chords_list']
                    content_type = "Chord"
                elif song_data.get('lyrics_text'):
                    content_to_show = song_data['lyrics_text']
                    content_type = "Syair"

                if content_to_show:
                    if content_type != "Full Score":
                        st.markdown(f"**🎼 {content_type}** *(Full Score tidak tersedia)*")

                    st.markdown(
                        f"""
                        <div style="
                            background-color: #fff8e1;
                            padding: 1rem;
                            border-radius: 8px;
                            border-left: 3px solid #ff9800;
                            font-family: 'Courier New', monospace;
                            white-space: pre-wrap;
                            font-size: 0.7rem;
                            line-height: 1.1;
                            max-height: 400px;
                            overflow-y: auto;
                        ">
                            {content_to_show}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("Tidak ada konten yang tersedia")

    except Exception as e:
        st.error(f"Error loading songs: {e}")
        st.info("Belum ada data lagu yang tersedia.")

def render_landing_sidebar():
    """Render landing page sidebar with navigation"""
    with st.sidebar:
        # Custom CSS for better button styling
        st.markdown("""
        <style>
        .nav-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .nav-header {
            font-size: 1.4rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 1rem;
            text-align: center;
            border-bottom: 2px solid #667eea;
            padding-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Navigation Section
        st.markdown("""
        <div class="nav-section">
            <div class="nav-header">🧭 Navigation</div>
        </div>
        """, unsafe_allow_html=True)

        # Home button
        if st.button("🏠 Home", type="primary", width='stretch', key="nav_home"):
            # Already on home page, just refresh
            st.rerun()

        # Info lomba button
        if st.button("📋 Info Lomba", type="secondary", width='stretch', key="nav_info"):
            st.session_state.show_info = True
            st.rerun()

        # Certificate download button
        if st.button("🏆 Download Sertifikat", type="secondary", width='stretch', key="nav_cert"):
            st.session_state.show_certificate = True
            st.rerun()

        # Check if user is logged in for dynamic login/dashboard button
        current_user = auth_service.get_current_user()
        if current_user:
            # User is logged in - show Dashboard button
            if st.button("📊 Dashboard", type="primary", width='stretch', key="nav_dashboard"):
                # Set flag to show main app instead of landing page
                st.session_state.show_dashboard = True
                st.rerun()
        else:
            # User not logged in - show Login button
            if st.button("🔐 Login", type="secondary", width='stretch', key="nav_login"):
                st.switch_page("pages/auth.py")

        st.markdown("---")

        # Song Display Section - Only show if winners are announced
        config = cache_service.get_cached_config()
        winner_announce_str = config.get('WINNER_ANNOUNCE_DATETIME', '2025-09-10 07:00:00')
        timezone_str = config.get('TIMEZONE', 'Asia/Jakarta')

        try:
            # Parse winner announcement datetime
            winner_announce_dt = pd.to_datetime(winner_announce_str)
            if winner_announce_dt.tz is None:
                winner_announce_dt = winner_announce_dt.tz_localize(timezone_str)

            # Get current time in the same timezone
            current_time = pd.Timestamp.now(tz=timezone_str)

            # Only show song display options if winners are announced
            if current_time >= winner_announce_dt:
                st.markdown("""
                <div class="nav-section">
                    <div class="nav-header">🎵 Song Display</div>
                </div>
                """, unsafe_allow_html=True)

                # Get current view mode from session state
                current_view = st.session_state.get('song_view_mode', '📋 Semua Lagu')

                if st.button("📋 Semua Lagu", type="primary" if current_view == "📋 Semua Lagu" else "secondary", width='stretch', key="view_all"):
                    st.session_state.song_view_mode = "📋 Semua Lagu"
                    st.rerun()

                if st.button("🏆 Hanya Pemenang", type="primary" if current_view == "🏆 Hanya Pemenang" else "secondary", width='stretch', key="view_winners"):
                    st.session_state.song_view_mode = "🏆 Hanya Pemenang"
                    st.rerun()

                if st.button("🎵 Lagu Lainnya", type="primary" if current_view == "🎵 Lagu Lainnya" else "secondary", width='stretch', key="view_others"):
                    st.session_state.song_view_mode = "🎵 Lagu Lainnya"
                    st.rerun()
            else:
                # Show info about when winners will be announced
                st.markdown("""
                <div class="nav-section">
                    <div class="nav-header">⏰ Pengumuman Pemenang</div>
                </div>
                """, unsafe_allow_html=True)

                st.info(f"🏆 Pemenang akan diumumkan pada:\n**{winner_announce_dt.strftime('%d/%m/%Y pukul %H:%M')}**")

        except Exception as e:
            # Fallback - show all songs if there's an error parsing datetime
            st.markdown("""
            <div class="nav-section">
                <div class="nav-header">🎵 Song Display</div>
            </div>
            """, unsafe_allow_html=True)

            current_view = st.session_state.get('song_view_mode', '📋 Semua Lagu')
            if st.button("📋 Semua Lagu", type="primary", width='stretch', key="view_all_fallback"):
                st.session_state.song_view_mode = "📋 Semua Lagu"
                st.rerun()

        return st.session_state.get('song_view_mode', '📋 Semua Lagu')


def render_landing_page():
    """Render beautiful landing page with poster and contest status"""
    # Render sidebar and get view mode
    view_mode = render_landing_sidebar()

    # Handle special views
    if st.session_state.get('show_certificate', False):
        st.session_state.show_certificate = False
        render_certificate_section()
        return
    elif st.session_state.get('show_info', False):
        st.session_state.show_info = False
        render_info_section()
        return

    # Main landing page - no header needed (already in sidebar)
    # st.markdown("# 🎵 Lomba Cipta Lagu Bulkel 2025")  # Removed double title

    # Get contest status
    config = cache_service.get_cached_config()
    contest_status = get_contest_status(config)

    # Custom CSS for beautiful styling
    st.markdown("""
    <style>
    .main > div {
        max-width: 1000px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    .landing-container {
        text-align: center;
        padding: 2rem 0;
        max-width: 800px;
        margin: 0 auto;
    }
    .poster-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    .poster-container img {
        max-width: 100%;
        height: auto;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem auto;
        max-width: 600px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .winners-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem auto;
        max-width: 600px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .login-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem auto;
        max-width: 500px;
        border: 2px solid #e9ecef;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main container
    st.markdown('<div class="landing-container">', unsafe_allow_html=True)

    # Title
    st.markdown("""
    <h1 style="color: #2c3e50; margin-bottom: 0.5rem;">🎵 Lomba Cipta Lagu Bulkel 2025</h1>
    <h3 style="color: #7f8c8d; margin-bottom: 2rem;">WAKTU BERSAMA HARTA BERHARGA</h3>
    """, unsafe_allow_html=True)

    # Display poster
    try:
        st.markdown('<div class="poster-container">', unsafe_allow_html=True)
        # Center the image using columns
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("assets/FLYER_01.png", caption="Poster Lomba Cipta Lagu Bulkel 2025", width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        st.warning("⚠️ Poster tidak dapat dimuat")

    # Contest status section
    if contest_status['is_closed'] and contest_status['show_winners']:
        # Show winners
        render_winners_section()
        # Show all songs section
        render_all_songs_section(view_mode)
    else:
        # Always show the beautiful theme and contest info
        render_theme_timeline()

def render_theme_timeline():
    """Render beautiful theme timeline card"""
    # Get configuration data for dates
    config = cache_service.get_cached_config()

    # Helper function to format date to Indonesian format
    def format_date_indonesian(date_str):
        """Convert date string to Indonesian format: DD Mmmm YYYY"""
        if not date_str:
            return "Belum ditentukan"

        try:
            from datetime import datetime
            # Parse the date string
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

            # Indonesian month names
            month_names = {
                1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
                5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
            }

            return f"{dt.day} {month_names[dt.month]} {dt.year}"
        except:
            return date_str

    # Get dates from configuration
    submission_start = config.get('SUBMISSION_START_DATETIME', '')
    submission_end = config.get('SUBMISSION_END_DATETIME', '')
    judging_start = config.get('FORM_OPEN_DATETIME', '')
    judging_end = config.get('FORM_CLOSE_DATETIME', '')
    announcement_date = config.get('WINNER_ANNOUNCE_DATETIME', '')

    # Format dates
    submission_start_formatted = format_date_indonesian(submission_start)
    submission_end_formatted = format_date_indonesian(submission_end)
    judging_start_formatted = format_date_indonesian(judging_start)
    judging_end_formatted = format_date_indonesian(judging_end)
    announcement_formatted = format_date_indonesian(announcement_date)

    # Create the card using streamlit components instead of raw HTML
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    ">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; font-weight: bold; margin: 0 0 1rem 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                🎯 Tema: WAKTU BERSAMA HARTA BERHARGA
            </h1>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 12px; margin: 1rem 0; backdrop-filter: blur(10px);">
                <h3 style="margin: 0 0 0.5rem 0; font-size: 1.3rem;">📜 Berdasarkan Efesus 5:15-16</h3>
                <p style="font-style: italic; margin: 0; font-size: 1.1rem; line-height: 1.6; opacity: 0.95;">
                    "Karena itu, perhatikanlah dengan saksama, bagaimana kamu hidup, janganlah
                    seperti orang bebal, tetapi seperti orang arif, dan pergunakanlah waktu yang
                    ada, karena hari-hari ini adalah jahat."
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Timeline sections using columns for better layout
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="
            background: rgba(46, 204, 113, 0.9);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        ">
            <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">📝 Periode Submission</h3>
            <p style="margin: 0; font-size: 1rem; line-height: 1.4;">
                <strong>Dibuka:</strong><br>{submission_start_formatted}<br><br>
                <strong>Ditutup:</strong><br>{submission_end_formatted}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: rgba(52, 152, 219, 0.9);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        ">
            <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">📅 Periode Penilaian Juri</h3>
            <p style="margin: 0; font-size: 1rem; line-height: 1.4;">
                <strong>Dibuka:</strong><br>{judging_start_formatted}<br><br>
                <strong>Ditutup:</strong><br>{judging_end_formatted}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: rgba(241, 196, 15, 0.9);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        ">
            <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">🏆 Pengumuman Pemenang</h3>
            <p style="margin: 0; font-size: 1rem; line-height: 1.4;">
                <strong>Tanggal:</strong><br>{announcement_formatted}
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_certificate_section():
    """Render certificate download section"""
    st.markdown("### 🏆 Download Sertifikat Peserta")
    st.markdown("**Peserta dapat mengunduh sertifikat secara mandiri:**")

    # Back button
    if st.button("← Kembali ke Beranda", type="secondary"):
        st.rerun()

    st.markdown("---")

    # Get list of participants for dropdown
    try:
        from services.database_service import db_service
        songs_df = db_service.get_songs()

        if not songs_df.empty:
            # Create list of "Composer - Title" options
            song_options = []
            for _, song in songs_df.iterrows():
                composer = song.get('composer', 'Unknown')
                title = song.get('title', 'Unknown')
                certificate_path = song.get('certificate_path')

                # Only include songs that have certificate_path
                if certificate_path:
                    option = f"{composer} - {title}"
                    song_options.append({
                        'display': option,
                        'composer': composer,
                        'title': title,
                        'certificate_path': certificate_path
                    })

            # Sort by composer name
            song_options.sort(key=lambda x: x['composer'])

            col1, col2 = st.columns([2, 1])

            with col1:
                if song_options:
                    display_options = ["-- Pilih Peserta & Karya --"] + [opt['display'] for opt in song_options]
                    selected_option = st.selectbox(
                        "Pilih peserta dan karya:",
                        display_options,
                        key="participant_selector"
                    )
                else:
                    st.info("📋 Tidak ada sertifikat yang tersedia")

            with col2:
                if song_options and 'selected_option' in locals() and selected_option and selected_option != "-- Pilih Peserta & Karya --":
                    # Find the selected song data
                    selected_song_data = None
                    for opt in song_options:
                        if opt['display'] == selected_option:
                            selected_song_data = opt
                            break

                    if selected_song_data:
                        certificate_path = selected_song_data['certificate_path']
                        composer = selected_song_data['composer']
                        title = selected_song_data['title']

                        # Construct direct public URL
                        import urllib.parse
                        supabase_project_url = st.secrets["supabase_url"]
                        bucket_name = "song-contest-files"
                        folder_name = "certificates"
                        encoded_path = urllib.parse.quote(f"{folder_name}/{certificate_path}")
                        direct_url = f"{supabase_project_url}/storage/v1/object/public/{bucket_name}/{encoded_path}"

                        # Download button
                        st.markdown(f"""
                        <a href="{direct_url}" target="_blank" style="text-decoration: none;">
                            <button style="
                                background-color: #4CAF50;
                                color: white;
                                padding: 10px 20px;
                                border: none;
                                border-radius: 5px;
                                cursor: pointer;
                                font-size: 16px;
                                width: 100%;
                            ">
                                📥 Download Sertifikat
                            </button>
                        </a>
                        """, unsafe_allow_html=True)

                        st.caption(f"Peserta: {composer}")
                        st.caption(f"Karya: {title}")
                        st.caption(f"File: {certificate_path}")
                    else:
                        st.warning("⚠️ Data sertifikat tidak ditemukan")
                        st.info("💡 Hubungi panitia jika ada pertanyaan")
        else:
            st.info("📋 Data peserta belum tersedia")

    except Exception as e:
        st.error(f"❌ Error loading participants: {e}")


def render_info_section():
    """Render contest information section"""
    st.markdown("### 📋 Informasi Lomba Cipta Lagu Bulkel 2025")

    # Back button
    if st.button("← Kembali ke Beranda", type="secondary"):
        st.rerun()

    st.markdown("---")

    # Contest information
    st.markdown("""
    #### 🎯 Tema Lomba
    **"Waktu Bersama Harta Berharga"**

    #### 📅 Timeline
    - **Pendaftaran**: Sudah ditutup
    - **Penilaian**: Sudah selesai
    - **Pengumuman**: Akan diumumkan segera

    #### 🏆 Kategori Penilaian
    1. **Tema (25%)** - Kesesuaian dengan tema lomba
    2. **Lirik (25%)** - Kualitas dan makna lirik
    3. **Musik (25%)** - Melodi, harmoni, dan aransemen
    4. **Kreativitas (15%)** - Orisinalitas dan inovasi
    5. **Jemaat (10%)** - Kemudahan untuk dinyanyikan jemaat

    #### 👥 Tim Juri
    - Juri ahli musik gereja
    - Praktisi musik rohani
    - Tokoh gereja berpengalaman

    #### 📞 Kontak
    Untuk pertanyaan lebih lanjut, silakan hubungi panitia lomba.
    """)


# ==================== MAIN APPLICATION ====================

def main():
    """Main application function with authentication"""
    # Hide Streamlit's built-in navigation (more specific)
    st.markdown("""
    <style>
    /* Hide only the built-in page navigation, not the entire sidebar */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Hide navigation links specifically */
    .css-1d391kg {
        display: none !important;
    }

    /* Hide the page selector */
    .css-17lntkn {
        display: none !important;
    }

    /* More specific selectors for page navigation */
    section[data-testid="stSidebar"] nav {
        display: none !important;
    }

    /* Hide page navigation list */
    section[data-testid="stSidebar"] ul[role="list"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize
    initialize_app()

    # Handle authentication callbacks
    handle_auth_callbacks()

    # Check authentication
    current_user = auth_service.get_current_user()

    # TEMPORARY: Test mode bypass
    if st.query_params.get("test") == "true":
        st.warning("🧪 TEST MODE - Authentication bypassed")
        current_user = {
            'id': '1',
            'email': 'alvin.mingguw@gmail.com',
            'full_name': 'Alvin Giovanni Mingguw',
            'role': 'admin',
            'judge_id': 1,
            'provider': 'test'
        }

    if not current_user:
        # Show landing page with contest status
        render_landing_page()
        return

    # Check if user is authorized (exists in judges table)
    if not current_user.get('judge_id'):
        render_unauthorized_page()
        return

    # Check if user wants to see dashboard (from sidebar button)
    show_dashboard = st.session_state.get('show_dashboard', False)

    if not show_dashboard:
        # User is logged in but still wants to see landing page
        render_landing_page()
        return

    # User is authenticated and wants dashboard - DUAL ROLE SUPPORT
    user_role = current_user.get('role', 'judge')
    is_impersonating = auth_service.is_impersonating()

    # Admin can choose between admin panel and judging
    if user_role == 'admin' and not is_impersonating:
        # Admin choice: Admin Panel or Judge Interface
        st.sidebar.markdown("---")
        st.sidebar.subheader("👨‍💼 Admin Options")

        mode = st.sidebar.radio(
            "Choose Mode:",
            ["🎵 Judge Songs", "⚙️ Admin Panel"],
            key="admin_mode"
        )

        if mode == "⚙️ Admin Panel":
            render_admin_panel(current_user)
            return
        else:
            # Admin acting as judge
            st.sidebar.success("🎵 Admin mode: Judging songs")

    # Show main application (for judges, impersonated users, or admin in judge mode)
    render_main_app(current_user)

def render_main_app(current_user):
    """Render main application for authenticated users"""
    # Check if user wants to see landing page
    if st.session_state.get('show_landing', False):
        # Clear the flag
        st.session_state.show_landing = False

        # Show user info in sidebar (still need navigation)
        render_user_sidebar(current_user)

        # Show admin impersonation controls in sidebar (if admin)
        render_admin_impersonation_sidebar(current_user)

        # Render landing page for authenticated user
        render_landing_page()
        return

    # Display banner
    display_banner()

    # Check form schedule
    schedule_status = check_form_schedule()

    # Show schedule information
    if 'error' not in schedule_status:
        current_time = schedule_status['current_time']
        st.caption(f"🕐 Waktu sekarang: {current_time.strftime('%d/%m/%Y %H:%M:%S %Z')}")

        if schedule_status['is_before_open']:
            st.warning(f"⏰ Form belum dibuka. Akan dibuka pada: {schedule_status['form_open'].strftime('%d/%m/%Y %H:%M')}")
        elif schedule_status['is_after_close']:
            st.info(f"⏰ Form sudah ditutup pada: {schedule_status['form_close'].strftime('%d/%m/%Y %H:%M')}")
        elif not schedule_status['can_evaluate']:
            st.warning("⏰ Form penilaian sedang tidak tersedia")

    # Show user info in sidebar
    render_user_sidebar(current_user)

    # Show admin impersonation controls in sidebar (if admin)
    render_admin_impersonation_sidebar(current_user)

    # Show admin data fix controls (if admin)
    if current_user and current_user.get('role') == 'admin':
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🔧 Admin Tools")
            if st.button("🔧 Fix Database Scores", help="Fix corrupted scores in database"):
                fix_corrupted_scores()
            if st.button("⚙️ Setup Missing Config", help="Add missing configuration keys"):
                setup_missing_config()

    # Main navigation with session state support (removed Analisis Lagu tab)
    tab_names = ["📝 Penilaian", "📋 History Penilaian", "📊 Hasil & Analitik"]

    # Check if active tab is set in session state (from edit button)
    if 'active_tab' in st.session_state:
        try:
            default_tab = tab_names.index(st.session_state.active_tab)
        except ValueError:
            default_tab = 0
        # Clear the session state after using it
        del st.session_state.active_tab
    else:
        default_tab = 0

    # Create tabs (removed tab3 - Analisis Lagu)
    tab1, tab2, tab3 = st.tabs(tab_names)

    with tab1:
        render_evaluation_tab(current_user)

    with tab2:
        render_evaluation_history_tab(current_user)

    with tab3:
        render_analytics_tab()

if __name__ == "__main__":
    main()
