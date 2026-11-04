import os
import shutil
import sys
from datetime import datetime


def get_latest_files(root_dir, exclude_dir=None):
    """
    Walk root_dir (and all subfolders) and return a dict:
        filename -> (full_path, mtime)
    keeping only the most recently modified file for each unique filename.
    """
    latest = {}
    exclude_dir = os.path.abspath(exclude_dir) if exclude_dir else None

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip the destination folder so we don't re-scan it on repeat runs
        if exclude_dir:
            dirnames[:] = [
                d for d in dirnames
                if os.path.abspath(os.path.join(dirpath, d)) != exclude_dir
            ]

        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            try:
                mtime = os.path.getmtime(full_path)
            except OSError:
                continue  # unreadable / broken symlink etc.

            if fname not in latest or mtime > latest[fname][1]:
                latest[fname] = (full_path, mtime)

    return latest


def main():
    raw = input("Enter the folder path to scan: ").strip().strip('"').strip("'")
    src_dir = os.path.abspath(os.path.expanduser(raw))

    if not os.path.isdir(src_dir):
        print(f"Error: '{src_dir}' is not a valid directory.")
        sys.exit(1)

    # Build the destination folder name: LATEST FILES - (MM-DD-YY)
    date_str = datetime.now().strftime("%m-%d-%y")
    dest_dir = os.path.join(src_dir, f"LATEST FILES - ({date_str})")

    print(f"\nScanning: {src_dir}")
    latest = get_latest_files(src_dir, exclude_dir=dest_dir)
    print(f"Found {len(latest)} unique filename(s).")

    os.makedirs(dest_dir, exist_ok=True)

    copied = 0
    failed = 0
    for fname, (full_path, _mtime) in latest.items():
        target = os.path.join(dest_dir, fname)

        # Don't copy a file onto itself
        if os.path.abspath(full_path) == os.path.abspath(target):
            continue

        try:
            shutil.copy2(full_path, target)  # copy2 preserves timestamps
            copied += 1
        except (OSError, shutil.Error) as e:
            print(f"  ! Failed to copy '{full_path}': {e}")
            failed += 1

    print("\n--- Done ---")
    print(f"Destination folder : {dest_dir}")
    print(f"Files copied       : {copied}")
    if failed:
        print(f"Files failed       : {failed}")


if __name__ == "__main__":
    main()