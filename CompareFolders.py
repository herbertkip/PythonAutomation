#!/usr/bin/env python3
"""
Folder Comparison Script
Compares two folders (including all subfolders) and generates a detailed
difference report as a .txt file.
"""

import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path


def get_folder_path(prompt):
    """Prompt user for a folder path until a valid one is provided."""
    while True:
        path = input(prompt).strip().strip('"').strip("'")
        if not path:
            print("  [!] No path entered. Please try again.")
            continue
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            return os.path.abspath(path)
        print(f"  [!] Not a valid folder: {path}")
        print("      Please enter an existing directory.")


def compute_file_hash(filepath, chunk_size=65536):
    """Compute SHA-256 hash of a file for content comparison."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


def scan_folder(root):
    """
    Walk a folder recursively and return a dict:
        { relative_path: {"size": int, "hash": str or None, "is_dir": bool} }
    """
    results = {}
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # Sort for deterministic output
        dirnames.sort()
        filenames.sort()

        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        # Record subdirectories
        for d in dirnames:
            rel_path = os.path.join(rel_dir, d) if rel_dir else d
            results[rel_path] = {"size": 0, "hash": None, "is_dir": True}

        # Record files
        for f in filenames:
            full_path = os.path.join(dirpath, f)
            rel_path = os.path.join(rel_dir, f) if rel_dir else f
            try:
                size = os.path.getsize(full_path)
            except OSError:
                size = -1
            file_hash = compute_file_hash(full_path)
            results[rel_path] = {
                "size": size,
                "hash": file_hash,
                "is_dir": False,
            }
    return results


def compare_folders(folder1, folder2):
    """Compare two folders and return a structured diff dictionary."""
    print("\n[+] Scanning folder 1 ...")
    files1 = scan_folder(folder1)
    print(f"    Found {len(files1)} items.")

    print("[+] Scanning folder 2 ...")
    files2 = scan_folder(folder2)
    print(f"    Found {len(files2)} items.")

    print("[+] Comparing ...")

    keys1 = set(files1.keys())
    keys2 = set(files2.keys())

    only_in_1 = sorted(keys1 - keys2)
    only_in_2 = sorted(keys2 - keys1)
    common = sorted(keys1 & keys2)

    differing = []
    identical = 0

    for rel in common:
        a = files1[rel]
        b = files2[rel]

        # Type mismatch (file vs folder)
        if a["is_dir"] != b["is_dir"]:
            differing.append({
                "path": rel,
                "reason": "Type mismatch (file vs folder)",
                "size1": a["size"] if not a["is_dir"] else "-",
                "size2": b["size"] if not b["is_dir"] else "-",
            })
            continue

        if a["is_dir"]:
            identical += 1
            continue

        # Compare file contents
        if a["hash"] is None or b["hash"] is None:
            differing.append({
                "path": rel,
                "reason": "Could not read file (permissions or error)",
                "size1": a["size"],
                "size2": b["size"],
            })
        elif a["hash"] != b["hash"]:
            differing.append({
                "path": rel,
                "reason": "Content differs",
                "size1": a["size"],
                "size2": b["size"],
            })
        else:
            identical += 1

    return {
        "folder1": folder1,
        "folder2": folder2,
        "total1": len(files1),
        "total2": len(files2),
        "only_in_1": only_in_1,
        "only_in_2": only_in_2,
        "differing": differing,
        "identical": identical,
        "files1": files1,
        "files2": files2,
    }


def human_size(num):
    """Convert bytes to a human-readable string."""
    if num is None:
        return "-"
    if num < 0:
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.2f} {unit}" if unit != "B" else f"{int(num)} B"
        num /= 1024.0
    return f"{num:.2f} PB"


def write_report(diff, output_path):
    """Write the comparison results to a text file."""
    lines = []
    add = lines.append

    add("=" * 78)
    add("FOLDER COMPARISON REPORT")
    add("=" * 78)
    add(f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    add(f"Folder 1  : {diff['folder1']}")
    add(f"Folder 2  : {diff['folder2']}")
    add("")

    # Summary
    add("-" * 78)
    add("SUMMARY")
    add("-" * 78)
    add(f"Items in Folder 1          : {diff['total1']}")
    add(f"Items in Folder 2          : {diff['total2']}")
    add(f"Identical files            : {diff['identical']}")
    add(f"Only in Folder 1           : {len(diff['only_in_1'])}")
    add(f"Only in Folder 2           : {len(diff['only_in_2'])}")
    add(f"Files with different content: {len(diff['differing'])}")
    add("")

    # Only in folder 1
    add("-" * 78)
    add(f"ONLY IN FOLDER 1 ({len(diff['only_in_1'])})")
    add("-" * 78)
    if diff["only_in_1"]:
        for rel in diff["only_in_1"]:
            info = diff["files1"][rel]
            kind = "<DIR>" if info["is_dir"] else human_size(info["size"])
            add(f"  {rel}   [{kind}]")
    else:
        add("  (none)")
    add("")

    # Only in folder 2
    add("-" * 78)
    add(f"ONLY IN FOLDER 2 ({len(diff['only_in_2'])})")
    add("-" * 78)
    if diff["only_in_2"]:
        for rel in diff["only_in_2"]:
            info = diff["files2"][rel]
            kind = "<DIR>" if info["is_dir"] else human_size(info["size"])
            add(f"  {rel}   [{kind}]")
    else:
        add("  (none)")
    add("")

    # Differing files
    add("-" * 78)
    add(f"FILES PRESENT IN BOTH BUT DIFFERENT ({len(diff['differing'])})")
    add("-" * 78)
    if diff["differing"]:
        for item in diff["differing"]:
            add(f"  {item['path']}")
            add(f"      Reason       : {item['reason']}")
            add(f"      Size Folder1 : {human_size(item['size1']) if isinstance(item['size1'], int) else item['size1']}")
            add(f"      Size Folder2 : {human_size(item['size2']) if isinstance(item['size2'], int) else item['size2']}")
    else:
        add("  (none)")
    add("")

    add("=" * 78)
    add("END OF REPORT")
    add("=" * 78)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    print("=" * 60)
    print("  FOLDER COMPARISON TOOL")
    print("=" * 60)
    print("This tool compares two folders (including all subfolders)")
    print("and generates a report of the differences.\n")

    folder1 = get_folder_path("Enter path for Folder 1: ")
    folder2 = get_folder_path("Enter path for Folder 2: ")

    if os.path.samefile(folder1, folder2):
        print("\n[!] Both paths point to the same folder. Nothing to compare.")
        sys.exit(1)

    diff = compare_folders(folder1, folder2)

    # Determine output location (default: current working directory)
    default_out = os.path.join(
        os.getcwd(),
        f"folder_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    )
    out_prompt = f"\nEnter output report path\n  (press Enter for '{default_out}'): "
    out_path = input(out_prompt).strip().strip('"').strip("'")
    if not out_path:
        out_path = default_out

    try:
        write_report(diff, out_path)
    except OSError as e:
        print(f"[!] Failed to write report: {e}")
        sys.exit(1)

    # Console summary
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Identical files            : {diff['identical']}")
    print(f"  Only in Folder 1           : {len(diff['only_in_1'])}")
    print(f"  Only in Folder 2           : {len(diff['only_in_2'])}")
    print(f"  Different content          : {len(diff['differing'])}")
    print(f"\n  Report written to:\n    {out_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Cancelled by user.")
        sys.exit(130)