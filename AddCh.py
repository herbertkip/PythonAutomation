import os
import sys

def rename_files_with_prefix():
    """
    Rename files in a folder by adding a character/string prefix followed by an underscore.
    """
    
    # Prompt for folder directory
    folder_path = input("Enter the folder directory path: ").strip()
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Directory '{folder_path}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory.")
        sys.exit(1)
    
    # Prompt for the character(s) to be added
    prefix_chars = input("Enter the character(s) to add as prefix: ")
    
    # Get all files in the directory
    try:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    except PermissionError:
        print(f"Error: Permission denied to access directory '{folder_path}'.")
        sys.exit(1)
    
    if not files:
        print("No files found in the specified directory.")
        return
    
    # Display files to be renamed
    print(f"\nFound {len(files)} file(s) in '{folder_path}'")
    print(f"Prefix to add: '{prefix_chars}_'")
    print("\nFiles to be renamed:")
    for file in files:
        print(f"  {file} -> {prefix_chars}_{file}")
    
    # Confirm with user
    confirm = input("\nProceed with renaming? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Rename files
    renamed_count = 0
    error_count = 0
    
    for file in files:
        old_path = os.path.join(folder_path, file)
        new_name = f"{prefix_chars}_{file}"
        new_path = os.path.join(folder_path, new_name)
        
        try:
            # Check if new filename already exists
            if os.path.exists(new_path):
                print(f"Error: Cannot rename '{file}' - '{new_name}' already exists.")
                error_count += 1
                continue
            
            os.rename(old_path, new_path)
            print(f"Renamed: '{file}' -> '{new_name}'")
            renamed_count += 1
            
        except OSError as e:
            print(f"Error renaming '{file}': {e}")
            error_count += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Operation completed!")
    print(f"Successfully renamed: {renamed_count} file(s)")
    if error_count > 0:
        print(f"Errors encountered: {error_count} file(s)")
    print(f"{'='*50}")

if __name__ == "__main__":
    try:
        rename_files_with_prefix()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)