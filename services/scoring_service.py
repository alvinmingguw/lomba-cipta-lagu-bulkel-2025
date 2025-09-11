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
            "harta", "permata", "berharga", "tak ternilai", "mutiara",
            "pelabuhan", "sauh", "jangkar", "bahtera", "rumahku"
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
        
        Args:
            chord_sequence: List of chord symbols
            
        Returns:
            Score from 1 to 5
        """
        if not chord_sequence:
            return 1
        
        unique_chords = list(dict.fromkeys(chord_sequence))
        
        # Calculate features
        uniqueness = min(len(set(unique_chords)) / 10.0, 1.0)
        
        # Transition entropy
        bigrams = list(zip(chord_sequence, chord_sequence[1:])) if len(chord_sequence) > 1 else []
        if bigrams:
            bigram_counts = Counter(bigrams)
            total = sum(bigram_counts.values())
            transition_entropy = self._calculate_entropy([v/total for v in bigram_counts.values()])
        else:
            transition_entropy = 0.0
        
        # Chord complexity features
        extensions = sum(1 for c in chord_sequence if self._has_extension(c)) / max(1, len(chord_sequence))
        slash_chords = sum(1 for c in chord_sequence if "/" in c) / max(1, len(chord_sequence))
        non_diatonic = sum(1 for c in chord_sequence if self._is_non_diatonic(c)) / max(1, len(chord_sequence))
        
        # Calculate weighted score
        raw_score = (
            15 * uniqueness +
            20 * transition_entropy +
            30 * extensions +
            20 * slash_chords +
            15 * non_diatonic
        )
        
        # Penalties for overly simple progressions
        if extensions == 0 and slash_chords == 0 and non_diatonic == 0:
            raw_score -= 18  # No color at all
        if len(set(unique_chords)) <= 4 and transition_entropy < 0.25:
            raw_score -= 8   # Few chords and monotonous transitions
        
        raw_score = max(0.0, min(100.0, raw_score))
        return self._map_score_to_scale(raw_score)
    
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
