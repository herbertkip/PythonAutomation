def main():
    print("=" * 60)
    print(" file_log formatter (template-based, branded)")
    print("=" * 60)

    directory = prompt_directory()

    # --- Template location ---
    # By default we look for 'template.xlsx' in the same directory as the script.
    # You can change this to an absolute path if the template lives elsewhere.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "template.xlsx")

    if not os.path.isfile(template_path):
        print(f"\n! Could not find template at: {template_path}")
        sys.exit(1)

    # --- Source file (for reading the filenames) ---
    src_path = os.path.join(directory, SOURCE_NAME)
    if not os.path.isfile(src_path):
        print(f"\n! Could not find '{SOURCE_NAME}' in {directory}")
        sys.exit(1)

    # --- Read sections from the SOURCE ---
    wb_src = load_workbook(src_path, data_only=True)
    sections = read_sections(wb_src.active)
    if not sections:
        print("\n! No job sections found in the source file.")
        sys.exit(1)

    job_ids = prompt_job_ids(len(sections))

    # --- Copy TEMPLATE -> OUTPUT ---
    dest_path = os.path.join(directory, OUTPUT_NAME)
    shutil.copyfile(template_path, dest_path)
    print(f"\nCopied template -> {dest_path}")

    # --- Open the copy and write the data ---
    wb = load_workbook(dest_path)
    ws = wb.active

    # Template layout constants (match make_template.py):
    TITLE_ROW   = 7    # where 'Job: ...' is written
    HEADER_ROW  = 8    # 'Number | Revised Drawings | Column1 | Column2'
    DATA_START  = 9    # first data row

    write_output(ws, sections, job_ids,
                 start_row=DATA_START,
                 title_offset_from_data=DATA_START - TITLE_ROW - 1)

    wb.save(dest_path)
    print(f"\n✓ Wrote branded workbook to:\n   {dest_path}")