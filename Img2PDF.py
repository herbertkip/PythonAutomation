import os
import sys
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class ImageToPDFConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to PDF Converter")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Supported image formats
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Image to PDF Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Directory selection frame
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=10)
        
        self.dir_label = ttk.Label(dir_frame, text="No directory selected", 
                                  relief=tk.SUNKEN, padding=5)
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(dir_frame, text="Browse", 
                               command=self.select_directory)
        browse_btn.pack(side=tk.RIGHT)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=20)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", 
                                     font=('Arial', 10))
        self.status_label.pack(pady=10)
        
        # Image list frame with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for image files
        self.image_listbox = tk.Listbox(list_frame, 
                                       yscrollcommand=scrollbar.set,
                                       selectmode=tk.EXTENDED)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.image_listbox.yview)
        
        # Conversion options frame
        options_frame = ttk.LabelFrame(main_frame, text="Conversion Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Output filename
        name_frame = ttk.Frame(options_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Output PDF Name:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.name_entry.insert(0, "output")
        
        # Quality option
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quality_frame, text="Image Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="High")
        quality_combo = ttk.Combobox(quality_frame, 
                                    textvariable=self.quality_var,
                                    values=["High", "Medium", "Low"],
                                    state="readonly", width=10)
        quality_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Convert button
        convert_btn = ttk.Button(main_frame, text="Convert to PDF", 
                                command=self.convert_images_to_pdf,
                                style='Accent.TButton')
        convert_btn.pack(pady=20, ipadx=20, ipady=5)
        
        # Configure style for accent button
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
        
        self.selected_directory = None
        
    def select_directory(self):
        """Open directory selection dialog"""
        directory = filedialog.askdirectory(title="Select Directory with Images")
        if directory:
            self.selected_directory = directory
            self.dir_label.config(text=directory)
            self.load_images_from_directory(directory)
            
    def load_images_from_directory(self, directory):
        """Load all image files from the selected directory"""
        self.image_listbox.delete(0, tk.END)
        
        try:
            files = os.listdir(directory)
            image_files = []
            
            for file in files:
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.supported_formats:
                        image_files.append(file)
            
            # Sort files alphabetically
            image_files.sort()
            
            if image_files:
                for file in image_files:
                    self.image_listbox.insert(tk.END, file)
                self.status_label.config(text=f"Found {len(image_files)} image(s)")
                self.progress_bar['maximum'] = len(image_files)
            else:
                self.status_label.config(text="No supported images found in directory")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load images: {str(e)}")
            self.status_label.config(text="Error loading images")
            
    def convert_images_to_pdf(self):
        """Convert selected images to a single PDF file"""
        if not self.selected_directory:
            messagebox.showwarning("Warning", "Please select a directory first")
            return
            
        # Get selected images
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one image")
            return
            
        # Get output filename
        output_name = self.name_entry.get().strip()
        if not output_name:
            output_name = "output"
            
        # Ensure .pdf extension
        if not output_name.lower().endswith('.pdf'):
            output_name += '.pdf'
            
        output_path = os.path.join(self.selected_directory, output_name)
        
        # Check if file exists
        if os.path.exists(output_path):
            if not messagebox.askyesno("File Exists", 
                                      f"'{output_name}' already exists. Overwrite?"):
                return
        
        # Get quality setting
        quality_map = {
            "High": 95,
            "Medium": 75,
            "Low": 50
        }
        quality = quality_map.get(self.quality_var.get(), 95)
        
        # Convert images
        try:
            self.progress_bar.start()
            self.status_label.config(text="Converting images...")
            self.root.update()
            
            images = []
            total = len(selected_indices)
            
            for idx, i in enumerate(selected_indices):
                filename = self.image_listbox.get(i)
                filepath = os.path.join(self.selected_directory, filename)
                
                # Open and convert image
                img = Image.open(filepath)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Optimize image
                img = self.optimize_image(img, quality)
                
                images.append(img)
                
                # Update progress
                self.status_label.config(text=f"Converting: {filename} ({idx+1}/{total})")
                self.root.update()
            
            # Save as PDF
            if images:
                first_image = images[0]
                remaining_images = images[1:] if len(images) > 1 else []
                
                self.status_label.config(text="Saving PDF...")
                self.root.update()
                
                first_image.save(output_path, 
                               save_all=True, 
                               append_images=remaining_images,
                               quality=quality,
                               optimize=True)
                
                self.status_label.config(text=f"Successfully created: {output_name}")
                messagebox.showinfo("Success", 
                                   f"PDF created successfully!\n\n"
                                   f"File: {output_name}\n"
                                   f"Location: {self.selected_directory}\n"
                                   f"Images: {len(images)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            self.status_label.config(text="Conversion failed")
        finally:
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
            
    def optimize_image(self, img, quality):
        """Optimize image based on quality setting"""
        # Get current size
        width, height = img.size
        
        # Resize if too large (optional optimization)
        max_size = 4000  # Maximum dimension
        if width > max_size or height > max_size:
            ratio = min(max_size/width, max_size/height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        return img

def main():
    # Check for PIL/Pillow
    try:
        from PIL import Image
    except ImportError:
        print("Pillow library is required. Install it with: pip install Pillow")
        sys.exit(1)
    
    root = tk.Tk()
    app = ImageToPDFConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()