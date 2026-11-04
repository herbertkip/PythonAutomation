import os
import shutil
import glob
import sys
import subprocess
import platform

def get_folder_path():
    """Prompt user for folder path via command line."""
    while True:
        folder_path = input("\nEnter the full path to the folder containing the Word document: ").strip()
        
        # Remove quotes if user pasted path with quotes
        folder_path = folder_path.strip('"').strip("'")
        
        if not folder_path:
            print("Error: No path entered. Please try again.")
            continue
            
        if not os.path.exists(folder_path):
            print(f"Error: Path '{folder_path}' does not exist. Please try again.")
            continue
            
        if not os.path.isdir(folder_path):
            print(f"Error: '{folder_path}' is not a directory. Please try again.")
            continue
            
        return folder_path

def find_word_document(folder_path):
    """Find Word documents in the specified folder."""
    # Look for both .docx and .doc files
    docx_files = glob.glob(os.path.join(folder_path, "*.docx"))
    doc_files = glob.glob(os.path.join(folder_path, "*.doc"))
    
    # Combine files
    word_files = docx_files + doc_files
    
    # Filter out temporary Word files (starting with ~$)
    word_files = [f for f in word_files if not os.path.basename(f).startswith('~$')]
    
    if len(word_files) == 0:
        print(f"\nError: No Word documents (.docx or .doc) found in '{folder_path}'")
        print("Please ensure the folder contains a Word document.")
        return None
    
    if len(word_files) > 1:
        print(f"\nWarning: Found {len(word_files)} Word documents:")
        for i, file in enumerate(word_files, 1):
            print(f"  {i}. {os.path.basename(file)}")
        
        while True:
            try:
                choice = input(f"Select file number (1-{len(word_files)}): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(word_files):
                    return word_files[choice_idx]
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(word_files)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                sys.exit(0)
    
    return word_files[0]

def get_sm_number():
    """Prompt for SM number via command line."""
    while True:
        sm_number = input("\nEnter the SM# number (e.g., 001): ").strip()
        
        if not sm_number:
            print("Error: SM number cannot be empty. Please try again.")
            continue
        
        # Clean the input
        sm_number = sm_number.replace('#', '').replace('SM', '').replace('sm', '')
        sm_number = sm_number.strip()
        
        try:
            # Convert to integer and format as 3-digit
            sm_number = f"{int(sm_number):03d}"
            return sm_number
        except ValueError:
            print(f"Error: '{sm_number}' is not a valid number. Please enter a numeric value.")
            continue

def get_copy_count():
    """Prompt for number of copies via command line."""
    while True:
        try:
            copies_input = input("\nHow many copies do you need in the DRAWINGS folder? (default: 1): ").strip()
            
            if not copies_input:
                return 1
            
            num_copies = int(copies_input)
            
            if num_copies < 1:
                print("Error: Number of copies must be at least 1. Please try again.")
                continue
            
            if num_copies > 100:
                confirm = input("Warning: More than 100 copies requested. Continue? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            return num_copies
            
        except ValueError:
            print("Error: Invalid number. Please enter a whole number.")
            continue
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)

def convert_to_pdf(input_path, output_path):
    """Convert Word document to PDF using appropriate method."""
    file_ext = os.path.splitext(input_path)[1].lower()
    
    if file_ext == '.docx':
        # Use docx2pdf for .docx files
        try:
            from docx2pdf import convert
            convert(input_path, output_path)
            return True
        except ImportError:
            print("docx2pdf is not installed.")
            return False
        except Exception as e:
            print(f"docx2pdf conversion failed: {e}")
            return False
    
    elif file_ext == '.doc':
        # For .doc files, try different methods
        return convert_doc_to_pdf(input_path, output_path)
    
    return False

def convert_doc_to_pdf(input_path, output_path):
    """Convert .doc file to PDF using available tools."""
    system = platform.system()
    
    # Method 1: Try using LibreOffice (works on all platforms)
    try:
        # Check common LibreOffice executable names
        libreoffice_cmds = ['soffice', 'libreoffice']
        
        for cmd in libreoffice_cmds:
            try:
                # Try to convert using LibreOffice
                subprocess.run(
                    [cmd, '--headless', '--convert-to', 'pdf', '--outdir', 
                     os.path.dirname(output_path), input_path],
                    check=True, 
                    capture_output=True,
                    timeout=60
                )
                
                # LibreOffice creates PDF with same name as input
                libreoffice_output = os.path.splitext(input_path)[0] + '.pdf'
                if os.path.exists(libreoffice_output):
                    # Rename to desired output
                    if libreoffice_output != output_path:
                        os.rename(libreoffice_output, output_path)
                    return True
                    
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
    
    except Exception as e:
        print(f"LibreOffice conversion failed: {e}")
    
    # Method 2: Try using Microsoft Word COM automation (Windows only)
    if system == 'Windows':
        try:
            import win32com.client
            import pythoncom
            
            # Initialize COM
            pythoncom.CoInitialize()
            
            # Create Word application object
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            try:
                # Open the document
                doc = word.Documents.Open(input_path)
                
                # Save as PDF
                doc.SaveAs(output_path, FileFormat=17)  # 17 = PDF format
                
                # Close document and quit Word
                doc.Close()
                word.Quit()
                
                return True
                
            except Exception as e:
                print(f"Word COM conversion failed: {e}")
                try:
                    word.Quit()
                except:
                    pass
                return False
                
        except ImportError:
            print("pywin32 is not installed. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
                print("pywin32 installed. Please run the script again.")
            except:
                print("Could not install pywin32 automatically.")
            return False
    
    print("No suitable conversion method found for .doc file.")
    print("Please install one of the following:")
    print("  - LibreOffice (https://www.libreoffice.org/)")
    print("  - Microsoft Word with pywin32 (Windows)")
    return False

def convert_docx_to_pdf():
    """Main function to convert Word document to PDF and manage copies."""
    print("\n" + "="*60)
    print("WORD TO PDF CONVERTER WITH DRAWING DISTRIBUTION")
    print("="*60)
    
    # Get folder path
    folder_path = get_folder_path()
    print(f"\nSelected folder: {folder_path}")
    
    # Find Word document
    print("\nSearching for Word documents...")
    docx_path = find_word_document(folder_path)
    
    if docx_path is None:
        return
    
    docx_filename = os.path.basename(docx_path)
    file_ext = os.path.splitext(docx_filename)[1].lower()
    print(f"Found document: {docx_filename} (Type: {file_ext})")
    
    # Get SM number
    sm_number = get_sm_number()
    
    # Create output filename
    output_filename = f"SM#{sm_number}.pdf"
    output_path = os.path.join(folder_path, output_filename)
    
    # Convert to PDF
    print(f"\nConverting '{docx_filename}' to PDF...")
    
    if file_ext == '.doc':
        print("(Using alternative method for .doc file conversion)")
    
    try:
        success = convert_to_pdf(docx_path, output_path)
        
        if not success:
            print(f"✗ Failed to convert '{docx_filename}' to PDF")
            return
        
        # Verify the PDF was created
        if not os.path.exists(output_path):
            print(f"✗ PDF file was not created at: {output_path}")
            return
            
        # Check file size
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            print(f"✗ PDF file is empty (0 bytes)")
            os.remove(output_path)
            return
            
        print(f"✓ PDF created successfully: {output_filename} ({file_size:,} bytes)")
        
    except Exception as e:
        print(f"✗ Error converting document: {e}")
        print("\nTroubleshooting tips:")
        print("  - For .doc files, install LibreOffice or Microsoft Word")
        print("  - Ensure the document is not corrupted")
        print("  - Close the Word document if it's currently open")
        return
    
    # Create DRAWINGS folder
    drawings_folder = os.path.join(folder_path, "DRAWINGS")
    if not os.path.exists(drawings_folder):
        os.makedirs(drawings_folder)
        print(f"✓ Created DRAWINGS folder: {drawings_folder}")
    else:
        print(f"✓ DRAWINGS folder already exists")
    
    # Get number of copies
    num_copies = get_copy_count()
    
    # Save copies in DRAWINGS folder
    print(f"\nCreating {num_copies} cop{'y' if num_copies == 1 else 'ies'} in DRAWINGS folder...")
    
    for i in range(num_copies):
        if num_copies == 1:
            copy_filename = output_filename
        else:
            # Multiple copies with sequential naming
            copy_filename = f"SM#{sm_number}_copy{i+1}.pdf"
        
        copy_path = os.path.join(drawings_folder, copy_filename)
        shutil.copy2(output_path, copy_path)
        print(f"  ✓ Copy {i+1}/{num_copies}: {copy_filename}")
    
    # Summary
    print("\n" + "="*60)
    print("PROCESS COMPLETED SUCCESSFULLY")
    print("="*60)
    print(f"Source document: {docx_filename}")
    print(f"Primary PDF: {output_path}")
    print(f"Copies created: {num_copies}")
    print(f"DRAWINGS folder: {drawings_folder}")
    print("="*60)

if __name__ == "__main__":
    # Check for required libraries
    missing_libs = []
    
    try:
        import docx2pdf
    except ImportError:
        missing_libs.append("docx2pdf")
    
    if platform.system() == 'Windows':
        try:
            import win32com.client
        except ImportError:
            # Not adding to missing_libs since LibreOffice can be used instead
            pass
    
    if missing_libs:
        print("Missing required libraries:", ", ".join(missing_libs))
        install = input("Would you like to install them now? (y/n): ").strip().lower()
        if install == 'y':
            import subprocess
            for lib in missing_libs:
                print(f"Installing {lib}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print("Installation complete!\n")
        else:
            print("Cannot proceed without required libraries. Exiting.")
            sys.exit(1)
    
    # Check for LibreOffice (for .doc files)
    if platform.system() != 'Windows':
        has_libreoffice = False
        for cmd in ['soffice', 'libreoffice']:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
                has_libreoffice = True
                break
            except:
                continue
        
        if not has_libreoffice:
            print("\nWarning: LibreOffice not found.")
            print("For .doc file conversion, please install LibreOffice:")
            print("  sudo apt-get install libreoffice  (Ubuntu/Debian)")
            print("  brew install libreoffice          (macOS)")
    
    try:
        convert_docx_to_pdf()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)