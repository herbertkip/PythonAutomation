#!/usr/bin/env python3
"""
split_drawing_set.py
Split a construction drawing set (PDF) into one PDF per sheet and name each
file "<sheet number> - <sheet name>.pdf", read from the title block.

Runs fully locally. Install once:
    pip install pymupdf

Usage:
    python split_drawing_set.py "Permit Set.pdf"
    python split_drawing_set.py "Permit Set.pdf" -o out_folder --zip
    python split_drawing_set.py "Permit Set.pdf" --dry-run      # preview names only

If the title block is not in the bottom-right corner, adjust:
    --right 0.25 --bottom 0.5     (search the right 25% x bottom 50% of each page)
"""
import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path

import pymupdf  # PyMuPDF

# Sheet numbers like S1.00, S1.00A, A-101, E2.1, M301, FP-1.1, C-100
SHEET_NO = re.compile(r"^[A-Z]{1,3}[-.]?\d{1,3}(?:\.\d{1,3})?[A-Z]?$")
# Labels that sit next to the sheet title in most title blocks
NAME_LABEL = re.compile(r"(SHEET|DRAWING)\s*(NAME|TITLE)\s*:?", re.I)
BAD_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def page_spans(page):
    """Yield (rect, size, text) for every text span, in *visual* page
    coordinates (so rotated sheets, e.g. rotation=270, still work)."""
    rot = page.rotation_matrix
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    yield pymupdf.Rect(span["bbox"]) * rot, span["size"], text


def read_title_block(page, right_frac, bottom_frac):
    """Return (sheet_number, sheet_name, how) for one page."""
    W, H = page.rect.width, page.rect.height
    # Try the bottom-right corner first, then the full right-hand strip.
    regions = [
        pymupdf.Rect(W * (1 - right_frac), H * (1 - bottom_frac), W, H),
        pymupdf.Rect(W * (1 - right_frac), 0, W, H),
    ]
    for region in regions:
        spans = [s for s in page_spans(page) if s[0].intersects(region)]

        # Sheet number: text matching the pattern, preferring the largest
        # font (the sheet number is the biggest text in a title block).
        candidates = [s for s in spans if SHEET_NO.match(s[2].upper())]
        if not candidates:
            continue
        num_rect, _, number = max(candidates, key=lambda s: (s[1], s[0].y0))

        # Sheet name: text below the "SHEET NAME" label if there is one,
        # otherwise the text just below the sheet number.
        labels = [s for s in spans if NAME_LABEL.search(s[2])]
        if labels:
            lab = max(labels, key=lambda s: s[0].y0)[0]
            below = [s for s in spans
                     if s[0].y0 > lab.y0 + 1 and s[0].x1 > lab.x0 - 5
                     and not s[2].endswith(":")]
            how = "label"
        else:
            below = [s for s in spans
                     if s[0].y0 > num_rect.y1 - 1 and not s[2].endswith(":")]
            how = "position"
        below.sort(key=lambda s: (round(s[0].y0), s[0].x0))
        name = " ".join(s[2] for s in below).strip()
        return number.upper(), name, how
    return None, "", "not found"


def clean(text):
    text = text.replace("&", "and")
    text = BAD_FILENAME_CHARS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--right", type=float, default=0.20,
                    help="fraction of page width (from right) to search")
    ap.add_argument("--bottom", type=float, default=0.40,
                    help="fraction of page height (from bottom) to search")
    ap.add_argument("--zip", action="store_true", help="also create a .zip")
    ap.add_argument("--dry-run", action="store_true", help="print names only")
    args = ap.parse_args()

    src = Path(args.pdf)
    outdir = Path(args.outdir) if args.outdir else src.with_suffix("")
    doc = pymupdf.open(src)
    rows, used = [], set()

    for i, page in enumerate(doc):
        number, name, how = read_title_block(page, args.right, args.bottom)
        if number:
            base = clean(f"{number} - {name}" if name else number)
        else:
            base = f"page_{i + 1:02d}_UNKNOWN"
        fname, n = base, 2
        while fname.lower() in used:           # avoid overwriting duplicates
            fname, n = f"{base} ({n})", n + 1
        used.add(fname.lower())
        rows.append((i + 1, number or "", name, how, fname + ".pdf"))
        print(f"page {i + 1:>3}: {fname}.pdf   [{how}]")

    if args.dry_run:
        return

    outdir.mkdir(parents=True, exist_ok=True)
    for (pno, *_, fname) in rows:
        single = pymupdf.open()
        single.insert_pdf(doc, from_page=pno - 1, to_page=pno - 1)
        single.save(outdir / fname, garbage=3, deflate=True)
        single.close()

    with open(outdir / "_sheet_index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["page", "sheet_number", "sheet_name", "detected_by", "file"])
        w.writerows(rows)

    if args.zip:
        zpath = outdir.with_suffix(".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(outdir.iterdir()):
                z.write(p, p.name)
        print(f"zip: {zpath}")

    missing = [r[0] for r in rows if not r[1]]
    if missing:
        print(f"WARNING: no sheet number found on pages {missing} "
              f"(scanned? try --right/--bottom, or OCR).", file=sys.stderr)


if __name__ == "__main__":
    main()
