import os
import zipfile
import re
import urllib.request
import urllib.parse
import ssl

def get_direct_download_url(url):
    """
    Converts common cloud storage 'view' links into 'direct download' links.
    """
    url = url.strip()
    
    # 1. Google Drive
    gdrive_match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if gdrive_match:
        file_id = gdrive_match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # 2. Dropbox
    if 'dropbox.com' in url:
        return url.replace('dl=0', 'dl=1')
        
    # 3. Direct Links
    return url

def download_file(url, save_path):
    """
    Downloads a file using built-in urllib. No external libraries needed.
    """
    try:
        # Create an SSL context to avoid certificate errors on some systems
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Add a User-Agent so servers don't block us as a bot
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )

        print("Connecting...")
        with urllib.request.urlopen(req, context=context, timeout=30) as response:
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                print("\n[Warning] The server returned an HTML page instead of a file.")
                print("This usually means the link is not a direct download link or requires login.")

            # Download in chunks
            with open(save_path, 'wb') as out_file:
                chunk_size = 8192
                total_downloaded = 0
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    total_downloaded += len(chunk)
                    # Print progress
                    print(f"\rDownloaded: {total_downloaded / 1024 / 1024:.2f} MB", end="")
        print() # New line after progress
        return True

    except Exception as e:
        print(f"\n[Error] Failed to download: {e}")
        return False

def create_zip_from_url(url, output_zip_name):
    direct_url = get_direct_download_url(url)
    
    # Determine filename from URL
    parsed_url = urllib.parse.urlparse(direct_url)
    filename = os.path.basename(urllib.parse.unquote(parsed_url.path))
    
    if not filename or filename == '' or filename == 'uc':
        filename = "downloaded_file"

    # Setup temp directory
    temp_dir = "temp_download"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, filename)

    print(f"Original URL: {url}")
    print(f"Direct URL:   {direct_url}")
    print(f"Saving as:    {filename}")
    
    success = download_file(direct_url, temp_file_path)
    
    if not success:
        print("Download failed. Aborting.")
        return

    # Create ZIP
    print(f"Packaging into {output_zip_name}...")
    try:
        with zipfile.ZipFile(output_zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_file_path, arcname=filename)
        print(f"\nSuccess! Created ZIP: {output_zip_name}")
        
    except Exception as e:
        print(f"\n[Error] Failed to create ZIP: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

def main():
    print("=== Read-Only Link Downloader & Zipper (No Install Required) ===")
    
    url_input = input("Enter the read-only link (URL): ").strip()
    if not url_input:
        print("Error: No URL provided.")
        return

    zip_name_input = input("Enter the output ZIP filename (default: download.zip): ").strip()
    if not zip_name_input:
        zip_name_input = "download.zip"
    if not zip_name_input.endswith('.zip'):
        zip_name_input += '.zip'

    create_zip_from_url(url_input, zip_name_input)

if __name__ == "__main__":
    main()