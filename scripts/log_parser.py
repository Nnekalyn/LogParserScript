#Log Parser

import os
import re
import json
from collections import Counter
import datetime


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
    local_counts = Counter()
    local_malformed = []
    try:
        with open(file_path, 'r') as file:
            for line_num, line in enumerate(file, 1):
                try:
                    log = re.search(r"^"
                                    r"(\d{4}-\d{2}-\d{2})"
                                    r"\s+\[(\w+)]\s+(.*)"
                                    r"$", line)
                    if log is None:
                        local_malformed.append({"file": file_path, "line": line_num})
                        continue
                    date, log_level, message = log.group(1), log.group(2), log.group(3)
                    local_counts[log_level] += 1
                except Exception as e:
                    print(f"Unexpected error parsing line {line_num}: {e}")
                    continue
        return {
            "status": "success",
            "log_level": local_counts,
            "malformed": local_malformed
        }
    except PermissionError:
        return {"status": "failed", "log_level": Counter(), "malformed": []}
    except FileNotFoundError:
        return {"status": "failed", "log_level": Counter(), "malformed": []}

if __name__ == "__main__":

    # test directory
    path = "/Users/neeks/PycharmProjects/LogParserScript/tests"

    total_files_processed = 0
    global_log_counts = Counter()
    global_malformed_records = []

    print("---Ingestion Pipeline Active---\n")

    for path_to_parse in directory_sweeper(path):
        file_metrics = parsing_gate(path_to_parse)

        if file_metrics["status"] == "success":
            total_files_processed += 1
        global_log_counts.update(file_metrics["log_level"])
        global_malformed_records.extend(file_metrics["malformed"])

    print("\n--- Pipeline Complete ---")
