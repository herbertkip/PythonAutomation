import os
import sys
import win32com.client
from pathlib import Path

def convert_word_to_pdf(word_path):
    """Convert Word document to PDF"""
    try:
        if not os.path.exists(word_path):
            print(f"Error: File not found - {word_path}")
            return None
            
        if not word_path.lower().endswith(('.docx', '.doc')):
            print("Error: File must be a Word document (.docx or .doc)")
            return None
        
        # Initialize Word application
        print("Opening Word...")
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        # Open the document
        print(f"Opening document: {os.path.basename(word_path)}")
        doc = word.Documents.Open(word_path)
        
        # Prepare PDF path
        pdf_dir = os.path.join(os.path.dirname(word_path), "PDF")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Create PDF filename
        base_name = os.path.splitext(os.path.basename(word_path))[0]
        pdf_path = os.path.join(pdf_dir, f"{base_name}.pdf")
        
        # Save as PDF
        print("Converting to PDF...")
        doc.SaveAs2(pdf_path, FileFormat=17)  # 17 = PDF format
        
        # Clean up
        doc.Close()
        word.Quit()
        
        print(f"Success! PDF saved to: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"Error converting file: {e}")
        return None

def main():
    print("=" * 60)
    print("WORD TO PDF CONVERTER")
    print("=" * 60)
    
    # Get file path from user
    while True:
        print("\nEnter the full path to the Word document:")
        print("(Example: Z:\\Tekla\\Tekla EPM\\DocumentIndex\\967_RHOADES 57A (BSI)\\DRAWINGS\\02-SHOP_DWGS\\D_RELEASES\\RELEASE#154 SHOP MEMO 154 - (8-12-26).docx)")
        print("or type 'exit' to quit")
        
        word_path = input("\nPath: ").strip('"').strip()
        
        if word_path.lower() == 'exit':
            print("Exiting...")
            sys.exit(0)
            
        if os.path.exists(word_path):
            break
        else:
            print("File not found. Please check the path and try again.")
    
    # Convert the document
    pdf_path = convert_word_to_pdf(word_path)
    
    if pdf_path:
        print("\n" + "=" * 60)
        print("CONVERSION COMPLETE!")
        print(f"PDF Location: {pdf_path}")
        print("=" * 60)
        
        # Ask if user wants to open the folder
        while True:
            response = input("\nOpen the PDF folder? (y/n): ").strip().lower()
            if response in ['y', 'n']:
                break
            print("Please enter 'y' or 'n'")
        
        if response == 'y':
            pdf_dir = os.path.dirname(pdf_path)
            os.startfile(pdf_dir)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    # Check for required dependencies
    try:
        import win32com.client
    except ImportError:
        print("Required module 'pywin32' not found.")
        print("Installing pywin32...")
        try:
            os.system("pip install pywin32")
            print("\nInstallation complete. Please run the script again.")
        except:
            print("Installation failed. Please install manually: pip install pywin32")
        sys.exit(1)
    
    main()