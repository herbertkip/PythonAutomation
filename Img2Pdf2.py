import os
import sys
from PIL import Image
from pathlib import Path

def images_to_pdf(directory, output_name="output.pdf", quality=95):
    """Convert all images in directory to a single PDF"""
    
    # Supported formats
    supported = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
    
    # Get all image files
    image_files = []
    for file in os.listdir(directory):
        if file.lower().endswith(supported):
            image_files.append(os.path.join(directory, file))
    
    if not image_files:
        print("No supported images found in directory")
        return False
    
    # Sort files
    image_files.sort()
    
    # Convert images
    images = []
    for filepath in image_files:
        try:
            img = Image.open(filepath)
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
            print(f"Loaded: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    if images:
        # Ensure .pdf extension
        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'
            
        output_path = os.path.join(directory, output_name)
        
        # Save as PDF
        try:
            first_image = images[0]
            remaining = images[1:] if len(images) > 1 else []
            
            first_image.save(output_path, 
                           save_all=True, 
                           append_images=remaining,
                           quality=quality,
                           optimize=True)
            
            print(f"Successfully created: {output_path}")
            print(f"Total images: {len(images)}")
            return True
        except Exception as e:
            print(f"Error saving PDF: {e}")
            return False

if __name__ == "__main__":
    # Prompt for directory
    dir_path = input("Enter the directory path containing images: ").strip()
    
    if not os.path.exists(dir_path):
        print("Directory not found!")
        sys.exit(1)
    
    # Optional: Custom output name
    output_name = input("Enter output PDF name (default: output.pdf): ").strip()
    if not output_name:
        output_name = "output.pdf"
    
    # Convert
    images_to_pdf(dir_path, output_name)