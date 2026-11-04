import os
import shutil
from pathlib import Path

try:
    import steamlite
except ImportError:
    steamlite = None


def get_steamlite_base_path():
    """Resolve the base path using steamlite, falling back to OneDrive/env vars."""
    # 1) Try steamlite (adjust API as needed)
    if steamlite is not None:
        # Common possibilities — try a few in order:
        for attr in ("get_base_path", "get_steam_path", "get_library_path", "base_path"):
            if hasattr(steamlite, attr):
                value = getattr(steamlite, attr)
                path = value() if callable(value) else value
                if path and os.path.exists(path):
                    return str(path)

        # Or if steamlite exposes a config/dict
        if hasattr(steamlite, "config"):
            cfg = steamlite.config
            for key in ("base_path", "root", "library"):
                if isinstance(cfg, dict) and cfg.get(key) and os.path.exists(cfg[key]):
                    return cfg[key]

    # 2) Fall back to OneDrive env vars
    onedrive_env = os.environ.get('OneDrive') or os.environ.get('OneDriveCommercial')
    if onedrive_env and os.path.exists(onedrive_env):
        return onedrive_env

    # 3) Hardcoded fallback
    fallback = r"C:\Users\hchepsoy\OneDrive - McCombs Steel Company, INC"
    if os.path.exists(fallback):
        return fallback

    raise FileNotFoundError("Could not locate a valid base folder (steamlite/OneDrive).")


def copy_folder_contents(source, destination):
    """Recursively copy contents of source into destination."""
    if not os.path.exists(destination):
        os.makedirs(destination)

    for item in os.listdir(source):
        src_item = os.path.join(source, item)
        dst_item = os.path.join(destination, item)

        if os.path.isdir(src_item):
            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            print(f"  Copied directory: {item}")
        else:
            shutil.copy2(src_item, dst_item)
            print(f"  Copied file: {item}")


def main():
    print("=" * 70)
    print("Folder Copy Utility (steamlite)")
    print("=" * 70)

    if steamlite is None:
        print("Warning: 'steamlite' module not found — falling back to OneDrive paths.\n")

    source_link = input("Paste the source folder path/link: ").strip().strip('"')
    source_path = source_link.replace('/', '\\')

    if not os.path.isdir(source_path):
        print(f"Error: Source path does not exist or is not a directory:\n  {source_path}")
        return

    folder_number = input("Enter folder number/prefix (e.g., 100): ").strip()
    if not folder_number:
        print("Error: Folder number cannot be empty.")
        return

    folder_name = Path(source_path).name
    new_folder_name = f"{folder_number} - {folder_name}"

    base_path = get_steamlite_base_path()
    print(f"\nBase path:     {base_path}")
    print(f"Outer folder:  {new_folder_name}")
    print(f"Inner folder:  {folder_name}")

    destination = os.path.join(base_path, new_folder_name)

    if os.path.exists(destination):
        overwrite = input(f"\nDestination exists:\n  {destination}\nOverwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Aborted.")
            return
        shutil.rmtree(destination)

    print(f"\nCreating outer folder:\n  {destination}")
    os.makedirs(destination, exist_ok=True)

    inner_folder = os.path.join(destination, folder_name)
    print(f"\nCopying contents into:\n  {inner_folder}\n")
    copy_folder_contents(source_path, inner_folder)

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()