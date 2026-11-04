#!/usr/bin/env python3
"""
ReportCheck.py  (combined)

1. Prompt for a directory.
2. Recursively search for a 'reports'/'report' folder.
3. Find files containing 'Assembly' in their name inside those folders.
4. For each matching file (.txt/.pdf/.docx), locate the 'Rev'/'Revision'
   column and verify that every value in it is zero.
5. Report pass/fail per file, with a final summary.
"""

import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Supported extensions for Rev-column checking
# ---------------------------------------------------------------------------
SUPPORTED_EXTS = {".txt", ".text", ".dat", ".prn", ".rpt", ".pdf", ".docx"}


# ===========================================================================
# SECTION 1 — Directory & file discovery  (from ReportCheck.py)
# ===========================================================================
def prompt_for_directory():
    """Prompt the user for a directory and validate it exists."""
    while True:
        directory = input("Please enter a directory path: ").strip().strip('"').strip("'")

        if not directory:
            print("No input provided. Please try again.\n")
            continue

        path = Path(directory).expanduser()

        try:
            path = path.resolve()
        except OSError as e:
            print(f"Error resolving path: {e}\n")
            continue

        if not path.exists():
            print(f"Error: '{path}' does not exist. Please try again.\n")
            continue

        if not path.is_dir():
            print(f"Error: '{path}' is not a directory. Please try again.\n")
            continue

        return path


def find_report_folder(root_dir):
    """Recursively search for folders named 'reports' or 'report'."""
    matches = []
    for current_root, dirs, _files in os.walk(root_dir):
        for d in dirs:
            if d.lower() in ("reports", "report"):
                matches.append(Path(current_root) / d)
    return matches


def find_assembly_file(folder):
    """Return files in `folder` whose name contains 'assembly' (case-insensitive)."""
    matches = []
    if not folder.exists():
        return matches

    for entry in folder.iterdir():
        if entry.is_file() and "assembly" in entry.name.lower():
            matches.append(entry)
    return matches


# ===========================================================================
# SECTION 2 — Text extraction  (TXT / PDF / DOCX)
# ===========================================================================
def extract_text_from_pdf(path):
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
            "PDF support requires 'pdfplumber' or 'PyPDF2'. "
            "Install with:  pip install pdfplumber"
        )


def extract_text_from_docx(path):
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError(
            "DOCX support requires 'python-docx'. "
            "Install with:  pip install python-docx"
        )

    doc = Document(str(path))
    lines = [p.text for p in doc.paragraphs]

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                lines.append("    ".join(cells))
    return "\n".join(lines)


def extract_text_from_txt(path):
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    if suffix == ".doc":
        raise RuntimeError(
            "Legacy .doc files are not supported. Convert to .docx or .pdf."
        )
    return extract_text_from_txt(path)


# ===========================================================================
# SECTION 3 — Rev-column detection & zero check
# ===========================================================================
REV_HEADER_RE = re.compile(r"\brev(?:ision)?\.?\b", re.IGNORECASE)
ZERO_RE = re.compile(r"^[-+]?0+(?:\.0+)?$")


def find_header_line(lines):
    companion_words = ("mark", "profile", "grade", "length", "weight",
                       "description", "code", "no.")
    for i, line in enumerate(lines):
        if not REV_HEADER_RE.search(line):
            continue
        hits = sum(1 for w in companion_words if w in line.lower())
        if hits >= 2:
            return i, line
    for i, line in enumerate(lines):
        if REV_HEADER_RE.search(line):
            return i, line
    return None, None


def find_rev_column_index(header_line: str):
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


def is_zero(value: str) -> bool:
    return bool(ZERO_RE.match(value.strip()))


def check_rev_column(filepath: Path) -> dict:
    """
    Returns:
      { status: 'pass'|'fail'|'skip'|'error',
        file:   Path,
        reason: str,
        bad:    list of (line_no, cell, full_line),
        total:  int }
    """
    result = {"status": "error", "file": filepath,
              "reason": "", "bad": [], "total": 0}

    try:
        text = extract_text(filepath)
    except Exception as e:
        result["reason"] = str(e)
        return result

    lines = text.splitlines()
    header_idx, header_line = find_header_line(lines)

    if header_idx is None:
        result["status"] = "skip"
        result["reason"] = "No 'Rev'/'Revision' header found."
        return result

    col_start, col_end = find_rev_column_index(header_line)
    if col_start is None:
        result["status"] = "skip"
        result["reason"] = "Could not locate 'Rev' column position."
        return result

    bad = []
    total = 0
    for line_no, line, cell in parse_rows(lines, header_idx, col_start, col_end):
        total += 1
        if not is_zero(cell):
            bad.append((line_no, cell, line.rstrip()))

    result["total"] = total
    result["bad"] = bad
    result["status"] = "fail" if bad else "pass"
    return result


# ===========================================================================
# SECTION 4 — Main
# ===========================================================================
def main():
    print("=" * 60)
    print("Report Folder & Assembly File Rev-Zero Checker")
    print("=" * 60)

    # Step 1: Prompt for directory
    root_dir = prompt_for_directory()
    print(f"\nSearching in: {root_dir}\n")

    # Step 2: Find 'reports'/'report' folders
    print("Searching for 'reports'/'report' folders (including child folders)...")
    report_folders = find_report_folder(root_dir)

    # Step 3: Report if missing
    if not report_folders:
        print("\n[RESULT] MISSING: No 'reports' or 'report' folder was found.")
        sys.exit(1)

    print(f"\n[RESULT] Found {len(report_folders)} matching folder(s):")
    for folder in report_folders:
        print(f"  - {folder}")

    # Step 4: For each report folder, find 'Assembly' files and check Rev column
    print("\nSearching for files with 'Assembly' in the name...")

    results = []          # list of dicts from check_rev_column
    files_checked = 0

    for folder in report_folders:
        print(f"\nFolder: {folder}")

        assembly_files = find_assembly_file(folder)

        if not assembly_files:
            print(f"  [RESULT] MISSING: No file containing 'Assembly' found.")
            continue

        for filepath in assembly_files:
            print(f"  [FOUND] {filepath.name}")

            # Only attempt Rev-check on supported file types
            if filepath.suffix.lower() not in SUPPORTED_EXTS:
                print(f"  [SKIP] Unsupported file type: {filepath.suffix}")
                continue

            res = check_rev_column(filepath)
            results.append(res)
            files_checked += 1

            if res["status"] == "pass":
                print(f"  [PASS] All {res['total']} Rev value(s) are zero.")
            elif res["status"] == "fail":
                print(f"  [FAIL] {len(res['bad'])} non-zero Rev value(s) "
                      f"out of {res['total']} row(s).")
                for line_no, cell, full in res["bad"][:5]:
                    print(f"         line {line_no}: Rev = {cell!r}")
                    print(f"           {full}")
                if len(res["bad"]) > 5:
                    print(f"         ... and {len(res['bad']) - 5} more.")
            elif res["status"] == "skip":
                print(f"  [SKIP] {res['reason']}")
            else:
                print(f"  [ERROR] {res['reason']}")

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if files_checked == 0:
        print("No 'Assembly' files were found or checked.")
        sys.exit(1)

    passed = [r for r in results if r["status"] == "pass"]
    failed = [r for r in results if r["status"] == "fail"]
    skipped = [r for r in results if r["status"] == "skip"]
    errored = [r for r in results if r["status"] == "error"]

    print(f"  Files checked : {files_checked}")
    print(f"  ✔ Passed      : {len(passed)}")
    print(f"  ✘ Failed      : {len(failed)}")
    print(f"  ⚠ Skipped     : {len(skipped)}")
    print(f"  ✖ Errors      : {len(errored)}")

    if failed:
        print("\nFiles with non-zero Rev values:")
        for r in failed:
            print(f"  • {r['file'].name}  ({r['file'].parent})")
            for line_no, cell, _full in r["bad"][:5]:
                print(f"      line {line_no}: Rev = {cell!r}")
            if len(r["bad"]) > 5:
                print(f"      ... and {len(r['bad']) - 5} more")

    if skipped:
        print("\nSkipped:")
        for r in skipped:
            print(f"  • {r['file'].name} — {r['reason']}")

    if errored:
        print("\nErrors:")
        for r in errored:
            print(f"  • {r['file'].name} — {r['reason']}")

    # Exit codes: 0 = all pass, 1 = any fail, 2 = errors only
    if failed:
        sys.exit(1)
    if errored and not passed and not skipped:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)