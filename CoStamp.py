import os
import sys
import datetime
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import io
from PIL import Image

def get_user_inputs():
    """Prompt user for all required information"""
    print("=" * 60)
    print("PDF STAMPING TOOL - Construction Drawings")
    print("=" * 60)
    
    # Get stamp image location - support both image and text-only modes
    stamp_path = input("\nEnter the path to your stamp image file (PNG, JPG, or PDF)\n"
                      "Or press ENTER to use text-only stamp: ").strip()
    
    # Validate if a path was provided
    if stamp_path:
        # Check if it's a file (not a folder)
        if os.path.isdir(stamp_path):
            print(f"Warning: '{stamp_path}' is a folder, not a file.")
            print("Looking for image files in this folder...")
            
            # Try to find an image file in the folder
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf']
            image_files = []
            for ext in image_extensions:
                for file in os.listdir(stamp_path):
                    if file.lower().endswith(ext):
                        image_files.append(os.path.join(stamp_path, file))
            
            if image_files:
                print(f"Found {len(image_files)} image file(s):")
                for i, f in enumerate(image_files, 1):
                    print(f"  {i}. {os.path.basename(f)}")
                choice = input("Enter the number of the file to use (or 0 to use text-only): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(image_files):
                    stamp_path = image_files[int(choice) - 1]
                else:
                    stamp_path = None
                    print("Using text-only stamp.")
            else:
                print("No image files found in folder. Using text-only stamp.")
                stamp_path = None
        elif not os.path.isfile(stamp_path):
            print(f"Error: File '{stamp_path}' not found.")
            print("Using text-only stamp instead.")
            stamp_path = None
    
    # Get PDF files location
    pdf_folder = input("\nEnter the folder path containing PDF files: ").strip()
    while not os.path.exists(pdf_folder):
        print(f"Error: Folder '{pdf_folder}' not found.")
        pdf_folder = input("Enter the folder path containing PDF files: ").strip()
    
    # Get user initials
    initials = input("\nEnter your initials (e.g., JD): ").strip().upper()
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
    
    # Stamp positioning (bottom-right corner)
    stamp_width = 2.5 * inch
    stamp_height = 2.5 * inch
    x_position = width - stamp_width - 0.5 * inch
    y_position = 0.5 * inch
    
    # Add the stamp image if provided and valid
    image_loaded = False
    if stamp_image_path and os.path.isfile(stamp_image_path):
        try:
            # Validate it's an image or PDF
            if stamp_image_path.lower().endswith('.pdf'):
                # For PDF stamps, we'll use text-only as PDF stamps are complex
                print("Note: PDF stamp images are not supported for overlay. Using text-only.")
            else:
                # Try to load with PIL to validate
                img = Image.open(stamp_image_path)
                img.close()
                
                # Draw the image
                c.drawImage(stamp_image_path, x_position, y_position, 
                           width=stamp_width, height=stamp_height, mask='auto')
                image_loaded = True
                print("✓ Stamp image loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load stamp image. Using text-only stamp.")
            print(f"  Details: {e}")
    
    # Add dynamic text (date and initials) - always shown
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)  # Black color
    
    # Position text below or inside the stamp
    if image_loaded:
        # Text below the stamp
        text_x = x_position
        text_y = y_position - 0.3 * inch
    else:
        # Create a text-based stamp box
        text_x = width - 3 * inch - 0.5 * inch
        text_y = 0.5 * inch
        
        # Draw a border box for text-only stamp
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(2)
        c.rect(text_x - 0.1 * inch, text_y - 0.1 * inch, 3.2 * inch, 1.2 * inch)
    
    # Draw the text
    c.drawString(text_x, text_y + 0.8 * inch, "STAMPED")
    c.drawString(text_x, text_y + 0.5 * inch, f"Date: {date_str}")
    c.drawString(text_x, text_y + 0.2 * inch, f"Initials: {initials}")
    
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
        if stamp_path:
            print(f"Stamp image: {os.path.basename(stamp_path)}")
        else:
            print("Stamp type: Text-only")
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