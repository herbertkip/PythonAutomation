import os
import datetime

def create_folder():
    # Get current date
    today = datetime.datetime.now()
    date_str = today.strftime("%m-%d-%y")  # Format: MM-DD-YY
    
    # Define folder type options with numbers
    folder_types = {
        1: "RELEASE",
        2: "SUB",
        3: "FIELD",
        4: "APPRV",
        5: "RECD"
    }
    
    # Display folder type options
    print("\nFolder Type Options:")
    print("1 - RELEASE")
    print("2 - SUB")
    print("3 - FIELD")
    print("4 - APPRV")
    print("5 - RECD")
    
    # Prompt for folder type (number)
    while True:
        try:
            type_choice = int(input("\nSelect folder type (1-5): "))
            if type_choice in folder_types:
                folder_type = folder_types[type_choice]
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # Prompt for directory path
    while True:
        directory = input("\nEnter the directory path where folder should be created: ").strip()
        if os.path.exists(directory):
            break
        else:
            print("Directory does not exist. Please enter a valid path.")
    
    # Prompt for number value
    while True:
        try:
            number = int(input("\nEnter the number value: "))
            if number >= 0:
                break
            else:
                print("Please enter a non-negative number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # Format number as 3 digits with leading zeros
    number_str = f"{number:03d}"
    
    # Create folder name
    folder_name = f"{folder_type}#{number_str} - ({date_str})"
    full_path = os.path.join(directory, folder_name)
    
    # Create the folder
    try:
        os.makedirs(full_path, exist_ok=False)
        print(f"\n✅ Folder created successfully!")
        print(f"📁 Location: {full_path}")
    except FileExistsError:
        print(f"\n❌ Error: Folder already exists at {full_path}")
    except PermissionError:
        print(f"\n❌ Error: Permission denied. Cannot create folder at {directory}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("📂 FOLDER CREATION SCRIPT")
    print("=" * 50)
    create_folder()
    print("\n" + "=" * 50)