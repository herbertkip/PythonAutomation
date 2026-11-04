# PythonAutomation

A collection of Python automation scripts for everyday file, folder, PDF,
image, text, and document-handling tasks. Scripts are small, standalone, and
largely CLI- or GUI-based utilities built to remove repetitive manual work.

> **Note:** Most scripts are independent one-off tools. There is no single
> installable package — run the individual file you need.

---

## Contents

- [Requirements](#requirements)
- [Usage](#usage)
- [Scripts by Category](#scripts-by-category)
  - [File & Folder Utilities](#file--folder-utilities)
  - [Renaming & Text Case](#renaming--text-case)
  - [PDF & Image Tools](#pdf--image-tools)
  - [Document / CAD / Drawing Tools](#document--cad--drawing-tools)
  - [GUI & App Builders](#gui--app-builders)
  - [Web / Browser & Scraping](#web--browser--scraping)
  - [Logging & Monitoring](#logging--monitoring)
- [License](#license)

---

## Requirements

- Python 3.8+
- Dependencies vary per script. Commonly used libraries include:
  - `Pillow` (image handling)
  - `PyPDF2` / `pypdf` (PDF operations)
  - `python-docx` (Word documents)
  - `tkinter` (bundled with Python, used by GUI scripts)
  - `watchdog` (directory monitoring)
  - `selenium` / `requests` / `beautifulsoup4` (browser & scraping)

Install common dependencies:

```bash
pip install pillow pypdf python-docx watchdog requests beautifulsoup4


## PythonAutomation Project Manifest

## 1. Overview

`PythonAutomation` is a flat repository of ~100 standalone Python scripts.
There is **no package structure** — every `.py` file is an independent tool.
The project is best understood as a *toolbox*, not a library.

- **Language:** Python 3
- **Structure:** flat (all files in repo root)
- **Entry points:** each `*.py` file
- **Build artifacts:** `FolderCreator.spec` (PyInstaller)
- **License:** see `LICENSE`

## 2. Repository Topology
PythonAutomation/
├── LICENSE
├── FolderCreator.spec # PyInstaller build spec
├── README.md # (this repo's guide)
├── MANIFOLD.md # (this file)
│
├── [FILE & FOLDER] AllFolders.py, CompareFolders.py, DeleteFiles.py,
│ DirMap.py, FolderMap.py, FindFile.py, FolderFilePeel.py,
│ LatestFiles.py, ScrapeFiles.py, ShareFile.py,
│ OneDriveSt.py
│
├── [RENAME & CASE] Rename.py, RN.py, Prefix.py, HyphenFix.py,
│ Tcase.py, TitleCase.py, Ucase.py, space.py,
│ CanamRename.py
│
├── [PDF & IMAGE] PDFBind.py, PDFComb.py, Img2PDF.py, DocToPdf2.py,
│ PageEdit.py, PdfSM.py, DocSM.py, Split23.py,
│ split2.py, split233.py
│
├── [DOC / CAD / DWG] LatestDWG.py, SplitDWG.py, split_drawing.py,
│ SplitDrawOcr.py, ExtendedParts.py, FieldFile.py,
│ McSplit.py, McTool.py, MccombsBrandTem.py,
│ Tekla1.py, ReportCheck.py, RptCheck.py, ZeroCheck.py
│
├── [GUI / APP] GUI00.py, app.py, createApp.py, create_app.py,
│ folder_creator_gui.py, FolderCreator.spec
│
├── [WEB / SHOP] browser.py, QuickAmazon.py, ShopMemo.py,
│ ShopNote.py, OneMagic.py
│
└── [LOGGING / MONITOR] FileLog.py, DirMonitor.py, CloseOutStamp.py,
CoStamp.py, RL.py, ProEx.py

text

## 3. Script Inventory (by group)

| Group | Files | Count |
|---|---|---|
| File & Folder | AllFolders(2), CompareFolders, DeleteFiles(2), DirMap, FolderMap, FindFile, FolderFilePeel, LatestFiles(3), ScrapeFiles, ShareFile(2), OneDriveSt(2) | ~18 |
| Rename & Case | Rename(2), RN variants (6), RNText, StRnText, Prefix(2), HyphenFix, Tcase, TitleCase, Ucase, space, CanamRename | ~17 |
| PDF & Image | PDFBind(4), PDFComb, Img2PDF(2), DocToPdf2, PageEdit, PdfSM, DocSM, Split23, split2, split233 | ~14 |
| Doc / CAD / DWG | LatestDWG, SplitDWG(2), split_drawing_set, split_drawings, SplitDrawOcr, ExtendedParts, FieldFile, McSplit(2), McTool, MccombsBrandTem, Tekla1, ReportCheck, RptCheck, ZeroCheck | ~16 |
| GUI / App | GUI001-003, app, createApp, create_app, folder_creator_gui | ~7 |
| Web / Shop | browser1-3, QuickAmazon, ShopMemo(3), ShopNote(3), OneMagic(2) | ~12 |
| Logging / Monitor | FileLog(3), DirMonitor, CloseOutStamp, CoStamp, RL, ProEx(4) | ~11 |

*(Counts approximate; some files overlap categories.)*

## 4. Dependency Graph (conceptual)

Most scripts are **independent**. The only real coupling is:
folder_creator_gui.py ──built by──▶ FolderCreator.spec
GUI00.py / app.py / create_app.py (shared tkinter pattern)
FileLog.py ──used by──▶ DirMonitor.py, CloseOutStamp.py (logging patterns)
SplitDWG.py / split_drawing.py (shared drawing-split logic family)
PDFBind*.py (shared PDF-merge logic family)

text

No shared `utils.py` exists — duplication between variants is expected.

## 5. External Dependencies (likely)

| Library | Used by (group) |
|---|---|
| `tkinter` | GUI / App |
| `Pillow` | PDF & Image |
| `pypdf` / `PyPDF2` | PDF & Image |
| `python-docx` | Doc / PDF |
| `watchdog` | DirMonitor |
| `requests`, `beautifulsoup4`, `selenium` | Web / Shop |
| `pyinstaller` | FolderCreator.spec |

## 6. How to Navigate

1. **Looking for a task?** → use `README.md` category tables.
2. **Looking for the code?** → use the topology tree above; group names map to filename prefixes.
3. **Want to run something?** → `python <file>.py`; check top-of-file constants for paths.
4. **Want to build a GUI tool?** → start from `folder_creator_gui.py` + `FolderCreator.spec`.

## 7. Conventions & Caveats

- **Naming:** inconsistent by design — many `*2`, `*3`, `RN_1`, `- Copy` files are iterative variants, not libraries.
- **No tests, no CI, no `requirements.txt`.**
- **No shared package** — scripts copy logic between each other.
- **Hard-coded paths** are likely; edit before running.
- **Entry point is always the file itself.**

## 8. Suggested Improvements (optional roadmap)

- Add `requirements.txt`
- Consolidate `RN*`, `PDFBind*`, `SplitDWG*` families behind a shared helper
- Add a `scripts/` index generator
- Add smoke tests for the most-used utilities
