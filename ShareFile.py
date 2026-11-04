import os
import requests
import zipfile
import re
import sys
from urllib.parse import urlparse, unquote

def get_direct_download_url(url):
    """
    Converts common cloud storage 'view' links into 'direct download' links.
    Supports Google Drive, Dropbox, and direct links.
    """
    url = url.strip()
    
    # 1. Google Drive
    # Pattern: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    gdrive_match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if gdrive_match:
        file_id = gdrive_match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # 2. Dropbox
    # Pattern: https://www.dropbox.com/s/xxxx/file.zip?dl=0
    if 'dropbox.com' in url:
        # Change dl=0 to dl=1 to force direct download
        return url.replace('dl=0', 'dl=1')
        
    # 3. Direct Links (already direct)
    return url

def download_file(url, save_path):
    """
    Downloads a file from a URL to a specific path.
    Returns True if successful, False otherwise.
    """
    try:
        # Use stream=True to download large files in chunks
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status() # Check for HTTP errors
            
            # Check if it's an HTML page (usually means the link is not direct or requires auth)
            content_type = r.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                print("\n[Warning] The link returned an HTML page, not a file.")
                print("This usually means the link requires authentication, or it's not a direct download link.")
                print("Attempting to save anyway...")

            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"\n[Error] Failed to download {url}: {e}")
        return False

def create_zip_from_url(url, output_zip_name):
    """
    Main logic: Downloads the file, determines if it's a zip or a single file,
    and packages it into the requested ZIP structure.
    """
    direct_url = get_direct_download_url(url)
    
    # Determine the filename from the URL
    parsed_url = urlparse(direct_url)
    # Try to get filename from Content-Disposition header first, fallback to URL path
    filename = os.path.basename(unquote(parsed_url.path))
    
    if not filename or filename == '':
        filename = "downloaded_file"

    # Create a temporary directory to hold the download
    temp_dir = "temp_download"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, filename)

    print(f"Downloading from: {url}")
    print(f"Saving temporary file as: {filename}")
    
    success = download_file(direct_url, temp_file_path)
    
    if not success:
        print("Download failed. Aborting ZIP creation.")
        return

    # Create the ZIP file
    print(f"Packaging into {output_zip_name}...")
    try:
        with zipfile.ZipFile(output_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # If the downloaded file is already a ZIP, we can either:
            # A) Just save it as is
            # B) Extract it and repackage (to ensure structure)
            # Here, we just put the downloaded file into the new zip.
            # If you want to extract a nested zip, you'd add logic here.
            
            zipf.write(temp_file_path, arcname=filename)
            
        print(f"\nSuccess! Created ZIP file: {output_zip_name}")
        
    except Exception as e:
        print(f"\n[Error] Failed to create ZIP: {e}")
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

def main():
    print("=== Read-Only Link Downloader & Zipper ===")
    
    # Prompt for URL
    url_input = input("Enter the read-only link (URL): ").strip()
    
    if not url_input:
        print("Error: No URL provided.")
        return

    # Prompt for output zip name
    zip_name_input = input("Enter the output ZIP filename (default: download.zip): ").strip()
    if not zip_name_input:
        zip_name_input = "download.zip"
    if not zip_name_input.endswith('.zip'):
        zip_name_input += '.zip'

    create_zip_from_url(url_input, zip_name_input)

if __name__ == "__main__":
    main()