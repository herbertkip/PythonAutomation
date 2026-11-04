import sys
from datetime import datetime
from pathlib import Path
from enum import Enum

class FolderType(Enum):
    RELEASE = 1
    SUB = 2
    FIELD = 3
    APPRV = 4
    RECD = 5

def create_folder() -> None:
    # Get current date
    date_str = datetime.now().strftime("%m-%d-%y")
    
    # Display folder type options dynamically
    print("\nFolder Type Options:")
    for item in FolderType:
        print(f"{item.value} - {item.name}")
    
    # Prompt for folder type
    while True:
        try:
            choice = int(input("\nSelect folder type (1-5): "))
            folder_type = FolderType(choice).name
            break
        except ValueError:
            print("Invalid choice. Please enter a valid number (1-5).")
    
    # Prompt for directory path
    while True:
        dir_input = input("\nEnter the directory path where folder should be created: ").strip()
        target_dir = Path(dir_input)
        if target_dir.is_dir():
            break
        print("Directory does not exist. Please enter a valid path.")
    
    # Prompt for number value
    while True:
        try:
            number = int(input("\nEnter the number value: "))
            if number >= 0:
                break
            print("Please enter a non-negative number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # Prompt for the description (allows spaces and any characters, converted to uppercase)
    while True:
        description = input("\nEnter the description: ").strip()
        if description:
            description = description.upper()
            break
        print("Description cannot be empty. Please enter some text.")
    
    # Create folder name and path
    folder_name = f"{folder_type}#{number:03d} {description} - ({date_str})"
    full_path = target_dir / folder_name
    
    # Create the folder
    try:
        full_path.mkdir(parents=False, exist_ok=False)
        print(f"\n✅ Folder created successfully!")
        print(f"📁 Location: {full_path}")
    except FileExistsError:
        print(f"\n❌ Error: Folder already exists at {full_path}")
    except PermissionError:
        print(f"\n❌ Error: Permission denied. Cannot create folder at {target_dir}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("📂 FOLDER CREATION SCRIPT")
    print("=" * 50)
    create_folder()
    print("\n" + "=" * 50)