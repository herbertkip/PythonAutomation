#!/usr/bin/env python3
"""
check_rev_column.py

Detects the 'Rev' / 'Revision' column in a report file (TXT, PDF, or DOCX)
and verifies that every value in that column is zero.

Accepts EITHER a single file OR a directory (searched recursively).

Usage:
    python check_rev_column.py
    python check_rev_column.py <file-or-directory>
"""

import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Supported extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTS = {".txt", ".text", ".dat", ".prn", ".rpt", ".pdf", ".docx"}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------
def extract_text_from_pdf(path):
    """Extract text from a PDF using pdfplumber (preferred) or PyPDF2."""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except ImportError:
        raise RuntimeError(
            "PDF support requires 'pdfplumber' or 'PyPDF2'.\n"
            "Install with:  pip install pdfplumber"
        )


def extract_text_from_docx(path):
    """Extract text from a .docx using python-docx, preserving tables."""
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError(
            "DOCX support requires 'python-docx'.\n"
            "Install with:  pip install python-docx"
        )

    doc = Document(str(path))
    lines = []

    for para in doc.paragraphs:
        lines.append(para.text)

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                lines.append("    ".join(cells))

    return "\n".join(lines)


def extract_text_from_txt(path):
    """Read plain text, trying common encodings."""
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(path: Path) -> str:
    """Dispatch to the right extractor based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    if suffix == ".doc":
        raise RuntimeError(
            "Legacy .doc files are not directly supported. "
            "Please convert to .docx or .pdf first."
        )
    return extract_text_from_txt(path)


# ---------------------------------------------------------------------------
# Header / column detection
# ---------------------------------------------------------------------------
REV_HEADER_RE = re.compile(r"\brev(?:ision)?\.?\b", re.IGNORECASE)


def find_header_line(lines):
    """Find the header line containing 'Rev'/'Revision' plus companion words."""
    companion_words = ("mark", "profile", "grade", "length", "weight",
                       "description", "code", "no.")

    for i, line in enumerate(lines):
        if not REV_HEADER_RE.search(line):
            continue
        lowered = line.lower()
        hits = sum(1 for w in companion_words if w in lowered)
        if hits >= 2:
            return i, line

    for i, line in enumerate(lines):
        if REV_HEADER_RE.search(line):
            return i, line

    return None, None


def find_rev_column_index(header_line: str):
    """Return (start, end) character offsets of the 'Rev' column."""
    match = REV_HEADER_RE.search(header_line)
    if not match:
        return None, None

    start = match.start()

    next_col_re = re.compile(
        r"\b(grade|length|weight|description|camber|stud|finish|seq|comments|"
        r"mark|profile|code|no\.)\b",
        re.IGNORECASE,
    )
    next_match = next_col_re.search(header_line, match.end())
    end = next_match.start() if next_match else len(header_line)

    return start, end


def parse_rows(lines, header_idx, col_start, col_end):
    """Yield (line_number, line, cell_value) for each data row below the header."""
    start = header_idx + 1
    while start < len(lines) and set(lines[start].strip()) <= {"-", " ", ""}:
        start += 1

    for i in range(start, len(lines)):
        line = lines[i]
        stripped = line.strip()

        if stripped and set(stripped) <= {"-"}:
            break
        if "Total Qty" in line or "Total Net Weight" in line:
            break
        if len(line) <= col_start:
            continue

        cell = line[col_start:col_end].strip()
        if not cell:
            continue

        yield i + 1, line, cell


# ---------------------------------------------------------------------------
# Zero-check
# ---------------------------------------------------------------------------
ZERO_RE = re.compile(r"^[-+]?0+(?:\.0+)?$")


def is_zero(value: str) -> bool:
    return bool(ZERO_RE.match(value.strip()))


# ---------------------------------------------------------------------------
# Core check (single file)
# ---------------------------------------------------------------------------
def check_file(filepath: Path, quiet: bool = False) -> dict:
    """
    Returns a dict:
      { status: 'pass'|'fail'|'skip'|'error',
        file:   Path,
        reason: str (optional),
        bad:    list of (line_no, cell, full_line),
        total:  int }
    """
    result = {"status": "error", "file": filepath,
              "reason": "", "bad": [], "total": 0}

    try:
        text = extract_text(filepath)
    except Exception as e:
        result["reason"] = str(e)
        if not quiet:
            print(f"[ERROR] {filepath.name}: {e}")
        return result

    lines = text.splitlines()

    header_idx, header_line = find_header_line(lines)
    if header_idx is None:
        result["status"] = "skip"
        result["reason"] = "No 'Rev'/'Revision' header found."
        if not quiet:
            print(f"[SKIP] {filepath.name}: {result['reason']}")
        return result

    col_start, col_end = find_rev_column_index(header_line)
    if col_start is None:
        result["status"] = "skip"
        result["reason"] = "Could not locate 'Rev' column position."
        if not quiet:
            print(f"[SKIP] {filepath.name}: {result['reason']}")
        return result

    bad = []
    total = 0
    for line_no, line, cell in parse_rows(lines, header_idx, col_start, col_end):
        total += 1
        if not is_zero(cell):
            bad.append((line_no, cell, line.rstrip()))

    result["total"] = total
    result["bad"] = bad

    if bad:
        result["status"] = "fail"
    else:
        result["status"] = "pass"

    if not quiet:
        if bad:
            print(f"[FAIL] {filepath.name} — {len(bad)} non-zero Rev value(s) "
                  f"out of {total} row(s).")
        else:
            print(f"[PASS] {filepath.name} — all {total} Rev values are zero.")

    return result


# ---------------------------------------------------------------------------
# Path discovery
# ---------------------------------------------------------------------------
def discover_files(root: Path):
    """Return a sorted list of supported files under root (recursive)."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden / temp / system folders
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d.lower() not in
                       ("__macosx", "$recycle.bin", "node_modules")]
        for name in filenames:
            if name.startswith("~$") or name.startswith("."):
                continue
            ext = Path(name).suffix.lower()
            if ext in SUPPORTED_EXTS:
                found.append(Path(dirpath) / name)
    return sorted(found)


# ---------------------------------------------------------------------------
# Interactive prompt
# ---------------------------------------------------------------------------
def prompt_for_path() -> Path:
    """
    Prompt the user for a file OR directory path.
    Loops until a valid path is provided.
    """
    while True:
        raw = input(
            "Enter a file or directory path\n"
            "  (drag-and-drop or paste is fine; 'q' to quit): "
        ).strip().strip('"').strip("'")

        if raw.lower() in ("q", "quit", "exit"):
            print("Cancelled.")
            sys.exit(0)

        if not raw:
            print("  → No input. Please try again.\n")
            continue

        path = Path(raw).expanduser()

        # Handle Windows paths pasted with backslashes
        try:
            path = path.resolve()
        except OSError as e:
            print(f"  → Invalid path: {e}\n")
            continue

        if not path.exists():
            print(f"  → Path does not exist: {path}\n")
            continue

        return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Command-line argument still works
    if len(sys.argv) > 1:
        target = Path(sys.argv[1]).expanduser()
        if not target.exists():
            print(f"[ERROR] Path does not exist: {target}")
            sys.exit(2)
        target = target.resolve()
    else:
        print("=" * 70)
        print("Rev-Column Zero Checker")
        print("=" * 70)
        target = prompt_for_path()

    # Decide: single file or directory?
    if target.is_file():
        files = [target]
        print(f"\nChecking single file: {target}\n")
    elif target.is_dir():
        print(f"\nScanning directory recursively: {target}\n")
        files = discover_files(target)
        if not files:
            print(f"[ERROR] No supported files "
                  f"({', '.join(sorted(SUPPORTED_EXTS))}) found in {target}")
            sys.exit(2)
        print(f"Found {len(files)} candidate file(s).\n")
    else:
        print(f"[ERROR] Not a file or directory: {target}")
        sys.exit(2)

    # Run checks
    results = [check_file(f) for f in files]

    # Summary
    passed = [r for r in results if r["status"] == "pass"]
    failed = [r for r in results if r["status"] == "fail"]
    skipped = [r for r in results if r["status"] == "skip"]
    errored = [r for r in results if r["status"] == "error"]

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total files checked : {len(results)}")
    print(f"  ✔ Passed            : {len(passed)}")
    print(f"  ✘ Failed            : {len(failed)}")
    print(f"  ⚠ Skipped           : {len(skipped)}")
    print(f"  ✖ Errors            : {len(errored)}")

    if failed:
        print("\nFiles with non-zero Rev values:")
        for r in failed:
            print(f"  • {r['file']}")
            for line_no, cell, full in r["bad"][:5]:
                print(f"      line {line_no}: Rev = {cell!r}")
            if len(r["bad"]) > 5:
                print(f"      ... and {len(r['bad']) - 5} more")

    if skipped:
        print("\nSkipped (no Rev header detected):")
        for r in skipped:
            print(f"  • {r['file']} — {r['reason']}")

    if errored:
        print("\nErrors:")
        for r in errored:
            print(f"  • {r['file']} — {r['reason']}")

    # Exit code: 0 = all pass (or only skips), 1 = failures, 2 = errors only
    if failed:
        sys.exit(1)
    if errored and not passed and not skipped:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(130)