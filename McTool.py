#!/usr/bin/env python3
"""
ProCore Tools Suite - Combined File Management Utility
Version: 1.0.0
Author: Combined from FindFile, ProEx2, and RN scripts

A comprehensive tool for file searching, drawing extraction, and folder creation.
"""

import os
import sys
import shutil
import glob
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """Configuration settings for the application"""
    max_results: int = 1000
    default_conflict_strategy: str = 'rename'
    log_file: str = "procore_tools.log"
    results_dir: str = "results"


class FolderType(Enum):
    """Enumeration of folder types for RN functionality"""
    RELEASE = "RELEASE"
    SUB = "SUB"
    FIELD = "FIELD"
    APPRV = "APPRV"
    RECD = "RECD"


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_file: str = "procore_tools.log") -> None:
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FileInfo:
    """Data structure for file information"""
    path: str
    size: int
    modified: datetime
    created: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'path': self.path,
            'size': self.size,
            'modified': self.modified.isoformat(),
            'created': self.created.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileInfo':
        """Create FileInfo from dictionary"""
        return cls(
            path=data['path'],
            size=data['size'],
            modified=datetime.fromisoformat(data['modified']),
            created=datetime.fromisoformat(data['created'])
        )


@dataclass
class ProcessResult:
    """Data structure for processing results"""
    total_files: int = 0
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    details: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


# ============================================================================
# FILE SEARCH ENGINE (FindFile functionality)
# ============================================================================

class FileSearchEngine:
    """Handles file searching functionality"""
    
    @staticmethod
    def get_file_info(filepath: str) -> Optional[FileInfo]:
        """Get file information including modification time and size"""
        try:
            stat_info = os.stat(filepath)
            return FileInfo(
                path=filepath,
                size=stat_info.st_size,
                modified=datetime.fromtimestamp(stat_info.st_mtime),
                created=datetime.fromtimestamp(stat_info.st_ctime)
            )
        except (OSError, FileNotFoundError) as e:
            logging.error(f"Error getting file info for {filepath}: {e}")
            return None
    
    @staticmethod
    def search_files(directory: str, filename_pattern: str, 
                     case_sensitive: bool = False,
                     recursive: bool = True,
                     max_results: int = 1000) -> List[FileInfo]:
        """Search for files matching pattern in directory"""
        results = []
        pattern = filename_pattern if case_sensitive else filename_pattern.lower()
        
        try:
            for root, dirs, files in os.walk(directory):
                if not recursive:
                    break
                    
                for file in files:
                    # Check if filename matches
                    check_name = file if case_sensitive else file.lower()
                    if pattern in check_name:
                        full_path = os.path.join(root, file)
                        file_info = FileSearchEngine.get_file_info(full_path)
                        if file_info:
                            results.append(file_info)
                            
                    if len(results) >= max_results:
                        logging.warning(f"Reached maximum results limit ({max_results})")
                        return results
                        
        except PermissionError as e:
            logging.error(f"Permission denied: {e}")
        except Exception as e:
            logging.error(f"Error searching files: {e}")
            
        return results
    
    @staticmethod
    def search_by_extensions(directory: str, extensions: List[str], 
                            recursive: bool = True) -> List[Path]:
        """Search for files with specific extensions"""
        results = []
        root_path = Path(directory)
        
        for ext in extensions:
            pattern = f"*.{ext.lower()}" if not ext.startswith('.') else f"*{ext.lower()}"
            if recursive:
                results.extend(root_path.rglob(pattern))
                # Also check uppercase variants
                results.extend(root_path.rglob(pattern.upper()))
            else:
                results.extend(root_path.glob(pattern))
                results.extend(root_path.glob(pattern.upper()))
                
        return list(set(results))
    
    @staticmethod
    def save_results(results: List[FileInfo], output_file: str, 
                     search_term: str, directory: str) -> bool:
        """Save search results to a file"""
        try:
            with open(output_file, 'w') as f:
                f.write("File Search Results\n")
                f.write("=" * 80 + "\n")
                f.write(f"Search: '{search_term}'\n")
                f.write(f"Directory: '{directory}'\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Files Found: {len(results)}\n")
                f.write("=" * 80 + "\n\n")
                
                sorted_results = sorted(results, key=lambda x: x.modified, reverse=True)
                
                for i, file in enumerate(sorted_results, 1):
                    f.write(f"File #{i}\n")
                    f.write(f"  Location: {file.path}\n")
                    f.write(f"  Modified: {file.modified.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"  Size: {file.size:,} bytes\n")
                    f.write("-" * 40 + "\n")
                    
            return True
        except Exception as e:
            logging.error(f"Failed to save results: {e}")
            return False


# ============================================================================
# DRAWING EXTRACTOR (ProEx2 functionality)
# ============================================================================

class DrawingExtractor:
    """Handles PDF drawing extraction and organization"""
    
    @staticmethod
    def get_drawing_number(filename: str) -> str:
        """Extract the drawing sheet number from the filename"""
        # Remove .pdf extension if present
        name = filename
        if name.lower().endswith('.pdf'):
            name = name[:-4]
        
        # Split on first dash and take the first part
        if '-' in name:
            return name.split('-')[0]
        else:
            return name
    
    @staticmethod
    def handle_duplicate(destination_dir: Path, sheet_number: str, 
                        source_path: Path, conflict_strategy: str = 'rename') -> Tuple[bool, str]:
        """Handle duplicate sheet numbers"""
        destination_path = destination_dir / f"{sheet_number}.pdf"
        
        if not destination_path.exists():
            shutil.copy2(source_path, destination_path)
            return True, f"Copied: {sheet_number}.pdf"
        else:
            if conflict_strategy == 'skip':
                return False, f"Skipped: {sheet_number}.pdf (already exists)"
            elif conflict_strategy == 'rename':
                counter = 1
                while True:
                    new_name = f"{sheet_number}_{counter}.pdf"
                    new_path = destination_dir / new_name
                    if not new_path.exists():
                        shutil.copy2(source_path, new_path)
                        return True, f"Copied: {new_name} (duplicate of {sheet_number})"
                    counter += 1
            elif conflict_strategy == 'overwrite':
                shutil.copy2(source_path, destination_path)
                return True, f"Overwrote: {sheet_number}.pdf"
            else:
                return False, f"Unknown conflict strategy: {conflict_strategy}"
    
    @staticmethod
    def extract_drawings(root_directory: Path, conflict_strategy: str = 'rename') -> ProcessResult:
        """Extract all PDF drawings to a DRAWINGS folder"""
        result = ProcessResult()
        
        # Create output folder
        drawings_dir = root_directory / "DRAWINGS"
        drawings_dir.mkdir(exist_ok=True)
        
        # Find all PDF files
        pdf_files = FileSearchEngine.search_by_extensions(
            str(root_directory), 
            ['pdf', 'PDF'],
            recursive=True
        )
        
        result.total_files = len(pdf_files)
        
        if not pdf_files:
            result.details.append("No PDF files found.")
            return result
        
        # Process each PDF file
        for pdf_path in pdf_files:
            try:
                original_filename = pdf_path.name
                sheet_number = DrawingExtractor.get_drawing_number(original_filename)
                
                success, message = DrawingExtractor.handle_duplicate(
                    drawings_dir, sheet_number, pdf_path, conflict_strategy
                )
                
                result.details.append(message)
                if success:
                    result.processed += 1
                else:
                    result.skipped += 1
                    
            except Exception as e:
                result.errors += 1
                error_msg = f"Error processing {pdf_path.name}: {e}"
                result.details.append(error_msg)
                logging.error(error_msg)
        
        return result


# ============================================================================
# FOLDER CREATOR (RN functionality)
# ============================================================================

class FolderCreator:
    """Handles folder creation with naming conventions"""
    
    @staticmethod
    def create_folder(directory: str, folder_type: FolderType, 
                     number: int, date: Optional[datetime] = None) -> Tuple[bool, str, str]:
        """Create a folder with the specified naming convention"""
        if date is None:
            date = datetime.now()
            
        date_str = date.strftime("%m-%d-%y")
        number_str = f"{number:03d}"
        
        folder_name = f"{folder_type.value}#{number_str} - ({date_str})"
        full_path = os.path.join(directory, folder_name)
        
        try:
            os.makedirs(full_path, exist_ok=False)
            return True, folder_name, full_path
        except FileExistsError:
            return False, folder_name, f"Folder already exists at {full_path}"
        except PermissionError:
            return False, folder_name, f"Permission denied at {directory}"
        except Exception as e:
            return False, folder_name, str(e)
    
    @staticmethod
    def get_folder_types() -> Dict[int, FolderType]:
        """Get available folder types"""
        return {i: ft for i, ft in enumerate(FolderType, 1)}
    
    @staticmethod
    def display_folder_types() -> None:
        """Display folder type options"""
        print("\nFolder Type Options:")
        for num, ft in FolderCreator.get_folder_types().items():
            print(f"  {num} - {ft.value}")
    
    @staticmethod
    def validate_directory(path: str) -> bool:
        """Validate if directory exists"""
        return os.path.exists(path) and os.path.isdir(path)


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class ProCoreTools:
    """Main application class that combines all functionality"""
    
    def __init__(self):
        self.config = Config()
        setup_logging(self.config.log_file)
        self.search_engine = FileSearchEngine()
        self.drawing_extractor = DrawingExtractor()
        self.folder_creator = FolderCreator()
    
    def run_search_mode(self, directory: str, filename: str, 
                        save_results: bool = True) -> List[FileInfo]:
        """Run file search mode"""
        print(f"\n🔎 Searching for '{filename}' in '{directory}'...")
        print("This may take a moment...\n")
        
        results = self.search_engine.search_files(
            directory, 
            filename,
            max_results=self.config.max_results
        )
        
        # Display results
        self._display_search_results(results, filename, directory)
        
        # Save results if requested
        if save_results and results:
            self._save_search_results(results, filename, directory)
            
        return results
    
    def run_extract_mode(self, directory: str, 
                        conflict_strategy: str = 'rename') -> ProcessResult:
        """Run drawing extraction mode"""
        print("\n" + "=" * 60)
        print("PROCORE DRAWINGS EXTRACTOR")
        print("=" * 60)
        
        root_path = Path(directory)
        if not root_path.exists() or not root_path.is_dir():
            print(f"Error: Directory '{directory}' does not exist.")
            return ProcessResult()
        
        print(f"\n✓ Output folder will be: {root_path / 'DRAWINGS'}")
        
        result = self.drawing_extractor.extract_drawings(root_path, conflict_strategy)
        
        # Display results
        self._display_extraction_results(result)
        
        return result
    
    def run_create_folder_mode(self, directory: str, folder_type: FolderType, 
                             number: int) -> None:
        """Run folder creation mode"""
        print("\n" + "=" * 50)
        print("📂 FOLDER CREATION")
        print("=" * 50)
        
        if not self.folder_creator.validate_directory(directory):
            print(f"❌ Directory '{directory}' does not exist.")
            return
        
        success, folder_name, message = self.folder_creator.create_folder(
            directory, folder_type, number
        )
        
        if success:
            print(f"\n✅ Folder created successfully!")
            print(f"📁 Location: {message}")
        else:
            print(f"\n❌ Error: {message}")
    
    def _display_search_results(self, results: List[FileInfo], 
                               search_term: str, directory: str) -> None:
        """Display search results in a formatted manner"""
        if not results:
            print("\n❌ No files found matching the search criteria.")
            return
        
        print(f"\n📁 Found {len(results)} file(s) matching your search:")
        print("=" * 80)
        
        # Sort by modification time (newest first)
        sorted_results = sorted(results, key=lambda x: x.modified, reverse=True)
        
        # Display all results (limit to 50 for readability)
        display_count = min(len(sorted_results), 50)
        for i, file in enumerate(sorted_results[:display_count], 1):
            print(f"\n📄 File #{i}")
            print(f"   📂 Location: {file.path}")
            print(f"   📅 Modified: {file.modified.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📦 Size: {file.size:,} bytes")
            print("-" * 80)
        
        if len(sorted_results) > 50:
            print(f"\n... and {len(sorted_results) - 50} more files")
        
        # Show the latest version
        latest = sorted_results[0]
        print(f"\n⭐ LATEST VERSION:")
        print(f"   📂 Location: {latest.path}")
        print(f"   📅 Modified: {latest.modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📦 Size: {latest.size:,} bytes")
    
    def _save_search_results(self, results: List[FileInfo], 
                            search_term: str, directory: str) -> None:
        """Save search results to a file"""
        # Create results directory if it doesn't exist
        results_dir = Path(self.config.results_dir)
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"file_search_results_{timestamp}.txt"
        
        if self.search_engine.save_results(results, str(output_file), search_term, directory):
            print(f"\n✅ Results saved to: {output_file}")
    
    def _display_extraction_results(self, result: ProcessResult) -> None:
        """Display drawing extraction results"""
        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"  Total PDF files found:   {result.total_files}")
        print(f"  Files processed:         {result.processed}")
        print(f"  Files skipped:           {result.skipped}")
        if result.errors > 0:
            print(f"  Errors encountered:      {result.errors}")
        
        # Show some details
        if result.details:
            print("\n  Details:")
            for detail in result.details[:10]:  # Show first 10 details
                print(f"    • {detail}")
            if len(result.details) > 10:
                print(f"    ... and {len(result.details) - 10} more items")


# ============================================================================
# INTERACTIVE MENU
# ============================================================================

class InteractiveMenu:
    """Interactive menu system for the application"""
    
    def __init__(self):
        self.tools = ProCoreTools()
    
    def display_menu(self) -> None:
        """Display the main menu"""
        print("\n" + "=" * 60)
        print("🏗️  PROCORE TOOLS SUITE")
        print("=" * 60)
        print("\nSelect an option:")
        print("  1. 🔍 Search for Files")
        print("  2. 📄 Extract Drawing PDFs")
        print("  3. 📂 Create Folder (RN format)")
        print("  4. ⚙️  Configure Settings")
        print("  5. ℹ️  About")
        print("  6. 🚪 Exit")
        print("-" * 60)
    
    def run(self) -> None:
        """Run the interactive menu"""
        while True:
            self.display_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self._run_search()
            elif choice == '2':
                self._run_extract()
            elif choice == '3':
                self._run_create_folder()
            elif choice == '4':
                self._run_config()
            elif choice == '5':
                self._run_about()
            elif choice == '6':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    def _run_search(self) -> None:
        """Run file search"""
        print("\n" + "=" * 50)
        print("🔍 FILE SEARCH")
        print("=" * 50)
        
        directory = input("\n📂 Enter directory path to search: ").strip()
        if not directory:
            print("❌ Directory path cannot be empty.")
            return
            
        directory = os.path.expanduser(directory)
        if not os.path.exists(directory) or not os.path.isdir(directory):
            print(f"❌ Directory '{directory}' does not exist or is not a valid directory.")
            return
        
        filename = input("🔍 Enter filename or part of filename to search: ").strip()
        if not filename:
            print("❌ Filename cannot be empty.")
            return
        
        self.tools.run_search_mode(directory, filename)
    
    def _run_extract(self) -> None:
        """Run drawing extraction"""
        print("\n" + "=" * 50)
        print("📄 DRAWING EXTRACTION")
        print("=" * 50)
        
        directory = input("\n📂 Enter root directory path: ").strip()
        if not directory:
            print("❌ Directory path cannot be empty.")
            return
            
        directory = os.path.expanduser(directory)
        if not os.path.exists(directory) or not os.path.isdir(directory):
            print(f"❌ Directory '{directory}' does not exist.")
            return
        
        # Conflict strategy
        print("\nChoose conflict handling strategy for duplicate sheet numbers:")
        print("  1. Rename duplicates (append _1, _2, etc.)")
        print("  2. Skip duplicates")
        print("  3. Overwrite duplicates")
        
        choice = input("Enter your choice (1-3) [default: 1]: ").strip()
        conflict_map = {'1': 'rename', '2': 'skip', '3': 'overwrite'}
        conflict_strategy = conflict_map.get(choice, 'rename')
        
        self.tools.run_extract_mode(directory, conflict_strategy)
    
    def _run_create_folder(self) -> None:
        """Run folder creation"""
        print("\n" + "=" * 50)
        print("📂 CREATE FOLDER")
        print("=" * 50)
        
        self.tools.folder_creator.display_folder_types()
        
        while True:
            try:
                type_choice = int(input("\nSelect folder type (1-5): "))
                folder_types = self.tools.folder_creator.get_folder_types()
                if type_choice in folder_types:
                    folder_type = folder_types[type_choice]
                    break
                else:
                    print("❌ Invalid choice. Please enter a number between 1 and 5.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
        
        while True:
            directory = input("\n📂 Enter the directory path where folder should be created: ").strip()
            directory = os.path.expanduser(directory)
            if self.tools.folder_creator.validate_directory(directory):
                break
            else:
                print("❌ Directory does not exist. Please enter a valid path.")
        
        while True:
            try:
                number = int(input("\n🔢 Enter the number value: "))
                if number >= 0:
                    break
                else:
                    print("❌ Please enter a non-negative number.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
        
        self.tools.run_create_folder_mode(directory, folder_type, number)
    
    def _run_config(self) -> None:
        """Run configuration"""
        print("\n" + "=" * 50)
        print("⚙️  CONFIGURATION")
        print("=" * 50)
        print(f"\nCurrent Settings:")
        print(f"  Max Results: {self.tools.config.max_results}")
        print(f"  Default Conflict Strategy: {self.tools.config.default_conflict_strategy}")
        print(f"  Log File: {self.tools.config.log_file}")
        print(f"  Results Directory: {self.tools.config.results_dir}")
        
        print("\nTo change these settings, edit the config file or source code.")
    
    def _run_about(self) -> None:
        """Display about information"""
        print("\n" + "=" * 50)
        print("ℹ️  ABOUT")
        print("=" * 50)
        print("\nProCore Tools Suite")
        print("Version: 1.0.0")
        print("\nA comprehensive file management utility combining:")
        print("  • File Search (FindFile)")
        print("  • Drawing Extractor (ProEx2)")
        print("  • Folder Creator (RN)")
        print("\nFeatures:")
        print("  • Recursive file searching with results sorting")
        print("  • PDF drawing extraction with duplicate handling")
        print("  • Folder creation with RN naming convention")
        print("  • Results saving and logging")
        print("  • Interactive and command-line modes")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="ProCore Tools Suite - File Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search -d /path/to/dir -f "drawing"
  %(prog)s extract -d /path/to/dir -c rename
  %(prog)s create -d /path/to/dir -t RELEASE -n 123
  %(prog)s interactive
        """
    )
    
    parser.add_argument('mode', nargs='?', choices=['search', 'extract', 'create', 'interactive'],
                       help='Operation mode to run')
    
    # Search mode arguments
    parser.add_argument('-d', '--directory', help='Directory path to operate on')
    parser.add_argument('-f', '--filename', help='Filename pattern to search for')
    
    # Extract mode arguments
    parser.add_argument('-c', '--conflict', choices=['rename', 'skip', 'overwrite'],
                       default='rename', help='Conflict resolution strategy')
    
    # Create mode arguments
    parser.add_argument('-t', '--type', choices=['RELEASE', 'SUB', 'FIELD', 'APPRV', 'RECD'],
                       help='Folder type for creation')
    parser.add_argument('-n', '--number', type=int, help='Number for folder creation')
    
    # General options
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--max-results', type=int, default=1000, 
                       help='Maximum number of search results')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save search results')
    
    return parser.parse_args()


def run_command_line(args):
    """Run the command line interface"""
    tools = ProCoreTools()
    tools.config.max_results = args.max_results
    
    if args.mode == 'interactive' or not args.mode:
        menu = InteractiveMenu()
        menu.run()
        return
    
    if args.mode == 'search':
        if not args.directory or not args.filename:
            print("❌ Error: Both directory and filename are required for search mode.")
            print("   Use: --directory DIR --filename PATTERN")
            sys.exit(1)
        
        tools.run_search_mode(args.directory, args.filename, not args.no_save)
    
    elif args.mode == 'extract':
        if not args.directory:
            print("❌ Error: Directory is required for extract mode.")
            print("   Use: --directory DIR")
            sys.exit(1)
        
        tools.run_extract_mode(args.directory, args.conflict)
    
    elif args.mode == 'create':
        if not args.directory or not args.type or args.number is None:
            print("❌ Error: Directory, type, and number are required for create mode.")
            print("   Use: --directory DIR --type TYPE --number NUM")
            sys.exit(1)
        
        folder_type = FolderType[args.type]
        tools.run_create_folder_mode(args.directory, folder_type, args.number)


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the application"""
    try:
        args = parse_arguments()
        
        # Set logging level
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Run the application
        run_command_line(args)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()