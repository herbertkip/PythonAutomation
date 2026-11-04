#!/usr/bin/env python3
"""
split_drawing_set.py
Split a construction drawing set (PDF) into one PDF per sheet and name each
file "<sheet number> - <sheet name>.pdf", read from the title block.

Runs fully locally. Install once:
    pip install pymupdf

Usage:
    python split_drawing_set.py "C:\\Jobs\\MapleTree"  # folder path on the command line
    python split_drawing_set.py                      # no path given: type it at a prompt
    python split_drawing_set.py "Permit Set.pdf"     # a specific PDF
    python split_drawing_set.py "Permit Set.pdf" --dry-run   # preview names only

Options:
    --zip            also create a .zip of the split sheets
    --right 0.25 --bottom 0.5   title-block search area (fraction of page,
                                measured from the bottom-right corner)
    --job-in-name    include the CONTRACTOR JOB No. in each output filename
    --debug          print diagnostic info for job-number extraction
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
# CONTRACTOR JOB No. label followed by its value
JOB_NO_LABEL = re.compile(
    r"CONTRACTOR\s+JOB\s+No\s*\.?\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-\./]*)", re.I
)
BAD_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


# ----------------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------------
def ask_folder():
    """Ask (typed, no pop-up) for the folder that holds the binder PDF."""
    while True:
        try:
            raw = input("Folder containing the binder PDF "
                        "(paste path, Enter = current folder, q = quit): ").strip()
        except EOFError:
            sys.exit("No input received.")
        if raw.lower() in ("q", "quit", "exit"):
            sys.exit("Cancelled.")
        folder = Path(raw.strip('"').strip("'")).expanduser() if raw else Path.cwd()
        if folder.is_dir():
            return folder        print(f"  Not a folder: {folder}")


def choose_pdfs(folder):
    """List PDFs in the folder and let the user pick one (or all)."""
    pdfs = sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix.lower() == ".pdf")
    if not pdfs:
        sys.exit(f"No PDF files found in: {folder}")
    if len(pdfs) == 1:
        print(f"Found 1 PDF: {pdfs[0].name}")
        return pdfs

    print(f"\nPDFs in {folder}:")
    for n, p in enumerate(pdfs, 1):
        print(f"  {n}. {p.name}")
    while True:
        try:
            pick = input("Enter a number, several separated by commas, "
                         "or A for all: ").strip().lower()
        except EOFError:
            sys.exit("No input received.")
        if pick in ("a", "all"):
            return pdfs
        try:
            idx = [int(x) for x in pick.split(",")]
            if all(1 <= i <= len(pdfs) for i in idx):
                return [pdfs[i - 1] for i in idx]
        except ValueError:
            pass
        print("  Invalid choice.")


def ask_yes_no(question, default=True):
    try:
        ans = input(f"{question} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    except EOFError:
        return default
    return default if not ans else ans.startswith("y")


# ----------------------------------------------------------------------------
# Title-block reading
# ----------------------------------------------------------------------------
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


def read_job_no(page, debug=False):
    """Return the CONTRACTOR JOB No. value, or '' if not found.

    Tries several strategies so it works regardless of how PyMuPDF splits
    the title-block text into spans/lines/blocks.
    """
    # Gather candidate text strings from several extraction methods.
    candidates = []

    # 1. Plain text (reading order)
    try:
        t = page.get_text("text")
        if t:
            candidates.append(("text", re.sub(r"\s+", " ", t)))
    except Exception:
        pass

    # 2. Words, sorted into reading order
    try:
        words = page.get_text("words")
        if words:
            words.sort(key=lambda w: (round(w[1] / 4), w[0]))
            t = " ".join(w[4] for w in words)
            candidates.append(("words", re.sub(r"\s+", " ", t)))
    except Exception:
        pass

    # 3. Spans, sorted into reading order
    try:
        spans = list(page_spans(page))
        spans.sort(key=lambda s: (round(s[0].y0 / 4), s[0].x0))
        t = " ".join(s[2] for s in spans)
        candidates.append(("spans", re.sub(r"\s+", " ", t)))
    except Exception:
        pass

    if debug:
        for method, text in candidates:
            idx = text.upper().find("CONTRACTOR")
            if idx >= 0:
                snippet = text[max(0, idx - 30):idx + 90]
                print(f"    [debug] {method}: ...{snippet}...")
            else:
                print(f"    [debug] {method}: 'CONTRACTOR' not found "
                      f"(first 200 chars: {text[:200]!r})")

    # Patterns to try, in order of specificity.
    patterns = [
        # CONTRACTOR JOB No. <value>
        r"CONTRACTOR\s+JOB\s+No\s*\.?\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-\./]*)",
        # CONTRACTOR JOB NO <value>  (no period)
        r"CONTRACTOR\s+JOB\s+NO\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-\./]*)",
        # CONTRACTOR JOB NUMBER <value>
        r"CONTRACTOR\s+JOB\s+(?:NUMBER|NUM|#)\s*\.?\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-\./]*)",
    ]

    for method, text in candidates:
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                val = m.group(1).strip(" .,:;#").upper()
                if val and val not in ("NO", "NO.", "ENGINEER", "DRG",
                                       "JOB", "NUMBER", "NUM"):
                    if debug:
                        print(f"    [debug] matched ({method}): {val!r}")
                    return val

    # Fallback: job-number-shaped token anywhere in the text
    # (three digits + letter + three digits, e.g. 401M024)
    for method, text in candidates:
        m = re.search(r"\b(\d{3}[A-Z]\d{3})\b", text)
        if m:
            if debug:
                print(f"    [debug] fallback ({method}): {m.group(1)!r}")
            return m.group(1)

    if debug:
        print("    [debug] no job number found")
    return ""


def read_title_block(page, right_frac, bottom_frac, debug=False):
    """Return (sheet_number, sheet_name, job_no, how) for one page."""
    job_no = read_job_no(page, debug=debug)

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
        return number.upper(), name, job_no, how
    return None, "", job_no, "not found"


def clean(text):
    text = text.replace("&", "and")
    text = BAD_FILENAME_CHARS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


# ----------------------------------------------------------------------------
# Processing
# ----------------------------------------------------------------------------
def process(src, outdir, args, make_zip):
    print(f"\n=== {src.name} ===")
    doc = pymupdf.open(src)
    rows, used = [], set()

    for i, page in enumerate(doc):
        if args.debug:
            print(f"  page {i + 1}:")
        number, name, job_no, how = read_title_block(
            page, args.right, args.bottom, debug=args.debug)
        if number:
            parts = [number]
            if args.job_in_name and job_no:
                parts.append(f"JOB {job_no}")
            if name:
                parts.append(name)
            base = clean(" - ".join(parts))
        else:
            base = f"page_{i + 1:02d}_UNKNOWN"
        fname, n = base, 2
        while fname.lower() in used:           # avoid overwriting duplicates
            fname, n = f"{base} ({n})", n + 1
        used.add(fname.lower())
        rows.append((i + 1, number or "", name, job_no, how, fname + ".pdf"))
        shown = f"{fname}.pdf   [{how}]"
        if job_no:
            shown += f"  JOB No. {job_no}"
        print(f"page {i + 1:>3}: {shown}")

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
        w.writerow(["page", "sheet_number", "sheet_name", "contractor_job_no",
                    "detected_by", "file"])
        w.writerows(rows)

    print(f"Saved {len(rows)} sheets to: {outdir}")

    if make_zip:
        zpath = outdir.parent / (outdir.name + ".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(outdir.iterdir()):
                z.write(p, p.name)
        print(f"Zip created: {zpath}")

    missing = [r[0] for r in rows if not r[1]]
    if missing:
        print(f"WARNING: no sheet number found on pages {missing} "
              f"(scanned? try --right/--bottom, or OCR).", file=sys.stderr)

    missing_job = [r[0] for r in rows if not r[3]]
    if missing_job:
        print(f"NOTE: no CONTRACTOR JOB No. found on pages {missing_job}.",
              file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=None,
                    help="folder containing the binder PDF(s), or a PDF file")
    ap.add_argument("-o", "--outdir", default=None,
                    help="parent folder for results (default: next to the PDF)")
    ap.add_argument("--right", type=float, default=0.20)
    ap.add_argument("--bottom", type=float, default=0.40)
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--job-in-name", action="store_true",
                    help="include the CONTRACTOR JOB No. in each output filename")
    ap.add_argument("--debug", action="store_true",
                    help="print diagnostic info for job-number extraction")
    args = ap.parse_args()

    interactive = args.path is None
    if interactive:
        target = ask_folder()
    else:
        target = Path(args.path.strip('"').strip("'")).expanduser()

    if target.is_dir():
        pdfs = choose_pdfs(target)
    elif target.is_file() and target.suffix.lower() == ".pdf":
        pdfs = [target]
    else:
        sys.exit(f"Not a PDF or folder: {target}")

    make_zip = args.zip
    if interactive and not args.dry_run and not args.zip:
        make_zip = ask_yes_no("Also create a .zip of the split sheets?", True)

    for pdf in pdfs:
        parent = Path(args.outdir).expanduser() if args.outdir else pdf.parent
        process(pdf, parent / f"{pdf.stem} - split sheets", args, make_zip)


if __name__ == "__main__":
    main()