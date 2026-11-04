import os
import shutil
import pandas as pd
from pathlib import Path
import datetime

# Define paths
EXCEL_PATH = r'C:\Users\hchepsoy\python tasks\Delete Files\EXCEL'
FILES_PATH = r'C:\Users\hchepsoy\python tasks\Delete Files\FILES'
DELETED_PATH = r'C:\Users\hchepsoy\python tasks\Delete Files\DELETED FILES'

# Create DELETED FILES folder if it doesn't exist
Path(DELETED_PATH).mkdir(parents=True, exist_ok=True)

# Create log file
log_file = os.path.join(DELETED_PATH, f'deletion_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

def log_message(message):
    """Write message to log file"""
    try:
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except:
        # Fallback to ASCII if UTF-8 fails
        with open(log_file, 'a', encoding='ascii', errors='ignore') as log:
            log.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    # Print without special characters
    print(message.encode('ascii', errors='ignore').decode('ascii'))

def get_excel_files():
    """Get all Excel files from the EXCEL folder"""
    excel_files = []
    try:
        for file in os.listdir(EXCEL_PATH):
            if file.endswith(('.xlsx', '.xls', '.xlsm')):
                excel_files.append(os.path.join(EXCEL_PATH, file))
    except Exception as e:
        log_message(f"Error accessing EXCEL folder: {str(e)}")
    return excel_files

def read_files_from_excel(excel_file):
    """Read file names from Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Try to find columns that might contain filenames
        file_list = []
        found_column = False
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['file', 'name', 'filename', 'document', 'doc']):
                file_list.extend(df[col].dropna().tolist())
                found_column = True
                break
        
        # If no matching column found, use the first column
        if not found_column and len(df.columns) > 0:
            file_list = df.iloc[:, 0].dropna().tolist()
        
        # Convert to strings and remove any extra spaces
        file_list = [str(f).strip() for f in file_list if pd.notna(f) and str(f).strip()]
        return file_list
        
    except Exception as e:
        log_message(f"Error reading Excel file {os.path.basename(excel_file)}: {str(e)}")
        return []

def delete_files(file_list):
    """Delete files and move them to DELETED FOLDER"""
    deleted_count = 0
    not_found_count = 0
    error_count = 0
    
    for filename in file_list:
        # Construct full file path
        file_path = os.path.join(FILES_PATH, filename)
        
        if os.path.exists(file_path):
            try:
                # Check if it's a file (not a directory)
                if os.path.isfile(file_path):
                    # Create unique filename in DELETED folder
                    dest_path = os.path.join(DELETED_PATH, filename)
                    
                    # If file already exists in DELETED folder, add timestamp to name
                    counter = 1
                    base_name, ext = os.path.splitext(filename)
                    while os.path.exists(dest_path):
                        new_name = f"{base_name}_{counter}{ext}"
                        dest_path = os.path.join(DELETED_PATH, new_name)
                        counter += 1
                    
                    # Move file to DELETED folder
                    shutil.move(file_path, dest_path)
                    log_message(f"[SUCCESS] Deleted: {filename} -> {os.path.basename(dest_path)}")
                    deleted_count += 1
                else:
                    log_message(f"[SKIPPED] Is a directory: {filename}")
                    not_found_count += 1
                    
            except Exception as e:
                log_message(f"[ERROR] Failed to delete {filename}: {str(e)}")
                error_count += 1
        else:
            log_message(f"[NOT FOUND] {filename}")
            not_found_count += 1
    
    return deleted_count, not_found_count, error_count

def main():
    """Main function"""
    log_message("="*60)
    log_message("FILE DELETION SCRIPT STARTED")
    log_message("="*60)
    log_message(f"Source folder: {FILES_PATH}")
    log_message(f"Destination folder: {DELETED_PATH}")
    log_message(f"Excel files folder: {EXCEL_PATH}")
    log_message("="*60)
    
    # Check if folders exist
    if not os.path.exists(EXCEL_PATH):
        log_message(f"ERROR: EXCEL folder not found at: {EXCEL_PATH}")
        return
    
    if not os.path.exists(FILES_PATH):
        log_message(f"ERROR: FILES folder not found at: {FILES_PATH}")
        return
    
    # Get all Excel files
    excel_files = get_excel_files()
    
    if not excel_files:
        log_message("No Excel files found in the EXCEL folder!")
        return
    
    log_message(f"Found {len(excel_files)} Excel file(s)")
    log_message("-"*60)
    
    all_files_to_delete = []
    
    # Read all Excel files
    for excel_file in excel_files:
        log_message(f"Reading: {os.path.basename(excel_file)}")
        files_list = read_files_from_excel(excel_file)
        if files_list:
            log_message(f"  Found {len(files_list)} file(s) to delete")
            all_files_to_delete.extend(files_list)
        else:
            log_message(f"  No files found to delete in this Excel")
    
    # Remove duplicates while preserving order
    unique_files = []
    seen = set()
    for file in all_files_to_delete:
        if file not in seen:
            unique_files.append(file)
            seen.add(file)
    
    if not unique_files:
        log_message("No files specified in Excel files!")
        return
    
    log_message("-"*60)
    log_message(f"Total unique files to delete: {len(unique_files)}")
    log_message("-"*60)
    
    # Ask for confirmation
    print("\n" + "="*60)
    print(f"WARNING: This will move {len(unique_files)} files to the DELETED FILES folder")
    print("="*60)
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        log_message("Operation cancelled by user")
        print("Operation cancelled.")
        return
    
    # Delete files
    deleted, not_found, errors = delete_files(unique_files)
    
    # Summary
    log_message("="*60)
    log_message("DELETION SUMMARY")
    log_message("="*60)
    log_message(f"[SUCCESS] Successfully moved: {deleted} file(s)")
    log_message(f"[NOT FOUND] Files not found: {not_found} file(s)")
    log_message(f"[ERROR] Errors: {errors}")
    log_message(f"Total files processed: {len(unique_files)}")
    log_message("="*60)
    log_message(f"Log file saved to: {log_file}")
    log_message("Script completed!")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"  Successfully moved: {deleted} file(s)")
    print(f"  Files not found: {not_found} file(s)")
    print(f"  Errors: {errors}")
    print(f"  Log file: {log_file}")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        # Try to log the error
        try:
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - FATAL ERROR: {str(e)}\n")
        except:
            pass
        print("Script failed. Check the log file for details.")