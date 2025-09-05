import re
import unicodedata
import math
import numpy as np
import pandas as pd
from collections import Counter
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Callable
from wordcloud import WordCloud, STOPWORDS
import io

# Assuming other core modules are in the same directory
from .pdf_utils import extract_pdf_text_cached
from .config import cfg_get
from .utils import _map_0_100_to_1_5

# =========================
# Text and Lyric Analysis
# =========================

def _normalize_text(s: str) -> str:
    """Normalizes a string by lowercasing, removing diacritics and punctuation."""
    s = s.lower()
    try:
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    except TypeError:
        pass # Handle potential errors on non-string input
    s = re.sub(r"[^a-z0-9\s']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def generate_wordcloud_image(text: str) -> io.BytesIO:
    """Generates a word cloud image from a text string."""
    if not text:
        return None

    custom_stopwords = set(STOPWORDS)
    custom_stopwords.update(["lagu", "lirik", "syair", "bait", "reff"])

    wc = WordCloud(
        background_color="white",
        max_words=100,
        stopwords=custom_stopwords,
        width=800,
        height=400,
        colormap='viridis'
    ).generate(text)

    img_buffer = io.BytesIO()
    wc.to_image().save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

def make_theme_functions(phrases: list, keywords: list) -> Tuple[Callable, Callable]:
    """Creates functions to score and highlight text based on theme keywords."""
    def score_theme(text: str) -> float:
        t_norm = _normalize_text(text or "")
        score = 0.0
        for p, w in phrases:
            score += t_norm.count(p.lower()) * float(w)
        for k, w in keywords:
            score += len(re.findall(rf"\b{re.escape(k.lower())}\w*\b", t_norm)) * float(w)
        return min(round(score, 2), 100.0)

    def highlight_theme(text: str) -> str:
        html = text or ""
        # Highlight longer phrases first to avoid partial matches
        for p, _ in sorted(phrases, key=lambda x: len(x[0]), reverse=True):
            html = re.sub(fr"(?i)({re.escape(p)})", r"<mark>\1</mark>", html, flags=re.IGNORECASE)
        for k, _ in keywords:
            html = re.sub(fr"(?i)\b({re.escape(k)}\w*)\b", r"<mark>\1</mark>", html, flags=re.IGNORECASE)
        return (html or "<i>(syair kosong)</i>").replace("\n", "<br>")

    return score_theme, highlight_theme

# Constants for lyric analysis
_EMO_WORDS_V2 = {
    "tema_dalam": ["waktu", "kesempatan", "bijaksana", "arif", "pergunakan", "saksama", "hadir", "saat ini", "dekat", "persekutuan"],
    "keluarga": ["keluarga", "bersama", "rumah", "ayah", "bunda", "ibu", "anak", "kasih", "rukun", "saling menjaga"],
    "iman": ["iman", "doa", "tuhan", "yesus", "syukur", "berkat", "pengharapan", "setia"]
}
_IMAGERY_V2 = ["harta", "permata", "berharga", "tak ternilai", "mutiara", "pelabuhan", "sauh", "jangkar", "bahtera", "rumahku"]
_DISTRACTIONS = ["dunia maya", "medsos", "layar", "gawai", "sibuk", "sendiri", "jarak"]
_CLICHES = ["tuhan pasti memberkati", "jalanmu lurus", "hidupku indah", "selalu bersama selamanya", "tetap semangat", "kau kuatkanku", "percaya saja", "kasih setiamu"]
_SECTION_TOKENS = ["reff", "refrein", "chorus", "verse", "bait", "bridge", "pre-chorus", "coda"]

def score_lyrics_strength(text: str) -> int:
    """Scores lyric strength (1-5) based on thematic depth, poetry, and structure."""
    if not text: return 1
    t_norm = _normalize_text(text)

    tema_score = min(sum(t_norm.count(w) for w in _EMO_WORDS_V2["tema_dalam"]), 8)
    relasi_score = min(sum(t_norm.count(w) for w in _EMO_WORDS_V2["keluarga"]) + sum(t_norm.count(w) for w in _EMO_WORDS_V2["iman"]), 10)
    img_score = min(sum(1 for kw in _IMAGERY_V2 if kw in t_norm), 5)

    lines = [l.strip() for l in t_norm.splitlines() if l.strip()]
    tokens = sum(1 for tok in _SECTION_TOKENS if tok in t_norm)
    struct_score = (2 if tokens >= 1 else 0) + (1 if tokens >= 2 else 0) + (1 if (len(set(lines)) / max(1, len(lines))) >= 0.7 else 0)

    penal = min(2, sum(1 for c in _CLICHES if c in t_norm))
    distraction_penalty = sum(1 for d in _DISTRACTIONS if d in t_norm) > 0 and not any(w in t_norm for w in _EMO_WORDS_V2["iman"] + ["bersama", "dekat"])
    penal += (2 if distraction_penalty else 0)

    raw_score = (35 * (tema_score / 8.0) + 25 * (relasi_score / 10.0) + 20 * (img_score / 5.0) + 20 * (struct_score / 4.0) - 15 * (penal / 4.0))
    return _map_0_100_to_1_5(max(0.0, min(100.0, raw_score)))

def highlight_lyrics_v2(text: str) -> str:
    """Highlights lyrics with different colors for different keyword categories."""
    if not text: return "<i>(Syair kosong)</i>"
    html = text.replace("\n", "<br>")
    colors = {"tema_dalam": "#FFD700", "iman": "#87CEEB", "keluarga": "#98FB98", "imagery": "#FFA07A", "distraksi": "#D3D3D3"}
    all_keywords = {"tema_dalam": _EMO_WORDS_V2["tema_dalam"], "iman": _EMO_WORDS_V2["iman"], "keluarga": _EMO_WORDS_V2["keluarga"], "imagery": _IMAGERY_V2, "distraksi": _DISTRACTIONS}

    for category, keywords in all_keywords.items():
        sorted_kws = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kws:
            pattern = re.compile(fr"\b({re.escape(kw)})\b", re.IGNORECASE)
            html = pattern.sub(f"<mark style='background-color:{colors[category]}; padding: 2px 4px; border-radius:4px;'>\\1</mark>", html)
    return html


# =========================
# Music and Chord Analysis
# =========================
CHORD_TOKEN = re.compile(r"^(?:[A-G](?:#|b)?(?:maj7|maj|min|m7|m|7|sus2|sus4|sus|dim|aug|add9|add11|add13|6|9|11|13)?)(?:/[A-G](?:#|b)?)?$")
SECTION_WORDS = {"bait", "reff", "chorus", "bridge", "intro", "outro", "coda", "verse", "do"}
_PITCH = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
_ROOT_RE = re.compile(r'^([A-G](?:#|b)?)')
QUAL_EXT = re.compile(r'(maj7|m7|maj|7|9|11|13|sus2|sus4|sus|dim|aug|add9|6|add11|add13)')

def strip_chords(text: str) -> str:
    """Removes chord notations from a lyric string."""
    if not text: return ""
    t = re.sub(r"\[[^\]]+\]", "", text) # Remove chords in brackets
    t = re.sub(r"(?<!\w)([A-G](?:#|b)?(?:m|maj7|m7|7|sus2|sus4|dim|aug|add9|6|9)?)(?!\w)", "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()

def extract_chords_strict(text: str) -> List[str]:
    """Extracts a list of unique chords from a text."""
    if not text: return []
    tokens = re.split(r"[^\w/#]+", text)
    seen, out = set(), []
    for tok in tokens:
        if not tok or tok.lower() in SECTION_WORDS: continue
        if CHORD_TOKEN.match(tok):
            norm = tok.strip().replace(" ", "")
            if norm not in seen:
                seen.add(norm)
                out.append(norm)
    return out

def _root_pc(ch: str) -> int | None:
    """Gets the pitch class of a chord's root."""
    m = _ROOT_RE.match((ch or "").split('/')[0].strip())
    return _PITCH.get(m.group(1).upper().replace('♭','b').replace('♯','#')) if m else None

def music_features_v2(seq: List[str]) -> Dict[str, Any]:
    """Calculates musical features from a chord sequence."""
    if not seq: return {"uniq_list": [], "big_count": 0, "ext": 0.0, "slash": 0.0, "nondi": 0.0}

    total = max(1, len(seq))
    uniq = list(dict.fromkeys(seq))
    bigrams = list(zip(seq, seq[1:])) if len(seq) > 1 else []

    ext = sum(1 for c in seq if QUAL_EXT.search(c)) / total
    slash = sum(1 for c in seq if "/" in c) / total
    nondi = sum(1 for c in seq if re.match(r'^[A-G](#|b)', c)) / total

    return {"uniq_list": uniq, "big_count": len(set(bigrams)), "ext": ext, "slash": slash, "nondi": nondi}

def score_harmonic_richness_v2(aset: Dict[str, Any], cfg: pd.DataFrame, chord_sources: List[str]) -> float:
    """Calculates a raw harmonic richness score (0-100)."""
    seq = chord_sequence_from_sources(aset, chord_sources)
    if not seq: return 0.0

    feats = music_features_v2(seq)
    uniq_norm = min(len(set(feats["uniq_list"])) / 12.0, 1.0)
    trans_norm = min(float(feats["big_count"]) / 12.0, 1.0)

    W_EXT = cfg_get(cfg, "MUSIC_W_EXT", 40, int) / 100.0
    W_SLA = cfg_get(cfg, "MUSIC_W_SLASH", 35, int) / 100.0
    W_NDI = cfg_get(cfg, "MUSIC_W_NDI", 25, int) / 100.0
    W_UQ = cfg_get(cfg, "MUSIC_W_UNIQ", 20, int) / 100.0
    W_TRA = cfg_get(cfg, "MUSIC_W_TRANS", 20, int) / 100.0

    raw = 100 * (W_EXT * feats["ext"] + W_SLA * feats["slash"] + W_NDI * feats["nondi"] + W_UQ * uniq_norm + W_TRA * trans_norm)

    if feats["slash"] == 0.0: raw -= cfg_get(cfg, "MUSIC_PENALTY_NO_SLASH", 15, int)
    if feats["ext"] == 0.0: raw -= cfg_get(cfg, "MUSIC_PENALTY_NO_EXT", 10, int)

    return max(0.0, float(raw))

def detect_key_from_chords(seq: List[str]) -> Tuple[str, float]:
    """Detects the musical key from a chord sequence."""
    pcs = [p for p in (_root_pc(ch) for ch in seq) if p is not None]
    if not pcs: return "?", 0.0

    weights = {0: 2.0, 2: 1.2, 4: 1.2, 5: 2.0, 7: 2.0, 9: 1.2}
    scores = []
    for t in range(12):
        s = sum(weights.get((r - t) % 12, -0.5) for r in pcs)
        scores.append(s)

    best_idx = int(np.argmax(scores))
    best_score = scores[best_idx]
    second_best = sorted(scores, reverse=True)[1] if len(scores) > 1 else 0.0
    conf = max(0.0, (best_score - second_best) / (abs(best_score) + 1e-9))

    pc_to_name = {v:k for k,v in {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}.items()}
    return pc_to_name.get(best_idx, "?"), round(conf, 3)

def detect_genre(seq: List[str]) -> str:
    """Estimates the genre from a chord sequence."""
    if not seq: return "Unknown"
    feats = music_features_v2(seq)
    E, B, X, U = feats["ext"], feats["slash"], feats["nondi"], len(feats["uniq_list"])
    if E > 0.2 or X > 0.15: return "Jazz/Gospel"
    if B > 0.15 and U <= 6: return "Worship/CCM"
    return "Pop/Ballad"

# =========================
# Combined Scoring and Suggestions
# =========================
def _pick_text_variant(song: dict, order: list, extract_syair: Callable, extract_notasi: Callable) -> Tuple[str, str]:
    """Picks the best available text source based on a priority list."""
    for src in order:
        if src in song and song[src].strip(): return src, song[src].strip()
        if src == "extract_syair" and (txt := (extract_syair() or "").strip()): return src, txt
        if src == "extract_notasi" and (txt := (extract_notasi() or "").strip()): return src, txt
    return "none", ""

def chord_sequence_from_sources(aset: dict, order: list) -> list[str]:
    """Gets a chord sequence from the best available source."""
    for src in order:
        if src == "chords_list" and aset.get(src):
            return [c.strip() for c in aset[src].split(',') if c.strip()]
        if src in ("syair_chord", "full_score") and aset.get(src):
            return extract_chords_strict(aset[src])
        if src == "extract_notasi" and aset.get("notasi"):
            return extract_chords_strict(extract_pdf_text_cached(aset["notasi"]))
        if src == "extract_syair" and aset.get("syair"):
            return extract_chords_strict(extract_pdf_text_cached(aset["syair"]))
    return []

def _get_lyric_features(text: str) -> dict:
    """Extracts features from lyrics for scoring."""
    t_norm = _normalize_text(text)
    words = t_norm.split()
    total = max(1, len(words))
    return {
        "ttr": len(set(words)) / total,
        "cliche_hits": sum(1 for c in _CLICHES if c in t_norm),
        "communal_prop": sum(1 for w in words if w in ["kita", "kami", "bersama", "umatmu"]) / total,
        "has_chorus": any(sec in t_norm for sec in _SECTION_TOKENS),
        "imagery_hits": sum(1 for img in _IMAGERY_V2 if img in t_norm)
    }

def score_creativity(aset: dict, lyrics_text: str, chord_sources: list) -> int:
    """Scores creativity (1-5) based on harmony and lyrics, v3."""
    # === 1. Pilar Harmoni (Bobot 50%) ===
    seq = chord_sequence_from_sources(aset, chord_sources)
    harmonic_score = 0.0 # Mulai dari nol
    if seq:
        feats = music_features_v2(seq)
        nondi_rate = feats.get("nondi", 0)
        ext_rate = feats.get("ext", 0)
        trans_uniq = feats.get("big_count", 0)
        num_uniq_chords = len(feats.get("uniq_list", []))

        # Poin dari kompleksitas (maks 1.0)
        complexity_score = (0.5 * min(nondi_rate * 4, 1.0)) + \
                           (0.3 * min(ext_rate * 3, 1.0)) + \
                           (0.2 * min(trans_uniq / 15.0, 1.0))

        # Bonus untuk "keberanian"
        if nondi_rate > 0.1 and ext_rate > 0.15:
            complexity_score += 0.15

        harmonic_score = min(complexity_score, 1.0)

        # Penalti untuk "terlalu aman" / sangat standar
        if num_uniq_chords <= 4 and ext_rate == 0 and nondi_rate < 0.05:
            harmonic_score *= 0.4 # Kurangi skor secara signifikan

    # === 2. Pilar Lirik (Bobot 50%) ===
    lyrical_score = 0.0 # Mulai dari nol
    if lyrics_text:
        lyric_feats = _get_lyric_features(lyrics_text)
        signals = analyze_originality_signals(lyrics_text, seq)

        # Poin dari orisinalitas (100% - penalti klise)
        originality_score = 1.0 - (signals.get("cliche_score", 0) / 100.0)

        # Poin dari kualitas puitis (imajinasi & TTR)
        poetic_score = (0.7 * min(lyric_feats.get("imagery_hits", 0) / 3.0, 1.0)) + \
                       (0.3 * (lyric_feats.get("ttr", 0) - 0.3) / 0.5) # Normalisasi TTR

        # Rata-rata dari orisinalitas dan kualitas puitis
        lyrical_score = max(0.0, (0.6 * originality_score) + (0.4 * poetic_score))

    # === 3. Agregasi Final ===
    raw_score = 100 * ((0.5 * harmonic_score) + (0.5 * lyrical_score))

    return _map_0_100_to_1_5(raw_score)

def score_singability(aset: dict, lyrics_text: str, chord_sources: list) -> int:
    """Scores singability (1-5) for congregational singing."""
    seq = chord_sequence_from_sources(aset, chord_sources)
    h_score = 1.0 - min((0.7 * music_features_v2(seq)["nondi"]) + (0.3 * music_features_v2(seq)["ext"]), 1.0) if seq else 0.8

    l_feats = _get_lyric_features(lyrics_text)
    l_score = (0.6 * (1.0 if l_feats["has_chorus"] else 0.4)) + (0.4 * min(l_feats["communal_prop"] * 10, 1.0))

    return _map_0_100_to_1_5(100 * ((0.5 * h_score) + (0.5 * l_score)))

def _find_key_like(substr: str, rubrik: List[Dict[str, Any]]) -> str | None:
    """Finds a rubrik key that matches a substring."""
    aliases = {"tema": ["tema", "kesesuaian"], "lirik": ["lirik", "syair", "diksi"], "musik": ["musik", "aransemen", "harmoni"], "kreativitas": ["kreativ", "orisinalitas"], "jemaat": ["jemaat", "singability"]}
    norm_sub = _normalize_text(substr)
    candidates = aliases.get(norm_sub, [norm_sub])
    for r_item in rubrik:
        haystack = _normalize_text(f"{r_item.get('key','')} {r_item.get('aspek','')}")
        if any(c in haystack for c in candidates):
            return r_item["key"]
    return None

def build_suggestions(aset: dict, lyric_txt_priorities: list, chord_src_priorities: list, theme_scorer: Callable, rubrik: list, music_score_map: dict, music_binner: Callable) -> dict:
    """Builds a dictionary of suggested scores for a song."""
    def _ex_sy(): return extract_pdf_text_cached(aset.get("syair", {}))
    def _ex_no(): return extract_pdf_text_cached(aset.get("notasi", {}))

    src, txt = _pick_text_variant(aset, lyric_txt_priorities, _ex_sy, _ex_no)
    clean_lyrics = strip_chords(txt) if src in ("syair_chord", "full_score", "extract_notasi") else txt

    s_theme = _map_0_100_to_1_5(theme_scorer(clean_lyrics) if clean_lyrics else 0.0)
    s_lyric = score_lyrics_strength(clean_lyrics) if clean_lyrics else 1
    s_music = int(music_binner(music_score_map.get(aset["judul"], 0.0))) if "judul" in aset else 3
    s_kreativ = score_creativity(aset, clean_lyrics, chord_src_priorities)
    s_jemaat = score_singability(aset, clean_lyrics, chord_src_priorities)

    out = {}
    key_map = {
        "tema": _find_key_like("tema", rubrik), "lirik": _find_key_like("lirik", rubrik),
        "musik": _find_key_like("musik", rubrik), "kreativitas": _find_key_like("kreativitas", rubrik),
        "jemaat": _find_key_like("jemaat", rubrik)
    }

    if key_map["tema"]: out[key_map["tema"]] = int(s_theme)
    if key_map["lirik"]: out[key_map["lirik"]] = int(s_lyric)
    if key_map["musik"]: out[key_map["musik"]] = int(s_music)
    if key_map["kreativitas"]: out[key_map["kreativitas"]] = int(s_kreativ)
    if key_map["jemaat"]: out[key_map["jemaat"]] = int(s_jemaat)

    return out

def _make_dynamic_binner(values: list[float]) -> Tuple[Callable, list]:
    """Creates a function to bin values into 5 categories based on percentiles."""
    arr = np.array([float(x) for x in values if pd.notna(x)], dtype=float)
    if arr.size < 5: # Not enough data for meaningful percentiles
        return (lambda v: _map_0_100_to_1_5(v or 0)), [20, 40, 60, 80]

    cuts = np.percentile(arr, [20, 40, 60, 80]).tolist()
    def _bin(v: float) -> int:
        return 1 + sum(float(v or 0) >= c for c in cuts)
    return _bin, cuts

def _build_pen_full_df(pen_df_raw: pd.DataFrame, rubrik: list, variants: dict) -> pd.DataFrame:
    """Builds a cleaned and complete DataFrame from raw Penilaian data."""
    if pen_df_raw is None or pen_df_raw.empty:
        return pd.DataFrame()
    df = pen_df_raw.copy().rename(columns=lambda c: variants.get(c, c))

    for r in rubrik:
        k, mx, wb = r["key"], r["max"], r["bobot"]
        if k in df.columns:
            df[k] = pd.to_numeric(df[k], errors="coerce")

    if "total" not in df.columns:
        total_calc = np.zeros(len(df))
        for r in rubrik:
            k, mx, wb = r["key"], r["max"], r["bobot"]
            if k in df.columns:
                total_calc += (df[k].fillna(0) / max(mx, 1)) * wb
        df["total"] = total_calc
    else:
        df["total"] = pd.to_numeric(df["total"], errors='coerce')

    return df

def analyze_originality_signals(lyrics: str, chord_seq: list) -> dict:
    """Analyzes AI or generic signals from lyrics and chords."""
    if not lyrics:
        return {"cliche_score": 0, "ttr": 0, "num_chords": 0}

    t_norm = _normalize_text(lyrics)
    words = t_norm.split()

    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    cliche_score = min(cliche_hits * 25, 100)

    ttr = len(set(words)) / len(words) if words else 0

    return {
        "cliche_score": cliche_score,
        "ttr": ttr,
        "num_chords": len(set(chord_seq))
    }

def calculate_internal_similarity(current_title: str, all_songs: dict, lyrics_score_priority: list, chord_sources: list) -> pd.DataFrame:
    """Calculates lyric and chord similarity with all other songs."""
    if len(all_songs) < 2:
        return pd.DataFrame()

    current_aset = all_songs[current_title]
    current_lyrics = get_clean_lyrics_for_song(current_aset, lyrics_score_priority)
    current_chords_str = " ".join(chord_sequence_from_sources(current_aset, chord_sources))

    titles = [t for t in all_songs if t != current_title]
    lyrics_corpus = [get_clean_lyrics_for_song(all_songs[t], lyrics_score_priority) for t in titles]

    try:
        vectorizer = TfidfVectorizer().fit(lyrics_corpus + [current_lyrics])
        tfidf_matrix = vectorizer.transform(lyrics_corpus)
        current_tfidf = vectorizer.transform([current_lyrics])
        lyric_sims = cosine_similarity(current_tfidf, tfidf_matrix).flatten()
    except ValueError:
        lyric_sims = [0.0] * len(titles)

    results = []
    for i, title in enumerate(titles):
        other_aset = all_songs[title]
        other_chords_str = " ".join(chord_sequence_from_sources(other_aset, chord_sources))
        chord_sim = SequenceMatcher(None, current_chords_str, other_chords_str).ratio()
        results.append({
            "Judul Lagu Pembanding": title,
            "Kemiripan Lirik (%)": round(lyric_sims[i] * 100, 1),
            "Kemiripan Akor (%)": round(chord_sim * 100, 1)
        })

    df = pd.DataFrame(results)
    if not df.empty:
        df['Skor Gabungan'] = df['Kemiripan Lirik (%)'] * 0.6 + df['Kemiripan Akor (%)'] * 0.4
        return df.sort_values('Skor Gabungan', ascending=False).head(3).drop(columns=['Skor Gabungan'])
    return df

def get_clean_lyrics_for_song(aset: dict, lyrics_score_priority: list) -> str:
    """Helper to get clean lyrics from a song's asset dictionary."""
    def _ex_sy(): return extract_pdf_text_cached(aset.get("syair", {}))
    def _ex_no(): return extract_pdf_text_cached(aset.get("notasi", {}))

    src, txt = _pick_text_variant(aset, lyrics_score_priority, _ex_sy, _ex_no)
    return strip_chords(txt) if src in ("syair_chord", "full_score", "extract_notasi") else txt

def process_penilaian_data(df_raw: pd.DataFrame, rubrik: list, variants: dict, show_author: bool, songs: dict):
    """Processes raw assessment data to generate analytics."""
    if df_raw.empty or "judul" not in df_raw.columns:
        return None, None, None, None, None, None, None

    p = _build_pen_full_df(df_raw, rubrik, variants)

    avg = p.groupby("judul", as_index=False)["total"].mean(numeric_only=True)
    if show_author:
        avg["Pengarang"] = avg["judul"].map(lambda t: songs.get(t, {}).get("author", ""))

    ranking = avg.sort_values("total", ascending=False).reset_index(drop=True)
    ranking["lead_to_next"] = ranking["total"] - ranking["total"].shift(-1)

    by_song = p.groupby("judul").agg(
        mean_total=("total", "mean"),
        std_total=("total", "std"),
        n_juri=("juri", "nunique")
    ).reset_index()

    jstat = None
    if "juri" in p.columns:
        jstat = p.groupby("juri").agg(
            rata2=("total", "mean"),
            std=("total", "std"),
            n=("total", "count")
        ).reset_index()

    present_keys = [r["key"] for r in rubrik if r["key"] in p.columns]
    corr_aspek = None
    if present_keys:
        corr_aspek = p[present_keys + ["total"]].corr(numeric_only=True)["total"].drop("total").sort_values(ascending=False)

    return p, ranking, by_song, jstat, corr_aspek, present_keys, avg
