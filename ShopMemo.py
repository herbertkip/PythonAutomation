import PyPDF2
import os
import re
from pathlib import Path
import sys
import shutil
from datetime import datetime

class AdvancedShopMemoProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        self.base_directory = self.pdf_path.parent
        self.output_folder = self.base_directory / "Drawings"
        self.backup_folder = self.base_directory / "Backup"
        self.drawing_numbers = []
        self.metadata = {}
        
    def extract_drawing_numbers(self, text):
        """
        Enhanced extraction with multiple patterns and filtering.
        """
        # More comprehensive patterns
        patterns = [
            # Standard format: 158P001
            r'\b(\d{3}P\d{3})\b',
            # With optional spaces: 158 P001
            r'\b(\d{3})\s*P\s*(\d{3})\b',
            # With dash: 158-P001
            r'\b(\d{3})-P(\d{3})\b',
            # Drawing numbers in tables
            r'DRG\s*No\.?\s*[:]?\s*(\d{3}P\d{3})',
            r'DRAWING\s*[:]?\s*(\d{3}P\d{3})',
            # In fabrication release sections
            r'FABRICATION\s+RELEASE.*?(\d{3}P\d{3})',
        ]
        
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle grouped patterns
                    match = ''.join(match)
                if match and len(match) >= 4:
                    all_matches.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in all_matches:
            # Clean up the match
            match = match.strip()
            # Filter out common false positives
            if match.isdigit() and len(match) == 6:
                # Could be a valid drawing number like 158001
                formatted = f"{match[:3]}P{match[3:]}"
                if formatted not in seen:
                    seen.add(formatted)
                    unique_matches.append(formatted)
            elif not match.isdigit() and len(match) >= 4:
                if match not in seen:
                    seen.add(match)
                    unique_matches.append(match)
        
        return unique_matches
    
    def extract_metadata(self, text):
        """
        Extract additional metadata from the shop memo.
        """
        metadata = {}
        
        # Extract job number
        job_match = re.search(r'Job\s*#?\s*(\d+)', text, re.IGNORECASE)
        if job_match:
            metadata['job_number'] = job_match.group(1)
        
        # Extract date
        date_match = re.search(r'Date:\s*(\d{1,2}-\s*\d{1,2}-\s*\d{2,4})', text, re.IGNORECASE)
        if date_match:
            metadata['date'] = date_match.group(1)
        
        # Extract project name
        project_match = re.search(r'PROJECT\s+NAME\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
        if project_match:
            metadata['project'] = project_match.group(1).strip()
        
        return metadata
    
    def read_pdf_text(self):
        """
        Read text content from PDF file with page-by-page reporting.
        """
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                text = ""
                
                print(f"  📄 Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                        # Show preview of first few characters from each page
                        preview = page_text[:50].replace('\n', ' ')
                        print(f"  Page {page_num}: {len(page_text)} chars - Preview: {preview}...")
                    else:
                        print(f"  ⚠️ Page {page_num}: No extractable text")
                
                return text
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return None
    
    def create_backup(self):
        """
        Create a backup of the original PDF.
        """
        if not self.backup_folder.exists():
            self.backup_folder.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_folder / f"{self.pdf_path.stem}_backup_{timestamp}{self.pdf_path.suffix}"
        
        try:
            shutil.copy2(self.pdf_path, backup_path)
            print(f"  💾 Backup created: {backup_path.name}")
            return True
        except Exception as e:
            print(f"  ⚠️ Could not create backup: {e}")
            return False
    
    def create_summary_file(self):
        """
        Create a summary text file with information about the extracted drawings.
        """
        if not self.drawing_numbers:
            return
        
        summary_path = self.output_folder / "_drawing_extract_summary.txt"
        
        try:
            with open(summary_path, 'w') as f:
                f.write("="*60 + "\n")
                f.write("SHOP MEMO DRAWING EXTRACTION SUMMARY\n")
                f.write("="*60 + "\n\n")
                f.write(f"Source File: {self.pdf_path.name}\n")
                f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if self.metadata:
                    f.write("METADATA:\n")
                    for key, value in self.metadata.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                
                f.write("EXTRACTED DRAWINGS:\n")
                for idx, drawing_num in enumerate(self.drawing_numbers, 1):
                    f.write(f"  {idx}. {drawing_num}.pdf\n")
                
                f.write("\n" + "="*60 + "\n")
            
            print(f"  📋 Summary file created: {summary_path.name}")
            
        except Exception as e:
            print(f"  ⚠️ Could not create summary file: {e}")
    
    def process(self):
        """
        Main processing method with enhanced features.
        """
        print(f"\n{'='*70}")
        print(f"📄 ADVANCED SHOP MEMO PROCESSOR")
        print(f"{'='*70}\n")
        print(f"📂 Source: {self.pdf_path.absolute()}")
        print(f"📁 Base Directory: {self.base_directory.absolute()}")
        print(f"📁 Output Folder: {self.output_folder.absolute()}")
        
        # Check if file exists
        if not self.pdf_path.exists():
            print(f"\n❌ Error: File '{self.pdf_path}' not found.")
            return False
        
        # Read PDF text
        print(f"\n🔍 Reading PDF content...")
        pdf_text = self.read_pdf_text()
        if not pdf_text:
            return False
        
        # Extract metadata
        print(f"\n📊 Extracting metadata...")
        self.metadata = self.extract_metadata(pdf_text)
        if self.metadata:
            for key, value in self.metadata.items():
                print(f"  {key}: {value}")
        
        # Extract drawing numbers
        print(f"\n🔎 Searching for drawing numbers...")
        self.drawing_numbers = self.extract_drawing_numbers(pdf_text)
        
        if not self.drawing_numbers:
            print("❌ No drawing numbers found in the PDF.")
            print("\n💡 TIPS:")
            print("  • Check that the PDF contains text (not scanned images)")
            print("  • Look for patterns like '158P001' or '128P002'")
            print("  • Verify the text is extractable from the PDF")
            return False
        
        print(f"✅ Found {len(self.drawing_numbers)} drawing number(s):")
        for idx, num in enumerate(self.drawing_numbers, 1):
            print(f"  {idx}. {num}")
        
        # Create backup
        print(f"\n💾 Creating backup...")
        self.create_backup()
        
        # Create output folder
        print(f"\n📁 Creating output folder...")
        self.output_folder.mkdir(exist_ok=True)
        print(f"  ✅ Folder created/verified: {self.output_folder.absolute()}")
        
        # Create copies
        print(f"\n📝 Creating drawing copies...")
        success_count = 0
        for idx, drawing_num in enumerate(self.drawing_numbers, 1):
            print(f"  [{idx}/{len(self.drawing_numbers)}] Processing {drawing_num}...")
            if self.create_copy(drawing_num):
                success_count += 1
        
        # Create summary file
        if success_count > 0:
            print(f"\n📋 Creating summary...")
            self.create_summary_file()
        
        # Final report
        print(f"\n{'='*70}")
        print(f"📊 PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"✅ Successfully created: {success_count}/{len(self.drawing_numbers)} files")
        print(f"📁 Location: {self.output_folder.absolute()}")
        
        if success_count > 0:
            print(f"\n📄 Created files:")
            for drawing_num in self.drawing_numbers:
                print(f"  • {drawing_num}.pdf")
        
        print(f"{'='*70}\n")
        
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
            
            return True
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
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
    processor = AdvancedShopMemoProcessor(pdf_path)
    success = processor.process()
    
    if not success:
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("  1. Make sure the PDF contains drawing numbers like '158P001' or '128P002'")
        print("  2. Verify the PDF text is selectable/copyable (not scanned images)")
        print("  3. Check that you have permission to read the file")
        print("  4. Try using the absolute path to the file")
        print("\n🔍 Look for patterns like:")
        print("  • 220ea- 158P001 (SEE DRAWING)")
        print("  • DRG No. 158P002")
        print("  • FABRICATION RELEASE: RELEASE#026")
    
    # Wait for user to press Enter before closing (for Windows)
    if sys.platform == "win32":
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()