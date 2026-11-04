#!/usr/bin/env python3
"""
Convert 'file_log - Copy.xlsx' -> 'file_log.xlsx' (formatted version).

Usage:
    python format_file_log.py

The script:
  1. Prompts for a directory containing the source Excel file.
  2. Reads all job sections from the source.
  3. Prompts the user for a Job ID for each section
     (source file has no job numbers).
  4. Writes the formatted 'file_log.xlsx' in the same directory.
"""

import os
import sys
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Alignment

# ---------- Configuration ----------
SOURCE_NAME = "file_log - Copy.xlsx"
OUTPUT_NAME = "file_log.xlsx"
MAX_ITEMS_PER_COLUMN = 10   # items > this get wrapped into the second column pair


def prompt_directory() -> str:
    while True:
        path = input("Enter the directory containing the Excel file: ").strip().strip('"').strip("'")
        if not path:
            print("  ! Please enter a path.")
            continue
        if not os.path.isdir(path):
            print(f"  ! Not a directory: {path}")
            continue
        return path


def read_sections(src_path: str):
    """
    Read the source workbook and return a list of sections.
    Each section is a list of filename strings (in order).
    A new section starts whenever we encounter a 'Number' header row
    after we've already collected at least one filename.
    """
    wb = load_workbook(src_path, data_only=True)
    ws = wb.active

    sections = []
    current = []

    for row in ws.iter_rows(values_only=True):
        # Pad short rows
        cells = list(row) + [None] * (2 - len(row))
        col_a, col_b = cells[0], cells[1]

        a = str(col_a).strip() if col_a is not None else ""
        b = str(col_b).strip() if col_b is not None else ""

        # Header row -> starts a new section (if we already have data)
        if a.lower() == "number" and b.lower() == "filename":
            if current:
                sections.append(current)
                current = []
            continue

        # Data row: numeric "Number" in col A, filename in col B
        if b and a.isdigit():
            current.append(b)

    if current:
        sections.append(current)

    return sections


def prompt_job_ids(num_sections: int):
    """Prompt user for a job ID per section."""
    print(f"\nDetected {num_sections} job section(s) in the source file.")
    print("The source file does not contain Job IDs — please supply them.\n")
    job_ids = []
    for i in range(num_sections):
        while True:
            jid = input(f"  Job ID for section {i + 1} (e.g. 974): ").strip()
            if jid:
                job_ids.append(jid)
                break
            print("    ! Job ID cannot be empty.")
    return job_ids


def write_output(dest_path: str, sections, job_ids):
    """Write the formatted workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = "File List"

    bold = Font(bold=True)

    current_row = 1

    for section, jid in zip(sections, job_ids):
        # --- Job title row (label in column B) ---
        ws.cell(row=current_row, column=2, value=f"Job: {jid}").font = bold
        current_row += 1

        # --- Decide if we need two column groups ---
        left_items = section[:MAX_ITEMS_PER_COLUMN]
        right_items = section[MAX_ITEMS_PER_COLUMN:]

        # Header row
        ws.cell(row=current_row, column=1, value="Number").font = bold
        ws.cell(row=current_row, column=2, value="Revised Drawings").font = bold

        if right_items:
            ws.cell(row=current_row, column=3, value="Number2").font = bold
            ws.cell(row=current_row, column=4, value="Revised Drawings3").font = bold
        else:
            # Keep parity with the sample output — always emit Column1/Column2 headers
            ws.cell(row=current_row, column=3, value="Column1").font = bold
            ws.cell(row=current_row, column=4, value="Column2").font = bold

        header_row = current_row
        current_row += 1

        # --- Data rows ---
        max_rows = max(len(left_items), len(right_items))
        for i in range(max_rows):
            r = current_row + i

            if i < len(left_items):
                ws.cell(row=r, column=1, value=i + 1)
                ws.cell(row=r, column=2, value=left_items[i])

            if i < len(right_items):
                # Numbering continues from left side length + 1
                ws.cell(row=r, column=3, value=len(left_items) + i + 1)
                ws.cell(row=r, column=4, value=right_items[i])

        current_row += max_rows

        # Blank row between jobs
        current_row += 1

    # Column widths for readability
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 20

    wb.save(dest_path)


def main():
    print("=" * 60)
    print(" file_log formatter")
    print("=" * 60)

    directory = prompt_directory()
    src_path = os.path.join(directory, SOURCE_NAME)

    if not os.path.isfile(src_path):
        print(f"\n! Could not find '{SOURCE_NAME}' in {directory}")
        sys.exit(1)

    sections = read_sections(src_path)
    if not sections:
        print("\n! No job sections found in the source file.")
        sys.exit(1)

    job_ids = prompt_job_ids(len(sections))

    dest_path = os.path.join(directory, OUTPUT_NAME)
    write_output(dest_path, sections, job_ids)

    print(f"\n✓ Wrote formatted workbook to:\n   {dest_path}")


if __name__ == "__main__":
    main()