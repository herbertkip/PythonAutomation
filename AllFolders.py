import os
import shutil
import sys


def get_all_folders(root_dir, exclude_dir=None):
    """
    Walk root_dir (and all subfolders) and return a sorted list of
    absolute paths to every subfolder found.

    The root_dir itself is NOT included, and individual files are
    ignored entirely. If exclude_dir is provided, it (and its
    descendants) are skipped during the walk so a previous
    destination folder isn't re-scanned on repeat runs.
    """
    folders = []
    exclude_dir = os.path.abspath(exclude_dir) if exclude_dir else None
    root_dir = os.path.abspath(root_dir)

    for dirpath, dirnames, _filenames in os.walk(root_dir):
        # Prune the destination folder so we don't re-scan it
        if exclude_dir:
            dirnames[:] = [
                d for d in dirnames
                if os.path.abspath(os.path.join(dirpath, d)) != exclude_dir
            ]

        for d in dirnames:
            full_path = os.path.abspath(os.path.join(dirpath, d))
            if full_path == root_dir:
                continue
            folders.append(full_path)

    folders.sort()
    return folders


def get_unique_dest(dest_root, folder_name):
    """
    Return a non-existent destination path inside dest_root for a folder
    named folder_name, avoiding collisions with real folders already
    present in dest_root.

    Strategy:
      1. Try the plain name.
      2. Try name_1, name_2, name_3, ... until a free numeric slot.
      3. If the numeric slots are saturated (e.g. real folders named
         'name_1', 'name_2', ... already exist in the destination),
         fall back to growing the base name with '+': name+, name++,
         name+++, etc.
    """
    plain = os.path.join(dest_root, folder_name)
    if not os.path.exists(plain):
        return plain

    n = 1
    while True:
        numbered = os.path.join(dest_root, f"{folder_name}_{n}")
        if not os.path.exists(numbered):
            return numbered
        n += 1
        # Safety valve: stop scanning numeric slots after a sane limit
        # and switch to '+' growth so we can't loop forever.
        if n > 1000:
            break

    plus = plain
    while os.path.exists(plus):
        plus = plus + "+"
    return plus


def main():
    raw = input("Enter the folder path to scan: ").strip().strip('"').strip("'")
    src_dir = os.path.abspath(os.path.expanduser(raw))

    if not os.path.isdir(src_dir):
        print(f"Error: '{src_dir}' is not a valid directory.")
        sys.exit(1)

    dest_dir = os.path.join(src_dir, "All Folders")

    print(f"\nScanning: {src_dir}")
    folders = get_all_folders(src_dir, exclude_dir=dest_dir)
    print(f"Found {len(folders)} subfolder(s).")

    os.makedirs(dest_dir, exist_ok=True)

    copied = 0
    failed = 0
    for folder_path in folders:
        folder_name = os.path.basename(folder_path)
        target = get_unique_dest(dest_dir, folder_name)

        if os.path.abspath(folder_path) == os.path.abspath(target):
            continue

        try:
            shutil.copytree(folder_path, target)
            copied += 1
            print(f"  + {folder_path}  ->  {target}")
        except (OSError, shutil.Error) as e:
            print(f"  ! Failed to copy '{folder_path}': {e}")
            failed += 1

    print("\n--- Done ---")
    print(f"Destination folder : {dest_dir}")
    print(f"Folders copied     : {copied}")
    if failed:
        print(f"Folders failed     : {failed}")


if __name__ == "__main__":
    main()