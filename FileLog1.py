import os
import pandas as pd
from pathlib import Path

def create_file_log():
    """
    Create an Excel file log of files in a selected folder.
    Lists filenames without extensions, numbered, and saves in the same directory.
    """
    
    # Prompt for folder directory
    folder_path = input("Enter the folder directory path: ").strip()
    
    # Validate the folder path
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory.")
        return
    
    try:
        # Get all files in the directory
        files = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            # Only include files, skip directories
            if os.path.isfile(item_path):
                # Get filename without extension
                filename_without_ext = Path(item).stem
                files.append(filename_without_ext)
        
        # Sort files alphabetically
        files.sort()
        
        if not files:
            print("No files found in the specified directory.")
            return
        
        # Create DataFrame with numbered list
        df = pd.DataFrame({
            'Number': range(1, len(files) + 1),
            'Filename': files
        })
        
        # Create Excel file in the same directory
        excel_filename = 'file_log.xlsx'
        excel_path = os.path.join(folder_path, excel_filename)
        
        # Save to Excel
        df.to_excel(excel_path, index=False, sheet_name='File List')
        
        print(f"\nFile log created successfully!")
        print(f"Location: {excel_path}")
        print(f"Total files listed: {len(files)}")
        
    except PermissionError:
        print("Error: Permission denied when accessing the folder or creating the file.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("=== File Log Creator ===\n")
    create_file_log()