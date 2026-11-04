import os
import sys

def rename_files_with_prefix(directory, prefix):
    """
    Rename all files in the specified directory by adding a prefix
    before the existing filename with a dash.
    
    Args:
        directory: Path to the directory containing files to rename
        prefix: String to add as prefix (e.g., 'C' or 'IMG')
    """
    try:
        # Check if directory exists
        if not os.path.exists(directory):
            print(f"Error: Directory '{directory}' does not exist.")
            return False
        
        # Get all files in the directory
        files = os.listdir(directory)
        
        # Filter out directories, only process files
        files_to_rename = [f for f in files if os.path.isfile(os.path.join(directory, f))]
        
        if not files_to_rename:
            print(f"No files found in directory '{directory}'.")
            return False
        
        renamed_count = 0
        skipped_count = 0
        
        print(f"\nFiles to rename in '{directory}':")
        print("-" * 50)
        
        for filename in files_to_rename:
            # Skip hidden files (optional)
            if filename.startswith('.'):
                skipped_count += 1
                continue
                
            # Construct new filename
            new_filename = f"{prefix}-{filename}"
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_filename)
            
            # Check if new filename already exists
            if os.path.exists(new_path):
                print(f"⚠️  Skipping '{filename}' -> '{new_filename}' (already exists)")
                skipped_count += 1
                continue
            
            # Rename the file
            try:
                os.rename(old_path, new_path)
                print(f"✅ Renamed: '{filename}' -> '{new_filename}'")
                renamed_count += 1
            except Exception as e:
                print(f"❌ Error renaming '{filename}': {e}")
                skipped_count += 1
        
        # Print summary
        print("-" * 50)
        print(f"Summary: {renamed_count} files renamed, {skipped_count} files skipped")
        return True
        
    except PermissionError:
        print(f"Error: Permission denied to access '{directory}'")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def parse_prefix(input_str):
    """
    Parse prefix from user input. Accepts:
    - A value wrapped in single quotes: 'C' or 'IMG'
    - A raw value: C or IMG
    Returns the parsed prefix string, or None if invalid.
    """
    input_str = input_str.strip()
    if not input_str:
        return None
    
    # If wrapped in single quotes, extract the content between them
    if len(input_str) >= 2 and input_str.startswith("'") and input_str.endswith("'"):
        prefix = input_str[1:-1]
    else:
        prefix = input_str
    
    return prefix if prefix else None

def main():
    print("File Renamer - Add Prefix to Filenames")
    print("=" * 40)
    
    # Get prefix string (supports multiple characters)
    while True:
        raw = input("\nEnter the prefix (e.g., 'C' or 'IMG'): ")
        prefix = parse_prefix(raw)
        if prefix:
            print(f"Using prefix: '{prefix}'")
            break
        else:
            print("Please enter at least one character.")
    
    # Get directory path
    while True:
        directory = input("Enter the directory path (or press Enter for current directory): ").strip()
        if not directory:
            directory = os.getcwd()
            print(f"Using current directory: {directory}")
            break
        elif os.path.exists(directory):
            break
        else:
            print(f"Directory '{directory}' does not exist. Please try again.")
    
    # Confirm before proceeding
    print(f"\nReady to rename files in: {directory}")
    print(f"Prefix to add: '{prefix}-'")
    confirm = input("Proceed with rename? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        rename_files_with_prefix(directory, prefix)
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    # Check if command line arguments are provided
    if len(sys.argv) > 1:
        # Command line mode: python script.py <directory> <prefix>
        if len(sys.argv) >= 3:
            directory = sys.argv[1]
            prefix = parse_prefix(sys.argv[2])
            if not prefix:
                print("Error: Invalid prefix. Please provide at least one character.")
                sys.exit(1)
            print(f"Command line mode: Directory='{directory}', Prefix='{prefix}'")
            rename_files_with_prefix(directory, prefix)
        else:
            print("Usage: python rename_files.py <directory> <prefix>")
    else:
        # Interactive mode
        main()