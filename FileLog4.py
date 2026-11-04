import os
import sys
import pandas as pd
from openpyxl import Workbook
from datetime import datetime

def get_directory_path():
    """
    Prompt user for directory path and validate it exists
    """
    while True:
        directory = input("\n📁 Enter directory path (or press Enter for current directory): ").strip()
        
        # If empty, use current directory
        if not directory:
            directory = os.getcwd()
            print(f"   Using current directory: {directory}")
            return directory
        
        # Remove quotes if present
        directory = directory.strip('"').strip("'")
        
        # Expand user home directory if ~ is used
        directory = os.path.expanduser(directory)
        
        if os.path.exists(directory) and os.path.isdir(directory):
            return directory
        else:
            print(f"❌ Directory '{directory}' does not exist or is not a valid directory.")
            print("   Please enter a valid path.\n")

def list_files_in_directory(directory, include_subdirs=True):
    """
    List all files in a directory
    Returns list of dictionaries with file info
    """
    files_data = []
    
    try:
        if include_subdirs:
            # Walk through all subdirectories
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, directory)
                    
                    # Get file info
                    name_without_ext = os.path.splitext(filename)[0]
                    extension = os.path.splitext(filename)[1] or 'No extension'
                    
                    # Get file size
                    try:
                        size = os.path.getsize(full_path)
                        size_mb = round(size / (1024 * 1024), 2)
                    except:
                        size_mb = 0
                    
                    files_data.append({
                        'Filename': name_without_ext,
                        'Full Name': filename,
                        'Extension': extension,
                        'Path': relative_path,
                        'Size (MB)': size_mb
                    })
        else:
            # Only current directory
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isfile(full_path):
                    name_without_ext = os.path.splitext(item)[0]
                    extension = os.path.splitext(item)[1] or 'No extension'
                    
                    # Get file size
                    try:
                        size = os.path.getsize(full_path)
                        size_mb = round(size / (1024 * 1024), 2)
                    except:
                        size_mb = 0
                    
                    files_data.append({
                        'Filename': name_without_ext,
                        'Full Name': item,
                        'Extension': extension,
                        'Path': item,
                        'Size (MB)': size_mb
                    })
    
    except PermissionError:
        print(f"⚠️  Permission denied accessing some files in {directory}")
    
    except Exception as e:
        print(f"❌ Error reading directory: {e}")
        return []
    
    # Sort alphabetically by filename without extension
    return sorted(files_data, key=lambda x: x['Filename'])

def save_file_list_excel(directory, files_data):
    """
    Save the list of files to an Excel file in the same directory
    """
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"file_list_{timestamp}.xlsx"
    output_path = os.path.join(directory, output_filename)
    
    try:
        # Create DataFrame
        df = pd.DataFrame(files_data)
        
        # Add index column starting from 1
        df.index = df.index + 1
        df.index.name = '#'
        
        # Create Excel writer with openpyxl engine
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='File List')
            
            # Auto-adjust column widths
            workbook = writer.book
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
        
        return output_path
    
    except Exception as e:
        print(f"❌ Error saving Excel file: {e}")
        return None

def main():
    """
    Main function with minimal prompts
    """
    print("\n" + "="*60)
    print("📋 FILE LIST GENERATOR - Quick Mode")
    print("="*60)
    
    # Get directory path (only essential prompt)
    directory = get_directory_path()
    
    # Ask if user wants subdirectories (simple yes/no)
    include_subdirs = input("\n📂 Include subdirectories? (Y/n): ").strip().lower()
    include_subdirs = include_subdirs not in ['n', 'no']  # Default to Yes
    
    print("\n⏳ Scanning directory...")
    
    # Get list of files
    files_data = list_files_in_directory(directory, include_subdirs)
    
    if not files_data:
        print("⚠️  No files found.")
        return
    
    print(f"\n✅ Found {len(files_data)} file(s).")
    
    # Save the file list to Excel
    output_path = save_file_list_excel(directory, files_data)
    
    if output_path:
        print(f"\n✅ File list saved successfully!")
        print(f"📄 Saved to: {output_path}")
        print(f"📊 Total files listed: {len(files_data)}")
        
        # Show first few files as preview
        print("\n📋 Preview (first 5 files - names without extensions):")
        print("-" * 40)
        for i, file_data in enumerate(files_data[:5], 1):
            ext_info = f"({file_data['Extension']})" if file_data['Extension'] != 'No extension' else "(no extension)"
            print(f"  {i}. {file_data['Filename']} {ext_info}")
        if len(files_data) > 5:
            print(f"  ... and {len(files_data)-5} more file(s)")
        print("-" * 40)
    else:
        print("❌ Failed to save file list.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)