#Log Parser

import os

# test directory
path = "/Users/neeks/PycharmProjects/LogParserScript/tests"

def directory_sweeper():
    """Filter out files by extension & readability.
    Inputs: directory path to unorganized log files
    Outputs: yields file paths for .log/.txt files
    Exceptions: UnicodeError, PermissionError, FileNotFoundError
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




