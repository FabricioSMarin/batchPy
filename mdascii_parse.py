def parse_text_file(file_path):
    """Parse a text file and process each line according to the specified rules."""
    with open(file_path, 'r') as file:
        for line in file:
            # Strip any leading/trailing whitespace (including newlines)
            stripped_line = line.strip()

            # Skip blank lines
            if not stripped_line:
                continue

            # Check if the line contains an "="
            if "=" in stripped_line:
                # Split the line at the "=" and print the part before it
                print(stripped_line.split("=")[0].strip())
            else:
                # If no "=", check if the line contains "Data Set" and print it
                if "Data Set" in stripped_line:
                    print(stripped_line)

# Example usage:
parse_text_file('/Users/marinf/Downloads/detector_example_files/mda_parse.txt')