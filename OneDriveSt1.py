import os
import shutil
import sys
import subprocess
import importlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Auto-fix: try to make 'steamlite' available without crashing the script.
# ---------------------------------------------------------------------------
def _load_steamlite():
    """
    Try to import steamlite. If missing, attempt a pip install once.
    Returns the module or None (never raises).
    """
    # 1) Already importable?
    try:
        return importlib.import_module("steamlite")
    except ImportError:
        pass

    # 2) Attempt a quiet pip install, then retry the import
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "steamlite"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        importlib.invalidate_caches()
        return importlib.import_module("steamlite")
    except Exception:
        # Install failed (not on PyPI, no network, etc.) — silently give up.
        return None


steamlite = _load_steamlite()


def get_base_path():
    """Resolve the base folder: steamlite first, then OneDrive, then fallback."""
    # 1) steamlite (probe common API shapes, ignore failures)
    if steamlite is not None:
        try:
            for attr in ("get_base_path", "get_steam_path",
                         "get_library_path", "base_path"):
                if hasattr(steamlite, attr):
                    value = getattr(steamlite, attr)
                    path = value() if callable(value) else value
                    if path and os.path.exists(str(path)):
                        return str(path)
            if hasattr(steamlite, "config"):
                cfg = steamlite.config
                for key in ("base_path", "root", "library"):
                    if isinstance(cfg, dict) and cfg.get(key) \
                            and os.path.exists(cfg[key]):
                        return cfg[key]
        except Exception:
            pass  # Any steamlite error → fall through to OneDrive

    # 2) OneDrive env vars
    onedrive_env = os.environ.get("OneDrive") or os.environ.get("OneDriveCommercial")
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
    print("Folder Copy Utility")
    print("=" * 70)
    print(f"steamlite available: {'yes' if steamlite else 'no (using OneDrive)'}")
    print()

    source_link = input("Paste the source folder path/link: ").strip().strip('"')
    source_path = source_link.replace("/", "\\")

    if not os.path.isdir(source_path):
        print(f"Error: Source path does not exist or is not a directory:\n  {source_path}")
        return

    folder_number = input("Enter folder number/prefix (e.g., 100): ").strip()
    if not folder_number:
        print("Error: Folder number cannot be empty.")
        return

    folder_name = Path(source_path).name
    new_folder_name = f"{folder_number} - {folder_name}"

    base_path = get_base_path()
    print(f"\nBase path:     {base_path}")
    print(f"Outer folder:  {new_folder_name}")
    print(f"Inner folder:  {folder_name}")

    destination = os.path.join(base_path, new_folder_name)

    if os.path.exists(destination):
        overwrite = input(f"\nDestination exists:\n  {destination}\nOverwrite? (y/n): ").strip().lower()
        if overwrite != "y":
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