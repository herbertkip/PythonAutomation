#!/usr/bin/env python3
"""
powerfab_batch_upload.py

Batch upload PDF drawings into Tekla PowerFab's Drawing Log
via UI automation of the "Batch Insert - From Files" dialog.

Dependencies:
    pip install pywinauto

Prerequisites:
    1. Tekla PowerFab desktop is already open.
    2. The correct Job and Drawing Log are selected.
    3. Run this script with the same privilege level as PowerFab
       (admin if PowerFab is running as admin).

Note:
    Tekla PowerFab does not expose a public API for batch drawing
    insertion. The only documented method is the UI dialog
    "Batch Insert - From Files" under the Drawing Log ribbon.
"""

import os
import sys
import time
import glob

try:
    from pywinauto import Desktop
except ImportError:
    print("[ERROR] pywinauto is not installed. Run: pip install pywinauto")
    sys.exit(1)


# ============================================================
# Interactive input collection
# ============================================================

def print_header():
    print("=" * 60)
    print("  Tekla PowerFab - Batch Drawing Upload Script")
    print("=" * 60)
    print()


def prompt_directory():
    """Prompt for the folder containing PDF drawings."""
    while True:
        path = input("Enter the folder path containing PDF drawings: ").strip().strip('"')
        if not path:
            print("  [ERROR] Path cannot be empty. Try again.")
            continue
        if not os.path.isdir(path):
            print(f"  [ERROR] Directory does not exist: {path}")
            continue

        pdfs = glob.glob(os.path.join(path, "*.pdf")) + \
               glob.glob(os.path.join(path, "*.PDF"))
        if not pdfs:
            print(f"  [WARNING] No PDF files found in {path}.")
            confirm = input("  Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                continue

        print(f"  [OK] Found {len(pdfs)} PDF file(s).")
        for f in pdfs[:5]:
            print(f"       {os.path.basename(f)}")
        if len(pdfs) > 5:
            print(f"       ... and {len(pdfs) - 5} more")
        return path


def prompt_prefix_suffix():
    """Prompt for filename prefix and suffix used for drawing number parsing."""
    print()
    print("-" * 60)
    print("File Prefix / Suffix (from Tekla PowerFab documentation):")
    print("  Example filename: C23847-100-r1.pdf")
    print("  File Prefix:      C23847-     (removed -> 100-r1.pdf)")
    print("  File Suffix:      -r1         (do NOT include .pdf)")
    print("  Resulting drawing number: 100")
    print("-" * 60)
    print()

    prefix = input("Enter file prefix (press Enter for none): ").strip()
    suffix = input("Enter file suffix, without .pdf (press Enter for none): ").strip()
    return prefix, suffix


def prompt_insert_mode():
    """Prompt for insert mode: Add Drawings or Add Revisions."""
    print()
    print("Insert Mode:")
    print("  1. Add Drawings   (new drawings, default)")
    print("  2. Add Revisions  (revisions to existing drawings)")
    while True:
        choice = input("Select (1/2) [default 1]: ").strip()
        if not choice or choice == "1":
            return "add_drawings"
        if choice == "2":
            return "add_revisions"
        print("  [ERROR] Enter 1 or 2.")


def prompt_copy_option():
    """Prompt whether to copy files into the Drawing Directory."""
    print()
    print("Copy Files into Drawing Directory:")
    print("  When checked, PDFs are copied into")
    print("  \\Tekla PowerFab Documents\\Drawing so the attachment")
    print("  link remains valid even if the originals move.")
    while True:
        choice = input("Check this option? (y/n) [default y]: ").strip().lower()
        if not choice or choice == 'y':
            return True
        if choice == 'n':
            return False
        print("  [ERROR] Enter y or n.")


def prompt_batch_properties():
    """Prompt for optional batch-level drawing properties."""
    print()
    print("-" * 60)
    print("Optional properties applied to all imported drawings.")
    print("Press Enter to leave any field blank.")
    print("-" * 60)

    props = {}
    props['description'] = input("  Description: ").strip()
    props['drawn_by'] = input("  Drawn By: ").strip()
    props['checked_by'] = input("  Checked By: ").strip()
    return props


def confirm_and_start(config):
    """Show a summary and ask for confirmation before automation."""
    print()
    print("=" * 60)
    print("  Configuration Summary")
    print("=" * 60)
    print(f"  Directory:    {config['directory']}")
    print(f"  Prefix:       '{config['prefix']}'")
    print(f"  Suffix:       '{config['suffix']}'")
    mode_label = "Add Drawings" if config['mode'] == 'add_drawings' else "Add Revisions"
    print(f"  Mode:         {mode_label}")
    print(f"  Copy Files:   {'Yes' if config['copy_files'] else 'No'}")
    if config['properties']['description']:
        print(f"  Description:  {config['properties']['description']}")
    if config['properties']['drawn_by']:
        print(f"  Drawn By:     {config['properties']['drawn_by']}")
    if config['properties']['checked_by']:
        print(f"  Checked By:   {config['properties']['checked_by']}")
    print("=" * 60)
    print()
    print("[IMPORTANT] Make sure Tekla PowerFab is open and the correct")
    print("            Drawing Log is selected before continuing.")
    print()

    while True:
        choice = input("Press Enter to start automation, or 'q' to quit: ").strip().lower()
        if choice == 'q':
            print("Cancelled.")
            sys.exit(0)
        return


# ============================================================
# UI automation core
# ============================================================

def find_powerfab_window():
    """Locate the Tekla PowerFab main window."""
    print("[AUTOMATION] Searching for Tekla PowerFab window...")

    try:
        for win in Desktop(backend="uia").windows():
            try:
                title = win.window_text()
                if "Tekla PowerFab" in title or "PowerFab" in title:
                    print(f"[AUTOMATION] Found window: {title}")
                    return win
            except Exception:
                continue
    except Exception as e:
        print(f"[AUTOMATION] Window enumeration failed: {e}")

    return None


def automate_batch_insert(window, config):
    """
    Drive the Batch Insert - From Files dialog.

    PowerFab is a .NET application; pywinauto support for its menu
    bar and ribbon is limited. The script therefore guides the user
    to open the dialog manually and then fills the fields it can
    locate automatically.
    """
    print("[AUTOMATION] Starting UI automation...")

    try:
        window.set_focus()
        time.sleep(0.5)
    except Exception as e:
        print(f"[AUTOMATION] Could not focus PowerFab window: {e}")

    print()
    print("=" * 60)
    print("[ACTION REQUIRED]")
    print("=" * 60)
    print("1. In Tekla PowerFab, open:")
    print("      Drawing Log  ->  Batch Insert  ->  From Files")
    print("2. Once the Insert Drawings dialog appears, return here.")
    print()
    input("Press Enter to continue after the dialog is open...")

    print("[AUTOMATION] Looking for the Insert Drawings dialog...")
    dialog = None

    for _ in range(10):
        try:
            for win in Desktop(backend="uia").windows():
                try:
                    title = win.window_text()
                    if "Insert Drawings" in title or "Batch Insert" in title:
                        dialog = win
                        print(f"[AUTOMATION] Found dialog: {title}")
                        break
                except Exception:
                    continue
            if dialog:
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not dialog:
        print("[ERROR] Could not find the Insert Drawings dialog.")
        print("        Open it manually and re-run the script.")
        return False

    dialog.set_focus()
    time.sleep(0.5)

    # Switch tab if Add Revisions was chosen
    if config['mode'] == 'add_revisions':
        print("[AUTOMATION] Switching to Add Revisions tab...")
        try:
            tab = dialog.child_window(title="Add Revisions", control_type="TabItem")
            tab.click_input()
            time.sleep(0.3)
        except Exception as e:
            print(f"[AUTOMATION] Could not switch tab automatically: {e}")
            print("             Please switch to Add Revisions manually.")

    # Directory field
    print(f"[AUTOMATION] Setting directory: {config['directory']}")
    try:
        dir_field = dialog.child_window(auto_id="Directory", control_type="Edit")
        dir_field.set_text(config['directory'])
        time.sleep(0.3)
    except Exception:
        try:
            dir_label = dialog.child_window(title="Directory", control_type="Text")
            dir_edit = dir_label.parent().children(control_type="Edit")[0]
            dir_edit.set_text(config['directory'])
        except Exception as e:
            print(f"[AUTOMATION] Could not fill Directory field: {e}")
            print("             Please fill it manually.")

    # Prefix field
    if config['prefix']:
        print(f"[AUTOMATION] Setting prefix: {config['prefix']}")
        try:
            prefix_field = dialog.child_window(auto_id="FilePrefix", control_type="Edit")
            prefix_field.set_text(config['prefix'])
        except Exception:
            print("[AUTOMATION] Could not fill Prefix field automatically.")

    # Suffix field
    if config['suffix']:
        print(f"[AUTOMATION] Setting suffix: {config['suffix']}")
        try:
            suffix_field = dialog.child_window(auto_id="FileSuffix", control_type="Edit")
            suffix_field.set_text(config['suffix'])
        except Exception:
            print("[AUTOMATION] Could not fill Suffix field automatically.")

    # Copy Files checkbox
    if config['copy_files']:
        print("[AUTOMATION] Checking 'Copy Files into Drawing Directory'...")
        try:
            checkbox = dialog.child_window(
                title="Copy Files into Drawing Directory",
                control_type="CheckBox"
            )
            if checkbox.get_toggle_state() == 0:
                checkbox.click_input()
        except Exception:
            print("[AUTOMATION] Could not toggle Copy Files checkbox.")

    print()
    print("=" * 60)
    print("[DONE] Fields have been filled where possible.")
    print("       Review the dialog contents, then click 'Add From Files'.")
    print("=" * 60)

    return True


# ============================================================
# Entry point
# ============================================================

def main():
    print_header()

    config = {
        'directory': prompt_directory(),
        'prefix': '',
        'suffix': '',
        'mode': 'add_drawings',
        'copy_files': True,
        'properties': {}
    }

    config['prefix'], config['suffix'] = prompt_prefix_suffix()
    config['mode'] = prompt_insert_mode()
    config['copy_files'] = prompt_copy_option()
    config['properties'] = prompt_batch_properties()

    confirm_and_start(config)

    window = find_powerfab_window()
    if not window:
        print("[ERROR] Tekla PowerFab window not found.")
        print("        Open PowerFab and run the script again.")
        sys.exit(1)

    automate_batch_insert(window, config)

    print()
    print("Script finished.")


if __name__ == "__main__":
    main()