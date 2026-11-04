#!/usr/bin/env python3
"""
Folder Creator Script
Creates a new folder with format: <FOLDER_TYPE>#001 - (MM-DD-YY)
"""

import os
import datetime
import re

def get_folder_type():
    """Prompt user to select folder type using number input."""
    print("\n=== Folder Type Options ===")
    print("1 - RELEASE (R)")
    print("2 - SUB (S)")
    print("3 - FIELD (F)")
    print("4 - APPRV (A)")
    print("5 - RECD (R)")  # Note: RECD also starts with R, but option 5 differentiates it
    
    while True:
        try:
            choice = input("\nSelect folder type (enter number 1-5): ").strip()
            if not choice:
                continue
                
            choice_num = int(choice)
            if choice_num == 1:
                return "RELEASE"
            elif choice_num == 2:
                return "SUB"
            elif choice_num == 3:
                return "FIELD"
            elif choice_num == 4:
                return "APPRV"
            elif choice_num == 5:
                return "RECD"
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number (1-5).")

def get_directory_path():
    """Prompt user for the directory path."""
    while True:
        dir_path = input("\nEnter the directory path where folder should be created: ").strip()
        if not dir_path:
            print("Directory path cannot be empty.")
            continue
        
        # Expand user home directory if ~ is used
        dir_path = os.path.expanduser(dir_path)
        
        # Check if directory exists
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            return dir_path
        else:
            print(f"Directory '{dir_path}' does not exist. Please enter a valid path.")

def get_number_value():
    """Prompt user for the number value (will be formatted to 3 digits)."""
    while True:
        num_input = input("\nEnter the number value (e.g., 1, 25, 100): ").strip()
        if not num_input:
            print("Number cannot be empty.")
            continue
        
        try:
            num = int(num_input)
            if num < 0:
                print("Please enter a positive number.")
                continue
            if num > 999:
                print("Number cannot exceed 999 (3-digit limit).")
                continue
            return num
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def format_date():
    """Get today's date in MM-DD-YY format."""
    today = datetime.datetime.now()
    return today.strftime("%m-%d-%y")

def create_folder(base_path, folder_type, number, date_str):
    """Create the folder with the specified naming convention."""
    # Format number as 3 digits with leading zeros
    number_formatted = f"{number:03d}"
    
    # Construct folder name
    folder_name = f"{folder_type}#{number_formatted} - ({date_str})"
    full_path = os.path.join(base_path, folder_name)
    
    try:
        os.makedirs(full_path, exist_ok=False)
        print(f"\n✅ Successfully created folder:")
        print(f"   {full_path}")
        return True
    except FileExistsError:
        print(f"\n❌ Error: Folder already exists at:")
        print(f"   {full_path}")
        return False
    except PermissionError:
        print(f"\n❌ Error: Permission denied to create folder at:")
        print(f"   {full_path}")
        return False
    except Exception as e:
        print(f"\n❌ Error creating folder: {e}")
        return False

def main():
    """Main execution function."""
    print("=" * 60)
    print("        FOLDER CREATOR SCRIPT")
    print("=" * 60)
    
    # Get folder type
    folder_type = get_folder_type()
    
    # Get directory path
    directory = get_directory_path()
    
    # Get number value
    number = get_number_value()
    
    # Get today's date
    date_str = format_date()
    
    # Show summary and confirm
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"  Folder Type: {folder_type}")
    print(f"  Directory:   {directory}")
    print(f"  Number:      {number:03d}")
    print(f"  Date:        {date_str}")
    print(f"\n  Folder will be named:")
    print(f"  {folder_type}#{number:03d} - ({date_str})")
    print("=" * 60)
    
    confirm = input("\nCreate this folder? (y/n): ").strip().lower()
    if confirm == 'y' or confirm == 'yes':
        create_folder(directory, folder_type, number, date_str)
    else:
        print("\n❌ Folder creation cancelled.")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()