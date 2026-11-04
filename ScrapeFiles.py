import os
import shutil
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def get_source_directory():
    """Prompt user to select source directory containing folders with files"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Make dialog appear on top
    
    source_dir = filedialog.askdirectory(
        title="Select the directory where your folders are located"
    )
    
    if not source_dir:
        print("No source directory selected. Exiting...")
        return None
    
    return source_dir

def get_destination_directory():
    """Prompt user to select destination directory where DRAWINGS folder will be created"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Make dialog appear on top
    
    dest_dir = filedialog.askdirectory(
        title="Select the directory where DRAWINGS folder should be created"
    )
    
    if not dest_dir:
        print("No destination directory selected. Exiting...")
        return None
    
    return dest_dir

def copy_all_files_to_drawings(source_dir, dest_dir):
    """
    Copy all files from all folders in source_dir to a DRAWINGS folder in dest_dir
    """
    # Create DRAWINGS folder in destination directory
    drawings_folder = os.path.join(dest_dir, "DRAWINGS")
    
    if not os.path.exists(drawings_folder):
        os.makedirs(drawings_folder)
        print(f"Created DRAWINGS folder at: {drawings_folder}")
    else:
        print(f"DRAWINGS folder already exists at: {drawings_folder}")
    
    # Counter for copied files
    copied_count = 0
    skipped_count = 0
    error_count = 0
    
    # Walk through all directories and subdirectories in source directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            source_file_path = os.path.join(root, file)
            destination_file_path = os.path.join(drawings_folder, file)
            
            # Handle duplicate filenames
            if os.path.exists(destination_file_path):
                # If file already exists in DRAWINGS folder, add a number to filename
                filename, extension = os.path.splitext(file)
                counter = 1
                
                while os.path.exists(destination_file_path):
                    new_filename = f"{filename}_{counter}{extension}"
                    destination_file_path = os.path.join(drawings_folder, new_filename)
                    counter += 1
                
                print(f"Duplicate found: {file} -> renamed to {os.path.basename(destination_file_path)}")
            
            try:
                # Copy the file
                shutil.copy2(source_file_path, destination_file_path)
                copied_count += 1
                print(f"Copied: {file}")
            except Exception as e:
                error_count += 1
                print(f"Error copying {file}: {str(e)}")
    
    # Print summary
    print("\n" + "="*50)
    print("COPY OPERATION COMPLETE")
    print("="*50)
    print(f"Total files copied: {copied_count}")
    print(f"Files with name conflicts (renamed): {skipped_count}")
    print(f"Errors encountered: {error_count}")
    print(f"All files are located in: {drawings_folder}")
    
    return drawings_folder

def main():
    print("="*50)
    print("FILE COPY TOOL - Copy all files to DRAWINGS folder")
    print("="*50)
    print("\nThis tool will copy all files from all folders in a")
    print("selected directory to a single 'DRAWINGS' folder.")
    print("\n")
    
    # Get source directory
    print("Step 1: Select source directory...")
    source_dir = get_source_directory()
    if not source_dir:
        return
    
    print(f"Source directory: {source_dir}\n")
    
    # Get destination directory
    print("Step 2: Select destination directory...")
    dest_dir = get_destination_directory()
    if not dest_dir:
        return
    
    print(f"Destination directory: {dest_dir}\n")
    
    # Confirm with user
    print("Summary:")
    print(f"- Will copy ALL files from: {source_dir}")
    print(f"- Will create DRAWINGS folder in: {dest_dir}")
    
    confirm = input("\nProceed with copy? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    print("\nStarting file copy operation...\n")
    
    # Perform the copy operation
    drawings_folder = copy_all_files_to_drawings(source_dir, dest_dir)
    
    print(f"\nOperation completed! Check the DRAWINGS folder at:")
    print(drawings_folder)

if __name__ == "__main__":
    main()