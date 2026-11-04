#!/usr/bin/env python3
"""
collect_field_drawings.py

Scans a folder and all of its subfolders, looks only at files that live inside
a folder whose name contains the word "FIELD" (any case: Field, field, FIELD,
"As-Built Field Markups", etc.), finds files that share the same file name,
keeps only the most recently modified copy of each, and copies those files
into a new folder named:

    FIELD DRAWINGS - (MM-DD-YY)      e.g.  FIELD DRAWINGS - (09-24-26)

The new folder is created inside the folder being scanned.

Which files are checked
-----------------------
A file is checked if ANY folder between the scanned root and the file has
"field" in its name. That includes files in subfolders of a FIELD folder
(e.g. ...\\Project A\\FIELD\\Rev2\\plan.pdf is checked).
The name of the root folder you type in is not used for matching, only the
folders beneath it.

Uniqueness rule
---------------
Two files are considered the "same drawing" if they have the same file name
(case-insensitive, extension included), regardless of which FIELD folder they
live in. The copy with the newest modified time wins.

Notes
-----
* Original files are never moved, changed or deleted.
* Any existing "FIELD DRAWINGS - (...)" folders are skipped while scanning
  (even though their names contain "FIELD"), so re-runs never pick up earlier
  output.
* shutil.copy2 is used so copied files keep their original modified time.
* If the output folder already exists (script re-run on the same day), its
  files are overwritten with the newest versions found.
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

KEYWORD = "field"                       # matched case-insensitively
OUTPUT_PREFIX = "FIELD DRAWINGS - "


def prompt_for_directory() -> Path:
    """Ask the user for a folder path until a valid one is given."""
    while True:
        raw = input("Enter the full path of the folder to check: ").strip()
        # Remove quotes that appear when pasting "Copy as path" in Windows
        raw = raw.strip('"').strip("'")
        if not raw:
            print("  ! No path entered. Please try again.\n")
            continue

        path = Path(raw).expanduser()
        if path.is_dir():
            return path.resolve()
        print(f"  ! '{raw}' is not a valid folder. Please try again.\n")


def is_output_folder(folder_name: str) -> bool:
    """True for any folder created by this script (current or past runs)."""
    return folder_name.upper().startswith(OUTPUT_PREFIX.upper())


def has_field_folder(folder_parts) -> bool:
    """True if any folder name in the given parts contains the keyword."""
    return any(KEYWORD in part.lower() for part in folder_parts)


def find_latest_files(root: Path) -> tuple[dict, int, list, set]:
    """
    Walk `root` recursively and return:
      latest   - {lower-case filename: (Path, mtime)} newest copy of each name
      total    - number of files examined (inside FIELD folders only)
      errors   - list of (path, error message) for unreadable files
      folders  - set of FIELD-related folders that contained files
    """
    latest: dict[str, tuple[Path, float]] = {}
    total = 0
    errors: list[tuple[Path, str]] = []
    folders: set[Path] = set()

    # Sorted for deterministic results when two files share the same mtime
    for path in sorted(root.rglob("*")):
        folder_parts = path.relative_to(root).parts[:-1]

        # Skip anything inside a previous "FIELD DRAWINGS" output folder
        if any(is_output_folder(part) for part in folder_parts):
            continue
        # Only look at files that sit inside a folder named with "FIELD"
        if not has_field_folder(folder_parts):
            continue
        if not path.is_file():
            continue

        try:
            mtime = path.stat().st_mtime
        except OSError as exc:
            errors.append((path, str(exc)))
            continue

        total += 1
        folders.add(path.parent)
        key = path.name.lower()
        current = latest.get(key)
        if current is None or mtime > current[1]:
            latest[key] = (path, mtime)

    return latest, total, errors, folders


def main() -> int:
    print("=" * 60)
    print(" FIELD DRAWINGS COLLECTOR")
    print("=" * 60)

    root = prompt_for_directory()

    # Folder name, e.g. "FIELD DRAWINGS - (09-24-26)"
    today = datetime.now().strftime("%m-%d-%y")
    dest = root / f"{OUTPUT_PREFIX}({today})"

    print(f"\nScanning: {root}")
    print(f"Looking in folders with '{KEYWORD.upper()}' in the name (any case)...")
    latest, total, errors, folders = find_latest_files(root)

    if not latest:
        print("\nNo files found inside any FIELD folder. Nothing to copy.")
        return 0

    dest.mkdir(exist_ok=True)
    print(f"Output  : {dest}")
    print(f"FIELD folders with files: {len(folders)}\n")

    copied = 0
    for path, mtime in sorted(latest.values(), key=lambda item: item[0].name.lower()):
        target = dest / path.name
        try:
            shutil.copy2(path, target)
            copied += 1
            stamp = datetime.fromtimestamp(mtime).strftime("%m-%d-%y %H:%M")
            print(f"  Copied: {path.name}  (modified {stamp})")
            print(f"          from {path.parent}")
        except (OSError, shutil.Error) as exc:
            errors.append((path, str(exc)))

    print("\n" + "-" * 60)
    print(f"Files examined (in FIELD folders): {total}")
    print(f"Unique file names                : {len(latest)}")
    print(f"Older duplicates skipped         : {total - len(latest)}")
    print(f"Files copied                     : {copied}")
    if errors:
        print(f"\nProblems ({len(errors)}):")
        for path, msg in errors:
            print(f"  ! {path}: {msg}")
    print("-" * 60)
    print("Done.")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        sys.exit(130)