#Log Parser

import os
import re

def directory_sweeper(path):
    """Filter out files by extension & readability.
    Inputs: directory path to unorganized log files
    Outputs: yields file paths for .log/.txt files
    Exceptions:
        UnicodeError: If file is binary.
        PermissionError: If file has strict permissions.
        FileNotFoundError: If file cannot be found.
       """
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                if not entry.is_symlink():
                    file_path = entry.path
                    file_path = file_path.lower()
                    if file_path.endswith(('.txt', '.log')):
                        yield file_path
                    elif file_path.count('.') < 1:
                        try:
                            with open(file_path, "r") as file:
                                try:
                                    file.read(1)
                                    yield file_path
                                except UnicodeDecodeError:
                                    continue
                        except (PermissionError, FileNotFoundError):
                            yield file_path


def parsing_gate(file_path):
    try:
        with open(file_path, 'r') as file:
            for line_num, line in enumerate(file, 1):
                try:
                    log = re.search(r"^(\d{4}-\d{2}-\d{2})\s+\[(\w+)\]\s+(.*)$", line)
                    if log is None:
                        print(f"File {file_path} | Line {line_num}: MALFORMED LOG")
                        continue
                    date, log_level, message = log.group(1), log.group(2), log.group(3)
                    print(f"    -> SUCCESS: found [{log_level}] message: {message}")
                except Exception as e:
                    print(f"Unexpected error parsing line {line_num}: {e}")
                    continue
    except PermissionError:
        print(f"Missing Permissions. File path:{file_path}")
    except FileNotFoundError:
        print(f"File Not Found. File path:{file_path}")

if __name__ == "__main__":

    # test directory
    path = "/Users/neeks/PycharmProjects/LogParserScript/tests"

    for path_to_parse in directory_sweeper(path):
        print(f"Processing next available resource: {path_to_parse}")
        parsing_gate(path_to_parse)

    print("\n--- Pipeline Complete ---")