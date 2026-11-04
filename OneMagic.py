import os
import shutil
from pathlib import Path


def get_onedrive_base_path():
    onedrive_env = os.environ.get('OneDrive') or os.environ.get('OneDriveCommercial')
    if onedrive_env and os.path.exists(onedrive_env):
        return onedrive_env

    fallback = r"C:\Users\hchepsoy\OneDrive - McCombs Steel Company, INC"
    if os.path.exists(fallback):
        return fallback

    raise FileNotFoundError("Could not locate OneDrive folder.")


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
    print("OneDrive Folder Copy Utility")
    print("=" * 70)

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

    onedrive_base = get_onedrive_base_path()
    print(f"\nOneDrive base: {onedrive_base}")
    print(f"Outer folder:  {new_folder_name}")
    print(f"Inner folder:  {folder_name}")

    # Destination: <OneDrive root>\<number> - <folder_name>
    destination = os.path.join(onedrive_base, new_folder_name)

    if os.path.exists(destination):
        overwrite = input(f"\nDestination exists:\n  {destination}\nOverwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Aborted.")
            return
        shutil.rmtree(destination)

    print(f"\nCreating outer folder:\n  {destination}")
    os.makedirs(destination, exist_ok=True)

    # Inner folder keeps the original folder name
    inner_folder = os.path.join(destination, folder_name)
    print(f"\nCopying contents into:\n  {inner_folder}\n")
    copy_folder_contents(source_path, inner_folder)

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()