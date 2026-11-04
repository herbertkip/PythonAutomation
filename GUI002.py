#!/usr/bin/env python3
"""
ProCore Tools Suite - GUI Application
Combined file management utility with graphical interface
"""

import os
import sys
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from dataclasses import dataclass
from enum import Enum
import logging


# ============================================================================
# BACKEND CLASSES (from combined script)
# ============================================================================

@dataclass
class FileInfo:
    """Data structure for file information"""
    path: str
    size: int
    modified: datetime
    created: datetime
    
    def get_size_str(self) -> str:
        """Get human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} TB"


class FolderType(Enum):
    """Enumeration of folder types"""
    RELEASE = "RELEASE"
    SUB = "SUB"
    FIELD = "FIELD"
    APPRV = "APPRV"
    RECD = "RECD"


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
        except (OSError, FileNotFoundError):
            return None
    
    @staticmethod
    def search_files(directory: str, filename_pattern: str, 
                     case_sensitive: bool = False,
                     max_results: int = 1000) -> List[FileInfo]:
        """Search for files matching pattern in directory"""
        results = []
        pattern = filename_pattern if case_sensitive else filename_pattern.lower()
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    check_name = file if case_sensitive else file.lower()
                    if pattern in check_name:
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
    """Handles PDF drawing extraction"""
    
    @staticmethod
    def get_drawing_number(filename: str) -> str:
        """Extract the drawing sheet number from the filename"""
        name = filename
        if name.lower().endswith('.pdf'):
            name = name[:-4]
        if '-' in name:
            return name.split('-')[0]
        return name
    
    @staticmethod
    def handle_duplicate(destination_dir: Path, sheet_number: str, 
                        source_path: Path, conflict_strategy: str = 'rename',
                        callback=None) -> tuple:
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
            return False, f"Unknown conflict strategy: {conflict_strategy}"


class FolderCreator:
    """Handles folder creation"""
    
    @staticmethod
    def create_folder(directory: str, folder_type: FolderType, 
                     number: int, date: Optional[datetime] = None) -> tuple:
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


# ============================================================================
# GUI APPLICATION CLASS
# ============================================================================

class ProCoreGUI:
    """Main GUI application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ProCore Tools Suite v1.0")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Set theme colors
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#2c3e50',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'header_bg': '#2c3e50',
            'header_fg': 'white'
        }
        
        # Initialize backend
        self.search_engine = FileSearchEngine()
        self.drawing_extractor = DrawingExtractor()
        self.folder_creator = FolderCreator()
        
        # State variables
        self.search_results = []
        self.is_running = False
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Header.TFrame', background=self.colors['header_bg'])
        style.configure('Header.TLabel', 
                       background=self.colors['header_bg'],
                       foreground=self.colors['header_fg'],
                       font=('Helvetica', 16, 'bold'))
        
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       font=('Helvetica', 10, 'bold'))
        style.map('Accent.TButton',
                 background=[('active', '#2980b9')])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white')
        style.map('Success.TButton',
                 background=[('active', '#219a52')])
        
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main_frame)
        
        # Tab control
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Create tabs
        self.create_search_tab()
        self.create_extract_tab()
        self.create_create_tab()
        self.create_settings_tab()
        self.create_about_tab()
        
        # Status bar
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        """Create application header"""
        header = ttk.Frame(parent, style='Header.TFrame')
        header.pack(fill='x', pady=(0, 10))
        
        title = ttk.Label(header, text="🏗️  PROCORE TOOLS SUITE", style='Header.TLabel')
        title.pack(side='left', padx=15, pady=10)
        
        version = ttk.Label(header, text="v1.0",
                           background=self.colors['header_bg'],
                           foreground='#bdc3c7',
                           font=('Helvetica', 10))
        version.pack(side='right', padx=15)
        
    def create_search_tab(self):
        """Create the search tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔍 Search")
        
        # Input frame
        input_frame = ttk.LabelFrame(tab, text="Search Parameters", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        # Directory
        ttk.Label(input_frame, text="Directory:").grid(row=0, column=0, sticky='e', padx=5)
        self.search_dir = ttk.Entry(input_frame, width=60)
        self.search_dir.grid(row=0, column=1, padx=5, sticky='ew')
        ttk.Button(input_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.search_dir)).grid(row=0, column=2, padx=5)
        
        # Filename
        ttk.Label(input_frame, text="Filename pattern:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.search_pattern = ttk.Entry(input_frame, width=60)
        self.search_pattern.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # Options
        options_frame = ttk.Frame(input_frame)
        options_frame.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Recursive search", 
                       variable=self.recursive_var).pack(side='left', padx=5)
        
        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Case sensitive",
                       variable=self.case_sensitive_var).pack(side='left', padx=5)
        
        # Buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=3, column=1, padx=5, pady=10, sticky='w')
        
        self.search_btn = ttk.Button(btn_frame, text="🔎 Search Now", 
                                     style='Accent.TButton',
                                     command=self.start_search)
        self.search_btn.pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="💾 Save Results", 
                  command=self.save_results).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="🔄 Clear", 
                  command=self.clear_results).pack(side='left', padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(tab, text="Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Results tree
        columns = ('#', 'Filename', 'Size', 'Modified', 'Location')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=12)
        
        self.results_tree.heading('#', text='#')
        self.results_tree.heading('Filename', text='Filename')
        self.results_tree.heading('Size', text='Size')
        self.results_tree.heading('Modified', text='Modified')
        self.results_tree.heading('Location', text='Location')
        
        self.results_tree.column('#', width=50, anchor='center')
        self.results_tree.column('Filename', width=200)
        self.results_tree.column('Size', width=100, anchor='e')
        self.results_tree.column('Modified', width=150, anchor='center')
        self.results_tree.column('Location', width=400)
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(results_frame, orient='vertical', 
                                   command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.results_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Results info
        info_frame = ttk.Frame(results_frame)
        info_frame.pack(fill='x', pady=(5, 0))
        
        self.results_count = ttk.Label(info_frame, text="Found 0 files")
        self.results_count.pack(side='left')
        
        # Double-click to open location
        self.results_tree.bind('<Double-Button-1>', self.open_file_location)
        
    def create_extract_tab(self):
        """Create the extract tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📄 Extract")
        
        # Input frame
        input_frame = ttk.LabelFrame(tab, text="Extraction Settings", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        # Directory
        ttk.Label(input_frame, text="Source Directory:").grid(row=0, column=0, sticky='e', padx=5)
        self.extract_dir = ttk.Entry(input_frame, width=60)
        self.extract_dir.grid(row=0, column=1, padx=5, sticky='ew')
        ttk.Button(input_frame, text="Browse",
                  command=lambda: self.browse_directory(self.extract_dir)).grid(row=0, column=2, padx=5)
        
        # Conflict strategy
        ttk.Label(input_frame, text="Conflict Strategy:").grid(row=1, column=0, sticky='e', padx=5, pady=10)
        self.conflict_var = tk.StringVar(value='rename')
        conflict_frame = ttk.Frame(input_frame)
        conflict_frame.grid(row=1, column=1, padx=5, pady=10, sticky='w')
        
        ttk.Radiobutton(conflict_frame, text="Rename duplicates", 
                       variable=self.conflict_var, value='rename').pack(side='left', padx=5)
        ttk.Radiobutton(conflict_frame, text="Skip duplicates",
                       variable=self.conflict_var, value='skip').pack(side='left', padx=5)
        ttk.Radiobutton(conflict_frame, text="Overwrite duplicates",
                       variable=self.conflict_var, value='overwrite').pack(side='left', padx=5)
        
        # Extract button
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=1, padx=5, pady=10, sticky='w')
        
        self.extract_btn = ttk.Button(btn_frame, text="▶ Start Extraction",
                                      style='Accent.TButton',
                                      command=self.start_extraction)
        self.extract_btn.pack(side='left', padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(tab, text="Extraction Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Stats
        stats_frame = ttk.Frame(results_frame)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        self.extract_stats = {}
        stats = [('Total', '0'), ('Processed', '0'), ('Skipped', '0'), ('Errors', '0')]
        for i, (label, value) in enumerate(stats):
            frame = ttk.Frame(stats_frame)
            frame.pack(side='left', padx=20)
            ttk.Label(frame, text=label + ":", font=('Helvetica', 10, 'bold')).pack(side='left')
            self.extract_stats[label] = ttk.Label(frame, text=value, font=('Helvetica', 10))
            self.extract_stats[label].pack(side='left', padx=5)
        
        # Log area
        log_frame = ttk.Frame(results_frame)
        log_frame.pack(fill='both', expand=True)
        
        self.extract_log = scrolledtext.ScrolledText(log_frame, height=12, wrap='word')
        self.extract_log.pack(fill='both', expand=True)
        
        # Configure log tags
        self.extract_log.tag_config('success', foreground='green')
        self.extract_log.tag_config('warning', foreground='orange')
        self.extract_log.tag_config('error', foreground='red')
        
        # Output location
        output_frame = ttk.Frame(results_frame)
        output_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(output_frame, text="Output:").pack(side='left')
        self.extract_output = ttk.Label(output_frame, text="DRAWINGS folder in source directory")
        self.extract_output.pack(side='left', padx=5)
        
        ttk.Button(output_frame, text="📂 Open Output Folder",
                  command=self.open_extract_output).pack(side='right')
        
    def create_create_tab(self):
        """Create the folder creation tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📂 Create")
        
        # Input frame
        input_frame = ttk.LabelFrame(tab, text="Folder Creation", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        # Directory
        ttk.Label(input_frame, text="Location:").grid(row=0, column=0, sticky='e', padx=5)
        self.create_dir = ttk.Entry(input_frame, width=60)
        self.create_dir.grid(row=0, column=1, padx=5, sticky='ew')
        ttk.Button(input_frame, text="Browse",
                  command=lambda: self.browse_directory(self.create_dir)).grid(row=0, column=2, padx=5)
        
        # Folder type
        ttk.Label(input_frame, text="Folder Type:").grid(row=1, column=0, sticky='e', padx=5, pady=10)
        self.folder_type_var = tk.StringVar(value='RELEASE')
        type_frame = ttk.Frame(input_frame)
        type_frame.grid(row=1, column=1, padx=5, pady=10, sticky='w')
        
        types = ['RELEASE', 'SUB', 'FIELD', 'APPRV', 'RECD']
        self.type_buttons = []
        for i, ft in enumerate(types):
            rb = ttk.Radiobutton(type_frame, text=ft, variable=self.folder_type_var, value=ft)
            rb.pack(side='left', padx=5)
            self.type_buttons.append(rb)
        
        # Number
        ttk.Label(input_frame, text="Number:").grid(row=2, column=0, sticky='e', padx=5)
        self.create_number = ttk.Entry(input_frame, width=20)
        self.create_number.grid(row=2, column=1, padx=5, sticky='w')
        ttk.Label(input_frame, text="(will be formatted as 3 digits)").grid(row=2, column=2, sticky='w', padx=5)
        
        # Preview
        ttk.Label(input_frame, text="Preview:").grid(row=3, column=0, sticky='e', padx=5, pady=10)
        self.preview_label = ttk.Label(input_frame, text="", font=('Helvetica', 10, 'bold'))
        self.preview_label.grid(row=3, column=1, padx=5, pady=10, sticky='w')
        
        # Update preview on change
        self.create_number.bind('<KeyRelease>', self.update_preview)
        self.folder_type_var.trace('w', lambda *args: self.update_preview())
        
        # Buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=4, column=1, padx=5, pady=10, sticky='w')
        
        ttk.Button(btn_frame, text="📁 Create Folder",
                  style='Success.TButton',
                  command=self.create_folder).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="📋 Preview Only",
                  command=self.show_preview).pack(side='left', padx=5)
        
        # History
        history_frame = ttk.LabelFrame(tab, text="Recent Folders", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.history_list = ttk.Treeview(history_frame, columns=('Date', 'Folder'), 
                                        show='headings', height=6)
        self.history_list.heading('Date', text='Date Created')
        self.history_list.heading('Folder', text='Folder Path')
        self.history_list.column('Date', width=150)
        self.history_list.column('Folder', width=600)
        
        hist_scroll = ttk.Scrollbar(history_frame, orient='vertical',
                                   command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=hist_scroll.set)
        
        self.history_list.pack(side='left', fill='both', expand=True)
        hist_scroll.pack(side='right', fill='y')
        
    def create_settings_tab(self):
        """Create the settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Settings")
        
        # Settings frame
        settings_frame = ttk.LabelFrame(tab, text="Application Settings", padding=15)
        settings_frame.pack(fill='x', padx=10, pady=10)
        
        # Max results
        ttk.Label(settings_frame, text="Maximum search results:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.max_results_var = tk.StringVar(value='1000')
        ttk.Entry(settings_frame, textvariable=self.max_results_var, width=20).grid(row=0, column=1, sticky='w', padx=5)
        
        # Default conflict strategy
        ttk.Label(settings_frame, text="Default conflict strategy:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.default_conflict = ttk.Combobox(settings_frame, values=['rename', 'skip', 'overwrite'], width=15)
        self.default_conflict.set('rename')
        self.default_conflict.grid(row=1, column=1, sticky='w', padx=5)
        
        # Save button
        ttk.Button(settings_frame, text="💾 Save Settings",
                  command=self.save_settings).grid(row=2, column=1, sticky='w', padx=5, pady=10)
        
        # Info frame
        info_frame = ttk.LabelFrame(tab, text="System Information", padding=15)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        info_text = f"""
Python Version: {sys.version.split()[0]}
Operating System: {os.name}
Current Working Directory: {os.getcwd()}
        """
        ttk.Label(info_frame, text=info_text, justify='left').pack(anchor='w')
        
    def create_about_tab(self):
        """Create the about tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="ℹ️ About")
        
        about_frame = ttk.Frame(tab)
        about_frame.pack(expand=True, fill='both', padx=50, pady=50)
        
        ttk.Label(about_frame, text="🏗️ ProCore Tools Suite",
                 font=('Helvetica', 24, 'bold')).pack(pady=10)
        
        ttk.Label(about_frame, text="Version 1.0.0",
                 font=('Helvetica', 12)).pack(pady=5)
        
        ttk.Label(about_frame, text="\nA comprehensive file management utility combining:\n",
                 font=('Helvetica', 10)).pack(pady=10)
        
        features = [
            "🔍 File Search - Find and organize files",
            "📄 Drawing Extractor - Extract PDF drawings",
            "📂 Folder Creator - Create folders with RN naming convention"
        ]
        
        for feature in features:
            ttk.Label(about_frame, text=feature, font=('Helvetica', 10)).pack(pady=2)
        
        ttk.Label(about_frame, text="\n© 2026 ProCore Tools", 
                 font=('Helvetica', 9)).pack(pady=20)
        
    def create_status_bar(self, parent):
        """Create the status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side='right', padx=5)
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side='left', padx=5)
    
    # ========================================================================
    # GUI EVENT HANDLERS
    # ========================================================================
    
    def browse_directory(self, entry_widget):
        """Browse for directory and set in entry widget"""
        directory = filedialog.askdirectory()
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory)
    
    def update_preview(self, *args):
        """Update folder name preview"""
        try:
            folder_type = FolderType[self.folder_type_var.get()]
            number_str = self.create_number.get().strip()
            if number_str:
                number = int(number_str)
                date_str = datetime.now().strftime("%m-%d-%y")
                number_str_f = f"{number:03d}"
                preview = f"{folder_type.value}#{number_str_f} - ({date_str})"
                self.preview_label.config(text=preview)
            else:
                self.preview_label.config(text="Enter a number to preview")
        except (ValueError, KeyError):
            self.preview_label.config(text="Invalid input")
    
    def show_preview(self):
        """Show folder preview in message box"""
        self.update_preview()
        preview = self.preview_label.cget('text')
        if preview and "Invalid" not in preview and "Enter" not in preview:
            messagebox.showinfo("Folder Preview", f"Folder name will be:\n\n{preview}")
        else:
            messagebox.showwarning("Preview Error", "Please enter valid folder type and number")
    
    # ========================================================================
    # SEARCH FUNCTIONS
    # ========================================================================
    
    def start_search(self):
        """Start file search in background thread"""
        if self.is_running:
            return
            
        directory = self.search_dir.get().strip()
        pattern = self.search_pattern.get().strip()
        
        if not directory or not pattern:
            messagebox.showwarning("Input Error", "Please enter both directory and filename pattern")
            return
            
        if not os.path.exists(directory) or not os.path.isdir(directory):
            messagebox.showerror("Directory Error", f"Directory '{directory}' does not exist")
            return
        
        # Clear previous results
        self.clear_results()
        
        # Disable search button
        self.search_btn.config(state='disabled')
        self.is_running = True
        self.progress.start()
        self.status_label.config(text=f"Searching for '{pattern}'...")
        
        # Start search in thread
        thread = threading.Thread(target=self._do_search, 
                                 args=(directory, pattern),
                                 daemon=True)
        thread.start()
    
    def _do_search(self, directory: str, pattern: str):
        """Perform search in background thread"""
        try:
            max_results = int(self.max_results_var.get())
        except ValueError:
            max_results = 1000
            
        results = self.search_engine.search_files(
            directory, 
            pattern,
            case_sensitive=self.case_sensitive_var.get(),
            max_results=max_results
        )
        
        # Update UI in main thread
        self.root.after(0, lambda: self._update_search_results(results))
    
    def _update_search_results(self, results):
        """Update UI with search results"""
        self.search_results = results
        
        # Update tree
        for i, file_info in enumerate(sorted(results, key=lambda x: x.modified, reverse=True), 1):
            self.results_tree.insert('', 'end', values=(
                i,
                os.path.basename(file_info.path),
                file_info.get_size_str(),
                file_info.modified.strftime('%Y-%m-%d %H:%M'),
                file_info.path
            ))
        
        # Update count
        self.results_count.config(text=f"Found {len(results)} files")
        
        # Reset UI
        self.progress.stop()
        self.search_btn.config(state='normal')
        self.is_running = False
        self.status_label.config(text=f"Search complete: Found {len(results)} files")
        
        if not results:
            messagebox.showinfo("Search Complete", "No files found matching the search criteria")
    
    def clear_results(self):
       