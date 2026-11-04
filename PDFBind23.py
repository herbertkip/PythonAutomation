"""
Modernized & optimized PDFBind2.py
"""
import argparse
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional, List

# Optional fast backend: pikepdf (QPDF) is ~5-10x faster than pypdf for merging.
try:
    import pikepdf  # type: ignore
    _HAS_PIKEPDF = True
except ImportError:
    _HAS_PIKEPDF = False
    from pypdf import PdfWriter

# Configure standardized logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def list_pdfs(directory: Path) -> List[Path]:
    """Fast one-pass listing of PDF files using os.scandir (avoids extra stat calls)."""
    pdfs: List[Path] = []
    with os.scandir(directory) as it:
        for entry in it:
            # DirEntry caches the is_file() result from the directory read on most platforms.
            if entry.name.lower().endswith(".pdf") and entry.is_file():
                pdfs.append(Path(entry.path))
    pdfs.sort(key=lambda p: p.name)
    return pdfs


def merge_pdfs(pdf_files: List[Path], output_path: Path) -> bool:
    """Merges multiple PDF files into a single output file."""
    logger.info(f"Combining {len(pdf_files)} PDF files...")
    try:
        if _HAS_PIKEPDF:
            # Fast path: QPDF-backed merge. Keep source handles alive until save().
            dst = pikepdf.Pdf.new()
            sources = [pikepdf.open(f) for f in pdf_files]
            try:
                for src in sources:
                    dst.pages.extend(src.pages)
                dst.save(output_path)
            finally:
                dst.close()
                for src in sources:
                    src.close()
        else:
            merger = PdfWriter()
            for pdf_file in pdf_files:
                merger.append(str(pdf_file))
            with open(output_path, "wb") as fh:
                merger.write(fh)
            merger.close()

        logger.info(f"Successfully created: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to merge PDFs: {e}")
        return False


def move_to_drawings(pdf_files: List[Path], drawings_folder: Path) -> List[Path]:
    """Moves original PDFs into DRAWINGS. Returns list of destination paths."""
    logger.info("Moving original PDFs to DRAWINGS folder...")
    drawings_folder.mkdir(parents=True, exist_ok=True)

    moved: List[Path] = []
    for pdf_file in pdf_files:
        dest = drawings_folder / pdf_file.name
        try:
            shutil.move(str(pdf_file), str(dest))
            moved.append(dest)
        except OSError as e:
            logger.error(f"Error moving {pdf_file.name}: {e}")
    return moved


def create_zip_archive(
    directory: Path, drawings_folder: Path, moved_files: List[Path]
) -> Optional[Path]:
    """Creates a ZIP archive of the DRAWINGS folder."""
    directory_name = directory.name
    first_word = directory_name.split()[0] if directory_name.strip() else "Archive"
    zip_path = directory / f"{first_word} DWG.zip"

    logger.info(f"Creating ZIP archive: {zip_path.name}")

    try:
        # ZIP_STORED: PDFs are already internally compressed, so DEFLATE adds
        # significant CPU cost for negligible size savings. This is the single
        # biggest speedup in the whole pipeline.
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zipf:
            for file_path in moved_files:
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)

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

    pdf_files = list_pdfs(directory)
    if not pdf_files:
        logger.warning(f"No PDF files found in '{directory}'")
        return False

    logger.info(f"Processing directory: {directory}")

    drawings_folder = directory / "DRAWINGS"
    output_path = directory / f"{directory.name} Binder.pdf"

    if not merge_pdfs(pdf_files, output_path):
        return False

    moved = move_to_drawings(pdf_files, drawings_folder)
    create_zip_archive(directory, drawings_folder, moved)

    logger.info("Process completed successfully.")
    return True


def get_directory_from_user() -> Optional[Path]:
    """Interactive fallback for user input when run without CLI arguments."""
    print("\n" + "=" * 50)
    print("📄 PDF COMBINER & ZIP ARCHIVER")
    print("=" * 50)

    while True:
        dir_input = input("\nEnter directory path (or 'quit' to exit): ").strip().strip("\"'")

        if dir_input.lower() in ("exit", "quit", ""):
            return None

        dir_path = Path(dir_input)
        if not dir_path.is_dir():
            logger.error("Invalid directory. Please try again.")
            continue

        if not list_pdfs(dir_path):
            logger.warning("No PDF files found in the specified directory.")
            continue

        return dir_path


def main():
    """Main entrypoint with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Merge, move, and zip PDF files in a directory."
    )
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