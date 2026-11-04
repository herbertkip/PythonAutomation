import PyPDF2
import os
import re
from pathlib import Path
import argparse
import sys

class ShopMemoProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        self.base_directory = self.pdf_path.parent
        self.output_folder = self.base_directory / "Drawings"
        self.drawing_numbers = []
        
    def extract_drawing_numbers(self, text):
        """
        Extract drawing numbers from text using multiple patterns.
        Handles various formats found in shop memos.
        """
        # More comprehensive patterns for drawing numbers
        patterns = [
            r'\b(\d{3}P\d{3})\b',  # Pattern: 158P001, 128P002
            r'\b(\d{3}-\d{3}P\d{3})\b',  # Pattern: 123-456P789
            r'\b(P\d{3})\b',  # Pattern: P001
            r'\b(\d{6})\b',  # Pattern: 6-digit numbers that might be drawing numbers
            r'(\d{3}P\d{3})',  # Same as first but without word boundary
        ]
        
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            all_matches.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in all_matches:
            # Filter out common false positives
            if len(match) >= 4 and not match.isdigit():
                if match not in seen:
                    seen.add(match)
                    unique_matches.append(match)
        
        return unique_matches
    
    def read_pdf_text(self):
        """
        Read text content from PDF file.
        """
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                        print(f"  Page {page_num}: Extracted {len(page_text)} characters")
                    else:
                        print(f"  Warning: Page {page_num} has no extractable text")
                return text
        except FileNotFoundError:
            print(f"Error: File '{self.pdf_path}' not found.")
            return None
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None
    
    def process(self):
        """
        Main processing method.
        """
        print(f"\n{'='*60}")
        print(f"Processing shop memo: {self.pdf_path}")
        print(f"Base directory: {self.base_directory}")
        print(f"{'='*60}\n")
        
        # Check if file exists
        if not self.pdf_path.exists():
            print(f"❌ Error: File '{self.pdf_path}' not found.")
            return False
        
        # Read PDF text
        print("📄 Reading PDF content...")
        pdf_text = self.read_pdf_text()
        if not pdf_text:
            return False
        
        # Extract drawing numbers
        print("\n🔍 Searching for drawing numbers...")
        self.drawing_numbers = self.extract_drawing_numbers(pdf_text)
        
        if not self.drawing_numbers:
            print("❌ No drawing numbers found in the PDF.")
            print("\n💡 Tip: Look for patterns like '158P001' or '128P002' in the text.")
            return False
        
        print(f"✅ Found drawing numbers: {', '.join(self.drawing_numbers)}")
        
        # Create output folder
        print(f"\n📁 Creating output folder: {self.output_folder}")
        self.output_folder.mkdir(exist_ok=True)
        
        # Create copies
        print("\n📝 Creating copies...")
        success_count = 0
        for drawing_num in self.drawing_numbers:
            if self.create_copy(drawing_num):
                success_count += 1
        
        print(f"\n{'='*60}")
        if success_count > 0:
            print(f"✅ SUCCESS: Created {success_count} drawing files in '{self.output_folder}' folder:")
            for drawing_num in self.drawing_numbers:
                print(f"  📄 {drawing_num}.pdf")
            print(f"\n📍 Location: {self.output_folder.absolute()}")
        else:
            print("❌ No files were created.")
        print(f"{'='*60}\n")
        
        return success_count > 0
    
    def create_copy(self, drawing_num):
        """
        Create a copy of the original PDF with the drawing number as filename.
        """
        new_filepath = self.output_folder / f"{drawing_num}.pdf"
        
        try:
            # Read the original PDF
            with open(self.pdf_path, 'rb') as original_file:
                pdf_reader = PyPDF2.PdfReader(original_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Copy all pages
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                # Save new PDF
                with open(new_filepath, 'wb') as new_file:
                    pdf_writer.write(new_file)
            
            print(f"  ✅ Created: {drawing_num}.pdf")
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating {drawing_num}.pdf: {e}")
            return False

def select_file():
    """
    Interactive file selection with support for drag-and-drop or manual entry.
    """
    print("\n" + "="*60)
    print("📄 SHOP MEMO DRAWING EXTRACTOR")
    print("="*60)
    
    # Option 1: Get file path from user
    print("\nPlease enter the path to the shop memo PDF file:")
    print("  • You can drag and drop the file into this window")
    print("  • Or type/paste the file path manually")
    print("  • Press Enter to use 'SM158.pdf' in current directory")
    
    pdf_input = input("\n📂 File path: ").strip()
    
    # If user just pressed Enter, try default filename
    if not pdf_input:
        pdf_input = "SM158.pdf"
        print(f"Using default: {pdf_input}")
    
    # Remove quotes if present (from drag and drop)
    pdf_input = pdf_input.strip('"\'')
    
    pdf_path = Path(pdf_input)
    
    # If the path is not absolute, try to resolve it
    if not pdf_path.is_absolute():
        # Check if file exists in current directory
        if pdf_path.exists():
            print(f"✅ Found file: {pdf_path.absolute()}")
        else:
            # Try to find it in the current directory
            current_dir = Path.cwd()
            possible_path = current_dir / pdf_path
            if possible_path.exists():
                pdf_path = possible_path
                print(f"✅ Found file: {pdf_path.absolute()}")
            else:
                # Ask user to try again
                print(f"❌ File not found: {pdf_path}")
                retry = input("\nWould you like to try again? (y/n): ").strip().lower()
                if retry == 'y':
                    return select_file()
                else:
                    print("Exiting...")
                    sys.exit(1)
    
    return pdf_path

def main():
    """
    Main function with support for command line arguments and interactive mode.
    """
    # Check if user provided command line arguments
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if not pdf_path.exists():
            print(f"Error: File '{pdf_path}' not found.")
            sys.exit(1)
    else:
        # Interactive mode - prompt user for file
        pdf_path = select_file()
    
    # Process the shop memo
    processor = ShopMemoProcessor(pdf_path)
    success = processor.process()
    
    if not success:
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("  1. Make sure the PDF contains drawing numbers like '158P001' or '128P002'")
        print("  2. Verify the PDF text is selectable/copyable (not scanned images)")
        print("  3. Check that you have permission to read the file")
        print("  4. Try using the absolute path to the file")
        
    # Wait for user to press Enter before closing (for Windows)
    if sys.platform == "win32":
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()