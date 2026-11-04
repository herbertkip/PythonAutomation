import os
import re
from pathlib import Path

def rename_pdf_files_simple(directory_path):
    """
    Simple version: Only rename files that contain "(Page" in the name
    """
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"ERROR: Directory not found: {directory_path}")
        return
    
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in: {directory_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files in the directory.\n")
    
    renamed_count = 0
    skipped_count = 0
    
    for filename in pdf_files:
        # Only process files with "(Page" in the name
        if '(Page' in filename and ')' in filename:
            # Extract the base name (everything before the page number)
            # Example: "CE-200 (Page 121).pdf" -> "CE-200"
            base_name = re.sub(r'\s*\(Page\s*\d+\)', '', filename)
            base_name = base_name.replace('.pdf', '')
            
            # Create new name with -1
            new_name = f"{base_name}-1.pdf"
            
            old_path = os.path.join(directory_path, filename)
            new_path = os.path.join(directory_path, new_name)
            
            # Handle duplicate names
            counter = 1
            while os.path.exists(new_path) and old_path != new_path:
                name_without_ext = new_name.replace('.pdf', '')
                new_name = f"{name_without_ext}_{counter}.pdf"
                new_path = os.path.join(directory_path, new_name)
                counter += 1
            
            try:
                os.rename(old_path, new_path)
                print(f"✓ Renamed: '{filename}' -> '{new_name}'")
                renamed_count += 1
            except Exception as e:
                print(f"✗ Error renaming '{filename}': {e}")
                skipped_count += 1
        else:
            # Skip files without page numbers
            print(f"⏭  Keeping as is: '{filename}'")
            skipped_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✓ Files renamed: {renamed_count}")
    print(f"  ⏭  Files skipped: {skipped_count}")
    print(f"  📁 Total PDF files: {len(pdf_files)}")
    print(f"{'='*60}")

# Run the script
if __name__ == "__main__":
    # Your specific file path
    directory_path = r"\\msc-s02\MSC Applications\Tekla\Tekla EPM\DocumentIndex\1022_IVY ACL (RC Andersen)\DRAWINGS\01-CONTRACT_DWGS\B-RECEIVED DWGS\RECD#001 - BID DRAWINGS -  (7-29-26)\DRAWINGS\UPLOAD"
    
    print(f"{'='*60}")
    print(f"PDF RENAME SCRIPT")
    print(f"{'='*60}")
    print(f"Target directory: {directory_path}")
    print(f"{'='*60}\n")
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"❌ ERROR: The specified directory does not exist!")
        print(f"   Please check the path and try again.")
        print(f"   Path: {directory_path}")
        exit(1)
    
    # Show the files that will be processed
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    files_with_page = [f for f in pdf_files if '(Page' in f and ')' in f]
    
    if files_with_page:
        print(f"📋 Files that will be renamed:")
        for f in files_with_page:
            base_name = re.sub(r'\s*\(Page\s*\d+\)', '', f)
            base_name = base_name.replace('.pdf', '')
            new_name = f"{base_name}-1.pdf"
            print(f"   • {f} → {new_name}")
        print()
    else:
        print(f"ℹ️  No files found with '(Page' in the name.")
        print(f"   All {len(pdf_files)} PDF files will be kept as is.\n")
    
    # Ask for confirmation
    print("⚠️  WARNING: This script will rename files. Make sure you have backups.")
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\n🔄 Processing files...\n")
        rename_pdf_files_simple(directory_path)
        print("\n✅ Script completed!")
    else:
        print("\n❌ Operation cancelled by user.")