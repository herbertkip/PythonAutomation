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
