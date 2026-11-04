import streamlit as st
from datetime import datetime
from pathlib import Path
from enum import Enum

class FolderType(Enum):
    RELEASE = 1
    SUB = 2
    FIELD = 3
    APPRV = 4
    RECD = 5

def create_folder(folder_type_name: str, target_dir: Path, number: int, description: str):
    """Create the folder and return (success, message)."""
    date_str = datetime.now().strftime("%m-%d-%y")
    folder_name = f"{folder_type_name}#{number:03d} {description} - ({date_str})"
    full_path = target_dir / folder_name

    try:
        full_path.mkdir(parents=False, exist_ok=False)
        return True, f"Folder created successfully at:\n{full_path}"
    except FileExistsError:
        return False, f"Folder already exists at:\n{full_path}"
    except PermissionError:
        return False, f"Permission denied. Cannot create folder at:\n{target_dir}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    st.set_page_config(page_title="Folder Creation", page_icon="📂")
    st.title("📂 Folder Creation Script")
    st.markdown("---")

    # Folder type selection
    st.subheader("1. Folder Type")
    folder_options = {f"{item.value} - {item.name}": item.name for item in FolderType}
    selected_label = st.selectbox("Select folder type", list(folder_options.keys()))
    folder_type_name = folder_options[selected_label]

    # Directory path input
    st.subheader("2. Target Directory")
    default_dir = str(Path.home())
    dir_input = st.text_input("Enter the directory path where folder should be created", value=default_dir)
    target_dir = Path(dir_input.strip()) if dir_input.strip() else None

    if target_dir is not None:
        if target_dir.is_dir():
            st.success(f"✅ Valid directory: {target_dir}")
        else:
            st.error("❌ Directory does not exist. Please enter a valid path.")

    # Number input
    st.subheader("3. Number Value")
    number = st.number_input("Enter the number value", min_value=0, step=1, value=1)

    # Description input
    st.subheader("4. Description")
    description_input = st.text_input("Enter the description (will be converted to uppercase)")

    st.markdown("---")

    # Preview
    description = description_input.strip().upper()
    if target_dir is not None and description:
        date_str = datetime.now().strftime("%m-%d-%y")
        preview_name = f"{folder_type_name}#{int(number):03d} {description} - ({date_str})"
        st.subheader("Preview")
        st.code(preview_name, language=None)

    # Create button
    create_disabled = target_dir is None or not target_dir.is_dir() or not description
    if st.button("Create Folder", type="primary", disabled=create_disabled):
        success, message = create_folder(folder_type_name, target_dir, int(number), description)
        if success:
            st.success(f"✅ {message}")
            st.balloons()
        else:
            st.error(f"❌ {message}")

    if create_disabled and not description:
        st.info("Please fill in all fields to enable folder creation.")


if __name__ == "__main__":
    main()