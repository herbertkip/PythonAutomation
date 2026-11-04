#!/usr/bin/env python3
"""
LATEST FILES COLLECTOR
Scans a directory tree, finds files sharing the exact same name,
and copies only the most recently modified one of each into a
dated 'LATEST FILES - (MM-DD-YY)' folder.
"""

import os
import sys
import time
import shutil
from datetime import datetime
from collections import defaultdict


# ------------------------------------------------------------------
# ANSI / terminal helpers
# ------------------------------------------------------------------
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_BLUE = "\033[44m"

    @staticmethod
    def disable():
        for k in list(vars(C)):
            if k.isupper():
                setattr(C, k, "")


# Enable ANSI on Windows 10+ terminals
if os.name == "nt":
    os.system("")
if not sys.stdout.isatty():
    C.disable()

TERM_W = shutil.get_terminal_size((100, 20)).columns


def hr(char="─", color=C.DIM):
    print(f"{color}{char * TERM_W}{C.RESET}")


def banner():
    title = "  LATEST FILES COLLECTOR  "
    pad = (TERM_W - len(title)) // 2
    print()
    print(f"{C.BG_BLUE}{C.WHITE}{C.BOLD}{' ' * TERM_W}{C.RESET}")
    print(f"{C.BG_BLUE}{C.WHITE}{C.BOLD}{' ' * max(0,pad)}{title}{C.RESET}")
    print(f"{C.BG_BLUE}{C.WHITE}{C.BOLD}{' ' * TERM_W}{C.RESET}")
    print(f"{C.DIM}  Deduplicate by exact filename · keep newest · copy to dated folder{C.RESET}")
    print()


def human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}" if unit != "B" else f"{n:,} B"
        n /= 1024
    return f"{n:,.1f} PB"


def bar(done, total, width=40, color=C.GREEN):
    if total <= 0:
        return f"{color}{'█' * width}{C.RESET}"
    filled = int(width * done / total)
    return f"{color}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.RESET}"


# ------------------------------------------------------------------
# Core logic
# ------------------------------------------------------------------
def scan_tree(root_dir, exclude_dir):
    """
    Walk the tree, return:
      all_files    : list of (full_path, mtime, size)
      latest       : dict filename -> (full_path, mtime, size)
      dup_counts   : dict filename -> number of occurrences
    """
    all_files = []
    latest = {}
    dup_counts = defaultdict(int)

    exclude_abs = os.path.abspath(exclude_dir) if exclude_dir else None

    # First pass: collect everything so we can show a progress bar
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if exclude_abs:
            dirnames[:] = [
                d for d in dirnames
                if os.path.abspath(os.path.join(dirpath, d)) != exclude_abs
            ]
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            try:
                st = os.stat(full)
            except OSError:
                continue
            all_files.append((full, st.st_mtime, st.st_size))

    total = len(all_files)
    if total == 0:
        return all_files, latest, dup_counts

    label = f"{C.CYAN}Scanning{C.RESET}"
    for i, (full, mtime, size) in enumerate(all_files, 1):
        fname = os.path.basename(full)
        dup_counts[fname] += 1
        if fname not in latest or mtime > latest[fname][1]:
            latest[fname] = (full, mtime, size)

        if i % 25 == 0 or i == total:
            pct = 100 * i / total
            sys.stdout.write(
                f"\r  {label}  {bar(i, total, 30)} {pct:5.1f}%  "
                f"{C.DIM}{i:,}/{total:,}{C.RESET}  "
            )
            sys.stdout.flush()
    print()

    return all_files, latest, dup_counts


def copy_files(latest, dest_dir):
    """Copy newest file of each name. Returns (copied, failed, skipped, bytes)."""
    total = len(latest)
    copied = failed = skipped = 0
    bytes_copied = 0

    if total == 0:
        return copied, failed, skipped, bytes_copied

    for i, (fname, (src, _mtime, size)) in enumerate(sorted(latest.items()), 1):
        target = os.path.join(dest_dir, fname)

        if os.path.abspath(src) == os.path.abspath(target):
            skipped += 1
        else:
            try:
                shutil.copy2(src, target)
                copied += 1
                bytes_copied += size
            except (OSError, shutil.Error) as e:
                failed += 1
                print(f"\n  {C.RED}✗{C.RESET} {src}  {C.DIM}({e}){C.RESET}")

        pct = 100 * i / total
        sys.stdout.write(
            f"\r  {C.MAGENTA}Copying {C.RESET}  {bar(i, total, 30, C.MAGENTA)} "
            f"{pct:5.1f}%  {C.DIM}{i:,}/{total:,}{C.RESET}  "
        )
        sys.stdout.flush()
    print()
    return copied, failed, skipped, bytes_copied


# ------------------------------------------------------------------
# Reporting
# ------------------------------------------------------------------
def section(title):
    print()
    print(f"{C.BOLD}{C.BLUE}▎{C.RESET} {C.BOLD}{title}{C.RESET}")
    hr("·")


def stat_line(label, value, value_color=C.WHITE):
    print(f"  {C.DIM}{label:<26}{C.RESET}{value_color}{value}{C.RESET}")


def print_scan_report(all_files, latest, dup_counts, elapsed):
    total = len(all_files)
    total_size = sum(f[2] for f in all_files)
    dups = total - len(latest)
    dup_names = {k: v for k, v in dup_counts.items() if v > 1}

    section("SCAN RESULTS")
    stat_line("Files scanned",        f"{total:,}", C.CYAN)
    stat_line("Total data scanned",   human_size(total_size), C.CYAN)
    stat_line("Unique filenames",     f"{len(latest):,}", C.GREEN)
    stat_line("Duplicate filenames",  f"{len(dup_names):,}", C.YELLOW if dup_names else C.GREEN)
    stat_line("Extra copies skipped", f"{dups:,}", C.YELLOW if dups else C.GREEN)
    stat_line("Scan time",            f"{elapsed:.2f}s", C.DIM + C.WHITE)

    # Top duplicated filenames
    if dup_names:
        section("TOP DUPLICATED NAMES")
        top = sorted(dup_names.items(), key=lambda kv: -kv[1])[:10]
        maxn = top[0][1]
        for name, count in top:
            shown = name if len(name) <= 42 else name[:39] + "..."
            bar_w = int(28 * count / maxn)
            print(f"  {C.YELLOW}{count:>3}×{C.RESET}  "
                  f"{shown:<45} "
                  f"{C.YELLOW}{'█' * bar_w}{C.RESET}")
        if len(dup_names) > 10:
            print(f"  {C.DIM}... and {len(dup_names) - 10:,} more{C.RESET}")

    # Extension breakdown
    ext_size = defaultdict(int)
    ext_count = defaultdict(int)
    for full, _m, size in all_files:
        ext = os.path.splitext(full)[1].lower() or "(no ext)"
        ext_size[ext] += size
        ext_count[ext] += 1

    if ext_count:
        section("FILE TYPES")
        top_ext = sorted(ext_count.items(), key=lambda kv: -kv[1])[:8]
        maxc = top_ext[0][1]
        for ext, count in top_ext:
            bar_w = int(28 * count / maxc)
            print(f"  {C.CYAN}{ext:<12}{C.RESET} "
                  f"{bar(count, maxc, 28, C.CYAN)} "
                  f"{count:>6,}  {C.DIM}{human_size(ext_size[ext])}{C.RESET}")


def print_copy_report(copied, failed, skipped, bytes_copied, dest_dir, elapsed):
    section("COPY SUMMARY")
    stat_line("Files copied",   f"{copied:,}",  C.GREEN)
    stat_line("Files skipped",  f"{skipped:,}", C.DIM + C.WHITE)
    stat_line("Files failed",   f"{failed:,}",  C.RED if failed else C.GREEN)
    stat_line("Data written",   human_size(bytes_copied), C.GREEN)
    stat_line("Copy time",      f"{elapsed:.2f}s", C.DIM + C.WHITE)

    print()
    print(f"  {C.BOLD}{C.GREEN}✔ Destination{C.RESET}")
    print(f"  {C.DIM}{dest_dir}{C.RESET}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    banner()

    raw = input(f"  {C.BOLD}Folder to scan:{C.RESET} ").strip().strip('"').strip("'")
    if not raw:
        print(f"  {C.RED}✗ No path entered.{C.RESET}\n")
        sys.exit(1)

    src_dir = os.path.abspath(os.path.expanduser(raw))
    if not os.path.isdir(src_dir):
        print(f"  {C.RED}✗ Not a valid directory:{C.RESET} {src_dir}\n")
        sys.exit(1)

    date_str = datetime.now().strftime("%m-%d-%y")
    dest_dir = os.path.join(src_dir, f"LATEST FILES - ({date_str})")

    print(f"  {C.DIM}Source:{C.RESET}      {src_dir}")
    print(f"  {C.DIM}Destination:{C.RESET} {dest_dir}")
    print()

    t0 = time.time()
    all_files, latest, dup_counts = scan_tree(src_dir, exclude_dir=dest_dir)
    scan_elapsed = time.time() - t0

    if not all_files:
        print(f"\n  {C.YELLOW}No files found to process.{C.RESET}\n")
        sys.exit(0)

    print_scan_report(all_files, latest, dup_counts, scan_elapsed)

    os.makedirs(dest_dir, exist_ok=True)
    print()

    t1 = time.time()
    copied, failed, skipped, bytes_copied = copy_files(latest, dest_dir)
    copy_elapsed = time.time() - t1

    print_copy_report(copied, failed, skipped, bytes_copied, dest_dir, copy_elapsed)

    print()
    hr("═", C.GREEN)
    print(f"  {C.BOLD}{C.GREEN}DONE{C.RESET}  "
          f"{C.DIM}total time {scan_elapsed + copy_elapsed:.2f}s{C.RESET}")
    hr("═", C.GREEN)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Interrupted by user.{C.RESET}\n")
        sys.exit(130)