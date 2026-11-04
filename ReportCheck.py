#!/usr/bin/env python3
"""
Script to search for a 'reports'/'report' folder in a directory tree,
then find and open a file containing 'Assembly' in its name.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def prompt_for_directory():
    """Prompt the user for a directory and validate it exists."""
    while True:
        directory = input("Please enter a directory path: ").strip().strip('"').strip("'")
        
        if not directory:
            print("No input provided. Please try again.\n")
            continue
        
        path = Path(directory).expanduser().resolve()
        
        if not path.exists():
            print(f"Error: '{path}' does not exist. Please try again.\n")
            continue
        
        if not path.is_dir():
            print(f"Error: '{path}' is not a directory. Please try again.\n")
            continue
        
        return path


def find_report_folder(root_dir):
    """
    Recursively search for a folder named 'reports' or 'report'.
    Returns the first match found, or None.
    """
    matches = []
    
    for current_root, dirs, files in os.walk(root_dir):
        for d in dirs:
            if d.lower() in ("reports", "report"):
                matches.append(Path(current_root) / d)
    
    return matches


def find_assembly_file(folder):
    """
    Find files in the folder that contain 'Assembly' in their name.
    Returns a list of matching file paths.
    """
    matches = []
    
    if not folder.exists():
        return matches
    
    for entry in folder.iterdir():
        if entry.is_file() and "assembly" in entry.name.lower():
            matches.append(entry)
    
    return matches


def open_file(filepath):
    """Open a file using the OS default application. Handles any file type."""
    try:
        system = platform.system()
        
        if system == "Windows":
            os.startfile(str(filepath))  # type: ignore[attr-defined]
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(filepath)], check=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", str(filepath)], check=True)
        
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False


def main():
    print("=" * 60)
    print("Report Folder & Assembly File Finder")
    print("=" * 60)
    
    # Step 1: Prompt for directory
    root_dir = prompt_for_directory()
    print(f"\nSearching in: {root_dir}\n")
    
    # Step 2: Search for 'reports' or 'report' folder (recursive)
    print("Searching for 'reports'/'report' folders (including child folders)...")
    report_folders = find_report_folder(root_dir)
    
    # Step 3: Report if missing
    if not report_folders:
        print("\n[RESULT] MISSING: No 'reports' or 'report' folder was found.")
        sys.exit(1)
    
    print(f"\n[RESULT] Found {len(report_folders)} matching folder(s):")
    for folder in report_folders:
        print(f"  - {folder}")
    
    # Step 4: Look for 'Assembly' file in each report folder
    print("\nSearching for files with 'Assembly' in the name...")
    
    total_found = 0
    for folder in report_folders:
        print(f"\nOpening folder: {folder}")
        
        assembly_files = find_assembly_file(folder)
        
        if not assembly_files:
            print(f"  [RESULT] MISSING: No file containing 'Assembly' found in {folder}")
            continue
        
        for filepath in assembly_files:
            print(f"  [FOUND] {filepath.name}")
            print(f"  Opening: {filepath}")
            
            if open_file(filepath):
                print(f"  [SUCCESS] File opened with default application.")
                total_found += 1
            else:
                print(f"  [FAILED] Could not open file.")
    
    # Final summary
    print("\n" + "=" * 60)
    if total_found == 0:
        print("SUMMARY: No 'Assembly' files were found or opened.")
        sys.exit(1)
    else:
        print(f"SUMMARY: Opened {total_found} 'Assembly' file(s) successfully.")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)