"""
Merge hyphenated PDFs (e.g. "73S001 - 1.pdf") into their parent PDF
(e.g. "73S001.pdf") and output everything to a "SORTED FOLDER".

Requirements:
    pip install pypdf
"""

import re
import shutil
from pathlib import Path
from pypdf import PdfWriter, PdfReader


def prompt_for_folder() -> Path:
    """Prompt the user for the folder containing the PDFs."""
    while True:
        raw = input("Enter the folder path containing the PDFs: ").strip().strip('"').strip("'")
        folder = Path(raw).expanduser()
        if folder.is_dir():
            return folder
        print(f"  [!] '{folder}' is not a valid directory. Try again.\n")


def classify_files(folder: Path):
    """
    Scan the folder and group PDFs.

    Returns:
        parents   : dict { base_name: [Path, ...] }  -> base files (no hyphen)
        children  : dict { base_name: [Path, ...] }  -> hyphenated files
    """
    parents = {}
    children = {}

    # Matches "<base> - <number>.pdf"  (spaces around hyphen optional-ish)
    hyphen_pattern = re.compile(r"^(?P<base>.+?)\s*-\s*\d+$")

    for pdf in sorted(folder.iterdir()):
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            continue

        stem = pdf.stem
        match = hyphen_pattern.match(stem)
        if match:
            base = match.group("base").strip()
            children.setdefault(base, []).append(pdf)
        else:
            parents.setdefault(stem.strip(), []).append(pdf)

    return parents, children


def main():
    source = prompt_for_folder()
    output = source / "SORTED FOLDER"
    output.mkdir(exist_ok=True)

    parents, children = classify_files(source)

    # Report orphans (children with no parent) up front
    orphan_children = [b for b in children if b not in parents]
    if orphan_children:
        print("\n[!] These hyphenated files have NO matching parent PDF:")
        for b in orphan_children:
            for p in children[b]:
                print(f"    - {p.name}")
        print("    They will be copied over as-is.\n")

    merged_count = 0
    copied_count = 0

    # 1) Process each parent (with or without children)
    for base, parent_list in parents.items():
        parent_pdf = parent_list[0]
        dest = output / parent_pdf.name

        child_list = children.get(base, [])

        if child_list:
            # ---- Merge parent + all children into one PDF ----
            writer = PdfWriter()
            try:
                with open(parent_pdf, "rb") as f:
                    for page in PdfReader(f).pages:
                        writer.add_page(page)

                # Sort children numerically by their trailing number
                def sort_key(p: Path):
                    m = re.search(r"-\s*(\d+)$", p.stem)
                    return int(m.group(1)) if m else 0

                for child in sorted(child_list, key=sort_key):
                    with open(child, "rb") as f:
                        for page in PdfReader(f).pages:
                            writer.add_page(page)

                with open(dest, "wb") as f:
                    writer.write(f)
            finally:
                writer.close()

            merged_count += 1
            print(f"[MERGED] {parent_pdf.name}  (+{len(child_list)} hyphenated file(s))")
        else:
            # ---- No children -> just copy the file ----
            shutil.copy2(parent_pdf, dest)
            copied_count += 1
            print(f"[COPIED] {parent_pdf.name}")

    # 2) Copy orphan hyphenated files as-is
    for base in orphan_children:
        for child in children[base]:
            shutil.copy2(child, output / child.name)
            copied_count += 1
            print(f"[COPIED] {child.name}  (orphan, no parent)")

    # 3) Any remaining hyphenated files not yet handled? Shouldn't happen,
    #    but this guarantees we never lose a file.
    handled = set()
    for base, lst in parents.items():
        handled.update(lst)
        handled.update(children.get(base, []))
    for base in orphan_children:
        handled.update(children[base])

    for pdf in source.iterdir():
        if pdf.is_file() and pdf.suffix.lower() == ".pdf" and pdf not in handled:
            shutil.copy2(pdf, output / pdf.name)
            copied_count += 1
            print(f"[COPIED] {pdf.name}  (fallback)")

    # 4) Verify no hyphenated file ended up in the output
    leftover = [p for p in output.iterdir()
                if p.is_file() and re.search(r"\s*-\s*\d+$", p.stem)]
    print("\n--- Summary ---")
    print(f"Merged files : {merged_count}")
    print(f"Copied files : {copied_count}")
    print(f"Output folder: {output}")
    if leftover:
        print(f"[!] WARNING: {len(leftover)} hyphenated file(s) still in output:")
        for p in leftover:
            print(f"    - {p.name}")
    else:
        print("OK: No hyphenated filenames in the output folder.")


if __name__ == "__main__":
    main()