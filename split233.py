"""
pdf_splitter.py

Splits multi-page PDF binders into single-page PDFs and renames each
based on the drawing name/number found on the page.

Performance:
  - Uses pypdfium2 (PDFium) for fast text extraction (~50-100x faster than pdfplumber)
  - Falls back to a cropped pdfplumber extraction (title block only) if needed
  - Falls back to PyPDF2 text extraction as a last resort

Usage:
    python pdf_splitter.py

The script will prompt for a directory. It will:
  1. Walk the directory tree looking for .pdf files (binders).
  2. Split each binder into single-page PDFs.
  3. Extract the drawing name/number from each page.
  4. Save each page to a "Drawings" folder next to the input directory,
     named after the drawing.
"""

import os
import re
import sys
from pathlib import Path

# --- Third-party imports ---
try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("Missing dependency: PyPDF2")
    print("Install with:  pip install PyPDF2")
    sys.exit(1)

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None
    print("[warn] pypdfium2 not installed — falling back to slower extraction.")
    print("       Install with:  pip install pypdfium2")

try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    print("[warn] pdfplumber not installed — title-block fallback disabled.")
    print("       Install with:  pip install pdfplumber")


# ---------------------------------------------------------------------------
# Drawing-name extraction
# ---------------------------------------------------------------------------
# Matches common AEC drawing numbers:
#   A-101, A101, E-2.01, M-101, P-101, FP-101, T-101, C-101, S-101
DRAWING_NUM_PATTERNS = [
    re.compile(r"\b([A-Z]{1,3})[-_. ]?(\d{1,3}(?:[.\-]\d{1,3})?)\b"),
]

# Keywords in folder paths -> discipline letter used to bias matches
DISCIPLINE_HINTS = {
    "MECHANICAL": "M",
    "PLUMBING": "P",
    "ELECTRICAL": "E",
    "FIRE PROTECTION": "FP",
    "FIRE": "FP",
    "SECURITY": "S",
    "TECHNOLOGY": "T",
    "CONTROLS": "C",
    "ARCHITECTURAL": "A",
    "TENANT": "A",
}


def sanitize_filename(name: str) -> str:
    """Remove characters not allowed in filenames on Windows/macOS/Linux."""
    name = name.strip()
    name = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(" .")[:180]


def extract_drawing_name(text: str, fallback: str, discipline_hint: str = "") -> str:
    """
    Pull a drawing number/name out of the page text.

    Priority:
      1. Explicit drawing-number pattern (A-101, E-2.01, etc.)
      2. First reasonable-looking short line (title block title)
      3. Fallback: "<binder>_page_NNN"
    """
    if text:
        text = re.sub(r"[ \t]+", " ", text)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        # 1. Drawing number pattern
        candidates = []
        for line in lines:
            for pat in DRAWING_NUM_PATTERNS:
                for m in pat.finditer(line):
                    disc, num = m.group(1), m.group(2)
                    if disc in {"I", "O"} or len(disc) > 3:
                        continue
                    candidates.append(f"{disc}-{num}")

        if candidates:
            if discipline_hint:
                for c in candidates:
                    if c.upper().startswith(discipline_hint.upper()):
                        return sanitize_filename(c)
            return sanitize_filename(candidates[0])

        # 2. Title-block-ish line
        for line in lines[:40]:
            if 3 <= len(line) <= 80 and re.search(r"[A-Za-z]", line):
                if line.lower().startswith("page "):
                    continue
                if re.fullmatch(r"[\d\s\-/]+", line):
                    continue
                return sanitize_filename(line)

    return sanitize_filename(fallback)


def guess_discipline(pdf_path: Path) -> str:
    """Guess the discipline letter from the file path."""
    parts = " ".join(pdf_path.parts).upper()
    for keyword, letter in DISCIPLINE_HINTS.items():
        if keyword in parts:
            return letter
    return ""


# ---------------------------------------------------------------------------
# Fast text extraction helpers
# ---------------------------------------------------------------------------
def extract_text_pdfium(pdfium_doc, page_index: int) -> str:
    """Fast path: pypdfium2 (PDFium engine)."""
    if pdfium_doc is None:
        return ""
    try:
        tp = pdfium_doc[page_index].get_textpage()
        return tp.get_text_range() or ""
    except Exception:
        return ""


def extract_text_pypdf2(page) -> str:
    """Medium path: PyPDF2 built-in extractor."""
    try:
        return page.extract_text() or ""
    except Exception:
        return ""


def extract_text_plumber_titleblock(plumber_doc, page_index: int) -> str:
    """
    Slow but accurate path: pdfplumber, cropped to the title-block region
    (bottom-right quadrant). Cropping makes it dramatically faster than
    extracting full-page text on complex drawings.
    """
    if plumber_doc is None:
        return ""
    try:
        page_obj = plumber_doc.pages[page_index]
        w, h = page_obj.width, page_obj.height
        # Bottom-right quadrant — where title blocks almost always live.
        crop = page_obj.crop((w * 0.55, h * 0.65, w, h))
        return crop.extract_text() or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------
def split_pdf(pdf_path: Path, output_dir: Path) -> int:
    """Split a PDF into single-page PDFs saved in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    discipline = guess_discipline(pdf_path)
    written = 0

    # --- Open with PyPDF2 (for splitting) ---
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"  [!] Could not read {pdf_path.name}: {e}", flush=True)
        return 0

    total = len(reader.pages)
    print(f"  -> {pdf_path.name}  ({total} pages)", flush=True)

    # --- Open with pypdfium2 once (fast text extraction) ---
    pdfium_doc = None
    if pdfium is not None:
        try:
            pdfium_doc = pdfium.PdfDocument(str(pdf_path))
        except Exception:
            pdfium_doc = None

    # --- Open with pdfplumber lazily (only if we need the fallback) ---
    plumber_doc = None

    for i, page in enumerate(reader.pages):
        # 1. Fast path: pdfium
        text = extract_text_pdfium(pdfium_doc, i)

        # 2. If nothing, try PyPDF2
        if not text.strip():
            text = extract_text_pypdf2(page)

        # 3. If still nothing, try cropped pdfplumber (lazy-open)
        if not text.strip() and pdfplumber is not None:
            if plumber_doc is None:
                try:
                    plumber_doc = pdfplumber.open(str(pdf_path))
                except Exception:
                    plumber_doc = False  # sentinel so we don't retry
            if plumber_doc:
                text = extract_text_plumber_titleblock(plumber_doc, i)

        fallback = f"{pdf_path.stem}_page_{i + 1:03d}"
        drawing_name = extract_drawing_name(text, fallback, discipline)

        # Avoid collisions
        target = output_dir / f"{drawing_name}.pdf"
        counter = 2
        while target.exists():
            target = output_dir / f"{drawing_name}_{counter}.pdf"
            counter += 1

        # Write single page
        writer = PdfWriter()
        writer.add_page(page)
        try:
            with open(target, "wb") as f:
                writer.write(f)
            written += 1
            print(f"     [{i + 1:>3}/{total}] -> {target.name}", flush=True)
        except Exception as e:
            print(f"     [!] Failed to write page {i + 1}: {e}", flush=True)

    # Cleanup
    if pdfium_doc is not None:
        try:
            pdfium_doc.close()
        except Exception:
            pass
    if plumber_doc and plumber_doc is not False:
        try:
            plumber_doc.close()
        except Exception:
            pass

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 64)
    print(" PDF Binder Splitter & Renamer")
    print("=" * 64)
    print()

    raw = input("Enter the directory containing the binder folders: ").strip().strip('"').strip("'")
    if not raw:
        print("No directory provided. Exiting.")
        sys.exit(1)

    source = Path(raw).expanduser().resolve()
    if not source.is_dir():
        print(f"Not a directory: {source}")
        sys.exit(1)

    output_dir = source / "Drawings"

    # Find PDFs (skip anything already in the output folder)
    binders = []
    seen = set()
    for pattern in ("*.pdf", "*.PDF"):
        for p in source.rglob(pattern):
            if output_dir in p.parents:
                continue
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            binders.append(p)

    if not binders:
        print(f"No PDF files found in {source}")
        sys.exit(0)

    print(f"\nSource:  {source}")
    print(f"Output:  {output_dir}")
    print(f"Found {len(binders)} binder(s).\n")

    total_pages = 0
    for binder in sorted(binders):
        total_pages += split_pdf(binder, output_dir)

    print()
    print("=" * 64)
    print(f"Done. {total_pages} drawing(s) written to:")
    print(f"  {output_dir}")
    print("=" * 64)


if __name__ == "__main__":
    main()