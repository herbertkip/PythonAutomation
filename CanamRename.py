import os
import shutil
import re

def rename_files():
    # Prompt for directory
    directory = input("Enter the directory path: ").strip().strip('"').strip("'")
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return
    
    # Create output folder
    output_folder = os.path.join(directory, "UPDATED DRAWINGS")
    os.makedirs(output_folder, exist_ok=True)
    print(f"Created/using output folder: {output_folder}\n")
    
    renamed_count = 0
    skipped = []
    
    for filename in os.listdir(directory):
        source_path = os.path.join(directory, filename)
        
        # Skip directories (including the new output folder)
        if not os.path.isfile(source_path):
            continue
        
        # Split name and extension
        name, ext = os.path.splitext(filename)
        
        # Find the middle part between the first and second "-"
        # Pattern: <anything>-<MIDDLE> - <anything>
        match = re.match(r'^[^-]+-(.+?)\s*-\s*.+$', name)
        
        if not match:
            skipped.append(filename)
            continue
        
        new_name = match.group(1).strip() + ext
        destination_path = os.path.join(output_folder, new_name)
        
        # Handle duplicate names
        counter = 1
        base_new_name, new_ext = os.path.splitext(new_name)
        while os.path.exists(destination_path):
            destination_path = os.path.join(
                output_folder, f"{base_new_name}_{counter}{new_ext}"
            )
            counter += 1
        
        shutil.copy2(source_path, destination_path)
        print(f"'{filename}'  ->  '{os.path.basename(destination_path)}'")
        renamed_count += 1
    
    print(f"\nDone. {renamed_count} file(s) copied and renamed.")
    if skipped:
        print(f"\nSkipped {len(skipped)} file(s) that didn't match the pattern:")
        for s in skipped:
            print(f"  - {s}")


if __name__ == "__main__":
    rename_files()