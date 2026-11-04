import os
import shutil
import sys
from copy import copy
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

SOURCE_NAME = "file_log - Copy.xlsx"
OUTPUT_NAME = "file_log.xlsx"
MAX_ITEMS_PER_COLUMN = 10


def copy_style(src_cell, dst_cell):
    """Copy font, fill, border, alignment, and number format from one cell to another."""
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.border = copy(src_cell.border)
        dst_cell.alignment = copy(src_cell.alignment)
        dst_cell.number_format = src_cell.number_format
        dst_cell.protection = copy(src_cell.protection)


def prompt_directory() -> str:
    while True:
        path = input("Enter the directory containing the Excel file: ").strip().strip('"').strip("'")
        if path and os.path.isdir(path):
            return path
        print(f"  ! Not a directory: {path}")


def read_sections(ws):
    """Return list of (section_items, style_refs) from an already-loaded worksheet."""
    sections = []
    current = []

    for row in ws.iter_rows():
        a = row[0].value
        b = row[1].value if len(row) > 1 else None

        a_s = str(a).strip() if a is not None else ""
        b_s = str(b).strip() if b is not None else ""

        if a_s.lower() == "number" and b_s.lower() == "filename":
            if current:
                sections.append(current)
                current = []
            continue

        if b_s and a_s.isdigit():
            # store the filename plus the style of the source filename cell (col B)
            current.append({"value": b_s, "src_cell": row[1]})

    if current:
        sections.append(current)
    return sections


def prompt_job_ids(n):
    print(f"\nDetected {n} job section(s). Enter a Job ID for each.\n")
    ids = []
    for i in range(n):
        while True:
            jid = input(f"  Job ID for section {i+1} (e.g. 974): ").strip()
            if jid:
                ids.append(jid)
                break
    return ids


def write_output(dest_path, ws, sections, job_ids):
    """Rebuild the sheet in place, copying styles from a reference row."""
    # Reference styles: use the first filename cell of the first section
    # as the "data" style template; use the header row of the source as the header style template.
    header_a_src = header_b_src = None
    for row in ws.iter_rows():
        if (row[0].value and str(row[0].value).strip().lower() == "number"
                and len(row) > 1 and str(row[1].value).strip().lower() == "filename"):
            header_a_src, header_b_src = row[0], row[1]
            break

    data_src = sections[0][0]["src_cell"] if sections and sections[0] else None

    # Save column widths before clearing
    col_widths = {k: v.width for k, v in ws.column_dimensions.items()}
    sheet_view = ws.sheet_view
    tab_color = ws.sheet_properties.tabColor
    freeze = ws.freeze_panes
    merged = list(ws.merged_cells.ranges)

    # Clear all cells but keep the worksheet object (preserves theme)
    ws.delete_rows(1, ws.max_row + 1)

    # Restore sheet-level settings
    for k, w in col_widths.items():
        ws.column_dimensions[k].width = w
    ws.sheet_view = sheet_view
    ws.sheet_properties.tabColor = tab_color
    ws.freeze_panes = freeze

    r = 1
    for section, jid in zip(sections, job_ids):
        # --- Job title row (col B) ---
        title_cell = ws.cell(row=r, column=2, value=f"Job: {jid}")
        if header_b_src is not None:
            copy_style(header_b_src, title_cell)
        title_cell.font = copy(title_cell.font)
        title_cell.font = title_cell.font.copy(bold=True)
        r += 1

        left = section[:MAX_ITEMS_PER_COLUMN]
        right = section[MAX_ITEMS_PER_COLUMN:]

        # --- Header row ---
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

        # --- Data rows ---
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
                c3 = ws.cell(row=row_idx, column=3, value=len(left) + i + 1)
                c4 = ws.cell(row=row_idx, column=4, value=right[i]["value"])
                if data_src is not None:
                    copy_style(data_src, c3)
                    copy_style(data_src, c4)

        r += max_rows + 1  # blank row between jobs

    # Re-apply any merges that don't conflict (optional)
    for mr in merged:
        try:
            ws.merge_cells(str(mr))
        except Exception:
            pass


def main():
    print("=" * 60)
    print(" file_log formatter (preserves theme & colors)")
    print("=" * 60)

    directory = prompt_directory()
    src_path = os.path.join(directory, SOURCE_NAME)

    if not os.path.isfile(src_path):
        print(f"\n! Could not find '{SOURCE_NAME}' in {directory}")
        sys.exit(1)

    # 1. Copy source -> output so the theme, styles, sheet props are inherited
    dest_path = os.path.join(directory, OUTPUT_NAME)
    shutil.copyfile(src_path, dest_path)

    # 2. Open the copy and rewrite the contents in place
    wb = load_workbook(dest_path)
    ws = wb.active

    sections = read_sections(ws)
    if not sections:
        print("\n! No job sections found.")
        sys.exit(1)

    job_ids = prompt_job_ids(len(sections))

    write_output(dest_path, ws, sections, job_ids)
    wb.save(dest_path)

    print(f"\n✓ Wrote formatted workbook (theme preserved) to:\n   {dest_path}")


if __name__ == "__main__":
    main()