# -*- coding: utf-8 -*-
"""
Export Service - Handles all export functionality (PDF, Excel, certificates)
Provides optimized export operations with better performance
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import io
import base64
import zipfile
import os
import re
from datetime import datetime
import logging

# ReportLab imports
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExportService:
    """Centralized export service for all document generation"""
    
    def __init__(self):
        """Initialize export service"""
        self.assets_path = "assets"
        self.banner_path = f"{self.assets_path}/banner.png"
        self.logo_path = f"{self.assets_path}/logo.png"
        self.watermark_text = "GKI PERUMNAS"
    
    # ==================== EXCEL EXPORTS ====================
    
    @st.cache_data(show_spinner=False)
    def export_comprehensive_excel(_self) -> bytes:
        """Export comprehensive Excel report with all data"""
        try:
            from services.database_service import db_service
            from services.analytics_service import analytics_service
            
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # Get all data
                evaluations_df = db_service.get_evaluations()
                songs_df = db_service.get_songs()
                judges_df = db_service.get_judges()
                leaderboard_df = analytics_service.get_global_leaderboard()
                judge_analytics_df = analytics_service.get_judge_analytics()
                rubric_analytics_df = analytics_service.get_rubric_analytics()
                
                # Export raw evaluations
                if not evaluations_df.empty:
                    evaluations_df.to_excel(writer, sheet_name='Raw_Evaluations', index=False)
                
                # Export leaderboard
                if not leaderboard_df.empty:
                    leaderboard_df.to_excel(writer, sheet_name='Leaderboard', index=False)
                
                # Export judge analytics
                if not judge_analytics_df.empty:
                    judge_analytics_df.to_excel(writer, sheet_name='Judge_Analytics', index=False)
                
                # Export rubric analytics
                if not rubric_analytics_df.empty:
                    rubric_analytics_df.to_excel(writer, sheet_name='Rubric_Analytics', index=False)
                
                # Export songs list
                if not songs_df.empty:
                    songs_df.to_excel(writer, sheet_name='Songs', index=False)
                
                # Export judges list
                if not judges_df.empty:
                    judges_df.to_excel(writer, sheet_name='Judges', index=False)
                
                # Summary statistics
                summary_data = _self._create_summary_statistics(
                    evaluations_df, leaderboard_df, judge_analytics_df
                )
                summary_df = pd.DataFrame([summary_data])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting Excel: {e}")
            return b""
    
    def _create_summary_statistics(self, evaluations_df: pd.DataFrame, 
                                 leaderboard_df: pd.DataFrame, 
                                 judge_analytics_df: pd.DataFrame) -> Dict:
        """Create summary statistics for Excel export"""
        summary = {
            'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_songs': len(leaderboard_df) if not leaderboard_df.empty else 0,
            'total_judges': len(judge_analytics_df) if not judge_analytics_df.empty else 0,
            'total_evaluations': len(evaluations_df) if not evaluations_df.empty else 0,
        }
        
        if not evaluations_df.empty:
            summary.update({
                'avg_score_overall': evaluations_df['total_score'].mean(),
                'score_std_overall': evaluations_df['total_score'].std(),
                'min_score': evaluations_df['total_score'].min(),
                'max_score': evaluations_df['total_score'].max(),
            })
        
        if not leaderboard_df.empty:
            summary.update({
                'leading_song': leaderboard_df.iloc[0]['title'],
                'leading_score': leaderboard_df.iloc[0]['avg_score'],
            })
        
        return summary
    
    # ==================== PDF EXPORTS ====================
    
    @st.cache_data(show_spinner=False)
    def export_leaderboard_pdf(_self, leaderboard_df: pd.DataFrame) -> bytes:
        """Export leaderboard as PDF"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, 
                                  topMargin=36, bottomMargin=36)
            
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name="H1", fontSize=18, leading=22, spaceAfter=12, alignment=1))
            styles.add(ParagraphStyle(name="H2", fontSize=13, leading=16, spaceBefore=8, spaceAfter=6))
            
            story = []
            
            # Title
            story.append(Paragraph("Leaderboard - Lomba Cipta Lagu GKI Perumnas 2025", styles["H1"]))
            story.append(Paragraph(datetime.now().strftime("%d %B %Y %H:%M"), styles["Normal"]))
            story.append(Spacer(1, 12))
            
            if not leaderboard_df.empty:
                # Create table data
                table_data = [["Rank", "Song Title", "Composer", "Avg Score", "Std Dev", "Judges"]]
                
                for _, row in leaderboard_df.head(15).iterrows():
                    table_data.append([
                        str(row['rank']),
                        str(row['title'])[:30],  # Truncate long titles
                        str(row['composer'])[:20],  # Truncate long names
                        f"{row['avg_score']:.2f}",
                        f"{row['score_std']:.2f}" if pd.notna(row['score_std']) else "N/A",
                        str(row['unique_judges'])
                    ])
                
                # Create table
                table = Table(table_data, colWidths=[1.5*cm, 6*cm, 4*cm, 2*cm, 2*cm, 1.5*cm])
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (3, 1), (5, -1), 'RIGHT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                ]))
                
                story.append(table)
            else:
                story.append(Paragraph("No evaluation data available.", styles["Normal"]))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting leaderboard PDF: {e}")
            return b""
    
    # ==================== CERTIFICATE GENERATION ====================
    
    @st.cache_data(show_spinner=False)
    def generate_certificate(_self, name: str, song_title: str, rank: int = None, 
                           is_winner: bool = False) -> bytes:
        """Generate individual certificate"""
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=landscape(A4))
            width, height = landscape(A4)
            
            # Draw certificate
            _self._draw_certificate_content(c, width, height, name, song_title, rank, is_winner)
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating certificate for {name}: {e}")
            return b""
    
    def _draw_certificate_content(self, canvas_obj, width: float, height: float, 
                                name: str, song_title: str, rank: int = None, 
                                is_winner: bool = False):
        """Draw certificate content on canvas"""
        # Background and watermark
        self._draw_watermark(canvas_obj, width, height)
        
        # Header with banner/logo
        self._draw_header(canvas_obj, width, height, is_winner)
        
        # Main content
        canvas_obj.setFillColor(colors.black)
        canvas_obj.setFont("Helvetica", 12)
        canvas_obj.drawCentredString(width/2, height/2 + 60, "Diberikan kepada")
        
        # Name (large, bold)
        self._fit_centered_text(canvas_obj, name or "(Nama)", y=height/2 + 20, 
                              max_width=width-180, font="Helvetica-Bold", 
                              start_size=36, min_size=16)
        
        # Award text
        if is_winner and rank:
            canvas_obj.setFillColor(colors.HexColor("#D4AF37"))
            canvas_obj.setFont("Helvetica-Bold", 18)
            canvas_obj.drawCentredString(width/2, height/2 - 20, f"JUARA {rank}")
            canvas_obj.setFillColor(colors.black)
            canvas_obj.setFont("Helvetica", 13)
            canvas_obj.drawCentredString(width/2, height/2 - 45, 
                                       "Atas prestasi gemilang dalam Lomba Cipta Lagu.")
        else:
            canvas_obj.setFont("Helvetica", 13)
            canvas_obj.drawCentredString(width/2, height/2 - 45, 
                                       "Atas partisipasi dalam Lomba Cipta Lagu.")
        
        # Song title
        if song_title:
            canvas_obj.setFont("Helvetica-Oblique", 12)
            self._fit_centered_text(canvas_obj, f'Lagu: "{song_title}"', 
                                  y=height/2 - 70, max_width=width-220, 
                                  font="Helvetica-Oblique", start_size=12, min_size=10)
        
        # Footer
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(60, 80, datetime.now().strftime("Diterbitkan: %d %B %Y"))
        canvas_obj.line(60, 120, 260, 120)
        canvas_obj.drawString(60, 125, "Panitia")
        canvas_obj.line(width-260, 120, width-60, 120)
        canvas_obj.drawRightString(width-60, 125, "Ketua Panitia")
    
    def _draw_watermark(self, canvas_obj, width: float, height: float):
        """Draw watermark on certificate"""
        canvas_obj.saveState()
        try:
            canvas_obj.setFillColor(colors.Color(0, 0, 0, alpha=0.06))
        except Exception:
            canvas_obj.setFillColor(colors.grey)
        
        canvas_obj.translate(width/2, height/2)
        canvas_obj.rotate(30)
        canvas_obj.setFont("Helvetica-Bold", 96)
        canvas_obj.drawCentredString(0, 0, self.watermark_text)
        canvas_obj.restoreState()
    
    def _draw_header(self, canvas_obj, width: float, height: float, is_winner: bool):
        """Draw header with banner and logo"""
        # Try to load and draw banner
        try:
            if os.path.exists(self.banner_path):
                banner_height = 150
                canvas_obj.drawImage(self.banner_path, 0, height-banner_height, 
                                   width=width, height=banner_height, 
                                   preserveAspectRatio=True, mask='auto')
            else:
                # Fallback: black rectangle
                canvas_obj.setFillColor(colors.black)
                canvas_obj.rect(0, height-110, width, 110, fill=1, stroke=0)
        except Exception:
            # Fallback: black rectangle
            canvas_obj.setFillColor(colors.black)
            canvas_obj.rect(0, height-110, width, 110, fill=1, stroke=0)
        
        # Try to draw logo
        try:
            if os.path.exists(self.logo_path):
                canvas_obj.drawImage(self.logo_path, 40, height-100, 
                                   width=90, height=90, 
                                   preserveAspectRatio=True, mask='auto')
        except Exception:
            pass  # Skip logo if not available
        
        # Title text
        canvas_obj.setFillColor(colors.whitesmoke)
        canvas_obj.setFont("Helvetica-Bold", 28)
        title_text = "SERTIFIKAT PEMENANG" if is_winner else "SERTIFIKAT"
        canvas_obj.drawCentredString(width/2, height-65, title_text)
        
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#D4AF37"))
        canvas_obj.drawCentredString(width/2, height-92, "Lomba Cipta Lagu — GKI Perumnas")
    
    def _fit_centered_text(self, canvas_obj, text: str, y: float, max_width: float, 
                         font: str, start_size: int, min_size: int):
        """Fit text within specified width by adjusting font size"""
        size = start_size
        while size >= min_size:
            canvas_obj.setFont(font, size)
            text_width = canvas_obj.stringWidth(text)
            if text_width <= max_width:
                break
            size -= 1
        
        canvas_obj.setFont(font, size)
        canvas_obj.drawCentredString(canvas_obj._pagesize[0]/2, y, text)
    
    # ==================== BATCH OPERATIONS ====================
    
    @st.cache_data(show_spinner=False)
    def generate_all_certificates(_self) -> bytes:
        """Generate certificates for all participants and winners"""
        try:
            from services.database_service import db_service
            from services.analytics_service import analytics_service
            
            # Get data
            songs_df = db_service.get_songs()
            leaderboard_df = analytics_service.get_global_leaderboard()
            
            # Determine winners (top 3)
            winners = {}
            if not leaderboard_df.empty:
                for i, row in leaderboard_df.head(3).iterrows():
                    winners[row['title']] = i + 1
            
            # Create ZIP file
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
                for _, song in songs_df.iterrows():
                    title = song['title']
                    composer = song['composer'] or "Peserta"
                    rank = winners.get(title)
                    is_winner = rank is not None
                    
                    # Generate certificate
                    cert_bytes = _self.generate_certificate(composer, title, rank, is_winner)
                    
                    # Create safe filename
                    safe_composer = re.sub(r"[^A-Za-z0-9 _-]+", "", composer)[:60] or "Peserta"
                    safe_title = re.sub(r"[^A-Za-z0-9 _-]+", "", title)[:60] or "Lagu"
                    filename = f"certificate/{safe_composer} - {safe_title}.pdf"
                    
                    zip_file.writestr(filename, cert_bytes)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating all certificates: {e}")
            return b""

# Global instance
export_service = ExportService()
