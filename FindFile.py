import os
import sys
from datetime import datetime
import glob

def get_file_info(filepath):
    """Get file information including modification time and size"""
    try:
        stat_info = os.stat(filepath)
        return {
            'path': filepath,
            'size': stat_info.st_size,
            'modified': datetime.fromtimestamp(stat_info.st_mtime),
            'created': datetime.fromtimestamp(stat_info.st_ctime)
        }
    except (OSError, FileNotFoundError):
        return None

def search_files(directory, filename):
    """Search for files matching the filename pattern in directory and subdirectories"""
    results = []
    
    # Walk through the directory tree
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the filename matches (case-insensitive)
            if filename.lower() in file.lower():
                full_path = os.path.join(root, file)
                file_info = get_file_info(full_path)
                if file_info:
                    results.append(file_info)
    
    return results

def display_results(results):
    """Display search results in a formatted manner"""
    if not results:
        print("\n❌ No files found matching the search criteria.")
        return
    
    print(f"\n📁 Found {len(results)} file(s) matching your search:")
    print("=" * 80)
    
    # Sort by modification time (newest first)
    sorted_results = sorted(results, key=lambda x: x['modified'], reverse=True)
    
    # Display all results
    for i, file in enumerate(sorted_results, 1):
        print(f"\n📄 File #{i}")
        print(f"   📂 Location: {file['path']}")
        print(f"   📅 Modified: {file['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📦 Size: {file['size']:,} bytes")
        print("-" * 80)
    
    # Show the latest version
    latest = sorted_results[0]
    print(f"\n⭐ LATEST VERSION:")
    print(f"   📂 Location: {latest['path']}")
    print(f"   📅 Modified: {latest['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   📦 Size: {latest['size']:,} bytes")

def main():
    try:
        # Get directory path
        while True:
            directory = input("📂 Enter directory path to search: ").strip()
            if not directory:
                print("❌ Directory path cannot be empty. Please try again.")
                continue
                
            # Expand user home directory if using ~
            directory = os.path.expanduser(directory)
            
            if os.path.exists(directory) and os.path.isdir(directory):
                break
            else:
                print(f"❌ Directory '{directory}' does not exist or is not a valid directory.")
                print("Please enter a valid path.")
        
        # Get filename to search
        while True:
            filename = input("🔍 Enter filename or part of filename to search: ").strip()
            if filename:
                break
            else:
                print("❌ Filename cannot be empty. Please try again.")
        
        print(f"\n🔎 Searching for '{filename}' in '{directory}'...")
        print("This may take a moment...\n")
        
        # Search for files
        results = search_files(directory, filename)
        
        # Display results
        display_results(results)
        
        # Optional: Save results to file
        if results:
            save = input("\n💾 Save results to text file? (y/n): ").strip().lower()
            if save == 'y':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"file_search_results_{timestamp}.txt"
                
                try:
                    with open(output_file, 'w') as f:
                        f.write(f"File Search Results\n")
                        f.write(f"Search: '{filename}'\n")
                        f.write(f"Directory: '{directory}'\n")
                        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 80 + "\n\n")
                        
                        for i, file in enumerate(sorted(results, key=lambda x: x['modified'], reverse=True), 1):
                            f.write(f"File #{i}\n")
                            f.write(f"Location: {file['path']}\n")
                            f.write(f"Modified: {file['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Size: {file['size']:,} bytes\n")
                            f.write("-" * 40 + "\n")
                    
                    print(f"✅ Results saved to: {output_file}")
                except Exception as e:
                    print(f"❌ Failed to save results: {e}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Search cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()