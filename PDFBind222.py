"""
Modernized PDFBind2.py
"""
import argparse
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Optional, List

from pypdf import PdfWriter

# Configure standardized logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def merge_pdfs(pdf_files: List[Path], output_path: Path) -> bool:
    """Merges multiple PDF files into a single output file."""
    logger.info(f"Combining {len(pdf_files)} PDF files...")
    merger = PdfWriter()
    
    try:
        for pdf_file in pdf_files:
            merger.append(pdf_file)
            logger.debug(f"Added: {pdf_file.name}")
        
        merger.write(output_path)
        merger.close()
        logger.info(f"Successfully created: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}")
        return False

def move_to_drawings(pdf_files: List[Path], drawings_folder: Path) -> None:
    """Moves original PDF files into the DRAWINGS directory safely across filesystems."""
    logger.info("Moving original PDFs to DRAWINGS folder...")
    drawings_folder.mkdir(parents=True, exist_ok=True)
    
    for pdf_file in pdf_files:
        try:
            dest = drawings_folder / pdf_file.name
            shutil.move(str(pdf_file), str(dest))
        except OSError as e:
            logger.error(f"Error moving {pdf_file.name}: {e}")

def create_zip_archive(directory: Path, drawings_folder: Path) -> Optional[Path]:
    """Creates a ZIP archive of the DRAWINGS folder."""
    directory_name = directory.name
    first_word = directory_name.split()[0] if directory_name.strip() else "Archive"
    zip_path = directory / f"{first_word} DWG.zip"
    
    logger.info(f"Creating ZIP archive: {zip_path.name}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in drawings_folder.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(drawings_folder)
                    zipf.write(file_path, arcname)
        
        logger.info(f"ZIP archive created successfully at: {zip_path}")
        return zip_path
    except (zipfile.BadZipFile, OSError) as e:
        logger.error(f"Failed to create ZIP archive: {e}")
        return None

def process_directory(directory_path: str | Path) -> bool:
    """Orchestrates the merge, move, and archive operations for a given directory."""
    directory = Path(directory_path).resolve()
    
    if not directory.is_dir():
        logger.error(f"Directory '{directory}' does not exist.")
        return False
        
    pdf_files = sorted(f for f in directory.iterdir() if f.suffix.lower() == '.pdf' and f.is_file())
    
    if not pdf_files:
        logger.warning(f"No PDF files found in '{directory}'")
        return False
        
    logger.info(f"Processing directory: {directory}")
    
    drawings_folder = directory / "DRAWINGS"
    output_filename = f"{directory.name} Binder.pdf"
    output_path = directory / output_filename
    
    if not merge_pdfs(pdf_files, output_path):
        return False
        
    move_to_drawings(pdf_files, drawings_folder)
    create_zip_archive(directory, drawings_folder)
    
    logger.info("Process completed successfully.")
    return True

def get_directory_from_user() -> Optional[Path]:
    """Interactive fallback for user input when run without CLI arguments."""
    print("\n" + "="*50)
    print("📄 PDF COMBINER & ZIP ARCHIVER")
    print("="*50)
    
    while True:
        dir_input = input("\nEnter directory path (or 'quit' to exit): ").strip().strip('"\'')
        
        if dir_input.lower() in ['exit', 'quit', '']:
            return None
            
        dir_path = Path(dir_input)
        if not dir_path.is_dir():
            logger.error("Invalid directory. Please try again.")
            continue
            
        if not any(f.suffix.lower() == '.pdf' for f in dir_path.iterdir() if f.is_file()):
            logger.warning("No PDF files found in the specified directory.")
            continue
            
        return dir_path

def main():
    """Main entrypoint with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Merge, move, and zip PDF files in a directory.")
    parser.add_argument("-d", "--dir", type=str, help="Target directory path", default=None)
    args = parser.parse_args()
    
    directory = Path(args.dir) if args.dir else get_directory_from_user()
    
    if directory:
        process_directory(directory)
    else:
        logger.info("Operation cancelled.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        logger.info("Operation cancelled by user.")
    except Exception as e:
        logger.critical(f"An unexpected fatal error occurred: {e}", exc_info=True)