import os

def generate_tree_structure(root_dir, output_file):
    """
    Generates a visual tree of the directory structure (folders only)
    and writes it to a file.
    
    Args:
        root_dir (str): The absolute path to the directory to scan.
        output_file (str): The path to the text file where the tree will be saved.
    """
    
    # List to hold the lines of the tree so we can write them all at once
    tree_lines = []
    
    # Counter for total folders
    stats = {'dirs': 0}

    def recurse(current_path, prefix=""):
        """
        Recursive helper function to walk the directory (folders only).
        """
        try:
            # Get all items in the current directory
            items = sorted(os.listdir(current_path))
        except PermissionError:
            tree_lines.append(f"{prefix}└── [Permission Denied]")
            return
        except Exception as e:
            tree_lines.append(f"{prefix}└── [Error: {e}]")
            return

        # Keep only directories
        dirs = [i for i in items if os.path.isdir(os.path.join(current_path, i))]
        count = len(dirs)

        for i, item in enumerate(dirs):
            path = os.path.join(current_path, item)
            is_last = (i == count - 1)
            
            # Define the connector style (├── or └──)
            connector = "└── " if is_last else "├── "
            
            # Add the folder to the tree lines
            tree_lines.append(f"{prefix}{connector}{item}")
            
            # Update stats
            stats['dirs'] += 1
            
            # Determine the prefix for the children
            extension = "    " if is_last else "│   "
            recurse(path, prefix + extension)

    # --- Main Execution ---
    
    # 1. Add a header
    tree_lines.append(f"Directory Tree for: {root_dir}")
    tree_lines.append("=" * 60)
    
    # 2. Start the recursion from the root
    tree_lines.append(os.path.basename(root_dir) or root_dir) 
    recurse(root_dir)
    
    # 3. Add summary
    tree_lines.append("=" * 60)
    tree_lines.append(f"Total Folders: {stats['dirs']}")

    # 4. Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(tree_lines))
        print(f"\nSuccess! Folder map created at: {output_file}")
    except Exception as e:
        print(f"Error writing to file: {e}")

def main():
    print("Directory Mapper (Folders Only)")
    print("-" * 30)
    
    # Prompt for input
    path_input = input("Enter the directory path to map: ").strip()
    
    # Normalize path (handle quotes if user copy-pasted path with quotes)
    path_input = path_input.strip('"').strip("'")
    
    if not os.path.exists(path_input):
        print(f"Error: The path '{path_input}' does not exist.")
        return

    if not os.path.isdir(path_input):
        print(f"Error: The path '{path_input}' is a file, not a directory.")
        return

    # Define output filename
    output_filename = "directory_map.txt"
    output_path = os.path.join(path_input, output_filename)
    
    # Run the mapper
    generate_tree_structure(path_input, output_path)

if __name__ == "__main__":
    main()