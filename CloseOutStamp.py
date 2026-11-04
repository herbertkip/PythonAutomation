import os
import sys
import datetime
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io

def get_user_inputs():
    """Prompt user for all required information"""
    print("=" * 60)
    print("PDF STAMPING TOOL - Construction Drawings")
    print("=" * 60)
    
    # Get stamp image location
    stamp_path = input("Enter the path to your stamp image file (PNG or PDF): ").strip()
    while not os.path.exists(stamp_path):
        print(f"Error: File '{stamp_path}' not found.")
        stamp_path = input("Enter the path to your stamp image file: ").strip()
    
    # Get PDF files location
    pdf_folder = input("Enter the folder path containing PDF files: ").strip()
    while not os.path.exists(pdf_folder):
        print(f"Error: Folder '{pdf_folder}' not found.")
        pdf_folder = input("Enter the folder path containing PDF files: ").strip()
    
    # Get user initials
    initials = input("Enter your initials (e.g., JD): ").strip().upper()
    while not initials:
        print("Error: Initials cannot be empty.")
        initials = input("Enter your initials: ").strip().upper()
    
    return stamp_path, pdf_folder, initials

def create_stamp_overlay(stamp_image_path, initials, date_str):
    """Create a PDF overlay with the stamp image and dynamic text"""
    # Create a temporary PDF with the stamp
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add the stamp image (position at bottom-right corner)
    try:
        # Adjust these values to position your stamp
        stamp_width = 2.5 * inch
        stamp_height = 2.5 * inch
        x_position = width - stamp_width - 0.5 * inch
        y_position = 0.5 * inch
        
        c.drawImage(stamp_image_path, x_position, y_position, 
                   width=stamp_width, height=stamp_height, mask='auto')
    except Exception as e:
        print(f"Warning: Could not load stamp image. Using text-only stamp. Error: {e}")
    
    # Add dynamic text (date and initials)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0, 0)  # Black color
    
    # Position text below the stamp
    text_x = width - 2.5 * inch - 0.5 * inch
    text_y = 0.25 * inch
    
    # Draw date and initials
    c.drawString(text_x, text_y, f"Date: {date_str}")
    c.drawString(text_x, text_y - 15, f"Initials: {initials}")
    
    c.save()
    buffer.seek(0)
    return buffer

def stamp_pdf(input_pdf_path, output_pdf_path, stamp_overlay):
    """Apply the stamp overlay to each page of the PDF"""
    try:
        # Read the input PDF
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        
        # Get the stamp overlay as a PDF
        stamp_reader = PdfReader(stamp_overlay)
        stamp_page = stamp_reader.pages[0]
        
        # Apply stamp to each page
        for page_num, page in enumerate(reader.pages, 1):
            # Merge the stamp with the page
            page.merge_page(stamp_page)
            writer.add_page(page)
        
        # Write the output PDF
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
    except Exception as e:
        print(f"Error processing {input_pdf_path}: {e}")
        return False

def main():
    """Main execution function"""
    try:
        # Get user inputs
        stamp_path, pdf_folder, initials = get_user_inputs()
        
        # Get today's date in the format MMDDYYYY
        today = datetime.datetime.now()
        date_str = today.strftime("%m%d%Y")  # e.g., 08242026
        
        # Create the stamp overlay once (to reuse for all PDFs)
        print("\nCreating stamp overlay...")
        stamp_overlay = create_stamp_overlay(stamp_path, initials, date_str)
        
        # Find all PDF files in the folder
        pdf_files = [f for f in os.listdir(pdf_folder) 
                    if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF files found in '{pdf_folder}'")
            return
        
        print(f"\nFound {len(pdf_files)} PDF file(s) to stamp.")
        print(f"Date: {date_str}")
        print(f"Initials: {initials}")
        print(f"Stamp image: {stamp_path}")
        print("-" * 60)
        
        # Process each PDF
        success_count = 0
        for filename in pdf_files:
            input_path = os.path.join(pdf_folder, filename)
            
            # Create output filename: "OriginalName Stamped MMDDYYYY.pdf"
            name_without_ext = os.path.splitext(filename)[0]
            output_filename = f"{name_without_ext} Stamped {date_str}.pdf"
            output_path = os.path.join(pdf_folder, output_filename)
            
            # Skip if output file already exists
            if os.path.exists(output_path):
                print(f"⚠ Skipping '{filename}': Output file already exists")
                continue
            
            print(f"Processing: {filename} → {output_filename}")
            
            # Stamp the PDF
            if stamp_pdf(input_path, output_path, stamp_overlay):
                success_count += 1
                print(f"  ✓ Successfully stamped")
            else:
                print(f"  ✗ Failed to stamp")
        
        # Final summary
        print("-" * 60)
        print(f"Complete! {success_count} of {len(pdf_files)} files stamped successfully.")
        print(f"Output files are in: {pdf_folder}")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()