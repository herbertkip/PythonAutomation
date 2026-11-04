import os

def rename_files_with_prefix():
    # Define the directory path
    directory = r"Z:\Tekla\Tekla EPM\DocumentIndex\999_PROLOGIS LEHIGH VALLEY WEST 56 (Allied)\DRAWINGS\01-CONTRACT_DWGS\B-RECEIVED DWGS\RECD#007 FIRE SPRINKLER INFO - (8-5-26)\PLD LV WEST 56 FIRE SPRINKLER\DRAWINGS\DWG"
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory not found: {directory}")
        return
    
    # Get all files in the directory
    try:
        files = os.listdir(directory)
    except PermissionError:
        print(f"Error: Permission denied to access: {directory}")
        return
    
    # Filter out directories, only process files
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    
    if not files:
        print("No files found in the directory.")
        return
    
    print(f"Found {len(files)} file(s) to process.")
    
    renamed_count = 0
    skipped_count = 0
    
    # Process each file
    for filename in files:
        # Check if file already has "FP-" prefix
        if filename.startswith("FP-"):
            print(f"Skipping '{filename}' - already has FP- prefix")
            skipped_count += 1
            continue
        
        # Create new filename with FP- prefix
        new_filename = f"FP-{filename}"
        
        # Full paths
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_filename)
        
        # Check if new filename already exists
        if os.path.exists(new_path):
            print(f"Warning: Cannot rename '{filename}' - '{new_filename}' already exists")
            skipped_count += 1
            continue
        
        # Rename the file
        try:
            os.rename(old_path, new_path)
            print(f"Renamed: '{filename}' -> '{new_filename}'")
            renamed_count += 1
        except Exception as e:
            print(f"Error renaming '{filename}': {e}")
            skipped_count += 1
    
    # Print summary
    print("\n" + "="*50)
    print(f"Rename complete!")
    print(f"Successfully renamed: {renamed_count} file(s)")
    print(f"Skipped: {skipped_count} file(s)")
    print("="*50)

if __name__ == "__main__":
    rename_files_with_prefix()