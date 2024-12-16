import os

def scan_directory(root_dir, dir_blacklist=None, file_blacklist=None, output_file="output.txt"):
    """
    Scans the directory recursively and prints and saves the complete content of each file, 
    while ignoring specified directories and files.

    Args:
        root_dir (str): The root directory to start scanning.
        dir_blacklist (list): List of directory names to ignore.
        file_blacklist (list): List of file names to ignore.
        output_file (str): Path to the file where output will be saved.
    """
    dir_blacklist = dir_blacklist or []
    file_blacklist = file_blacklist or []

    # Open the output file for writing
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for root, dirs, files in os.walk(root_dir):
            # Filter out directories in the blacklist
            dirs[:] = [d for d in dirs if d not in dir_blacklist]

            for file_name in files:
                # Skip files in the file blacklist
                if file_name in file_blacklist:
                    continue

                file_path = os.path.join(root, file_name)

                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        # Write and print file information
                        out_file.write(f"File: {file_path}\n")
                        out_file.write("-" * 80 + "\n")
                        print(f"File: {file_path}")
                        print("-" * 80)
                        
                        # Read and save the complete file content
                        for line in file:
                            out_file.write(line)
                            print(line.rstrip())
                        
                        out_file.write("-" * 80 + "\n\n")
                        print("-" * 80 + "\n")
                except Exception as e:
                    error_message = f"Error reading {file_path}: {e}\n"
                    out_file.write(error_message)
                    print(error_message)

if __name__ == "__main__":
    # Specify the root directory, directory blacklist, and file blacklist
    root_directory = "./"  # Change to the desired root directory
    directories_to_ignore = ["__pycache__","_site",".git","venv","image","output","xd"]  # Add directory names to ignore
    files_to_ignore = ["README.md", "LICENSE","output.txt","dirOutput.py","prompt.txt"]  # Add file names to ignore

    # Specify the output file
    output_file_path = "output.txt"

    scan_directory(root_directory, dir_blacklist=directories_to_ignore, file_blacklist=files_to_ignore, output_file=output_file_path)
