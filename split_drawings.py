#!/usr/bin/env python3
"""
split_drawings.py

Prompts for a directory, finds every PDF binder underneath it, splits each
binder into single-sheet PDFs, reads the title block on each page to get the
sheet number + sheet title, and saves everything into one folder called
"Drawings" inside the directory you chose.

Also writes "Drawings_log.csv" (next to the Drawings folder) listing every page,
what it was named, and whether it needs a manual look.

Requires:  pip install pymupdf
Optional:  Tesseract OCR installed on the machine (only used for pages that
           have no selectable text).
"""

import csv
import re
import sys
from pathlib import Path

try:
    import pymupdf as fitz  # newer PyMuPDF
except ImportError:
    try:
        import fitz  # older PyMuPDF
    except ImportError:
        sys.exit("PyMuPDF is not installed. Run:  pip install pymupdf")

# ----------------------------------------------------------------------------
# SETTINGS - tune these to match your title blocks
# ----------------------------------------------------------------------------
OUTPUT_FOLDER_NAME = "Drawings"

# Title block search area as a fraction of the page (left, top, right, bottom).
# Default = bottom-right corner: right 30% of the width, bottom 35% of the height.
# Many sets put the title block in a vertical strip on the right edge instead;
# if so, try (0.80, 0.0, 1.0, 1.0).
TITLE_BLOCK_REGION = (0.70, 0.65, 1.0, 1.0)

# If nothing is found in that region, search the whole page as a fallback.
FALLBACK_TO_FULL_PAGE = True

# Sheet number pattern, e.g. M-101, M101, E0.01, FP-001, T-101A, A1.01
SHEET_NUMBER_RE = re.compile(r"^[A-Z]{1,3}[-. ]?\d{1,3}(?:\.\d{1,2})?[A-Z]?$")

# Words that appear in title blocks but are never the sheet title
NOISE_WORDS = {
    "SHEET", "SHEET NUMBER", "SHEET NO", "SHEET NO.", "SHEET TITLE", "TITLE",
    "DRAWN BY", "CHECKED BY", "APPROVED BY", "PROJECT", "PROJECT NO",
    "PROJECT NO.", "PROJECT NUMBER", "DATE", "SCALE", "REVISION", "REVISIONS",
    "ISSUE", "ISSUED", "DESCRIPTION", "NO.", "NO", "BY", "CHK", "DWN", "DRAWN",
    "CHECKED", "NOT FOR CONSTRUCTION", "DD FINAL", "DESIGN DEVELOPMENT",
    "NORTH", "N.T.S.", "NTS", "AS NOTED", "COPYRIGHT",
}

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MAX_NAME_LENGTH = 150

# ----------------------------------------------------------------------------
# TEXT EXTRACTION
# ----------------------------------------------------------------------------

def region_rect(page):
    r = page.rect
    l, t, rt, b = TITLE_BLOCK_REGION
    return fitz.Rect(
        r.x0 + r.width * l, r.y0 + r.height * t,
        r.x0 + r.width * rt, r.y0 + r.height * b,
    )


def get_lines(page, clip=None):
    """Return cleaned, non-empty text lines (top to bottom) from the page/clip."""
    text = page.get_text("text", clip=clip, sort=True)
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    return [l for l in lines if l]


def ocr_lines(page, clip=None):
    """OCR fallback for pages with no selectable text. Silent if Tesseract is missing."""
    try:
        tp = page.get_textpage_ocr(flags=0, dpi=200, full=True)
        text = page.get_text("text", clip=clip, textpage=tp, sort=True)
        lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
        return [l for l in lines if l]
    except Exception:
        return []

# ----------------------------------------------------------------------------
# PARSING
# ----------------------------------------------------------------------------

def is_noise(line):
    up = line.upper().strip(" :.")
    return (
        up in NOISE_WORDS
        or up + "." in NOISE_WORDS
        or len(up) < 4
        or re.fullmatch(r"[\d\s/.\-:]+", up) is not None      # dates / numbers
        or re.search(r"\b(19|20)\d{2}\b", up) is not None      # contains a year
    )


def looks_like_title(line):
    letters = [c for c in line if c.isalpha()]
    if len(letters) < 4:
        return False
    upper_ratio = sum(c.isupper() for c in letters) / len(letters)
    return upper_ratio > 0.8 and not is_noise(line)


def parse_sheet(lines):
    """
    Return (sheet_number, sheet_title) from a list of title-block lines.
    Either can be None if not found.
    """
    # 1. Sheet number: a line that IS a sheet number. Title blocks usually put
    #    it last, so search from the bottom up.
    num, num_idx = None, None
    for i in range(len(lines) - 1, -1, -1):
        candidate = lines[i].strip().upper()
        if SHEET_NUMBER_RE.match(candidate) and any(c.isdigit() for c in candidate):
            num, num_idx = candidate.replace(" ", ""), i
            break

    # 2. Sheet title: look at the lines just above the number first
    title = None
    if num_idx is not None:
        above = []
        for j in range(num_idx - 1, max(num_idx - 4, -1), -1):
            if looks_like_title(lines[j]):
                above.insert(0, lines[j])
            elif above:
                break
        if above:
            title = " ".join(above[:2])

    # 3. Fallback: longest title-looking line in the block
    if not title:
        cands = [l for l in lines if looks_like_title(l) and l.upper() != num]
        if cands:
            title = max(cands, key=len)

    return num, title

# ----------------------------------------------------------------------------
# FILE HELPERS
# ----------------------------------------------------------------------------

def clean_filename(name):
    name = INVALID_FILENAME_CHARS.sub("", name)
    name = re.sub(r"\s+", " ", name).strip(" .-")
    return name[:MAX_NAME_LENGTH].rstrip(" .-")


def unique_path(folder, stem):
    """Return a path that doesn't exist yet, appending _2, _3... if needed."""
    path = folder / f"{stem}.pdf"
    n = 2
    while path.exists():
        path = folder / f"{stem}_{n}.pdf"
        n += 1
    return path


def find_pdfs(root, out_dir):
    pdfs = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".pdf":
            if out_dir in p.parents:      # don't re-process our own output
                continue
            pdfs.append(p)
    return sorted(pdfs)

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def process_binder(pdf_path, out_dir, root, log):
    discipline = pdf_path.parent.name
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  ! Could not open {pdf_path.name}: {e}")
        log.append([discipline, pdf_path.name, "", "", "ERROR", str(e)])
        return 0

    count = 0
    for i, page in enumerate(doc):
        page_no = i + 1
        lines = get_lines(page, clip=region_rect(page))
        num, title = parse_sheet(lines)

        if not num and FALLBACK_TO_FULL_PAGE:
            full = get_lines(page)
            n2, t2 = parse_sheet(full)
            num, title = n2 or num, title or t2

        if not num and not lines:                     # no text at all -> try OCR
            ocr = ocr_lines(page, clip=region_rect(page)) or ocr_lines(page)
            num, title = parse_sheet(ocr)

        if num:
            stem = clean_filename(f"{num} - {title}" if title else num)
            status = "OK" if title else "REVIEW (no title found)"
        else:
            stem = clean_filename(f"UNKNOWN - {pdf_path.stem[-40:]} - p{page_no:03d}")
            status = "REVIEW (no sheet number found)"

        out_path = unique_path(out_dir, stem)
        single = fitz.open()
        single.insert_pdf(doc, from_page=i, to_page=i)
        single.save(out_path, garbage=3, deflate=True)
        single.close()

        log.append([discipline, pdf_path.name, page_no, out_path.name, status, ""])
        count += 1
        flag = "" if status == "OK" else "   <-- check"
        print(f"  p{page_no:>3}: {out_path.name}{flag}")

    doc.close()
    return count


def main():
    raw = input("Enter the directory containing your drawing folders: ").strip()
    raw = raw.strip('"').strip("'")                    # handles paste-as-path quotes
    root = Path(raw).expanduser()

    if not root.is_dir():
        sys.exit(f"Not a valid directory: {root}")

    out_dir = root / OUTPUT_FOLDER_NAME
    out_dir.mkdir(exist_ok=True)

    pdfs = find_pdfs(root, out_dir)
    if not pdfs:
        sys.exit("No PDF files found.")

    print(f"\nFound {len(pdfs)} binder(s). Output -> {out_dir}\n")

    log, total = [], 0
    for pdf in pdfs:
        print(f"{pdf.relative_to(root)}")
        total += process_binder(pdf, out_dir, root, log)
        print()

    log_path = root / "Drawings_log.csv"
    with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Discipline folder", "Source file", "Source page",
                    "Output file", "Status", "Notes"])
        w.writerows(log)

    review = sum(1 for r in log if str(r[4]).startswith(("REVIEW", "ERROR")))
    print(f"Done. {total} drawings saved to: {out_dir}")
    print(f"Log: {log_path}")
    if review:
        print(f"{review} page(s) flagged for review - filter the log's Status column.")


if __name__ == "__main__":
    main()
