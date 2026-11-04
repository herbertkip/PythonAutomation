"""
Folder Creation Tool - GUI version
-----------------------------------
A simple front end for creating folders named like:
    RELEASE#001 - (08-25-26)

Build a Windows .exe with:
    pip install pyinstaller
    pyinstaller --onefile --windowed --name "FolderCreator" folder_creator_gui.py

The .exe will appear in the "dist" folder.
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

FOLDER_TYPES = ["RELEASE", "SUB", "FIELD", "APPRV", "RECD"]


class FolderCreatorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Folder Creation Tool")
        self.resizable(False, False)
        self.geometry("460x340")

        # Center the window on screen
        self.update_idletasks()
        w, h = 460, 340
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.directory_var = tk.StringVar()
        self.number_var = tk.StringVar()
        self.type_var = tk.StringVar(value=FOLDER_TYPES[0])

        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        header = tk.Label(
            self, text="📂 Folder Creation Tool", font=("Segoe UI", 15, "bold")
        )
        header.pack(pady=(16, 4))

        subtitle = tk.Label(
            self,
            text="Creates a folder named:  TYPE#NNN - (MM-DD-YY)",
            font=("Segoe UI", 9),
            fg="#555555",
        )
        subtitle.pack(pady=(0, 10))

        form = tk.Frame(self)
        form.pack(fill="x", **pad)

        # Folder type dropdown
        tk.Label(form, text="Folder Type:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", pady=6
        )
        type_dropdown = ttk.Combobox(
            form,
            textvariable=self.type_var,
            values=FOLDER_TYPES,
            state="readonly",
            width=25,
        )
        type_dropdown.grid(row=0, column=1, sticky="ew", pady=6)

        # Number entry
        tk.Label(form, text="Number:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky="w", pady=6
        )
        number_entry = tk.Entry(form, textvariable=self.number_var, width=27)
        number_entry.grid(row=1, column=1, sticky="ew", pady=6)

        # Directory picker
        tk.Label(form, text="Directory:", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky="w", pady=6
        )
        dir_frame = tk.Frame(form)
        dir_frame.grid(row=2, column=1, sticky="ew", pady=6)
        dir_entry = tk.Entry(dir_frame, textvariable=self.directory_var, width=20)
        dir_entry.pack(side="left", fill="x", expand=True)
        browse_btn = tk.Button(dir_frame, text="Browse…", command=self.browse_directory)
        browse_btn.pack(side="left", padx=(6, 0))

        form.columnconfigure(1, weight=1)

        # Preview label
        self.preview_var = tk.StringVar()
        self.preview_var.set(self._compute_preview_name())
        preview_label = tk.Label(
            self,
            textvariable=self.preview_var,
            font=("Consolas", 10, "italic"),
            fg="#2a6f2a",
        )
        preview_label.pack(pady=(6, 0))

        # Update preview live
        self.type_var.trace_add("write", lambda *_: self._refresh_preview())
        self.number_var.trace_add("write", lambda *_: self._refresh_preview())

        # Create button
        create_btn = tk.Button(
            self,
            text="Create Folder",
            font=("Segoe UI", 11, "bold"),
            bg="#2a6f2a",
            fg="white",
            activebackground="#245e24",
            activeforeground="white",
            command=self.create_folder,
            padx=10,
            pady=8,
        )
        create_btn.pack(pady=18)

        # Status bar
        self.status_var = tk.StringVar()
        status_label = tk.Label(
            self, textvariable=self.status_var, font=("Segoe UI", 9), fg="#333333"
        )
        status_label.pack(side="bottom", pady=(0, 10))

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _compute_preview_name(self):
        date_str = datetime.datetime.now().strftime("%m-%d-%y")
        number = self.number_var.get().strip()
        number_str = f"{int(number):03d}" if number.isdigit() else "###"
        return f"Preview:  {self.type_var.get()}#{number_str} - ({date_str})"

    def _refresh_preview(self):
        self.preview_var.set(self._compute_preview_name())

    def browse_directory(self):
        chosen = filedialog.askdirectory(title="Select destination directory")
        if chosen:
            self.directory_var.set(chosen)

    # ------------------------------------------------------------------ #
    # Core action
    # ------------------------------------------------------------------ #
    def create_folder(self):
        folder_type = self.type_var.get()
        directory = self.directory_var.get().strip()
        number_raw = self.number_var.get().strip()

        # Validate directory
        if not directory:
            messagebox.showerror("Missing directory", "Please choose a destination directory.")
            return
        if not os.path.exists(directory):
            messagebox.showerror("Invalid directory", "That directory does not exist.")
            return

        # Validate number
        if not number_raw.isdigit():
            messagebox.showerror("Invalid number", "Please enter a non-negative whole number.")
            return
        number = int(number_raw)

        date_str = datetime.datetime.now().strftime("%m-%d-%y")
        number_str = f"{number:03d}"
        folder_name = f"{folder_type}#{number_str} - ({date_str})"
        full_path = os.path.join(directory, folder_name)

        try:
            os.makedirs(full_path, exist_ok=False)
            self.status_var.set(f"✅ Created: {full_path}")
            messagebox.showinfo("Success", f"Folder created:\n{full_path}")
        except FileExistsError:
            messagebox.showerror("Already exists", f"Folder already exists:\n{full_path}")
        except PermissionError:
            messagebox.showerror(
                "Permission denied", f"Cannot create folder at:\n{directory}"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = FolderCreatorApp()
    app.mainloop()
