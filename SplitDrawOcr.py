#!/usr/bin/env python3
"""
split_drawings_ocr.py  -  OCR + AI-assisted version

Prompts for a directory, finds every PDF binder under it, splits each binder
into single-sheet PDFs, works out each sheet's number + title, and saves all
of them into one folder called "Drawings" inside the directory you chose.

How each page is identified (it stops at the first step that succeeds):
  1. Embedded text   - read straight from the PDF (fast, free)
  2. OCR             - Tesseract on a high-resolution crop of the title block,
                       then on the whole page
  3. Vision AI       - Claude reads an image of the title block
                       (only if ANTHROPIC_API_KEY is set)
  4. Derivation      - cross-checks against the binder's own drawing index
                       (cover sheet list), fixes OCR mix-ups (O/0, I/1),
                       and verifies the prefix fits the discipline folder

Every page is always saved, even if it can't be identified (it becomes
UNKNOWN - ... - pNNN.pdf), and a log CSV shows how each name was derived.

Install:
    pip install pymupdf pillow pytesseract          (required for OCR)
    pip install anthropic                           (optional, vision AI)
Also install the Tesseract program itself:
    Windows: https://github.com/UB-Mannheim/tesseract/wiki
    Mac:     brew install tesseract
    Linux:   sudo apt install tesseract-ocr
Optional vision AI:
    set ANTHROPIC_API_KEY=your_key        (Windows)
    export ANTHROPIC_API_KEY=your_key     (Mac/Linux)
"""

import base64
import csv
import difflib
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        sys.exit("PyMuPDF is not installed. Run:  pip install pymupdf")

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = ImageOps = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import anthropic
except ImportError:
    anthropic = None

# ----------------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------------
OUTPUT_FOLDER_NAME = "Drawings"

# Title block search area as fractions of the page: (left, top, right, bottom).
TITLE_BLOCK_REGION = (0.70, 0.65, 1.0, 1.0)

OCR_DPI = 300
VISION_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
USE_VISION = True                 # set False to never call the API
INDEX_PAGES_TO_SCAN = 4           # first N pages of each binder, to find a sheet index

SHEET_NUMBER_RE = re.compile(r"^[A-Z]{1,3}[-. ]?\d{1,3}(?:\.\d{1,2})?[A-Z]?$")
INDEX_LINE_RE = re.compile(
    r"^([A-Z]{1,3}[-. ]?\d{1,3}(?:\.\d{1,2})?[A-Z]?)\s+[-:]?\s*([A-Z0-9][^\n]{3,})$"
)

# Folder-name keyword -> sheet-number prefixes that are normal for it
DISCIPLINE_PREFIXES = {
    "MECH": {"M", "MH", "MP", "ME"},
    "PLUMB": {"P", "PL", "PP"},
    "ELEC": {"E", "EL", "EP", "ES"},
    "FIRE": {"FP", "FA", "F"},
    "SECUR": {"S", "SE", "SEC", "SY", "ES"},
    "TECH": {"T", "TC", "TD", "TN", "TE", "IT", "LV"},
    "CONTROL": {"C", "BAS", "TC", "CT", "DDC"},
    "ARCH": {"A", "AD", "AE", "AI", "AS"},
}

NOISE_WORDS = {
    "SHEET", "SHEET NUMBER", "SHEET NO", "SHEET TITLE", "TITLE", "DRAWN BY",
    "CHECKED BY", "APPROVED BY", "PROJECT", "PROJECT NO", "PROJECT NUMBER",
    "DATE", "SCALE", "REVISION", "REVISIONS", "ISSUE", "ISSUED", "DESCRIPTION",
    "NO", "BY", "CHK", "DWN", "DRAWN", "CHECKED", "NOT FOR CONSTRUCTION",
    "DD FINAL", "DESIGN DEVELOPMENT", "NORTH", "NTS", "AS NOTED", "COPYRIGHT",
}

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MAX_NAME_LENGTH = 150

# ----------------------------------------------------------------------------
# TOOL AVAILABILITY
# ----------------------------------------------------------------------------

def find_tesseract():
    if pytesseract is None or Image is None:
        return False
    if shutil.which("tesseract"):
        return True
    for p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
              r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            return True
    return False


HAVE_OCR = find_tesseract()
HAVE_VISION = bool(USE_VISION and anthropic and os.environ.get("ANTHROPIC_API_KEY"))
_client = None

# ----------------------------------------------------------------------------
# TEXT / IMAGE EXTRACTION
# ----------------------------------------------------------------------------

def region_rect(page):
    r = page.rect
    l, t, rt, b = TITLE_BLOCK_REGION
    return fitz.Rect(r.x0 + r.width * l, r.y0 + r.height * t,
                     r.x0 + r.width * rt, r.y0 + r.height * b)


def to_lines(text):
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    return [l for l in lines if l]


def embedded_lines(page, clip=None):
    return to_lines(page.get_text("text", clip=clip, sort=True))


def render(page, clip=None, dpi=OCR_DPI):
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    return Image.open(io.BytesIO(pix.tobytes("png")))


def ocr_lines(page, clip=None):
    """OCR a crop. Tries two Tesseract layout modes and merges the results."""
    if not HAVE_OCR:
        return []
    img = ImageOps.autocontrast(render(page, clip).convert("L"))
    out, seen = [], set()
    for psm in (6, 11):
        try:
            txt = pytesseract.image_to_string(img, config=f"--psm {psm}")
        except Exception:
            continue
        for line in to_lines(txt):
            if line not in seen:
                seen.add(line)
                out.append(line)
        if len(out) >= 6:           # enough to work with; skip the slower mode
            break
    return out


def vision_read(page, clip, discipline):
    """Ask Claude to read the sheet number/title from an image. Returns (num, title)."""
    global _client
    if not HAVE_VISION:
        return None, None
    try:
        if _client is None:
            _client = anthropic.Anthropic()
        img = render(page, clip, dpi=200).convert("RGB")
        img.thumbnail((1800, 1800))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.standard_b64encode(buf.getvalue()).decode()
        prompt = (
            "This is the title block (or full sheet) of a construction drawing in the "
            f"'{discipline}' discipline. Find the SHEET NUMBER (e.g. M-101, E0.01, FP-001) "
            "and the SHEET TITLE (e.g. FIRST FLOOR HVAC PLAN). Ignore project name, "
            "dates, revision tables and company names. Reply with ONLY JSON: "
            '{"sheet_number": "...", "sheet_title": "..."}. Use null for anything you '
            "cannot read with confidence; never guess."
        )
        msg = _client.messages.create(
            model=VISION_MODEL, max_tokens=300,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                                             "media_type": "image/png", "data": b64}},
                {"type": "text", "text": prompt}]}],
        )
        raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
        data = json.loads(raw)
        return data.get("sheet_number"), data.get("sheet_title")
    except Exception as e:
        print(f"      (vision call failed: {type(e).__name__}: {e})")
        return None, None

# ----------------------------------------------------------------------------
# PARSING + DERIVATION
# ----------------------------------------------------------------------------

def is_noise(line):
    up = line.upper().strip(" :.")
    return (up in NOISE_WORDS or len(up) < 4
            or re.fullmatch(r"[\d\s/.\-:]+", up) is not None
            or re.search(r"\b(19|20)\d{2}\b", up) is not None)


def looks_like_title(line):
    letters = [c for c in line if c.isalpha()]
    if len(letters) < 4:
        return False
    return sum(c.isupper() for c in letters) / len(letters) > 0.8 and not is_noise(line)


def normalize_number(raw):
    """Clean a sheet number and fix common OCR confusions (O/0, I/1, S/5)."""
    if not raw:
        return None
    s = re.sub(r"\s+", "", str(raw).upper()).replace(",", ".")
    m = re.match(r"^([A-Z0]{1,3}?)([-.]?)([0-9OISl][0-9OISl.]{0,5}[A-Z]?)$", s)
    if m:
        pre, sep, dig = m.groups()
        pre = pre.replace("0", "O")
        head = re.match(r"^[0-9OISl.]+", dig).group(0)
        tail = dig[len(head):]
        head = head.replace("O", "0").replace("I", "1").replace("l", "1").replace("S", "5")
        s = f"{pre}{sep}{head}{tail}"
    return s if SHEET_NUMBER_RE.match(s) and any(c.isdigit() for c in s) else None


def parse_sheet(lines):
    """Heuristic title-block parser -> (sheet_number, sheet_title)."""
    num, num_idx = None, None
    for i in range(len(lines) - 1, -1, -1):
        n = normalize_number(lines[i])
        if n:
            num, num_idx = n, i
            break
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
    if not title:
        cands = [l for l in lines if looks_like_title(l) and l.upper() != num]
        if cands:
            title = max(cands, key=len)
    return num, title


def parse_full_page(lines):
    """Full-page parse, but refuse pages that list many sheet numbers (index/cover lists)."""
    listed = sum(1 for l in lines if INDEX_LINE_RE.match(l.upper()))
    if listed >= 3:
        return None, None
    return parse_sheet(lines)


def build_index(doc):
    """Read the binder's own drawing index (sheet list) from its first pages."""
    index, index_pages = {}, set()
    for i in range(min(INDEX_PAGES_TO_SCAN, len(doc))):
        page = doc[i]
        lines = embedded_lines(page)
        if len(lines) < 10 and HAVE_OCR:
            lines = ocr_lines(page)
        hits = 0
        for line in lines:
            m = INDEX_LINE_RE.match(line.upper())
            if m:
                n = normalize_number(m.group(1))
                if n:
                    hits += 1
                    index.setdefault(n, m.group(2).strip())
        if hits >= 3:
            index_pages.add(i)
    if len(index) < 3:                      # need a real list, not stray matches
        return {}, set()
    return index, index_pages


def similar(a, b):
    return difflib.SequenceMatcher(None, a.upper(), b.upper()).ratio()


def derive(num, title, index):
    """Use the index to fill gaps / correct OCR slips. Returns (num, title, note)."""
    note = ""
    if not index:
        return num, title, note
    if num and num not in index:
        # Only "correct" a number when the title independently backs up the match;
        # M-102 vs M-103 differ by one character but are different sheets.
        close = difflib.get_close_matches(num, index.keys(), n=3, cutoff=0.6)
        backed = [c for c in close if title and similar(title, index[c]) >= 0.85]
        if backed:
            note = f"number corrected {num}->{backed[0]} via index (title matched)"
            num = backed[0]
        else:
            note = "not in drawing index"
    if not num and title:
        best = max(index.items(), key=lambda kv: similar(title, kv[1]))
        if similar(title, best[1]) >= 0.85:
            num, note = best[0], "number derived from title via index"
    if num in index:
        if not title:
            title, note = index[num], (note + "; " if note else "") + "title from index"
        elif similar(title, index[num]) < 0.5:
            title, note = index[num], (note + "; " if note else "") + "title replaced by index"
    return num, title, note


def discipline_ok(num, folder_name):
    up = folder_name.upper()
    prefix = re.match(r"[A-Z]+", num or "")
    if not prefix:
        return True
    for key, allowed in DISCIPLINE_PREFIXES.items():
        if key in up:
            return prefix.group(0) in allowed
    return True        # unknown discipline folder: no opinion

# ----------------------------------------------------------------------------
# FILE HELPERS
# ----------------------------------------------------------------------------

def clean_filename(name):
    name = INVALID_FILENAME_CHARS.sub("", name)
    name = re.sub(r"\s+", " ", name).strip(" .-")
    return name[:MAX_NAME_LENGTH].rstrip(" .-")


def unique_path(folder, stem):
    path, n = folder / f"{stem}.pdf", 2
    while path.exists():
        path = folder / f"{stem}_{n}.pdf"
        n += 1
    return path


def find_pdfs(root, out_dir):
    return sorted(p for p in root.rglob("*")
                  if p.is_file() and p.suffix.lower() == ".pdf" and out_dir not in p.parents)

# ----------------------------------------------------------------------------
# PER-PAGE PIPELINE
# ----------------------------------------------------------------------------

def identify_page(page, discipline):
    """Return (num, title, method) using the cheapest method that works."""
    clip = region_rect(page)
    num = title = None

    def done():
        return bool(num and title)

    steps = [
        ("embedded text", lambda: parse_sheet(embedded_lines(page, clip))),
        ("embedded text (full page)", lambda: parse_full_page(embedded_lines(page))),
        ("OCR", lambda: parse_sheet(ocr_lines(page, clip))),
        ("OCR (full page)", lambda: parse_full_page(ocr_lines(page))),
        ("vision AI", lambda: vision_read(page, clip, discipline)),
        ("vision AI (full page)", lambda: vision_read(page, None, discipline)),
    ]
    method = "none"
    for name, fn in steps:
        n, t = fn()
        n = normalize_number(n) if n else None
        if n and not num:
            num, method = n, name
        if t and not title:
            title = re.sub(r"\s+", " ", str(t)).strip().upper()
            method = method if num else name
        if done():
            break
    return num, title, method


def process_binder(pdf_path, out_dir, log):
    discipline = pdf_path.parent.name
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  ! Could not open: {e}")
        log.append([discipline, pdf_path.name, "", "", "ERROR", "", str(e)])
        return 0, 0

    n_pages = len(doc)
    index, index_pages = build_index(doc)
    print(f"  {n_pages} page(s)" + (f", drawing index found ({len(index)} sheets)" if index else ""))

    saved = 0
    for i, page in enumerate(doc):
        num, title, method = identify_page(page, discipline)
        num, title, note = derive(num, title, index)
        is_index = (not num) and i in index_pages

        problems = []
        if not num:
            problems.append("no sheet number")
        if num and not title:
            problems.append("no title")
        if note == "not in drawing index":
            problems.append("sheet number not found in the binder's drawing index")
        if num and not discipline_ok(num, discipline):
            problems.append(f"prefix '{re.match(r'[A-Z]+', num).group(0)}' unusual for this folder")

        if is_index:
            stem = clean_filename(f"INDEX - {pdf_path.stem[-40:]} - p{i + 1:03d}")
            problems = []
            note = "drawing index / cover list page"
        elif num:
            stem = clean_filename(f"{num} - {title}" if title else num)
        else:
            stem = clean_filename(f"UNKNOWN - {pdf_path.stem[-40:]} - p{i + 1:03d}")
        out_path = unique_path(out_dir, stem)

        single = fitz.open()
        single.insert_pdf(doc, from_page=i, to_page=i)
        single.save(out_path, garbage=3, deflate=True)
        single.close()

        status = "OK" if not problems else "REVIEW: " + "; ".join(problems)
        log.append([discipline, pdf_path.name, i + 1, out_path.name, status, method, note])
        flag = "" if status == "OK" else "   <-- check"
        extra = f"   [{method}{'; ' + note if note else ''}]"
        print(f"  p{i + 1:>3}: {out_path.name}{extra}{flag}")
        saved += 1

    doc.close()
    return n_pages, saved

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    raw = input("Enter the directory containing your drawing folders: ").strip().strip('"').strip("'")
    root = Path(raw).expanduser()
    if not root.is_dir():
        sys.exit(f"Not a valid directory: {root}")

    print("\nCapabilities:")
    print(f"  Embedded text : yes")
    print(f"  OCR           : {'yes' if HAVE_OCR else 'NO  (install tesseract + pip install pytesseract pillow)'}")
    print(f"  Vision AI     : {'yes (' + VISION_MODEL + ')' if HAVE_VISION else 'no  (set ANTHROPIC_API_KEY and pip install anthropic)'}")

    out_dir = root / OUTPUT_FOLDER_NAME
    out_dir.mkdir(exist_ok=True)
    pdfs = find_pdfs(root, out_dir)
    if not pdfs:
        sys.exit("No PDF files found.")
    print(f"\nFound {len(pdfs)} binder(s). Output -> {out_dir}\n")

    log, total_pages, total_saved = [], 0, 0
    for pdf in pdfs:
        print(pdf.relative_to(root))
        p, s = process_binder(pdf, out_dir, log)
        total_pages += p
        total_saved += s
        print()

    log_path = root / "Drawings_log.csv"
    with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Discipline folder", "Source file", "Source page", "Output file",
                    "Status", "Method", "Derivation note"])
        w.writerows(log)

    review = sum(1 for r in log if str(r[4]).startswith(("REVIEW", "ERROR")))
    print(f"Pages found: {total_pages}   Drawings saved: {total_saved}")
    if total_pages != total_saved:
        print("WARNING: page count and saved count differ - check the log for ERROR rows.")
    print(f"Output: {out_dir}\nLog:    {log_path}")
    if review:
        print(f"{review} page(s) flagged for review - filter the log's Status column.")


if __name__ == "__main__":
    main()
