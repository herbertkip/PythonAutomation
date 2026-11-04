import os
import re
from pathlib import Path
from PyPDF2 import PdfMerger
import sys

def find_pdf_pairs(directory):
    """
    Find PDF files and their suffix variants.
    Returns a dictionary with base files as keys and list of suffix files as values.
    """
    directory = Path(directory)
    pdf_files = list(directory.glob("*.pdf"))
    
    # Group files by base name
    file_groups = {}
    
    for pdf_file in pdf_files:
        # Get the stem (filename without extension)
        stem = pdf_file.stem
        
        # Pattern to match suffix: optional spaces, hyphen, optional spaces, number(s)
        # Examples: "file - 2", "file-2", "file -1", "file- 2", "file - 10"
        suffix_pattern = r'^(.+?)(\s*-\s*\d+)$'
        match = re.match(suffix_pattern, stem)
        
        if match:
            # This file has a suffix
            base_name = match.group(1).strip()
            suffix = match.group(2)
            
            if base_name not in file_groups:
                file_groups[base_name] = {'base': None, 'suffixes': []}
            file_groups[base_name]['suffixes'].append(pdf_file)
        else:
            # This is a base file (no suffix)
            if stem not in file_groups:
                file_groups[stem] = {'base': None, 'suffixes': []}
            file_groups[stem]['base'] = pdf_file
    
    # Filter to only include groups that have both base and suffix files
    valid_groups = {}
    for base_name, group in file_groups.items():
        if group['base'] is not None and group['suffixes']:
            # Sort suffix files by their suffix number
            def get_suffix_number(file_path):
                stem = file_path.stem
                match = re.search(r'-\s*(\d+)$', stem)
                return int(match.group(1)) if match else 0
            
            group['suffixes'].sort(key=get_suffix_number)
            valid_groups[base_name] = group
        elif group['suffixes'] and group['base'] is None:
            # Check if there's a base file that might be named differently
            # (e.g., if base file is missing but suffix files exist)
            print(f"Warning: Found suffix files for '{base_name}' but no base file exists:")
            for sf in group['suffixes']:
                print(f"  - {sf.name}")
    
    return valid_groups

def combine_pdfs(base_file, suffix_files, output_dir=None):
    """
    Combine base PDF with its suffix files.
    The output file keeps the base file's name.
    Returns True if successful, False otherwise.
    """
    try:
        merger = PdfMerger()
        
        # Add the base file first
        print(f"  Adding base file: {base_file.name}")
        merger.append(str(base_file))
        
        # Add suffix files in order
        for suffix_file in suffix_files:
            print(f"  Adding suffix file: {suffix_file.name}")
            merger.append(str(suffix_file))
        
        # Determine output path (same as base file)
        if output_dir:
            output_path = Path(output_dir) / base_file.name
        else:
            output_path = base_file
        
        # Create a temporary file first to avoid conflicts
        temp_output = output_path.with_suffix('.temp.pdf')
        
        # Write the merged PDF
        with open(temp_output, 'wb') as f:
            merger.write(f)
        
        merger.close()
        
        # Replace the original base file with the merged file
        if output_path.exists():
            output_path.unlink()
        temp_output.rename(output_path)
        
        print(f"  ✓ Successfully combined into: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error combining PDFs: {e}")
        return False

def delete_suffix_files(suffix_files):
    """Delete the suffix files after successful combination."""
    for suffix_file in suffix_files:
        try:
            suffix_file.unlink()
            print(f"  ✓ Deleted: {suffix_file.name}")
        except Exception as e:
            print(f"  ✗ Error deleting {suffix_file.name}: {e}")

def main():
    # Prompt for directory location
    print("PDF Combiner - Combines PDF files with suffix values to their parent files")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("Enter the directory path containing PDF files: ").strip()
    
    # Remove quotes if present
    directory = directory.strip('"').strip("'")
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return
    
    print(f"\nScanning directory: {directory}")
    print("-" * 70)
    
    # Find PDF pairs
    file_groups = find_pdf_pairs(directory)
    
    if not file_groups:
        print("No PDF files with suffix values found to combine.")
        return
    
    # Display what will be combined
    print(f"\nFound {len(file_groups)} file group(s) to combine:\n")
    for base_name, group in file_groups.items():
        print(f"• {group['base'].name}")
        for suffix_file in group['suffixes']:
            print(f"  + {suffix_file.name}")
        print()
    
    # Confirm before proceeding
    response = input("Proceed with combining and deleting suffix files? (y/n): ").strip().lower()
    if response != 'y':
        print("Operation cancelled.")
        return
    
    print("\nCombining PDFs...")
    print("-" * 70)
    
    success_count = 0
    fail_count = 0
    
    for base_name, group in file_groups.items():
        print(f"\nProcessing: {group['base'].name}")
        
        if combine_pdfs(group['base'], group['suffixes']):
            # Delete suffix files after successful combination
            delete_suffix_files(group['suffixes'])
            success_count += 1
        else:
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Successfully combined: {success_count} group(s)")
    print(f"Failed: {fail_count} group(s)")
    
    if success_count > 0:
        print("\nAll combined files maintain their original base names.")

if __name__ == "__main__":
    main()