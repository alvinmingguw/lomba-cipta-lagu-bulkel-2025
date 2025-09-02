#!/usr/bin/env python3
# ocr_redact_combo.py  (with PREVIEW | PAINT | REDACT)
#
# Pipeline:
# 1) (Optional) OCR (auto/always/never)
# 2) Preview / Paint / Redact names
# 3) Optional header masking
# 4) Verification pass + summary
#
# Modes:
# - preview: draw RED OUTLINES ONLY (no fill, no text removal) to visualize matches
# - paint:   draw BLACK FILLS (text remains under the box; still searchable)
# - redact:  remove text + BLACK fill; optionally add overlay to ensure black in all viewers
#
# Examples:
#   python tools_redact_pdfs.py --src ./files --dst ./files_preview \
#     --names "Andre,Sigit" --ocr auto --mode preview --stroke 1.2
#
#   python tools_redact_pdfs.py --src ./files --dst ./files_anon \
#     --names "Andre,Sigit" --ocr auto --mode redact --overlay --header-mask 60
#
#   python tools_redact_pdfs.py --src ./files --dst ./files_paint \
#     --names-file names.txt --ocr always --mode paint
#
import os, sys, shutil, argparse, subprocess
import fitz  # PyMuPDF

def _variants(name: str):
    base = (name or "").strip()
    if not base:
        return []
    vs = set()
    vs.add(base)
    vs.add(base.replace("-", " "))
    vs.add(" ".join(base.replace("-", " ").split()))
    more = set()
    for v in list(vs):
        more.add(v.lower()); more.add(v.upper()); more.add(v.title())
    vs |= more
    return [v for v in vs if v]

def has_searchable_text(path: str, min_chars: int = 40) -> bool:
    try:
        doc = fitz.open(path)
        count = 0
        for p in doc:
            count += len(p.get_text("text") or "")
            if count >= min_chars:
                doc.close(); return True
        doc.close(); return False
    except Exception:
        return False

def run_ocr(src: str, dst: str, lang: str = "eng+ind", force: bool = False) -> bool:
    try:
        args = ["ocrmypdf", "--rotate-pages", "--deskew", "--clean", "--language", lang]
        if force: args.insert(1, "--force-ocr")
        args += [src, dst]
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return os.path.exists(dst)
    except FileNotFoundError:
        print("[WARN] ocrmypdf not found. Skipping OCR. Install with: brew install ocrmypdf tesseract")
        return False
    except subprocess.CalledProcessError as e:
        print("[WARN] ocrmypdf failed:", e)
        return False

def _collect_hits(page, terms):
    rects = []
    for term in terms:
        try: r = page.search_for(term)
        except TypeError: r = page.search_for(str(term))
        if r: rects.extend(r)
    return rects

def apply_header(page, mode: str, header_mask: float, overlay: bool, stroke: float):
    """
    Header helper yang AMAN:
    - Hanya menggambar outline merah saat preview (untuk melihat batas header).
    - TIDAK melakukan apa pun pada mode 'paint' atau 'redact' (jadi tidak ada fill hitam).
    """
    if not header_mask or header_mask <= 0:
        return

    r = page.rect
    head = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + header_mask)

    # preview: outline saja, tanpa fill
    if mode == "preview":
        page.draw_rect(head, color=(1, 0, 0), width=stroke, fill=None)

    # paint / redact: sengaja tidak melakukan apa-apa agar header tidak tertutup
    return


def process_pdf(src_pdf: str, dst_pdf: str, names: list, mode: str,
                overlay: bool, header_mask: float, stroke: float) -> dict:
    doc = fitz.open(src_pdf)
    terms = []
    for n in names: terms.extend(_variants(n))
    terms = list(dict.fromkeys(terms))

    total_hits, total_pages = 0, 0
    for page in doc:
        apply_header(page, mode, header_mask, overlay, stroke)

        rects = _collect_hits(page, terms)
        if rects:
            total_pages += 1; total_hits += len(rects)

            if mode == "preview":
                for r in rects:
                    page.draw_rect(r, color=(1,0,0), width=stroke, fill=None)  # outline only
            elif mode == "paint":
                for r in rects:
                    page.draw_rect(r, color=None, fill=(0,0,0))               # fill black
            else:  # redact
                for r in rects:
                    page.add_redact_annot(r, fill=(0,0,0))
                page.apply_redactions()
                if overlay:
                    for r in rects:
                        page.draw_rect(r, color=None, fill=(0,0,0))

    os.makedirs(os.path.dirname(dst_pdf), exist_ok=True)
    doc.save(dst_pdf, incremental=False, deflate=True, garbage=4)
    doc.close()
    return {"hits": total_hits, "pages": total_pages, "terms": len(terms)}

def verify_search(pdf_path: str, names: list) -> int:
    try:
        doc = fitz.open(pdf_path)
        terms = []
        for n in names: terms.extend(_variants(n))
        terms = list(dict.fromkeys(terms))
        hits = 0
        for p in doc: hits += len(_collect_hits(p, terms))
        doc.close(); return hits
    except Exception:
        return -1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Source folder PDFs")
    ap.add_argument("--dst", required=True, help="Destination folder")
    ap.add_argument("--names", default="", help="Comma-separated names")
    ap.add_argument("--names-file", default="", help="Text file of names (one per line)")
    ap.add_argument("--ocr", choices=["auto","always","never"], default="auto", help="When to OCR")
    ap.add_argument("--lang", default="eng+ind", help="Tesseract language(s) e.g. 'eng+ind'")
    ap.add_argument("--mode", choices=["preview","paint","redact"], default="preview",
                    help="preview=outlines only; paint=black boxes; redact=remove text + black boxes")
    ap.add_argument("--overlay", action="store_true", help="For redact: add black overlay for viewer consistency")
    ap.add_argument("--header-mask", type=float, default=0.0, help="Mask header area from top (points). 0=disabled")
    ap.add_argument("--stroke", type=float, default=1.0, help="Outline width for preview mode")
    args = ap.parse_args()

    names = []
    if args.names.strip():
        names.extend([n.strip() for n in args.names.split(",") if n.strip()])
    if args.names_file:
        with open(args.names_file, "r", encoding="utf-8") as f:
            names.extend([ln.strip() for ln in f if ln.strip()])
    if not names:
        print("No names provided. Use --names or --names-file."); sys.exit(1)

    os.makedirs(args.dst, exist_ok=True)

    tmp_ocr_dir = os.path.join(args.dst, "_tmp_ocr")
    os.makedirs(tmp_ocr_dir, exist_ok=True)

    summary = []
    for fn in sorted(os.listdir(args.src)):
        if not fn.lower().endswith(".pdf"): continue
        src_pdf = os.path.join(args.src, fn)

        # Decide OCR pathway
        use_pdf = src_pdf
        need_ocr = (args.ocr == "always") or (args.ocr == "auto" and not has_searchable_text(src_pdf))
        if args.ocr != "never" and need_ocr:
            ocr_out = os.path.join(tmp_ocr_dir, fn)
            ok = run_ocr(src_pdf, ocr_out, lang=args.lang, force=(args.ocr=="always"))
            use_pdf = ocr_out if ok else src_pdf
            ocr_flag = "OCR" if ok else "no-OCR"
        else:
            ocr_flag = "skip-OCR"

        # Process
        dst_pdf = os.path.join(args.dst, fn)
        stats = process_pdf(use_pdf, dst_pdf, names, mode=args.mode,
                            overlay=args.overlay, header_mask=args.header_mask, stroke=args.stroke)

        # Verify (paint/preview will still find text, redact should be 0)
        post_hits = verify_search(dst_pdf, names)

        summary.append({
            "file": fn, "ocr": ocr_flag, "pre_text": has_searchable_text(src_pdf),
            "hits": stats["hits"], "post_hits": post_hits, "pages": stats["pages"]
        })
        if args.mode == "redact":
            ok_str = "OK" if post_hits == 0 else "WARN"
        else:
            ok_str = "OK"
        print(f"{ok_str} {fn} | {ocr_flag} | matches: {stats['hits']} | post_hits: {post_hits} | pages_with_hits: {stats['pages']}")

    # Cleanup tmp if empty
    try:
        if not os.listdir(tmp_ocr_dir): os.rmdir(tmp_ocr_dir)
    except Exception:
        pass

    print("\\n=== SUMMARY ===")
    for item in summary:
        print(f"{item['file']}: ocr={item['ocr']}, pre_text={item['pre_text']}, hits={item['hits']}, post_hits={item['post_hits']}")

if __name__ == "__main__":
    main()