import os
import pandas as pd
from pathlib import Path
from datetime import datetime

def create_file_log_with_options():
    """
    Create an Excel file log of files in a selected folder with additional options.
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
        file_details = []
        
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            # Only include files, skip directories
            if os.path.isfile(item_path):
                filename_without_ext = Path(item).stem
                files.append(filename_without_ext)
                
                # Get file details (optional)
                file_stats = os.stat(item_path)
                file_details.append({
                    'filename': filename_without_ext,
                    'size': file_stats.st_size,
                    'modified': datetime.fromtimestamp(file_stats.st_mtime)
                })
        
        # Sort files alphabetically
        files.sort()
        file_details.sort(key=lambda x: x['filename'])
        
        if not files:
            print("No files found in the specified directory.")
            return
        
        # Ask user what information to include
        print("\nWhat information would you like to include?")
        print("1. Just filenames (numbered)")
        print("2. Filenames with file size and modified date")
        
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == '2':
            # Create detailed DataFrame
            df = pd.DataFrame({
                'Number': range(1, len(file_details) + 1),
                'Filename': [d['filename'] for d in file_details],
                'Size (bytes)': [d['size'] for d in file_details],
                'Modified Date': [d['modified'] for d in file_details]
            })
        else:
            # Create simple DataFrame
            df = pd.DataFrame({
                'Number': range(1, len(files) + 1),
                'Filename': files
            })
        
        # Create Excel file in the same directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f'file_log_{timestamp}.xlsx'
        excel_path = os.path.join(folder_path, excel_filename)
        
        # Save to Excel with formatting
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='File List')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['File List']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"\n✓ File log created successfully!")
        print(f"Location: {excel_path}")
        print(f"Total files listed: {len(files)}")
        
    except PermissionError:
        print("Error: Permission denied when accessing the folder or creating the file.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("=== File Log Creator ===\n")
    create_file_log_with_options()