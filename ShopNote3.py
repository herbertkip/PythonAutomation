#!/usr/bin/env python3
"""
Convert 'file_log - Copy.xlsx' -> 'file_log.xlsx' (formatted version),
preserving the source workbook's theme, fonts, and color palette.

Usage:
    python format_file_log.py

The script:
  1. Prompts for a directory containing 'file_log - Copy.xlsx'.
  2. Copies the source file to 'file_log.xlsx' (this keeps the theme,
     styles, and sheet properties intact).
  3. Reads all job sections from the source.
  4. Prompts the user for a Job ID for each section
     (the source file has no job numbers).
  5. Rewrites the copy in-place into the desired layout and saves it.

Requirements:
    pip install openpyxl
"""

import os
import shutil
import sys
from copy import copy
from openpyxl import load_workbook

# ---------- Configuration ----------
SOURCE_NAME = "file_log - Copy.xlsx"
OUTPUT_NAME = "file_log.xlsx"
MAX_ITEMS_PER_COLUMN = 10   # items beyond this get wrapped into the 2nd column pair


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def copy_style(src_cell, dst_cell):
    """Copy font, fill, border, alignment, number format, and protection."""
    if src_cell is None:
        return
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.border = copy(src_cell.border)
        dst_cell.alignment = copy(src_cell.alignment)
        dst_cell.number_format = src_cell.number_format
        dst_cell.protection = copy(src_cell.protection)


def prompt_directory() -> str:
    while True:
        path = input("Enter the directory containing the Excel file: ").strip()
        path = path.strip('"').strip("'")
        if not path:
            print("  ! Please enter a path.")
            continue
        if not os.path.isdir(path):
            print(f"  ! Not a directory: {path}")
            continue
        return path


def prompt_job_ids(num_sections: int):
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


# ---------------------------------------------------------------------------
# Reading source
# ---------------------------------------------------------------------------
def read_sections(ws):
    """
    Return a list of sections. Each section is a list of dicts:
        {"value": "<filename>", "src_cell": <openpyxl Cell>}

    A new section starts whenever we encounter a 'Number | Filename'
    header row after we've already collected at least one filename.
    """
    sections = []
    current = []

    for row in ws.iter_rows():
        a = row[0].value if len(row) > 0 else None
        b = row[1].value if len(row) > 1 else None
        b_cell = row[1] if len(row) > 1 else None

        a_s = str(a).strip() if a is not None else ""
        b_s = str(b).strip() if b is not None else ""

        # Header row -> start of a new section (if we already have data)
        if a_s.lower() == "number" and b_s.lower() == "filename":
            if current:
                sections.append(current)
                current = []
            continue

        # Data row: numeric "Number" in col A, filename in col B
        if b_s and a_s.isdigit():
            current.append({"value": b_s, "src_cell": b_cell})

    if current:
        sections.append(current)

    return sections


# ---------------------------------------------------------------------------
# Writing output
# ---------------------------------------------------------------------------
def write_output(ws, sections, job_ids):
    """Rebuild the sheet in place, copying styles from reference cells."""

    # --- Find reference cells for styling ---
    header_a_src = header_b_src = None
    for row in ws.iter_rows():
        if (len(row) > 1
                and row[0].value is not None
                and row[1].value is not None
                and str(row[0].value).strip().lower() == "number"
                and str(row[1].value).strip().lower() == "filename"):
            header_a_src, header_b_src = row[0], row[1]
            break

    data_src = sections[0][0]["src_cell"] if sections and sections[0] else None

    # --- Save sheet-level settings we want to keep ---
    # NOTE: ws.sheet_view is a read-only property — do NOT reassign it.
    #       We don't touch it, so gridlines / zoom / freeze are preserved.
    col_widths = {k: v.width for k, v in ws.column_dimensions.items()}
    tab_color = ws.sheet_properties.tabColor
    freeze = ws.freeze_panes
    merged = list(ws.merged_cells.ranges)

    # --- Clear all cell contents (keeps worksheet object -> theme preserved) ---
    ws.delete_rows(1, ws.max_row + 1)

    # --- Restore sheet-level settings ---
    for k, w in col_widths.items():
        ws.column_dimensions[k].width = w
    ws.sheet_properties.tabColor = tab_color
    ws.freeze_panes = freeze

    # --- Write the new layout ---
    r = 1
    for section, jid in zip(sections, job_ids):
        # Job title row (label in column B)
        title_cell = ws.cell(row=r, column=2, value=f"Job: {jid}")
        if header_b_src is not None:
            copy_style(header_b_src, title_cell)
            # Make the title bold without losing other font attributes
            title_cell.font = copy(title_cell.font)
            title_cell.font = title_cell.font.copy(bold=True)
        r += 1

        left = section[:MAX_ITEMS_PER_COLUMN]
        right = section[MAX_ITEMS_PER_COLUMN:]

        # Header row
        headers = ["Number", "Revised Drawings"]
        if right:
            headers += ["Number2", "Revised Drawings3"]
        else:
            headers += ["Column1", "Column2"]

        for c, h in enumerate(headers, start=1):
            cell = ws.cell(row=r, column=c, value=h)
            src = header_a_src if c == 1 else header_b_src
            if src is not None:
                copy_style(src, cell)
        r += 1

        # Data rows (left + right side by side)
        max_rows = max(len(left), len(right))
        for i in range(max_rows):
            row_idx = r + i

            if i < len(left):
                c1 = ws.cell(row=row_idx, column=1, value=i + 1)
                c2 = ws.cell(row=row_idx, column=2, value=left[i]["value"])
                if data_src is not None:
                    copy_style(data_src, c1)
                    copy_style(data_src, c2)

            if i < len(right):
                c3 = ws.cell(row=row_idx, column=3,
                             value=len(left) + i + 1)
                c4 = ws.cell(row=row_idx, column=4, value=right[i]["value"])
                if data_src is not None:
                    copy_style(data_src, c3)
                    copy_style(data_src, c4)

        r += max_rows + 1  # blank row between jobs

    # Re-apply merges that still make sense (skip if they conflict)
    for mr in merged:
        try:
            ws.merge_cells(str(mr))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print(" file_log formatter (preserves theme & colors)")
    print("=" * 60)

    directory = prompt_directory()
    src_path = os.path.join(directory, SOURCE_NAME)

    if not os.path.isfile(src_path):
        print(f"\n! Could not find '{SOURCE_NAME}' in {directory}")
        sys.exit(1)

    # 1. Copy source -> output so theme, styles, and sheet props are inherited
    dest_path = os.path.join(directory, OUTPUT_NAME)
    shutil.copyfile(src_path, dest_path)
    print(f"\nCopied source -> {dest_path}")

    # 2. Open the copy and read the sections
    wb = load_workbook(dest_path)
    ws = wb.active

    sections = read_sections(ws)
    if not sections:
        print("\n! No job sections found in the source file.")
        sys.exit(1)

    # 3. Ask the user for Job IDs
    job_ids = prompt_job_ids(len(sections))

    # 4. Rewrite the sheet in place
    write_output(ws, sections, job_ids)

    # 5. Save
    wb.save(dest_path)

    print(f"\n✓ Wrote formatted workbook (theme preserved) to:\n   {dest_path}")


if __name__ == "__main__":
    main()