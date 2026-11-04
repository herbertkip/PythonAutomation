import os
import datetime
import shutil

def create_release_folder_advanced():
    """
    Enhanced version with template folder option and validation
    """
    
    # Get current date
    today = datetime.datetime.now()
    date_str = f"{today.month}-{today.day}-{str(today.year)[-2:]}"
    
    # Get directory path
    print("\nCurrent working directory:", os.getcwd())
    directory = input("Enter the directory path (press Enter for current directory): ").strip()
    
    if not directory:
        directory = os.getcwd()
    
    # Validate directory
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return
    
    # Get release number with validation
    while True:
        number_input = input("Enter the release number (e.g., 1, 2, 3): ").strip()
        if number_input.isdigit() and int(number_input) >= 0:
            number = int(number_input)
            number_str = f"{number:03d}"
            break
        else:
            print("Error: Please enter a valid non-negative integer.")
    
    # Create folder name
    folder_name = f"RELEASE#{number_str} - ({date_str})"
    full_path = os.path.join(directory, folder_name)
    
    # Check for existing folder
    if os.path.exists(full_path):
        print(f"⚠️  Warning: Folder '{folder_name}' already exists!")
        choice = input("Choose: (o)verwrite, (s)kip, or (c)ancel: ").strip().lower()
        if choice == 'c':
            print("Operation cancelled.")
            return
        elif choice == 's':
            print("Skipping folder creation.")
            return
        elif choice == 'o':
            try:
                shutil.rmtree(full_path)
                print(f"Removed existing folder: {folder_name}")
            except Exception as e:
                print(f"Error removing folder: {e}")
                return
    
    # Create the folder
    try:
        os.makedirs(full_path, exist_ok=False)
        print(f"\n✅ Successfully created folder: {folder_name}")
        print(f"📍 Location: {full_path}")
        
        # Display folder contents (if any)
        print("\n📁 Folder created. You can now add your release files.")
        
    except FileExistsError:
        print(f"❌ Folder already exists: {folder_name}")
    except PermissionError:
        print("❌ Permission denied. Please check your write permissions.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🏷️  RELEASE FOLDER CREATOR")
    print("=" * 60)
    print("Format: RELEASE#001 - (M-D-YY)")
    print("=" * 60)
    
    create_release_folder_advanced()
    
    # Pause to see output
    input("\nPress Enter to exit...")