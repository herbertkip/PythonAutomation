import os
import shutil
import pandas as pd
from pathlib import Path
import datetime
import fnmatch

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
        with open(log_file, 'a', encoding='ascii', errors='ignore') as log:
            log.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
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
        df = pd.read_excel(excel_file)
        
        file_list = []
        found_column = False
        
        # Try to find columns that might contain filenames
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['file', 'name', 'filename', 'document', 'doc']):
                file_list.extend(df[col].dropna().tolist())
                found_column = True
                break
        
        # If no matching column found, use the first column
        if not found_column and len(df.columns) > 0:
            file_list = df.iloc[:, 0].dropna().tolist()
        
        # Convert to strings and clean up
        file_list = [str(f).strip() for f in file_list if pd.notna(f) and str(f).strip()]
        return file_list
        
    except Exception as e:
        log_message(f"Error reading Excel file {os.path.basename(excel_file)}: {str(e)}")
        return []

def find_matching_files(filename_pattern):
    """
    Find all files in FILES_PATH that match the given pattern.
    Supports partial matches, wildcards, and extension variations.
    """
    matching_files = []
    
    try:
        # Get all files in the FILES folder
        all_files = [f for f in os.listdir(FILES_PATH) if os.path.isfile(os.path.join(FILES_PATH, f))]
        
        # Check if the pattern has an extension
        has_extension = '.' in filename_pattern
        
        if has_extension:
            # Exact match with extension
            if filename_pattern in all_files:
                matching_files.append(filename_pattern)
        else:
            # No extension - match any file that starts with the name
            # This will match: file.txt, file.pdf, file.docx, file_v2.pdf, etc.
            for file in all_files:
                # Get filename without extension for comparison
                name_without_ext = os.path.splitext(file)[0]
                
                # Check if the filename starts with the pattern
                # or contains the pattern (more flexible)
                if file == filename_pattern or name_without_ext == filename_pattern:
                    matching_files.append(file)
                elif filename_pattern in name_without_ext:
                    matching_files.append(file)
                    
    except Exception as e:
        log_message(f"Error searching for files: {str(e)}")
    
    return matching_files

def delete_files(file_patterns, match_mode='flexible'):
    """
    Delete files based on patterns.
    
    match_mode options:
    - 'exact': Only exact filename matches
    - 'flexible': Match by name (ignoring extension) or partial matches
    - 'wildcard': Support wildcard patterns (* and ?)
    """
    deleted_count = 0
    not_found_count = 0
    error_count = 0
    files_found = []
    
    for pattern in file_patterns:
        if match_mode == 'wildcard':
            # Use wildcard matching
            all_files = [f for f in os.listdir(FILES_PATH) if os.path.isfile(os.path.join(FILES_PATH, f))]
            matching_files = fnmatch.filter(all_files, pattern)
        else:
            # Find matching files
            matching_files = find_matching_files(pattern)
            
            # If flexible mode and no matches found, try with wildcard
            if not matching_files and match_mode == 'flexible':
                # Try wildcard pattern for flexibility
                all_files = [f for f in os.listdir(FILES_PATH) if os.path.isfile(os.path.join(FILES_PATH, f))]
                # Check if any file contains the pattern
                for file in all_files:
                    if pattern.lower() in file.lower():
                        matching_files.append(file)
        
        if matching_files:
            for filename in matching_files:
                file_path = os.path.join(FILES_PATH, filename)
                
                try:
                    if os.path.isfile(file_path):
                        # Create unique filename in DELETED folder
                        dest_path = os.path.join(DELETED_PATH, filename)
                        
                        # If file already exists in DELETED folder, add timestamp
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
                        files_found.append(filename)
                    else:
                        log_message(f"[SKIPPED] Is a directory: {filename}")
                        not_found_count += 1
                        
                except Exception as e:
                    log_message(f"[ERROR] Failed to delete {filename}: {str(e)}")
                    error_count += 1
        else:
            log_message(f"[NOT FOUND] No files matching: {pattern}")
            not_found_count += 1
    
    return deleted_count, not_found_count, error_count, files_found

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
    
    # Remove duplicates
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
    
    # Show matching mode options
    print("\n" + "="*60)
    print("MATCHING MODE OPTIONS:")
    print("  1. Exact match (filename must match exactly, including extension)")
    print("  2. Flexible match (matches filenames with or without extension)")
    print("  3. Wildcard match (use * and ? patterns)")
    print("="*60)
    
    mode_choice = input("Select matching mode (1, 2, or 3) [default: 2]: ").strip()
    
    match_modes = {
        '1': 'exact',
        '2': 'flexible',
        '3': 'wildcard'
    }
    
    match_mode = match_modes.get(mode_choice, 'flexible')
    
    # Show files that will be deleted
    log_message(f"Using {match_mode} matching mode")
    log_message("-"*60)
    
    # Preview matching files
    preview_files = []
    for pattern in unique_files:
        if match_mode == 'wildcard':
            all_files = [f for f in os.listdir(FILES_PATH) if os.path.isfile(os.path.join(FILES_PATH, f))]
            preview_files.extend(fnmatch.filter(all_files, pattern))
        else:
            preview_files.extend(find_matching_files(pattern))
    
    if preview_files:
        log_message(f"Files that will be deleted ({len(preview_files)}):")
        for f in preview_files[:20]:  # Show first 20
            log_message(f"  - {f}")
        if len(preview_files) > 20:
            log_message(f"  ... and {len(preview_files) - 20} more")
    else:
        log_message("WARNING: No matching files found in the FILES folder!")
        response = input("Continue anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            log_message("Operation cancelled by user")
            return
    
    # Ask for confirmation
    print("\n" + "="*60)
    print(f"WARNING: This will move {len(unique_files)} file pattern(s) to the DELETED FILES folder")
    print("="*60)
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        log_message("Operation cancelled by user")
        print("Operation cancelled.")
        return
    
    # Delete files
    deleted, not_found, errors, files_found = delete_files(unique_files, match_mode)
    
    # Summary
    log_message("="*60)
    log_message("DELETION SUMMARY")
    log_message("="*60)
    log_message(f"[SUCCESS] Successfully moved: {deleted} file(s)")
    log_message(f"[NOT FOUND] Files not found: {not_found} file(s)")
    log_message(f"[ERROR] Errors: {errors}")
    log_message(f"Total patterns processed: {len(unique_files)}")
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
        try:
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - FATAL ERROR: {str(e)}\n")
        except:
            pass
        print("Script failed. Check the log file for details.")