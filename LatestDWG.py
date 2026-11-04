#!/usr/bin/env python3
"""
collect_latest_drawings.py

Scans a folder and all of its subfolders, finds files that share the same
file name, keeps only the most recently modified copy of each, and copies
those "latest" files into a new folder named:

    LATEST DRAWINGS - (MM-DD-YY)      e.g.  LATEST DRAWINGS - (09-24-26)

The new folder is created inside the folder being scanned.

Uniqueness rule
---------------
Two files are considered the "same drawing" if they have the same file name
(case-insensitive, extension included), regardless of which subfolder they
live in. The copy with the newest modified time wins.

Notes
-----
* Original files are never moved, changed or deleted.
* Any existing "LATEST DRAWINGS - (...)" folders are skipped while scanning,
  so re-running the script never picks up its own (or earlier) output.
* shutil.copy2 is used so the copied file keeps its original modified time.
* If the output folder already exists (script re-run on the same day), its
  files are overwritten with the newest versions found.
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_PREFIX = "LATEST DRAWINGS - "


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


def find_latest_files(root: Path) -> tuple[dict, int, list]:
    """
    Walk `root` recursively and return:
      latest   - {lower-case filename: (Path, mtime)} for the newest copy
      total    - total number of files examined
      errors   - list of (path, error message) for unreadable files
    """
    latest: dict[str, tuple[Path, float]] = {}
    total = 0
    errors: list[tuple[Path, str]] = []

    # Sorted for deterministic results when two files share the same mtime
    for path in sorted(root.rglob("*")):
        # Skip anything located inside a previous "LATEST DRAWINGS" folder
        if any(is_output_folder(part) for part in path.relative_to(root).parts[:-1]):
            continue
        if not path.is_file():
            continue

        try:
            mtime = path.stat().st_mtime
        except OSError as exc:
            errors.append((path, str(exc)))
            continue

        total += 1
        key = path.name.lower()
        current = latest.get(key)
        if current is None or mtime > current[1]:
            latest[key] = (path, mtime)

    return latest, total, errors


def main() -> int:
    print("=" * 60)
    print(" LATEST DRAWINGS COLLECTOR")
    print("=" * 60)

    root = prompt_for_directory()

    # Folder name, e.g. "LATEST DRAWINGS - (09-24-26)"
    today = datetime.now().strftime("%m-%d-%y")
    dest = root / f"{OUTPUT_PREFIX}({today})"

    print(f"\nScanning: {root}")
    latest, total, errors = find_latest_files(root)

    if not latest:
        print("No files found. Nothing to copy.")
        return 0

    dest.mkdir(exist_ok=True)
    print(f"Output  : {dest}\n")

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
    print(f"Files examined        : {total}")
    print(f"Unique file names     : {len(latest)}")
    print(f"Older duplicates skipped: {total - len(latest)}")
    print(f"Files copied          : {copied}")
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