"""
pdf_splitter.py

Splits multi-page PDF binders into single-page PDFs and renames each
based on the drawing name/number found on the page.

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
import shutil
from pathlib import Path

# --- Third-party imports ---
try:
    import pdfplumber
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("Missing dependencies. Install them with:")
    print("    pip install pdfplumber PyPDF2")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Drawing-name extraction
# ---------------------------------------------------------------------------
# Common title-block patterns for AEC drawings. Extend as needed.
# Examples this matches:
#   "A-101", "A101", "E-2.01", "M-101", "P-101", "FP-101", "T-101"
#   "A-101 - Floor Plan", "E-2.01 FIRST FLOOR POWER PLAN"
DRAWING_NUM_PATTERNS = [
    # Discipline letter + separator + number, e.g. A-101, E-2.01, FP-101
    re.compile(r"\b([A-Z]{1,3})[-_. ]?(\d{1,3}(?:[.\-]\d{1,3})?)\b"),
]

# Keywords that typically sit near the drawing name in a title block
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
}


def sanitize_filename(name: str) -> str:
    """Remove characters not allowed in filenames on Windows/macOS/Linux."""
    name = name.strip()
    name = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(" .")[:180]  # keep filenames reasonable


def extract_drawing_name(text: str, fallback: str, discipline_hint: str = "") -> str:
    """
    Try to pull a drawing number/name out of the page text.

    Priority:
      1. Explicit drawing-number pattern (A-101, E-2.01, etc.)
      2. A line that looks like a title block entry
      3. Fallback (e.g. "<binder>_page_01")
    """
    if text:
        # Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        # 1. Look for drawing number pattern. Prefer the "cleanest" match.
        candidates = []
        for line in lines:
            for pat in DRAWING_NUM_PATTERNS:
                for m in pat.finditer(line):
                    disc, num = m.group(1), m.group(2)
                    # Skip obvious false positives (years, dimensions, etc.)
                    if disc in {"I", "O"}:
                        continue
                    if len(disc) > 3:
                        continue
                    candidates.append(f"{disc}-{num}")

        if candidates:
            # Prefer the discipline letter if we know it
            if discipline_hint:
                for c in candidates:
                    if c.upper().startswith(discipline_hint.upper()):
                        return sanitize_filename(c)
            return sanitize_filename(candidates[0])

        # 2. Fall back to the first "prominent" short line that looks like a title
        for line in lines[:40]:
            if 3 <= len(line) <= 80 and re.search(r"[A-Za-z]", line):
                # skip lines that look like page numbers or the filename itself
                if line.lower().startswith("page "):
                    continue
                if re.fullmatch(r"[\d\s\-/]+", line):
                    continue
                return sanitize_filename(line)

    # 3. Fallback
    return sanitize_filename(fallback)


def guess_discipline(pdf_path: Path) -> str:
    """Guess the discipline letter from the file path (folder names)."""
    parts = " ".join(pdf_path.parts).upper()
    for keyword, letter in DISCIPLINE_HINTS.items():
        if keyword in parts:
            return letter
    return ""


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------
def split_pdf(pdf_path: Path, output_dir: Path, prefix: str = "") -> int:
    """
    Split a PDF into single-page PDFs saved in output_dir.
    Returns number of pages written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    discipline = guess_discipline(pdf_path)
    written = 0

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"  [!] Could not read {pdf_path.name}: {e}")
        return 0

    total = len(reader.pages)
    print(f"  -> {pdf_path.name}  ({total} pages)")

    # Open with pdfplumber once for text extraction (more reliable than PyPDF2)
    try:
        plumber = pdfplumber.open(str(pdf_path))
    except Exception:
        plumber = None

    for i, page in enumerate(reader.pages):
        # --- extract text ---
        text = ""
        if plumber is not None and i < len(plumber.pages):
            try:
                text = plumber.pages[i].extract_text() or ""
            except Exception:
                text = ""
        if not text:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

        fallback = f"{pdf_path.stem}_page_{i + 1:03d}"
        drawing_name = extract_drawing_name(text, fallback, discipline)

        # Avoid collisions: if the name already exists, append a counter
        target = output_dir / f"{drawing_name}.pdf"
        counter = 2
        while target.exists():
            target = output_dir / f"{drawing_name}_{counter}.pdf"
            counter += 1

        # --- write the single page ---
        writer = PdfWriter()
        writer.add_page(page)
        try:
            with open(target, "wb") as f:
                writer.write(f)
            written += 1
            print(f"     [{i + 1:>3}/{total}] -> {target.name}")
        except Exception as e:
            print(f"     [!] Failed to write page {i + 1}: {e}")

    if plumber is not None:
        plumber.close()

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 64)
    print(" PDF Binder Splitter & Renamer")
    print("=" * 64)
    print()

    # Prompt for the source directory
    raw = input("Enter the directory containing the binder folders: ").strip().strip('"').strip("'")
    if not raw:
        print("No directory provided. Exiting.")
        sys.exit(1)

    source = Path(raw).expanduser().resolve()
    if not source.is_dir():
        print(f"Not a directory: {source}")
        sys.exit(1)

    # Output goes into a "Drawings" folder *inside* the source directory
    output_dir = source / "Drawings"

    # Find all PDFs (skip anything already inside our output folder)
    binders = [
        p for p in source.rglob("*.pdf")
        if output_dir not in p.parents and p.suffix.lower() == ".pdf"
    ]
    # Also catch .PDF (uppercase extension)
    binders += [
        p for p in source.rglob("*.PDF")
        if output_dir not in p.parents and p not in binders
    ]

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