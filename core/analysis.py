import re
import unicodedata
import math
import numpy as np
import pandas as pd
from collections import Counter
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Callable, Tuple

# Re-using configs/constants from the main app, will need to be passed in or centralized
# For now, defining them here to make the module self-contained for logic.

_EMO_WORDS_V2 = {
    "tema_dalam": ["waktu", "kesempatan", "bijaksana", "arif", "pergunakan", "saksama", "hadir", "saat ini", "dekat", "persekutuan"],
    "keluarga": ["keluarga", "bersama", "rumah", "ayah", "bunda", "ibu", "anak", "kasih", "rukun", "saling menjaga"],
    "iman": ["iman", "doa", "tuhan", "yesus", "syukur", "berkat", "pengharapan", "setia"]
}
_IMAGERY_V2 = ["harta", "permata", "berharga", "tak ternilai", "mutiara", "pelabuhan", "sauh", "jangkar", "bahtera", "rumahku"]
_DISTRACTIONS = ["dunia maya", "medsos", "layar", "gawai", "sibuk", "sendiri", "jarak"]
_CLICHES = ["tuhan pasti memberkati", "jalanmu lurus", "hidupku indah", "selalu bersama selamanya", "tetap semangat", "kau kuatkanku", "percaya saja", "kasih setiamu"]
_SECTION_TOKENS = ["reff", "refrein", "chorus", "verse", "bait", "bridge", "pre-chorus", "coda"]

CHORD_TOKEN = re.compile(
    r"^(?:[A-G](?:#|b)?(?:maj7|maj|min|m7|m|7|sus2|sus4|sus|dim|aug|add9|add11|add13|6|9|11|13)?)"
    r"(?:/[A-G](?:#|b)?)?$"
)
SECTION_WORDS = {
    "bait","bait1","bait2","bait3","bait4",
    "reff","ref","reffrein","chorus","prechorus","pre-chorus","pre_chorus",
    "bridge","intro","interlude","outro","ending","coda",
    "verse","verse1","verse2","verse3",
    "do"
}
QUAL_EXT = re.compile(r'(maj7|m7|maj|7|9|11|13|sus2|sus4|sus|dim|aug|add9|6|add11|add13)')
_PITCH = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'Fb':4,'E#':5,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11,'Cb':11}
_ROOT_RE = re.compile(r'^([A-G](?:#|b)?)')
_PC_TO_NAME = {v:k for k,v in {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}.items()}


# =========================
# Normalization and Basic Helpers
# =========================
def _norm_id(s: str) -> str:
    s = s.lower()
    try:
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    except Exception:
        pass
    s = re.sub(r"[^a-z0-9\s']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def _map_0_100_to_1_5(x: float) -> int:
    cuts = [20, 40, 60, 80]
    return 1 + sum(x >= c for c in cuts)

def _entropy(probs):
    if not probs: return 0.0
    return -sum(p*math.log(p+1e-12) for p in probs if p>0)/math.log(max(2, len(probs)))

def strip_chords(text: str) -> str:
    BRACKET_CHORD = re.compile(r"\[[^\]]+\]")
    INLINE_CHORD  = re.compile(r"(?<!\w)([A-G](?:#|b)?(?:m|maj7|m7|7|sus2|sus4|dim|aug|add9|6|9)?)(?!\w)")
    if not text: return ""
    t = BRACKET_CHORD.sub("", text)
    t = INLINE_CHORD.sub("", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

# =========================
# Chord & Music Analysis
# =========================
def _normalize_chord(tok: str) -> str:
    return tok.strip().replace(" ", "")

def extract_chords_strict(text: str) -> list[str]:
    if not text: return []
    tokens = re.split(r"[^\w/#]+", text)
    seen, out = set(), []
    for tok in tokens:
        if not tok: continue
        low = tok.lower()
        if low in SECTION_WORDS: continue
        if CHORD_TOKEN.match(tok):
            norm = _normalize_chord(tok)
            if norm not in seen:
                seen.add(norm)
                out.append(norm)
    return out

def _root_pc(ch: str) -> int | None:
    if not ch: return None
    base = ch.split('/')[0].strip()
    m = _ROOT_RE.match(base)
    if not m: return None
    r = m.group(1).upper().replace('♭','b').replace('♯','#')
    return _PITCH.get(r)

def music_features_v2(seq: list[str]) -> dict:
    uniq = list(dict.fromkeys(seq))
    U = min(len(set(uniq))/10.0, 1.0)
    bigrams = list(zip(seq, seq[1:])) if len(seq)>1 else []
    T = _entropy([v/sum(Counter(bigrams).values()) for v in Counter(bigrams).values()]) if bigrams else 0.0
    ext = sum(1 for c in seq if QUAL_EXT.search(c)) / max(1,len(seq))
    slash = sum(1 for c in seq if "/" in c) / max(1,len(seq))
    nondi = sum(1 for c in seq if re.match(r'^[A-G](#|b)', c)) / max(1,len(seq))
    return {"U":U, "T":T, "ext":ext, "slash":slash, "nondi":nondi, "uniq_list": uniq, "big_count": len(set(bigrams))}

def detect_key_from_chords(seq: list[str]) -> tuple[str, float]:
    pcs = [p for p in (_root_pc(ch) for ch in seq) if p is not None]
    if not pcs: return ("?", 0.0)
    weights = {0:2.0, 2:1.2, 4:1.2, 5:2.0, 7:2.0, 9:1.2}
    scores = []
    for t in range(12):
        s = sum(weights.get((r - t) % 12, -0.5) for r in pcs)
        scores.append(s)
    best_idx = int(np.argmax(scores))
    best = scores[best_idx]
    second = sorted(scores, reverse=True)[1] if len(scores) > 1 else 0.0
    denom = abs(best) + sum(abs(x) for x in scores) / max(1, len(scores))
    conf = max(0.0, min(1.0, (best - second) / (denom + 1e-9)))
    return (_PC_TO_NAME.get(best_idx, "?"), float(round(conf, 3)))

def detect_genre(seq):
    if not seq: return "Pop/Ballad"
    feats = music_features_v2(seq)
    E, B, X, U = feats["ext"], feats["slash"], feats["nondi"], len(feats["uniq_list"])
    if E > 0.2 or X > 0.15: return "Jazz/Gospel"
    if B > 0.15 and U <= 6: return "Worship/CCM"
    if X > 0.1 and U <= 5: return "Rock"
    if U >= 7 and E < 0.1 and B < 0.1: return "Folk/Acoustic"
    return "Pop/Ballad"

# =========================
# Lyrics Analysis & Scoring
# =========================
def make_theme_functions(phrases, keywords):
    def score(text):
        t = _norm_id(text or "")
        s = sum(t.count(p.lower()) * float(w) for p, w in phrases)
        s += sum(len(re.findall(rf"\b{re.escape(k.lower())}\w*\b", t)) * float(w) for k, w in keywords)
        return float(min(round(s, 2), 100.0))
    def highlight(text):
        html = text or ""
        for p, _ in sorted(phrases, key=lambda x: len(x[0]), reverse=True):
            html = re.sub(fr"(?i)({re.escape(p)})", r"<mark>\1</mark>", html)
        for k, _ in keywords:
            html = re.sub(fr"(?i)\b({re.escape(k)}\w*)\b", r"<mark>\1</mark>", html)
        return (html or "<i>(syair kosong)</i>").replace("\n", "<br>")
    return score, highlight

def _get_lyric_features(text: str) -> dict:
    t_norm = _norm_id(text)
    words = t_norm.split()
    if not words: return {"ttr": 0, "cliche_hits": 0, "communal_words_prop": 0, "has_chorus": False, "imagery_hits": 0}
    total_words, unique_words = len(words), len(set(words))
    return {
        "ttr": unique_words / total_words if total_words > 0 else 0,
        "cliche_hits": sum(1 for c in _CLICHES if c in t_norm),
        "communal_words_prop": sum(1 for w in words if w in ["kita", "kami", "bersama", "umatmu"]) / total_words,
        "has_chorus": any(sec in t_norm for sec in ["reff", "refrein", "chorus"]),
        "imagery_hits": sum(1 for img in _IMAGERY_V2 if img in t_norm)
    }

def score_lyrics_strength(text: str) -> int:
    if not text: return 1
    t_norm = _norm_id(text)
    tema_score = min(sum(t_norm.count(w) for w in _EMO_WORDS_V2["tema_dalam"]), 8)
    relasi_score = min(sum(t_norm.count(w) for w in _EMO_WORDS_V2["keluarga"]) + sum(t_norm.count(w) for w in _EMO_WORDS_V2["iman"]), 10)
    img_score = min(sum(1 for kw in _IMAGERY_V2 if kw in t_norm), 5)
    lines = [l.strip() for l in t_norm.splitlines() if l.strip()]
    struct_score = (2 if any(tok in t_norm for tok in _SECTION_TOKENS) else 0) + (1 if len(set(lines)) / max(1, len(lines)) >= 0.7 else 0)
    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    distraction_penalty = any(d in t_norm for d in _DISTRACTIONS) and not any(w in t_norm for w in _EMO_WORDS_V2["iman"] + ["bersama", "dekat"])
    penal = min(2, cliche_hits) + (2 if distraction_penalty else 0)
    raw_score = (35*(tema_score/8.0)) + (25*(relasi_score/10.0)) + (20*(img_score/5.0)) + (20*(struct_score/3.0)) - (15*(penal/4.0))
    return _map_0_100_to_1_5(max(0.0, min(100.0, raw_score)))

def chord_sequence_from_sources(aset: dict, order: list, extract_pdf_text_cached_func: Callable) -> list[str]:
    """Ambil urutan chord dari sumber prioritas. Selalu filter dengan regex chord."""
    from .pdf_utils import extract_pdf_text_cached
    seq: list[str] = []
    for src in order:
        if src == "chords_list" and aset.get("chords_list"):
            # This needs parse_chords_list_field, which is also in analysis.py
            seq = parse_chords_list_field(aset["chords_list"])
            break
        if src in ("syair_chord","full_score"):
            seq = extract_chords_strict(aset.get(src,""))
            break
        if src == "extract_notasi" and aset.get("notasi"):
            txt = extract_pdf_text_cached_func(aset["notasi"]); seq = extract_chords_strict(txt); break
        if src == "extract_syair" and aset.get("syair"):
            txt = extract_pdf_text_cached_func(aset["syair"]);  seq = extract_chords_strict(txt); break
    return seq

def score_creativity(aset: dict, lyrics_text: str, chord_source_priority) -> int:
    seq = chord_sequence_from_sources(aset, chord_source_priority, extract_pdf_text_cached)
    harmonic_score = 0.0
    if seq:
        feats = music_features_v2(seq)
        nondi_score = min(feats.get("nondi", 0) * 4, 1.0)
        ext_score = min(feats.get("ext", 0) * 2, 1.0)
        trans_score = min(feats.get("big_count", 0) / 15.0, 1.0)
        bonus = 0.2 if (nondi_score > 0.5 and ext_score > 0.3) else 0
        harmonic_score = min((0.5 * nondi_score) + (0.3 * ext_score) + (0.2 * trans_score) + bonus, 1.0)
        if len(feats.get("uniq_list", [])) <= 4 and feats.get("ext", 0) == 0 and feats.get("nondi", 0) < 0.05:
            harmonic_score *= 0.4

    lyrical_score = 0.0
    if lyrics_text:
        lyric_feats = _get_lyric_features(lyrics_text)
        originality_score = 1.0 - (lyric_feats.get("cliche_hits", 0) * 0.25)
        poetic_score = (0.7 * min(lyric_feats.get("imagery_hits", 0) / 3.0, 1.0)) + (0.3 * (lyric_feats.get("ttr", 0) - 0.3) / 0.5)
        lyrical_score = max(0.0, (0.6 * originality_score) + (0.4 * poetic_score))

    raw_score = 100 * ((0.5 * harmonic_score) + (0.5 * lyrical_score))
    return _map_0_100_to_1_5(raw_score)

def score_singability(aset: dict, lyrics_text: str, chord_source_priority) -> int:
    seq = chord_sequence_from_sources(aset, chord_source_priority, extract_pdf_text_cached)
    harmonic_score = 0.8
    if seq:
        feats = music_features_v2(seq)
        complexity_penalty = (0.7 * feats.get("nondi", 0)) + (0.3 * feats.get("ext", 0))
        harmonic_score = 1.0 - min(complexity_penalty, 1.0)

    lyric_feats = _get_lyric_features(lyrics_text)
    repetition_score = 1.0 if lyric_feats["has_chorus"] else 0.4
    communal_score = min(lyric_feats["communal_words_prop"] * 10, 1.0)
    lyrical_score = (0.6 * repetition_score) + (0.4 * communal_score)

    raw_score = 100 * ((0.5 * harmonic_score) + (0.5 * lyrical_score))
    return _map_0_100_to_1_5(raw_score)

def explain_lyrics_strength(text: str) -> str:
    if not text: return "<p><i>Lirik kosong.</i></p>"
    t_norm = _norm_id(text)
    reasons = []
    if any(w in t_norm for w in ["waktu", "kesempatan", "bijaksana"]): reasons.append("✨ **Koneksi Teologis:** Menangkap esensi Efesus 5 (menggunakan waktu dengan bijaksana).")
    if any(w in t_norm for w in ["persekutuan", "hadir", "bersama"]): reasons.append("❤️ **Kedalaman Relasional:** Menggambarkan tujuan tema (membangun persekutuan).")
    if any(kw in t_norm for kw in _IMAGERY_V2): reasons.append("🎨 **Puitis & Imajinatif:** Menggunakan metafora yang memperkaya pesan.")
    if any(d in t_norm for d in _DISTRACTIONS) and any(w in t_norm for w in _EMO_WORDS_V2["iman"]): reasons.append("💡 **Sangat Kontekstual:** Mengakui tantangan modern dan menawarkan iman sebagai solusi.")
    if not reasons: reasons.append("📝 **Pesan Tersampaikan:** Lirik memiliki pesan yang cukup jelas.")
    return f"<div style='line-height:1.6;'><ul style='margin:0; padding-left: 20px;'>{''.join(f'<li>{r}</li>' for r in reasons[:3])}</ul></div>"

def highlight_lyrics(text: str, phrases, keywords) -> str:
    if not text: return "<i>(Syair kosong)</i>"
    html = text.replace("\n", "<br>")
    colors = {"tema_dalam": "#FFD700", "iman": "#87CEEB", "keluarga": "#98FB98", "imagery": "#FFA07A", "distraksi": "#D3D3D3"}
    all_kws = {"tema_dalam": _EMO_WORDS_V2["tema_dalam"], "iman": _EMO_WORDS_V2["iman"], "keluarga": _EMO_WORDS_V2["keluarga"], "imagery": _IMAGERY_V2, "distraksi": _DISTRACTIONS}
    for category, kws in all_kws.items():
        for kw in sorted(kws, key=len, reverse=True):
            pattern = re.compile(fr"\b({re.escape(kw)})\b", re.IGNORECASE)
            html = re.sub(pattern, f"<mark style='background-color:{colors[category]}; padding: 2px 4px; border-radius:4px;'>\\1</mark>", html)
    return html

# =========================
# Originality Analysis
# =========================
def get_clean_lyrics_for_song(aset: dict, LYRICS_SCORE_PRIORITY, _pick_text_variant, extract_pdf_text_cached_func) -> str:
    def _ex_sy(): return extract_pdf_text_cached_func(aset.get("syair", {}))
    def _ex_no(): return extract_pdf_text_cached_func(aset.get("notasi", {}))
    src, txt = _pick_text_variant(aset, LYRICS_SCORE_PRIORITY, _ex_sy, _ex_no)
    return strip_chords(txt) if src in ("syair_chord", "full_score", "extract_notasi") else txt

def analyze_originality_signals(lyrics: str, chord_seq: list) -> dict:
    if not lyrics: return {"cliche_score": 0, "ttr": 0, "num_chords": 0}
    t_norm = _norm_id(lyrics)
    words = t_norm.split()
    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    return {"cliche_score": min(cliche_hits * 25, 100), "ttr": len(set(words)) / len(words) if words else 0, "num_chords": len(set(chord_seq))}

def calculate_internal_similarity(current_title: str, all_songs: dict, get_clean_lyrics_for_song_func, chord_source_priority) -> pd.DataFrame:
    if len(all_songs) < 2: return pd.DataFrame()
    current_aset = all_songs[current_title]
    current_lyrics = get_clean_lyrics_for_song_func(current_aset)
    current_chords_str = " ".join(chord_sequence_from_sources(current_aset, chord_source_priority, extract_pdf_text_cached))
    titles = [t for t in all_songs if t != current_title]
    lyrics_corpus = [get_clean_lyrics_for_song_func(all_songs[t]) for t in titles]
    try:
        vectorizer = TfidfVectorizer().fit(lyrics_corpus + [current_lyrics])
        lyric_sims = cosine_similarity(vectorizer.transform([current_lyrics]), vectorizer.transform(lyrics_corpus)).flatten()
    except ValueError:
        lyric_sims = [0.0] * len(titles)
    results = []
    for i, title in enumerate(titles):
        other_chords_str = " ".join(chord_sequence_from_sources(all_songs[title], chord_source_priority, extract_pdf_text_cached))
        chord_sim = SequenceMatcher(None, current_chords_str, other_chords_str).ratio()
        results.append({"Judul Lagu Pembanding": title, "Kemiripan Lirik (%)": round(lyric_sims[i] * 100, 1), "Kemiripan Akor (%)": round(chord_sim * 100, 1)})
    df = pd.DataFrame(results)
    df['Skor Gabungan'] = df['Kemiripan Lirik (%)'] * 0.6 + df['Kemiripan Akor (%)'] * 0.4
    return df.sort_values('Skor Gabungan', ascending=False).head(3).drop(columns=['Skor Gabungan'])

def generate_wordcloud_image(text: str) -> io.BytesIO:
    """Generates a word cloud image from a string of text."""
    from wordcloud import WordCloud
    import io

    if not text or not isinstance(text, str) or not text.strip():
        return None

    # Customize the word cloud
    wc = WordCloud(
        background_color="white",
        max_words=100,
        width=800,
        height=400,
        contour_width=3,
        contour_color='steelblue',
        collocations=False # Avoid grouping words
    )

    # Generate word cloud
    wc.generate(text)

    # Save to a bytes buffer
    img_buffer = io.BytesIO()
    wc.to_image().save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return img_buffer
