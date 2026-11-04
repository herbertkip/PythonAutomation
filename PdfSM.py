import os
import shutil
import glob
import sys
import subprocess
import platform


def get_folder_path():
    """Prompt user for folder path via command line."""
    while True:
        folder_path = input("\nEnter the full path to the folder containing the PDF: ").strip()
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


def find_pdf(folder_path):
    """Find PDF files in the specified folder."""
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    pdf_files = [f for f in pdf_files if not os.path.basename(f).startswith('~$')]

    if len(pdf_files) == 0:
        print(f"\nError: No PDF files found in '{folder_path}'")
        return None

    if len(pdf_files) > 1:
        print(f"\nWarning: Found {len(pdf_files)} PDF files:")
        for i, file in enumerate(pdf_files, 1):
            print(f"  {i}. {os.path.basename(file)}")
        while True:
            try:
                choice = input(f"Select file number (1-{len(pdf_files)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(pdf_files):
                    return pdf_files[idx]
                print(f"Invalid choice. Enter 1-{len(pdf_files)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                sys.exit(0)

    return pdf_files[0]


def get_sm_number():
    """Prompt for SM number via command line."""
    while True:
        sm_number = input("\nEnter the SM# number (e.g., 001): ").strip()
        if not sm_number:
            print("Error: SM number cannot be empty. Please try again.")
            continue

        sm_number = sm_number.replace('#', '').replace('SM', '').replace('sm', '').strip()
        try:
            return f"{int(sm_number):03d}"
        except ValueError:
            print(f"Error: '{sm_number}' is not a valid number. Please try again.")
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
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)


def rename_pdf_to_sm():
    """Main function to rename a PDF to SM#<number>.pdf and manage copies."""
    print("\n" + "=" * 60)
    print("PDF RENAMER WITH DRAWING DISTRIBUTION")
    print("=" * 60)

    folder_path = get_folder_path()
    print(f"\nSelected folder: {folder_path}")

    print("\nSearching for PDF files...")
    pdf_path = find_pdf(folder_path)
    if pdf_path is None:
        return

    pdf_filename = os.path.basename(pdf_path)
    print(f"Found PDF: {pdf_filename}")

    sm_number = get_sm_number()

    output_filename = f"SM#{sm_number}.pdf"
    output_path = os.path.join(folder_path, output_filename)

    if os.path.abspath(pdf_path) == os.path.abspath(output_path):
        print(f"\n[INFO] File is already named '{output_filename}'. No rename needed.")
    else:
        print(f"\nRenaming '{pdf_filename}' -> '{output_filename}'...")
        try:
            os.rename(pdf_path, output_path)
            print(f"[DONE] Renamed successfully.")
        except PermissionError:
            print(f"[ERROR] Permission denied. Close the file if it is open.")
            return
        except OSError as e:
            print(f"[ERROR] Rename failed: {e}")
            return

    if not os.path.exists(output_path):
        print(f"[ERROR] PDF not found at: {output_path}")
        return

    file_size = os.path.getsize(output_path)
    if file_size == 0:
        print("[ERROR] PDF file is empty (0 bytes).")
        return
    print(f"[INFO] File size: {file_size:,} bytes")

    drawings_folder = os.path.join(folder_path, "DRAWINGS")
    if not os.path.exists(drawings_folder):
        os.makedirs(drawings_folder)
        print(f"[DONE] Created DRAWINGS folder: {drawings_folder}")
    else:
        print("[INFO] DRAWINGS folder already exists.")

    num_copies = get_copy_count()

    print(f"\nCreating {num_copies} cop{'y' if num_copies == 1 else 'ies'} in DRAWINGS folder...")
    for i in range(num_copies):
        if num_copies == 1:
            copy_filename = output_filename
        else:
            copy_filename = f"SM#{sm_number}_copy{i + 1}.pdf"
        copy_path = os.path.join(drawings_folder, copy_filename)
        shutil.copy2(output_path, copy_path)
        print(f"  [DONE] Copy {i + 1}/{num_copies}: {copy_filename}")

    print("\n" + "=" * 60)
    print("PROCESS COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Source PDF:      {pdf_filename}")
    print(f"Renamed PDF:     {output_path}")
    print(f"Copies created:  {num_copies}")
    print(f"DRAWINGS folder: {drawings_folder}")
    print("=" * 60)


if __name__ == "__main__":
    # Preflight checks
    missing_libs = []
    try:
        import docx2pdf  # optional, kept for parity
    except ImportError:
        pass  # not required for PDF-only workflow

    if platform.system() != 'Windows':
        has_libreoffice = False
        for cmd in ['soffice', 'libreoffice']:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
                has_libreoffice = True
                break
            except Exception:
                continue
        if not has_libreoffice:
            print("\nWarning: LibreOffice not found (not required for PDF renaming).")
            print("  Install with: sudo apt-get install libreoffice  (Linux)")
            print("                brew install libreoffice          (macOS)")

    try:
        rename_pdf_to_sm()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except ImportError as e:
        print(f"\n[ERROR] Missing library: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)