import os
import subprocess

def combine_files_into_text(directory, output_file="combined_code.txt"):
    print(f"Scanning directory: {directory}")

    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return

    # Add the user-provided directory name to the output file
    output_file = f"{directory}_combined_code.txt"

    # Remove the previous file if it exists
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
            print(f"Previous file '{output_file}' deleted.")
        except Exception as e:
            print(f"Error deleting file '{output_file}': {e}")

    combined_content = []
    combined_content.append(f"# Directory: {directory}\n")
    combined_content.append("=" * 80 + "\n")

    # Add tree output
    try:
        tree_output = subprocess.check_output(["tree", directory], text=True)
        combined_content.append("# Directory Structure\n")
        combined_content.append(tree_output)
        combined_content.append("=" * 80 + "\n")
    except FileNotFoundError:
        print("Tree command not found. Skipping directory structure.")
        combined_content.append("# Directory structure not available (tree command not found)\n")
        combined_content.append("=" * 80 + "\n")

    for root, _, files in os.walk(directory):
        print(f"Checking directory: {root}")
        for file in sorted(files):
            if file.endswith(".py") or file == "requirements.txt":
                # Skip the .env file
                if file == ".env":
                    print(f"Skipping .env file: {os.path.join(root, file)}")
                    continue

                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        relative_path = os.path.relpath(file_path, directory)
                        combined_content.append(f"# {relative_path}\n")
                        combined_content.append(f.read())
                        combined_content.append("\n" + "=" * 80 + "\n")
                except UnicodeDecodeError:
                    print(f"UnicodeDecodeError: Cannot read file {file_path}. Skipping...")
                except FileNotFoundError:
                    print(f"FileNotFoundError: File {file_path} not found. Skipping...")
                except Exception as e:
                    print(f"Unexpected error reading file {file_path}: {e}")

    if combined_content:
        try:
            with open(output_file, "w", encoding="utf-8") as output:
                output.write("\n".join(combined_content))
            print(f"Combined content written to {output_file}")
        except Exception as e:
            print(f"Error writing to file {output_file}: {e}")
    else:
        print("No Python or requirements.txt files found to combine.")

if __name__ == "__main__":
    # Request directory name from the user
    directory = input("Enter the name of the directory to scan: ").strip()
    combine_files_into_text(directory)
