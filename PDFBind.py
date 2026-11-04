import os
import PyPDF2
from pathlib import Path

def combine_pdfs_in_directory(directory_path):
    """
    Combines all PDF files in a directory into a single PDF,
    creates a folder called 'DRAWINGS', moves all original PDFs into it,
    but leaves the combined Binder PDF outside the DRAWINGS folder
    """
    
    # Convert to Path object for easier handling
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory '{directory_path}' does not exist or is not a folder.")
        return False
    
    # Get all PDF files in the directory (non-recursive)
    pdf_files = sorted([f for f in directory.iterdir() if f.suffix.lower() == '.pdf' and f.is_file()])
    
    if not pdf_files:
        print(f"No PDF files found in '{directory_path}'")
        return False
    
    print(f"\n📁 Processing directory: {directory}")
    print(f"📄 Found {len(pdf_files)} PDF files to combine:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    # Create the DRAWINGS folder
    drawings_folder = directory / "DRAWINGS"
    drawings_folder.mkdir(exist_ok=True)
    print(f"\n📂 Created folder: {drawings_folder}")
    
    # Create a PDF merger object
    pdf_merger = PyPDF2.PdfMerger()
    
    # Add all PDF files to the merger
    print("\n📑 Combining PDF files...")
    for pdf_file in pdf_files:
        try:
            with open(pdf_file, 'rb') as file:
                pdf_merger.append(file)
            print(f"  ✓ Added: {pdf_file.name}")
        except Exception as e:
            print(f"  ✗ Error adding {pdf_file.name}: {e}")
            return False
    
    # Create the output filename: folder_name + " Binder.pdf"
    folder_name = directory.name
    output_filename = f"{folder_name} Binder.pdf"
    
    # Save the Binder PDF in the main directory (outside DRAWINGS folder)
    output_path = directory / output_filename
    
    # Write the combined PDF
    try:
        with open(output_path, 'wb') as output_file:
            pdf_merger.write(output_file)
        print(f"\n✅ Successfully created: {output_path}")
    except Exception as e:
        print(f"Error writing combined PDF: {e}")
        return False
    
    # Move all original PDF files into the DRAWINGS folder
    print("\n📦 Moving original PDF files to DRAWINGS folder...")
    for pdf_file in pdf_files:
        try:
            # Move file to DRAWINGS folder
            new_location = drawings_folder / pdf_file.name
            pdf_file.rename(new_location)
            print(f"  ✓ Moved: {pdf_file.name}")
        except Exception as e:
            print(f"  ✗ Error moving {pdf_file.name}: {e}")
    
    print("\n" + "="*50)
    print("✨ PROCESS COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"📄 Combined Binder PDF (outside DRAWINGS): {output_path}")
    print(f"📂 All original PDFs are in: {drawings_folder}")
    print("="*50)
    
    return True

def get_directory_from_user():
    """
    Prompts the user for a directory path and validates it
    """
    print("\n" + "="*50)
    print("📄 PDF COMBINER SCRIPT")
    print("="*50)
    
    while True:
        print("\nEnter the path to the directory containing the PDF files you want to combine.")
        print("(You can drag and drop a folder here, or type/paste the path)")
        print("Type 'exit' or 'quit' to cancel.\n")
        
        directory_path = input("Directory path: ").strip()
        
        # Check if user wants to exit
        if directory_path.lower() in ['exit', 'quit', '']:
            print("\n❌ Operation cancelled by user.")
            return None
        
        # Remove quotes if user pasted with quotes (common when drag-dropping)
        directory_path = directory_path.strip('"').strip("'")
        
        # Convert to Path object
        dir_path = Path(directory_path)
        
        # Validate the directory exists
        if not dir_path.exists():
            print(f"\n❌ Error: The path '{directory_path}' does not exist.")
            print("Please check the path and try again.")
            continue
        
        if not dir_path.is_dir():
            print(f"\n❌ Error: '{directory_path}' is not a directory/folder.")
            print("Please provide a folder path.")
            continue
        
        # Check if there are any PDF files
        pdf_files = [f for f in dir_path.iterdir() if f.suffix.lower() == '.pdf' and f.is_file()]
        if not pdf_files:
            print(f"\n❌ Error: No PDF files found in '{directory_path}'.")
            print("Please provide a folder that contains PDF files.")
            
            # Ask if they want to continue anyway
            retry = input("\nDo you want to try another folder? (y/n): ").strip().lower()
            if retry != 'y':
                return None
            continue
        
        # Valid directory with PDF files
        return dir_path

def main():
    """Main function to run the script"""
    # Get directory from user
    directory = get_directory_from_user()
    
    if directory is None:
        return
    
    # Process the directory
    print(f"\n📂 Processing folder: {directory}")
    combine_pdfs_in_directory(str(directory))

if __name__ == "__main__":
    try:
        main()
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        input("\nPress Enter to exit...")