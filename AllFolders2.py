import os
import shutil
import sys


def get_file_bearing_folders(root_dir, exclude_dir=None):
    """
    Walk root_dir (and all subfolders) and return a sorted list of
    absolute paths to every folder that directly contains at least
    one file.

    Folders that contain only subfolders (no files of their own) are
    excluded. Individual files are never returned — only the folders
    that hold them. If exclude_dir is provided, it (and its
    descendants) are skipped so a previous destination isn't
    re-scanned on repeat runs.
    """
    folders = []
    exclude_dir = os.path.abspath(exclude_dir) if exclude_dir else None
    root_dir = os.path.abspath(root_dir)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        if exclude_dir:
            dirnames[:] = [
                d for d in dirnames
                if os.path.abspath(os.path.join(dirpath, d)) != exclude_dir
            ]

        # Only keep folders that have at least one file directly inside
        if filenames and os.path.abspath(dirpath) != root_dir:
            folders.append(os.path.abspath(dirpath))

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
      3. If the numeric slots are saturated, grow the base name with
         '+' (name+, name++, ...) until free.
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
        if n > 1000:
            break

    plus = plain
    while os.path.exists(plus):
        plus = plus + "+"
    return plus


def copy_folder_files_only(src_folder, dest_folder):
    """
    Copy only the files directly inside src_folder into dest_folder.
    Subfolders are NOT copied — they live at the top level of
    'All Folders' as their own entries.
    """
    os.makedirs(dest_folder, exist_ok=True)
    for entry in os.listdir(src_folder):
        src_path = os.path.join(src_folder, entry)
        if os.path.isfile(src_path) or os.path.islink(src_path):
            shutil.copy2(src_path, os.path.join(dest_folder, entry))


def main():
    raw = input("Enter the folder path to scan: ").strip().strip('"').strip("'")
    src_dir = os.path.abspath(os.path.expanduser(raw))

    if not os.path.isdir(src_dir):
        print(f"Error: '{src_dir}' is not a valid directory.")
        sys.exit(1)

    dest_dir = os.path.join(src_dir, "All Folders")

    print(f"\nScanning: {src_dir}")
    folders = get_file_bearing_folders(src_dir, exclude_dir=dest_dir)
    print(f"Found {len(folders)} folder(s) containing files.")

    os.makedirs(dest_dir, exist_ok=True)

    copied = 0
    failed = 0
    for folder_path in folders:
        folder_name = os.path.basename(folder_path)
        target = get_unique_dest(dest_dir, folder_name)

        if os.path.abspath(folder_path) == os.path.abspath(target):
            continue

        try:
            copy_folder_files_only(folder_path, target)
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