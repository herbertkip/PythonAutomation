#!/usr/bin/env python3
"""
consolidate_drawings.py

Recursively walks a user-specified source directory, creates a
'DRAWINGS FOLDER' inside it, and copies every file into that folder.
When duplicate filenames are encountered, the file with the most
recent modification time wins.

Author: Senior Automation Engineer
Python: 3.8+
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

# ----------------------------- CONFIGURATION ----------------------------- #

TARGET_FOLDER_NAME = "DRAWINGS FOLDER"
SKIP_FOLDERS = {"$RECYCLE.BIN", "System Volume Information", ".git", "__pycache__"}

# ------------------------------- LOGGING --------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("consolidate")


# ------------------------------ HELPERS ---------------------------------- #

def prompt_for_source_folder() -> Path:
    """Prompt the user for the source folder location and validate it."""
    while True:
        raw = input("Enter the folder location to scan: ").strip().strip('"').strip("'")
        if not raw:
            print("  [!] No input provided. Please try again.")
            continue

        path = Path(raw).expanduser().resolve()
        if not path.exists():
            print(f"  [!] Path does not exist: {path}")
            continue
        if not path.is_dir():
            print(f"  [!] Path is not a directory: {path}")
            continue
        return path


def is_hidden(path: Path) -> bool:
    """Cross-platform hidden-file check (dotfiles + Windows hidden attribute)."""
    name = path.name
    if name.startswith("."):
        return True
    if os.name == "nt":
        try:
            attrs = os.stat(path).st_file_attributes  # type: ignore[attr-defined]
            return bool(attrs & 0x2)  # FILE_ATTRIBUTE_HIDDEN
        except (AttributeError, OSError):
            return False
    return False


def get_mtime(path: Path) -> float:
    """Return the last-modified timestamp, tolerating I/O errors."""
    try:
        return path.stat().st_mtime
    except OSError as exc:
        log.warning("Could not stat %s: %s", path, exc)
        return 0.0


def unique_destination(dest: Path) -> Path:
    """Return a non-colliding path by appending ' (n)' before the extension."""
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# --------------------------- CORE OPERATION ------------------------------ #

def consolidate(source_root: Path) -> None:
    """
    Walk `source_root`, create the target folder, and copy files with
    latest-modified-wins collision handling.
    """
    target_dir = source_root / TARGET_FOLDER_NAME

    # Sanity check: ensure we aren't re-ingesting our own output.
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        log.error("Unable to create target folder %s: %s", target_dir, exc)
        sys.exit(1)

    log.info("Source root : %s", source_root)
    log.info("Target dir  : %s", target_dir)

    # Map: lowercase filename -> (Path to currently-winning source, mtime)
    winners: Dict[str, Tuple[Path, float]] = {}
    skipped_self = 0
    total_seen = 0

    # ---- Pass 1: discover files, decide the winner for each name ----
    for dirpath, dirnames, filenames in os.walk(source_root):
        current = Path(dirpath).resolve()

        # Don't descend into the target folder or system folders.
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_FOLDERS and (current / d).resolve() != target_dir
        ]

        if current == target_dir:
            continue  # already handled by dirnames pruning, but belt & braces

        for fname in filenames:
            src = current / fname

            # Skip symlinks to avoid copying outside the tree accidentally.
            if src.is_symlink():
                log.debug("Skipping symlink: %s", src)
                continue

            if is_hidden(src):
                log.debug("Skipping hidden file: %s", src)
                continue

            total_seen += 1
            key = fname.lower()  # Windows-safe case-insensitive dedupe
            mtime = get_mtime(src)

            existing = winners.get(key)
            if existing is None:
                winners[key] = (src, mtime)
            else:
                prev_src, prev_mtime = existing
                if mtime > prev_mtime:
                    log.info(
                        "Replacing older duplicate '%s'\n    old: %s (%s)\n    new: %s (%s)",
                        fname,
                        prev_src, _fmt(prev_mtime),
                        src, _fmt(mtime),
                    )
                    winners[key] = (src, mtime)
                else:
                    log.info(
                        "Keeping existing '%s' (%s); ignoring %s (%s)",
                        fname, _fmt(prev_mtime), src, _fmt(mtime),
                    )

    log.info("Discovered %d file(s); %d unique name(s) to copy.",
             total_seen, len(winners))

    # ---- Pass 2: copy winners into the target folder ----
    copied, failed = 0, 0
    for key, (src, _) in winners.items():
        dest = target_dir / src.name

        # If a file with this name somehow already exists in target
        # (e.g. from a previous run), overwrite only if ours is newer;
        # otherwise give the newcomer a uniquified name.
        if dest.exists():
            dest_mtime = get_mtime(dest)
            if dest_mtime >= _:
                dest = unique_destination(dest)

        try:
            shutil.copy2(src, dest)  # copy2 preserves metadata
            copied += 1
            log.debug("Copied: %s -> %s", src, dest)
        except (OSError, shutil.Error) as exc:
            failed += 1
            log.error("Failed to copy %s -> %s: %s", src, dest, exc)

    log.info("Done. Copied %d file(s); %d failure(s).", copied, failed)
    log.info("Output folder: %s", target_dir)


def _fmt(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "n/a"


# -------------------------------- MAIN ----------------------------------- #

def main() -> int:
    print("=" * 62)
    print("  File Consolidator  ->  'DRAWINGS FOLDER'")
    print("  Duplicate names resolved by newest modification time.")
    print("=" * 62)

    try:
        source_root = prompt_for_source_folder()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted by user.")
        return 130

    confirm = input(f"Proceed with scan of:\n  {source_root}\n[y/N]: ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("Cancelled.")
        return 0

    try:
        consolidate(source_root)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())