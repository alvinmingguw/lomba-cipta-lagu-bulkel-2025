# -*- coding: utf-8 -*-
"""
Scoring Service - Handles all scoring and evaluation logic
Extracted from the monolithic application for better maintainability
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import re
import unicodedata
import math
from collections import Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoringService:
    """Centralized scoring service for all evaluation logic"""
    
    def __init__(self):
        """Initialize scoring service"""
        self.chord_token_pattern = re.compile(
            r"^(?:[A-G](?:#|b)?(?:maj7|maj|min|m7|m|7|sus2|sus4|sus|dim|aug|add9|add11|add13|6|9|11|13)?)"
            r"(?:/[A-G](?:#|b)?)?$"
        )
        
        self.section_words = {
            "bait", "bait1", "bait2", "bait3", "bait4",
            "reff", "ref", "reffrein", "chorus", "prechorus", "pre-chorus", "pre_chorus",
            "bridge", "intro", "interlude", "outro", "ending", "coda",
            "verse", "verse1", "verse2", "verse3", "do"
        }
        
        # Theme-related keywords
        self.theme_keywords = {
            "tema_dalam": [
                "waktu", "kesempatan", "bijaksana", "arif", "pergunakan", "saksama",
                "hadir", "saat ini", "dekat", "persekutuan"
            ],
            "keluarga": [
                "keluarga", "bersama", "rumah", "ayah", "bunda", "ibu", "anak",
                "kasih", "rukun", "saling menjaga"
            ],
            "iman": [
                "iman", "doa", "tuhan", "yesus", "syukur", "berkat", "pengharapan", "setia"
            ]
        }
        
        self.imagery_words = [
            # Value & treasure imagery
            "harta", "permata", "berharga", "tak ternilai", "mutiara", "berlian", "emas",
            # Nautical & journey imagery
            "pelabuhan", "sauh", "jangkar", "bahtera", "rumahku", "jalan", "perjalanan",
            # Light & spiritual imagery
            "cahaya", "terang", "sinar", "bersinar", "gemilang", "cemerlang",
            # Nature & beauty imagery
            "bunga", "kembang", "taman", "sungai", "mata air", "embun", "fajar",
            # Metaphorical expressions from actual songs
            "seperti", "bagaikan", "laksana", "ibarat", "umpama", "bagai", "layaknya",
            # Depth & authenticity
            "dalam", "mendalam", "nyata", "sejati", "hakiki", "murni", "tulus"
        ]
        
        self.cliche_phrases = [
            "tuhan pasti memberkati", "jalanmu lurus", "hidupku indah", 
            "selalu bersama selamanya", "tetap semangat", "kau kuatkanku", 
            "percaya saja", "kasih setiamu"
        ]
    
    # ==================== LYRICS SCORING ====================
    
    def score_lyrics_strength(self, text: str) -> int:
        """
        Score lyrics strength (1-5) based on theme relevance and quality
        
        Args:
            text: Lyrics text to analyze
            
        Returns:
            Score from 1 to 5
        """
        if not text:
            return 1
        
        normalized_text = self._normalize_text(text)
        
        # 1. Theme depth (35% weight)
        theme_score = sum(normalized_text.count(w) for w in self.theme_keywords["tema_dalam"])
        theme_score = min(theme_score, 8)  # Cap at 8 hits
        
        # 2. Family & faith elements (25% weight)
        family_score = sum(normalized_text.count(w) for w in self.theme_keywords["keluarga"])
        faith_score = sum(normalized_text.count(w) for w in self.theme_keywords["iman"])
        relation_score = min(family_score + faith_score, 10)  # Cap at 10 total hits
        
        # 3. Poetic quality & imagery (20% weight)
        imagery_score = sum(1 for kw in self.imagery_words if kw in normalized_text)
        imagery_score = min(imagery_score, 5)
        
        # 4. Song structure (20% weight)
        lines = [l.strip() for l in normalized_text.splitlines() if l.strip()]
        section_tokens = sum(1 for tok in ["reff", "refrein", "chorus", "verse", "bait"] 
                           if tok in normalized_text)
        unique_lines = len(set(lines))
        varied_lines = (unique_lines / max(1, len(lines))) >= 0.7
        structure_score = (2 if section_tokens >= 1 else 0) + \
                         (1 if section_tokens >= 2 else 0) + \
                         (1 if varied_lines else 0)
        
        # 5. Penalties for clichés and unsolved distractions
        cliche_hits = sum(1 for c in self.cliche_phrases if c in normalized_text)
        distraction_penalty = self._check_distraction_penalty(normalized_text)
        penalty = min(2, cliche_hits) + (2 if distraction_penalty else 0)
        
        # Calculate final score (0-100)
        raw_score = (
            35 * (theme_score / 8.0) +
            25 * (relation_score / 10.0) +
            20 * (imagery_score / 5.0) +
            20 * (structure_score / 4.0) -
            15 * (penalty / 4.0)
        )
        raw_score = max(0.0, min(100.0, raw_score))
        
        return self._map_score_to_scale(raw_score)
    
    def _check_distraction_penalty(self, text: str) -> bool:
        """Check if text mentions distractions without offering solutions"""
        distractions = ["dunia maya", "medsos", "layar", "gawai", "sibuk", "sendiri", "jarak"]
        solutions = self.theme_keywords["iman"] + ["bersama", "dekat"]
        
        has_distractions = any(d in text for d in distractions)
        has_solutions = any(s in text for s in solutions)
        
        return has_distractions and not has_solutions
    
    # ==================== MUSIC SCORING ====================
    
    def score_harmonic_richness(self, chord_sequence: List[str]) -> int:
        """
        Score harmonic richness (1-5) based on chord complexity and variety
        Optimized for congregational songs - balanced scoring

        Args:
            chord_sequence: List of chord symbols

        Returns:
            Score from 1 to 5
        """
        if not chord_sequence:
            return 2  # Default for missing data, not 1

        unique_chords = list(dict.fromkeys(chord_sequence))
        unique_count = len(set(unique_chords))
        total_chords = len(chord_sequence)

        # Base score from chord variety (more generous)
        if unique_count >= 8:
            variety_score = 5
        elif unique_count >= 6:
            variety_score = 4
        elif unique_count >= 4:
            variety_score = 3
        elif unique_count >= 3:
            variety_score = 2
        else:
            variety_score = 1

        # Bonus features (not penalties)
        bonus_score = 0

        # Extensions bonus (7th, 9th, etc.)
        extensions = sum(1 for c in chord_sequence if self._has_extension(c))
        if extensions > 0:
            extension_ratio = extensions / max(1, len(chord_sequence))
            if extension_ratio >= 0.3:
                bonus_score += 1.0  # Many extensions
            elif extension_ratio >= 0.1:
                bonus_score += 0.5  # Some extensions

        # Slash chords bonus
        slash_chords = sum(1 for c in chord_sequence if "/" in c)
        if slash_chords > 0:
            bonus_score += min(0.5, slash_chords / max(1, len(chord_sequence)) * 2)

        # Non-diatonic bonus (but not required)
        non_diatonic = sum(1 for c in chord_sequence if self._is_non_diatonic(c))
        if non_diatonic > 0:
            bonus_score += min(0.3, non_diatonic / max(1, len(chord_sequence)))

        # Progression length bonus
        if total_chords >= 16:
            bonus_score += 0.3  # Good length
        elif total_chords >= 8:
            bonus_score += 0.2  # Adequate length

        # Calculate final score
        final_score = variety_score + bonus_score

        # Special boost for sophisticated songs (like winning songs)
        # If song has good variety + complexity, boost it
        if unique_count >= 8 and total_chords >= 20:
            final_score += 0.5  # Boost for sophisticated songs
        elif unique_count >= 6 and total_chords >= 15:
            final_score += 0.3  # Moderate boost

        # Ensure reasonable range for congregational music
        final_score = max(2.0, min(5.0, final_score))  # Minimum 2, not 1

        return int(round(final_score))
    
    def _has_extension(self, chord: str) -> bool:
        """Check if chord has extensions (7th, 9th, etc.)"""
        extension_pattern = re.compile(r'(maj7|m7|maj|7|9|11|13|sus2|sus4|sus|dim|aug|add9|6|add11|add13)')
        return bool(extension_pattern.search(chord))
    
    def _is_non_diatonic(self, chord: str) -> bool:
        """Simple check for non-diatonic chords (sharps/flats)"""
        return bool(re.match(r'^[A-G](#|b)', chord))
    
    # ==================== THEME SCORING ====================
    
    def score_theme_relevance(self, text: str, keywords: List[Tuple[str, float]], 
                            phrases: List[Tuple[str, float]]) -> float:
        """
        Score theme relevance based on keyword and phrase matching
        
        Args:
            text: Text to analyze
            keywords: List of (keyword, weight) tuples
            phrases: List of (phrase, weight) tuples
            
        Returns:
            Theme score (0-100)
        """
        if not text:
            return 0.0
        
        normalized_text = self._normalize_text(text)
        score = 0.0
        
        # Score phrases
        for phrase, weight in phrases:
            score += normalized_text.count(phrase.lower()) * float(weight)
        
        # Score keywords
        for keyword, weight in keywords:
            matches = len(re.findall(rf"\b{re.escape(keyword.lower())}\w*\b", normalized_text))
            score += matches * float(weight)
        
        return float(min(round(score, 2), 100.0))

    def score_lyrical_quality(self, text: str) -> float:
        """
        Score lyrical quality based on poetic elements, depth, and sophistication

        Args:
            text: Lyrics text to analyze

        Returns:
            Lyrical quality score (0-100)
        """
        if not text:
            return 0.0

        normalized_text = self._normalize_text(text)
        score = 0.0

        # 1. Poetic Quality Indicators (30 points max)
        poetic_words = [
            'indah', 'puitis', 'syair', 'sajak', 'bait', 'rima', 'irama', 'melodi',
            'cantik', 'elok', 'molek', 'anggun', 'gemilang', 'cemerlang'
        ]
        poetic_matches = sum(1 for word in poetic_words if word in normalized_text)
        score += min(30, poetic_matches * 5)

        # 2. Emotional Depth (25 points max)
        emotional_words = [
            'hati', 'jiwa', 'rasa', 'perasaan', 'emosi', 'rindu', 'duka', 'suka',
            'cinta', 'kasih', 'tulus', 'ikhlas', 'dalam', 'mendalam'
        ]
        emotional_matches = sum(1 for word in emotional_words if word in normalized_text)
        score += min(25, emotional_matches * 4)

        # 3. Imagery & Metaphors (25 points max) - CRITICAL for poetic quality!
        imagery_words = [
            'seperti', 'bagaikan', 'laksana', 'ibarat', 'umpama', 'bagai', 'layaknya',
            'cahaya', 'terang', 'sinar', 'harta', 'permata', 'mutiara', 'berlian'
        ]
        imagery_matches = sum(1 for word in imagery_words if word in normalized_text)
        score += min(25, imagery_matches * 6)  # Higher weight for metaphors

        # 4. Spiritual & Meaningful Content (20 points max)
        spiritual_words = [
            'makna', 'arti', 'hikmah', 'pelajaran', 'renungan', 'refleksi',
            'berkat', 'syukur', 'tuhan', 'kudus', 'suci', 'sejati', 'nyata'
        ]
        spiritual_matches = sum(1 for word in spiritual_words if word in normalized_text)
        score += min(20, spiritual_matches * 4)

        # 5. Length & Structure Bonus (bonus points for substantial lyrics)
        word_count = len(normalized_text.split())
        if word_count >= 50:
            score += 10  # Substantial lyrics
        elif word_count >= 30:
            score += 5   # Adequate length

        # 6. Repetition & Flow (check for good structure)
        lines = text.split('\n')
        if len(lines) >= 8:  # Multiple verses/sections
            score += 5

        return float(min(round(score, 2), 100.0))

    # ==================== UTILITY FUNCTIONS ====================
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for analysis"""
        text = text.lower()
        text = "".join(c for c in unicodedata.normalize("NFKD", text) 
                      if not unicodedata.combining(c))
        text = re.sub(r"[^a-z0-9\s']+", " ", text)
        return re.sub(r"\s+", " ", text).strip()
    
    def _map_score_to_scale(self, raw_score: float) -> int:
        """Map 0-100 score to 1-5 scale"""
        cuts = [20, 40, 60, 80]
        return 1 + sum(raw_score >= c for c in cuts)
    
    def _calculate_entropy(self, probabilities: List[float]) -> float:
        """Calculate entropy for transition analysis"""
        return -sum(p * math.log(p + 1e-12) for p in probabilities if p > 0) / \
               math.log(max(2, len(probabilities)))
    
    # ==================== CHORD ANALYSIS ====================
    
    def extract_chords_from_text(self, text: str) -> List[str]:
        """Extract chord symbols from text"""
        if not text:
            return []
        
        tokens = re.split(r"[^\w/#]+", text)
        seen, chords = set(), []
        
        for token in tokens:
            if not token:
                continue
            
            # Skip section words
            if token.lower() in self.section_words:
                continue
            
            # Check if it's a valid chord
            if self.chord_token_pattern.match(token):
                normalized_chord = token.strip().replace(" ", "")
                if normalized_chord not in seen:
                    seen.add(normalized_chord)
                    chords.append(normalized_chord)
        
        return chords
    
    def detect_key_from_chords(self, chord_sequence: List[str]) -> Tuple[str, float]:
        """
        Detect musical key from chord sequence
        
        Args:
            chord_sequence: List of chord symbols
            
        Returns:
            Tuple of (key_name, confidence)
        """
        if not chord_sequence:
            return ("?", 0.0)
        
        # Extract root notes
        root_notes = [self._extract_root_note(chord) for chord in chord_sequence]
        root_notes = [note for note in root_notes if note is not None]
        
        if not root_notes:
            return ("?", 0.0)
        
        # Pitch class mapping
        pitch_classes = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, 
                        "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, 
                        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
        
        pc_to_name = {v: k for k, v in pitch_classes.items() if "#" not in k and "b" not in k}
        
        # Score each possible tonic
        scores = []
        weights = {0: 2.0, 2: 1.2, 4: 1.2, 5: 2.0, 7: 2.0, 9: 1.2}  # I, ii, iii, IV, V, vi
        
        for tonic in range(12):
            score = 0.0
            for root in root_notes:
                root_pc = pitch_classes.get(root)
                if root_pc is not None:
                    offset = (root_pc - tonic) % 12
                    if offset in weights:
                        score += weights[offset]
                    else:
                        score -= 0.5  # Penalty for non-diatonic
            scores.append(score)
        
        # Find best key
        best_idx = int(np.argmax(scores))
        best_score = scores[best_idx]
        second_best = sorted(scores, reverse=True)[1] if len(scores) > 1 else 0.0
        
        # Calculate confidence
        denominator = abs(best_score) + sum(abs(x) for x in scores) / max(1, len(scores))
        confidence = max(0.0, min(1.0, (best_score - second_best) / (denominator + 1e-9)))
        
        key_name = pc_to_name.get(best_idx, "?")
        return (key_name, float(round(confidence, 3)))
    
    def _extract_root_note(self, chord: str) -> Optional[str]:
        """Extract root note from chord symbol"""
        if not chord:
            return None
        
        # Take the part before slash (if any)
        base_chord = chord.split('/')[0].strip()
        
        # Extract root note
        match = re.match(r'^([A-G](?:#|b)?)', base_chord)
        if match:
            return match.group(1).upper().replace('♭', 'b').replace('♯', '#')
        
        return None

# Global instance
scoring_service = ScoringService()
