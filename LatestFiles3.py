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
# Minimal ANSI palette (bold / dim + default fg only)
# ------------------------------------------------------------------
class C:
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"

    @staticmethod
    def disable():
        for k in list(vars(C)):
            if k.isupper() and isinstance(getattr(C, k), str):
                setattr(C, k, "")


if os.name == "nt":
    os.system("")
if not sys.stdout.isatty():
    C.disable()


def human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}" if unit != "B" else f"{n:,} B"
        n /= 1024
    return f"{n:,.1f} PB"


def bar(done, total, width=28):
    if total <= 0:
        return "█" * width
    filled = int(width * done / total)
    return "█" * filled + "·" * (width - filled)


# ------------------------------------------------------------------
# Core logic
# ------------------------------------------------------------------
def scan_tree(root_dir, exclude_dir):
    all_files = []
    latest = {}
    dup_counts = defaultdict(int)

    exclude_abs = os.path.abspath(exclude_dir) if exclude_dir else None

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

    for i, (full, mtime, size) in enumerate(all_files, 1):
        fname = os.path.basename(full)
        dup_counts[fname] += 1
        if fname not in latest or mtime > latest[fname][1]:
            latest[fname] = (full, mtime, size)

        if i % 25 == 0 or i == total:
            sys.stdout.write(f"\r  scanning {bar(i, total)}  {100*i/total:5.1f}%")
            sys.stdout.flush()
    print()

    return all_files, latest, dup_counts


def copy_files(latest, dest_dir):
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
                print(f"\n  ! {src}  ({e})")

        sys.stdout.write(f"\r  copying  {bar(i, total)}  {100*i/total:5.1f}%")
        sys.stdout.flush()
    print()
    return copied, failed, skipped, bytes_copied


# ------------------------------------------------------------------
# Reporting
# ------------------------------------------------------------------
def print_scan_report(all_files, latest, dup_counts, elapsed):
    total = len(all_files)
    total_size = sum(f[2] for f in all_files)
    dups = total - len(latest)
    dup_names = {k: v for k, v in dup_counts.items() if v > 1}

    print()
    print(f"{C.BOLD}Scan{C.RESET}")
    print(f"  files scanned      {total:,}")
    print(f"  data scanned       {human_size(total_size)}")
    print(f"  unique filenames   {len(latest):,}")
    print(f"  duplicate names    {len(dup_names):,}")
    print(f"  extra copies       {dups:,}  (skipped)")
    print(f"  time               {elapsed:.2f}s")

    if dup_names:
        print()
        print(f"{C.BOLD}Top duplicated names{C.RESET}")
        top = sorted(dup_names.items(), key=lambda kv: -kv[1])[:10]
        maxn = top[0][1]
        for name, count in top:
            shown = name if len(name) <= 42 else name[:39] + "..."
            bar_w = int(20 * count / maxn)
            print(f"  {count:>3}×  {shown:<45} {'█' * bar_w}")
        if len(dup_names) > 10:
            print(f"  {C.DIM}... and {len(dup_names) - 10:,} more{C.RESET}")

    ext_count = defaultdict(int)
    ext_size = defaultdict(int)
    for full, _m, size in all_files:
        ext = os.path.splitext(full)[1].lower() or "(none)"
        ext_count[ext] += 1
        ext_size[ext] += size

    if ext_count:
        print()
        print(f"{C.BOLD}File types{C.RESET}")
        top_ext = sorted(ext_count.items(), key=lambda kv: -kv[1])[:8]
        maxc = top_ext[0][1]
        for ext, count in top_ext:
            bar_w = int(20 * count / maxc)
            print(f"  {ext:<12} {'█' * bar_w:<20} {count:>6,}  {human_size(ext_size[ext])}")


def print_copy_report(copied, failed, skipped, bytes_copied, dest_dir, elapsed):
    print()
    print(f"{C.BOLD}Copy{C.RESET}")
    print(f"  copied             {copied:,}")
    print(f"  skipped            {skipped:,}")
    print(f"  failed             {failed:,}")
    print(f"  data written       {human_size(bytes_copied)}")
    print(f"  time               {elapsed:.2f}s")
    print()
    print(f"  {C.DIM}destination:{C.RESET} {dest_dir}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    print()
    raw = input("Folder to scan: ").strip().strip('"').strip("'")
    if not raw:
        print("No path entered.")
        sys.exit(1)

    src_dir = os.path.abspath(os.path.expanduser(raw))
    if not os.path.isdir(src_dir):
        print(f"Not a valid directory: {src_dir}")
        sys.exit(1)

    date_str = datetime.now().strftime("%m-%d-%y")
    dest_dir = os.path.join(src_dir, f"LATEST FILES - ({date_str})")

    print()
    print(f"source       {src_dir}")
    print(f"destination  {dest_dir}")
    print()

    t0 = time.time()
    all_files, latest, dup_counts = scan_tree(src_dir, exclude_dir=dest_dir)
    scan_elapsed = time.time() - t0

    if not all_files:
        print("\nNo files found.\n")
        sys.exit(0)

    print_scan_report(all_files, latest, dup_counts, scan_elapsed)

    os.makedirs(dest_dir, exist_ok=True)
    print()

    t1 = time.time()
    copied, failed, skipped, bytes_copied = copy_files(latest, dest_dir)
    copy_elapsed = time.time() - t1

    print_copy_report(copied, failed, skipped, bytes_copied, dest_dir, copy_elapsed)
    print(f"  {C.DIM}total time: {scan_elapsed + copy_elapsed:.2f}s{C.RESET}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted.\n")
        sys.exit(130)