import os
import shutil
from pathlib import Path
from collections import defaultdict

def get_drawing_number(filename):
    """
    Extract the drawing sheet number from the filename.
    Takes everything before the first dash.
    """
    # Remove .pdf extension if present
    name = filename
    if name.lower().endswith('.pdf'):
        name = name[:-4]
    
    # Split on first dash and take the first part
    if '-' in name:
        return name.split('-')[0]
    else:
        # If no dash, return the whole name (without extension)
        return name

def find_pdf_files(root_directory, drawings_folder):
    """
    Recursively find all PDF files in the given directory and its subfolders.
    Excludes the DRAWINGS folder to avoid reprocessing already extracted files.
    """
    pdf_files = []
    root_path = Path(root_directory)
    
    # Walk through all directories
    for file_path in root_path.rglob('*.pdf'):
        # Skip files in the DRAWINGS folder
        if drawings_folder in file_path.parents:
            continue
        pdf_files.append(file_path)
    
    for file_path in root_path.rglob('*.PDF'):
        # Skip files in the DRAWINGS folder
        if drawings_folder in file_path.parents:
            continue
        pdf_files.append(file_path)
    
    return pdf_files

def check_source_duplicates(pdf_files):
    """
    Check for duplicate sheet numbers in the source files.
    Returns a set of sheet numbers that appear more than once.
    """
    sheet_count = defaultdict(int)
    for pdf_path in pdf_files:
        sheet_number = get_drawing_number(pdf_path.name)
        sheet_count[sheet_number] += 1
    
    return {sheet for sheet, count in sheet_count.items() if count > 1}

def process_files(pdf_files, drawings_dir, conflict_strategy):
    """
    Process all PDF files and copy them to the DRAWINGS folder.
    """
    processed_count = 0
    skipped_count = 0
    error_count = 0
    processed_sheets = set()  # Track which sheet numbers we've already processed
    
    # Find duplicates in source files
    source_duplicates = check_source_duplicates(pdf_files)
    if source_duplicates:
        print(f"\n⚠ Warning: Found {len(source_duplicates)} duplicate sheet numbers in source files:")
        for sheet in sorted(source_duplicates):
            print(f"  • {sheet} appears multiple times")
    
    print("\nProcessing files...")
    print("-" * 60)
    
    for pdf_path in pdf_files:
        try:
            original_filename = pdf_path.name
            sheet_number = get_drawing_number(original_filename)
            
            # Check if this sheet number has already been processed
            if sheet_number in processed_sheets and conflict_strategy == 'skip':
                print(f"  Skipped: {sheet_number}.pdf (duplicate in source)")
                skipped_count += 1
                continue
            
            # Build destination path
            dest_path = drawings_dir / f"{sheet_number}.pdf"
            
            # Check if file already exists in DRAWINGS
            if dest_path.exists():
                if conflict_strategy == 'skip':
                    print(f"  Skipped: {sheet_number}.pdf (already exists in DRAWINGS)")
                    skipped_count += 1
                    continue
                elif conflict_strategy == 'rename':
                    # Find a unique name
                    counter = 1
                    while True:
                        new_name = f"{sheet_number}_{counter}.pdf"
                        new_path = drawings_dir / new_name
                        if not new_path.exists():
                            shutil.copy2(pdf_path, new_path)
                            print(f"  Copied: {new_name} (original: {sheet_number})")
                            processed_count += 1
                            processed_sheets.add(sheet_number)
                            break
                        counter += 1
                elif conflict_strategy == 'overwrite':
                    shutil.copy2(pdf_path, dest_path)
                    print(f"  Overwrote: {sheet_number}.pdf")
                    processed_count += 1
                    processed_sheets.add(sheet_number)
            else:
                # No conflict, copy the file
                shutil.copy2(pdf_path, dest_path)
                print(f"  Copied: {sheet_number}.pdf")
                processed_count += 1
                processed_sheets.add(sheet_number)
                
        except Exception as e:
            error_count += 1
            print(f"  Error processing {pdf_path.name}: {e}")
    
    return processed_count, skipped_count, error_count

def main():
    # Get the root directory from user
    print("=" * 60)
    print("PROCORE DRAWINGS EXTRACTOR")
    print("=" * 60)
    print("\nThis script will:")
    print("  • Search all folders for PDF files")
    print("  • Rename files to their drawing sheet number")
    print("  • Copy all drawings to a 'DRAWINGS' folder")
    print("  • Create the DRAWINGS folder in the directory you specify")
    print("-" * 60)
    
    root_dir = input("\nEnter the root directory path: ").strip()
    
    if not root_dir:
        print("No directory entered. Exiting...")
        return
    
    root_path = Path(root_dir)
    
    if not root_path.exists():
        print(f"Error: Directory '{root_dir}' does not exist.")
        return
    
    if not root_path.is_dir():
        print(f"Error: '{root_dir}' is not a directory.")
        return
    
    # Create the DRAWINGS folder INSIDE the root directory
    drawings_dir = root_path / "DRAWINGS"
    drawings_dir.mkdir(exist_ok=True)
    
    print(f"\n✓ DRAWINGS folder created at: {drawings_dir}")
    
    # Find all PDF files (excluding those already in DRAWINGS folder)
    print("\nScanning for PDF files in all subfolders...")
    pdf_files = find_pdf_files(root_path, drawings_dir)
    
    if not pdf_files:
        print("No PDF files found outside the DRAWINGS folder.")
        print("(All PDFs may have already been extracted.)")
        return
    
    print(f"✓ Found {len(pdf_files)} PDF files outside the DRAWINGS folder.")
    
    # Show sample of found files
    print("\nSample of found files:")
    for i, pdf in enumerate(pdf_files[:5], 1):
        print(f"  {i}. {pdf.name} → {get_drawing_number(pdf.name)}.pdf")
    if len(pdf_files) > 5:
        print(f"  ... and {len(pdf_files) - 5} more files")
    
    # Ask for conflict handling strategy
    print("\nChoose conflict handling strategy for duplicate sheet numbers:")
    print("  1. Rename duplicates (append _1, _2, etc.)")
    print("  2. Skip duplicates")
    print("  3. Overwrite duplicates")
    
    choice = input("Enter your choice (1-3) [default: 1]: ").strip()
    
    conflict_map = {
        '1': 'rename',
        '2': 'skip',
        '3': 'overwrite'
    }
    
    conflict_strategy = conflict_map.get(choice, 'rename')
    
    # Process the files
    processed_count, skipped_count, error_count = process_files(
        pdf_files, drawings_dir, conflict_strategy
    )
    
    # Summary
    print("-" * 60)
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE!")
    print("=" * 60)
    print(f"  Total PDF files found:    {len(pdf_files)}")
    print(f"  Files processed:          {processed_count}")
    print(f"  Files skipped:            {skipped_count}")
    if error_count > 0:
        print(f"  Errors encountered:       {error_count}")
    print(f"\n  📁 DRAWINGS folder location: {drawings_dir}")
    
    # Optional: Show list of extracted files
    show_list = input("\nWould you like to see the list of extracted files? (y/n): ").strip().lower()
    if show_list == 'y':
        print("\nExtracted files in DRAWINGS folder:")
        extracted_files = sorted(drawings_dir.glob('*.pdf'))
        if extracted_files:
            for file in extracted_files:
                print(f"  • {file.name}")
        else:
            print("  No files were extracted.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your directory path and try again.")
        input("\nPress Enter to exit...")