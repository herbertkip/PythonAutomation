#!/usr/bin/env python3
"""
ProCore Tools Suite - GUI Application
Version: 1.0.0
A comprehensive GUI for file searching, drawing extraction, and folder creation.
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
import threading

# Try to import PyQt5, fallback to PySide6 if needed
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    try:
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
    except ImportError:
        print("ERROR: PyQt5 or PySide6 is required. Install with: pip install PyQt5")
        sys.exit(1)

# ============================================================================
# BACKEND LOGIC (Reused from combined script)
# ============================================================================

@dataclass
class FileInfo:
    path: str
    size: int
    modified: datetime
    created: datetime

@dataclass
class ProcessResult:
    total_files: int = 0
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    details: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []

class FolderType(Enum):
    RELEASE = "RELEASE"
    SUB = "SUB"
    FIELD = "FIELD"
    APPRV = "APPRV"
    RECD = "RECD"

class FileSearchEngine:
    @staticmethod
    def get_file_info(filepath: str) -> Optional[FileInfo]:
        try:
            stat_info = os.stat(filepath)
            return FileInfo(
                path=filepath,
                size=stat_info.st_size,
                modified=datetime.fromtimestamp(stat_info.st_mtime),
                created=datetime.fromtimestamp(stat_info.st_ctime)
            )
        except (OSError, FileNotFoundError):
            return None
    
    @staticmethod
    def search_files(directory: str, filename_pattern: str, 
                     max_results: int = 1000) -> List[FileInfo]:
        results = []
        pattern = filename_pattern.lower()
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if pattern in file.lower():
                        full_path = os.path.join(root, file)
                        file_info = FileSearchEngine.get_file_info(full_path)
                        if file_info:
                            results.append(file_info)
                        if len(results) >= max_results:
                            return results
        except Exception as e:
            logging.error(f"Error searching files: {e}")
            
        return results

class DrawingExtractor:
    @staticmethod
    def get_drawing_number(filename: str) -> str:
        name = filename
        if name.lower().endswith('.pdf'):
            name = name[:-4]
        if '-' in name:
            return name.split('-')[0]
        return name
    
    @staticmethod
    def extract_drawings(root_directory: Path, conflict_strategy: str = 'rename') -> ProcessResult:
        result = ProcessResult()
        drawings_dir = root_directory / "DRAWINGS"
        drawings_dir.mkdir(exist_ok=True)
        
        pdf_files = []
        for ext in ['*.pdf', '*.PDF']:
            pdf_files.extend(root_directory.rglob(ext))
        
        result.total_files = len(pdf_files)
        
        for pdf_path in pdf_files:
            try:
                sheet_number = DrawingExtractor.get_drawing_number(pdf_path.name)
                destination_path = drawings_dir / f"{sheet_number}.pdf"
                
                if not destination_path.exists():
                    shutil.copy2(pdf_path, destination_path)
                    result.processed += 1
                    result.details.append(f"Copied: {sheet_number}.pdf")
                else:
                    if conflict_strategy == 'skip':
                        result.skipped += 1
                        result.details.append(f"Skipped: {sheet_number}.pdf")
                    elif conflict_strategy == 'rename':
                        counter = 1
                        while True:
                            new_name = f"{sheet_number}_{counter}.pdf"
                            new_path = drawings_dir / new_name
                            if not new_path.exists():
                                shutil.copy2(pdf_path, new_path)
                                result.processed += 1
                                result.details.append(f"Copied: {new_name}")
                                break
                            counter += 1
                    elif conflict_strategy == 'overwrite':
                        shutil.copy2(pdf_path, destination_path)
                        result.processed += 1
                        result.details.append(f"Overwrote: {sheet_number}.pdf")
            except Exception as e:
                result.errors += 1
                result.details.append(f"Error: {pdf_path.name} - {e}")
        
        return result

class FolderCreator:
    @staticmethod
    def create_folder(directory: str, folder_type: FolderType, 
                     number: int) -> tuple:
        date_str = datetime.now().strftime("%m-%d-%y")
        number_str = f"{number:03d}"
        folder_name = f"{folder_type.value}#{number_str} - ({date_str})"
        full_path = os.path.join(directory, folder_name)
        
        try:
            os.makedirs(full_path, exist_ok=False)
            return True, folder_name, full_path
        except FileExistsError:
            return False, folder_name, f"Folder already exists at {full_path}"
        except Exception as e:
            return False, folder_name, str(e)

# ============================================================================
# GUI THREAD WORKERS
# ============================================================================

class SearchWorker(QThread):
    """Worker thread for file search operations"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, directory: str, filename: str):
        super().__init__()
        self.directory = directory
        self.filename = filename
    
    def run(self):
        try:
            results = FileSearchEngine.search_files(self.directory, self.filename)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class ExtractWorker(QThread):
    """Worker thread for drawing extraction"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(ProcessResult)
    error = pyqtSignal(str)
    
    def __init__(self, directory: str, conflict_strategy: str):
        super().__init__()
        self.directory = directory
        self.conflict_strategy = conflict_strategy
    
    def run(self):
        try:
            result = DrawingExtractor.extract_drawings(
                Path(self.directory), 
                self.conflict_strategy
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# ============================================================================
# MAIN GUI APPLICATION
# ============================================================================

class ProCoreToolsGUI(QMainWindow):
    """Main GUI window for ProCore Tools Suite"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProCore Tools Suite")
        self.setMinimumSize(900, 700)
        self.setWindowIcon(self.create_icon())
        
        # Apply modern style
        self.setup_style()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        self.create_header(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.search_tab = SearchTab(self)
        self.extract_tab = ExtractTab(self)
        self.folder_tab = FolderTab(self)
        
        self.tab_widget.addTab(self.search_tab, "🔍 Search")
        self.tab_widget.addTab(self.extract_tab, "📄 Extract")
        self.tab_widget.addTab(self.folder_tab, "📂 Create Folder")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def create_header(self, layout: QVBoxLayout):
        """Create application header"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 5px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        
        title = QLabel("🏗️  ProCore Tools Suite")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        header_layout.addWidget(version)
        
        layout.addWidget(header_widget)
    
    def setup_style(self):
        """Apply modern dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                border: 1