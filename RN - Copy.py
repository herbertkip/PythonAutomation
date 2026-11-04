import os
import datetime
import shutil

def create_folder():
    """
    Creates a folder with options: RELEASE, SUB, FIELD, APPRV, RECD
    Format: RELEASE#001 - (8-25-26)
    """
    
    # Get current date
    today = datetime.datetime.now()
    date_str = f"{today.month}-{today.day}-{str(today.year)[-2:]}"
    
    # Define folder types
    FOLDER_TYPES = {
        'R': {'name': 'RELEASE', 'number_format': '#{:03d}'},
        'S': {'name': 'SUB', 'number_format': '#{:03d}'},
        'F': {'name': 'FIELD', 'number_format': '#{:03d}'},
        'A': {'name': 'APPRV', 'number_format': '#{:03d}'},
        'D': {'name': 'RECD', 'number_format': '#{:03d}'}
    }
    
    # Display folder type options
    print("\n" + "=" * 60)
    print("📁 FOLDER TYPE OPTIONS")
    print("=" * 60)
    print("  R - RELEASE")
    print("  S - SUB")
    print("  F - FIELD")
    print("  A - APPRV")
    print("  D - RECD")
    print("=" * 60)
    
    # Get folder type choice
    while True:
        choice = input("\nEnter folder type (R/S/F/A/D) or number (1-5): ").strip().upper()
        
        # Map numbers to letters
        number_map = {'1': 'R', '2': 'S', '3': 'F', '4': 'A', '5': 'D'}
        
        # Convert number choice to letter if applicable
        if choice in number_map:
            choice = number_map[choice]
        
        # Validate choice
        if choice in FOLDER_TYPES:
            folder_type = FOLDER_TYPES[choice]
            break
        else:
            print("❌ Invalid choice. Please enter R, S, F, A, D or 1-5.")
    
    # Get directory path
    print(f"\nCurrent working directory: {os.getcwd()}")
    directory = input("Enter the directory path (press Enter for current directory): ").strip()
    
    if not directory:
        directory = os.getcwd()
    
    # Validate directory
    if not os.path.exists(directory):
        print(f"❌ Error: Directory '{directory}' does not exist.")
        return
    
    # Get number value
    while True:
        number_input = input("Enter the number value (e.g., 1, 2, 3): ").strip()
        if number_input.isdigit() and int(number_input) >= 0:
            number = int(number_input)
            number_str = folder_type['number_format'].format(number)
            break
        else:
            print("❌ Error: Please enter a valid non-negative integer.")
    
    # Create folder name
    folder_name = f"{folder_type['name']}{number_str} - ({date_str})"
    full_path = os.path.join(directory, folder_name)
    
    # Check for existing folder
    if os.path.exists(full_path):
        print(f"\n⚠️  Warning: Folder '{folder_name}' already exists!")
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
        print(f"📂 Type: {folder_type['name']}")
        print(f"📅 Date: {date_str}")
        
    except FileExistsError:
        print(f"❌ Folder already exists: {folder_name}")
    except PermissionError:
        print("❌ Permission denied. Please check your write permissions.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def create_multiple_folders():
    """
    Advanced version to create multiple folders at once
    """
    
    # Get current date
    today = datetime.datetime.now()
    date_str = f"{today.month}-{today.day}-{str(today.year)[-2:]}"
    
    # Define folder types
    FOLDER_TYPES = {
        'R': 'RELEASE',
        'S': 'SUB',
        'F': 'FIELD',
        'A': 'APPRV',
        'D': 'RECD'
    }
    
    print("\n" + "=" * 60)
    print("📁 BULK FOLDER CREATOR")
    print("=" * 60)
    print("Create multiple folders at once")
    print("=" * 60)
    
    # Get directory path
    print(f"\nCurrent working directory: {os.getcwd()}")
    directory = input("Enter the directory path (press Enter for current directory): ").strip()
    
    if not directory:
        directory = os.getcwd()
    
    if not os.path.exists(directory):
        print(f"❌ Error: Directory '{directory}' does not exist.")
        return
    
    # Get folder types
    print("\nSelect folder types (enter letters without spaces, e.g., RSA):")
    print("  R - RELEASE, S - SUB, F - FIELD, A - APPRV, D - RECD")
    
    while True:
        types_input = input("Enter types: ").strip().upper()
        if all(c in FOLDER_TYPES for c in types_input) and len(types_input) > 0:
            selected_types = [FOLDER_TYPES[c] for c in types_input]
            break
        else:
            print("❌ Invalid input. Please use only R, S, F, A, D.")
    
    # Get starting number
    while True:
        start_num = input("Enter starting number: ").strip()
        if start_num.isdigit() and int(start_num) >= 0:
            start_num = int(start_num)
            break
        else:
            print("❌ Error: Please enter a valid non-negative integer.")
    
    # Create folders
    print("\n📁 Creating folders...")
    created = []
    failed = []
    
    for i, folder_type in enumerate(selected_types):
        number = start_num + i
        number_str = f"#{number:03d}"
        folder_name = f"{folder_type}{number_str} - ({date_str})"
        full_path = os.path.join(directory, folder_name)
        
        try:
            os.makedirs(full_path, exist_ok=True)
            created.append(folder_name)
            print(f"  ✅ {folder_name}")
        except Exception as e:
            failed.append((folder_name, str(e)))
            print(f"  ❌ {folder_name} - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully created: {len(created)} folders")
    if failed:
        print(f"❌ Failed: {len(failed)} folders")
        for name, error in failed:
            print(f"   - {name}: {error}")
    print(f"📍 Location: {directory}")

if __name__ == "__main__":
    print("=" * 60)
    print("🏷️  FOLDER CREATOR - MULTI-TYPE")
    print("=" * 60)
    
    while True:
        print("\n📋 MAIN MENU")
        print("=" * 60)
        print("  1 - Create single folder")
        print("  2 - Create multiple folders (bulk)")
        print("  3 - Exit")
        print("=" * 60)
        
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == '1':
            create_folder()
        elif choice == '2':
            create_multiple_folders()
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
        
        if choice in ['1', '2']:
            input("\nPress Enter to continue...")