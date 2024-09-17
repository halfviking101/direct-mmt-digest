#!/usr/bin/env python3
import json
import os


def merge_json_files(input_directory, output_file):
    # List to store JSON data from all files
    all_data = []

    # Iterate over each file in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".json"):
            file_path = os.path.join(input_directory, filename)

            # Read and load JSON content from the file
            with open(file_path, "r") as file:
                try:
                    data = json.load(file)
                    all_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {file_path}: {e}")

    # Write the combined data to the output file
    with open(output_file, "w") as output_file:
        json.dump(all_data, output_file, indent=2)


# Example usage: Merge JSON files in the "input_files" directory into "merged_output.json"
merge_json_files("fetched_data", "merged_output.json")
