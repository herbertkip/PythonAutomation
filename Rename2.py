import os
import re

def rename_files(preview_only=False):
    # Directory path
    directory = r'Z:\Tekla\Tekla EPM\DocumentIndex\976_BRIDGE INDUSTRIAL(Penntex)\DRAWINGS\02-SHOP_DWGS\E_FIELD_USE\FIELD#001 J&D FIELD USE - (8-3-26)\DWG'
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory not found: {directory}")
        return
    
    # Get all files in the directory
    files = os.listdir(directory)
    
    # Counter for renamed files
    renamed_count = 0
    skipped_count = 0
    
    print("=" * 60)
    if preview_only:
        print("PREVIEW MODE - No files will be renamed")
    else:
        print("RENAMING FILES...")
    print("=" * 60)
    
    for filename in files:
        # Get full file path
        old_path = os.path.join(directory, filename)
        
        # Skip directories
        if os.path.isdir(old_path):
            continue
        
        # Get the base filename and extension
        base_name, extension = os.path.splitext(filename)
        
        # Check if filename ends with 'JE' (case insensitive)
        if base_name.endswith('JE'):
            # Remove 'JE' from the end
            new_base = base_name[:-2]
            
            # Add 'JE' to the front
            new_base = 'JE' + new_base
            
            # Construct new filename
            new_filename = new_base + extension
            new_path = os.path.join(directory, new_filename)
            
            # Check if target filename already exists
            if os.path.exists(new_path):
                print(f"⚠️  SKIPPED: {filename} -> {new_filename} (target exists)")
                skipped_count += 1
                continue
            
            if preview_only:
                print(f"📋 Would rename: {filename} -> {new_filename}")
            else:
                # Rename the file
                try:
                    os.rename(old_path, new_path)
                    print(f"✅ Renamed: {filename} -> {new_filename}")
                    renamed_count += 1
                except Exception as e:
                    print(f"❌ Error renaming {filename}: {e}")
                    skipped_count += 1
        else:
            # Skip files that don't end with 'JE'
            skipped_count += 1
    
    # Print summary
    print("\n" + "=" * 60)
    if preview_only:
        print(f"PREVIEW SUMMARY:")
    else:
        print(f"RENAME SUMMARY:")
    print(f"Files renamed: {renamed_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Total files processed: {renamed_count + skipped_count}")
    print("=" * 60)

if __name__ == "__main__":
    # OPTION 1: Preview changes first (recommended - run this first)
    # rename_files(preview_only=True)
    
    # OPTION 2: Actually rename files (uncomment this line to run)
    rename_files(preview_only=False)