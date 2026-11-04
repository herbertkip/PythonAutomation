#!/usr/bin/env python3
"""
Rename ASI drawing PDFs at the root level of a directory
to a clean "SHEETNO - SHEET NAME.pdf" format.

Only renames files located directly in the chosen directory
(NOT files inside subfolders like GROUPED/).
"""

import os
import re
import sys
from pathlib import Path

# Ordered list of (pattern_regex, replacement function) rules.
# Each pattern captures the sheet number and sheet name from the
# original filename.
RENAME_RULES = [
    # G-000-1 / G-000-2 / G-000-3 COVER SHEET
    (r"_(G-000-\d)\s*-\s*(COVER SHEET.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # G-001-1 / G-001-2 / G-001-3 SHEET INDEX
    (r"_(G-001-\d)\s*-\s*(SHEET INDEX.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # E-002 ELECTRICAL SCHEDULES
    (r"_(E-002)_(ELECTRICAL SCHEDULES)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # E-501 / E-503 / E-504 ELECTRICAL PANEL SCHEDULES
    (r"_(E-50[134])_(ELECTRICAL PANEL SCHEDULES)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-101 / A-102 PARTIAL BUILDING PLAN
    (r"_(A-10[12])\s*-\s*(PARTIAL BUILDING PLAN.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-200 EXTERIOR ELEVATIONS & NOTES
    (r"_(A-200)\s*-\s*(EXTERIOR ELEVATIONS.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-504 EXTERIOR AND INTERIOR WALL DETAILS
    (r"_(A-504)\s*-\s*(EXTERIOR AND INTERIOR WALL DETAILS.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # C-501 UTILITY PLAN - 1
    (r"_(C-501)\s*-\s*(UTILITY PLAN.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # C-302 SITE PLAN
    (r"_(C-302)\s*-\s*(SITE PLAN.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-400 / A-400B ENLARGED ...
    (r"_(A-400B?)\s*-\s*(ENLARGED.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-404 ENLARGED REMOTE RESTROOM PLANS AND ELEVS
    (r"_(A-404)\s*-\s*(ENLARGED REMOTE RESTROOM PLANS AND ELEVS.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-507 CANOPY DETAILS
    (r"_(A-507)\s*-\s*(CANOPY DETAILS.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # E-300 ENLARGED POWER PLANS
    (r"_(E-300)_(ENLARGED POWER PLANS.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-600 DOOR - WINDOW SCHEDULES
    (r"_(A-600)\s*-\s*(DOOR - WINDOW SCHEDULES.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # A-601 DOOR HARDWARE SETS
    (r"_(A-601)\s*-\s*(DOOR HARDWARE SETS.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),

    # C-401 GRADING AND DRAINAGE-1
    (r"_(C-401)\s+(GRADING AND DRAINAGE.*?)_\d{4}\.\d{2}\.\d{2}\.pdf$",
     lambda m: f"{m.group(1)} - {m.group(2).strip()}.pdf"),
]


def determine_new_name(filename: str) -> str | None:
    """Return the new filename for a recognized drawing PDF, else None."""
    for pattern, make_name in RENAME_RULES:
        match = re.search(pattern, filename, flags=re.IGNORECASE)
        if match:
            new_name = make_name(match)
            # sanitize path-illegal characters just in case
            new_name = new_name.replace("/", "-").replace("\\", "-")
            return new_name
    return None


def main():
    # Prompt for directory
    default_dir = r"C:\Users\hchepsoy\Downloads\ASI 1 - 10-27-26"
    prompt = f"Enter the directory containing the drawing PDFs\n[{default_dir}]: "
    user_input = input(prompt).strip().strip('"').strip("'")
    directory = Path(user_input) if user_input else Path(default_dir)

    if not directory.is_dir():
        print(f"ERROR: '{directory}' is not a valid directory.")
        sys.exit(1)

    # Only files DIRECTLY in the target directory (skip subfolders)
    pdf_files = sorted(
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        print(f"No PDF files found directly in '{directory}'.")
        sys.exit(0)

    print(f"\nScanning {len(pdf_files)} PDF file(s) in:\n  {directory}\n")

    planned = []          # (old_path, new_path)
    unmatched = []

    for pdf in pdf_files:
        new_name = determine_new_name(pdf.name)
        if new_name is None:
            unmatched.append(pdf.name)
            continue
        new_path = directory / new_name
        if new_path == pdf:
            # Already correctly named; skip.
            continue
        planned.append((pdf, new_path))

    # Report planned renames
    if planned:
        print("Planned renames:")
        for old, new in planned:
            print(f"  {old.name}")
            print(f"    -> {new.name}")
    else:
        print("No renames needed — all recognized files already have clean names.")

    if unmatched:
        print("\nUnrecognized files (left untouched):")
        for name in unmatched:
            print(f"  {name}")

    if not planned:
        return

    # Check for collisions
    collisions = [
        new for _, new in planned
        if new.exists() and new not in {old for old, _ in planned}
    ]
    if collisions:
        print("\nERROR: The following target filenames already exist:")
        for c in collisions:
            print(f"  {c.name}")
        print("Aborting — no files were renamed.")
        sys.exit(1)

    # Confirm
    confirm = input("\nProceed with renaming? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Aborted. No files were renamed.")
        return

    # Perform renames
    renamed, failed = 0, 0
    for old, new in planned:
        try:
            old.rename(new)
            renamed += 1
        except OSError as e:
            failed += 1
            print(f"FAILED: {old.name} -> {new.name}  ({e})")

    print(f"\nDone. Renamed: {renamed}  |  Failed: {failed}  |  Skipped (unrecognized): {len(unmatched)}")


if __name__ == "__main__":
    main()