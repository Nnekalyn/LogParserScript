#!/usr/bin/env python3
"""
DevOps Triage Utility - Log Parser Engine
Author: Nneka Lyn <nneka.e.lyn@gmail.com>
Version: 1.0.0

Description:
    A resilient, high-performance CLI utility designed to scan, validate,
    and parse unstructured log directories. Outputs structured JSON
    telemetry for system ingestion and a CLI summary.

Usage:
    python scripts/log_parser.py <target_directory> [--output <output_directory>]
"""

import argparse
import datetime
import json
import os
import platform
import re
from collections import Counter


def dir_validation(path):
    """Validates if provided target path is a directory.
    Function is called by parse_cli_arguments()
    Args:
        path(str): absolute or relative target directory path.
    Raises:
        ArgumentTypeError: If the path doesn't exist or points to a file."""

    # Raising argparse.ArgumentTypeError tells the parent parser
    # to capture failure, exit status with code 2 to protect the main orchestrator.
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"{path} does not exist")
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"{path} is not a directory")
    return path


def parse_cli_arguments():
    """Configures the CLI entry gate and extracts execution variables.

    Returns:
        tuple[str, str | None]
            - target_dir: validated path of sweep directory
            - output (str or None): Destination path for telemetry serialization."""
    parser = argparse.ArgumentParser(description="Flat Directory Log Parser")
    # Registered the validator function directly as a type factory callback rule
    # to dynamically execute the disk checks during terminal evaluation.
    parser.add_argument(
        "target_dir",
        help="Path to the unorganized target dir to sweep for logs",
        type=dir_validation,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional destination path to write structured JSON report",
        default=None,
    )
    args = parser.parse_args()
    path = args.target_dir
    output = args.output
    return path, output


def directory_sweeper(path):
    """Filter out files by extension & readability.
    Args:
    path (str): validated path to target directory path to unorganized log files
    Yields:
         str: OS-agnostic absolute file path verified to be text data
    """
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                if not entry.is_symlink():
                    file_path = entry.path
                    file_name_lower = entry.name.lower()
                    if file_name_lower.endswith((".txt", ".log")):
                        yield file_path
                    elif file_name_lower.count(".") < 1:
                        yield file_path


def parsing_gate(file_path):
    """Opens a streaming pipeline into a text log to extract structured records.
    Implements regex pattern extraction wrapped in a loop containment model to
    process rows continuously
    Args:
        file_path (str): the target file path to parse.
    Returns:
        dict: A structured summary status report of parsing successes, aggregated
        counters, and an array of malformed lines
    """
    local_counts = Counter()
    local_malformed = []
    local_records = []
    try:
        with open(file_path, "r") as file:
            for line_num, line in enumerate(file, 1):
                try:
                    log = re.search(
                        r"^"
                        r"(\d{4}-\d{2}-\d{2})"
                        r"\s+\[(\w+)]\s+(.*)"
                        r"$",
                        line,
                    )
                    if log is None:
                        local_malformed.append({"file": file_path, "line": line_num})
                        continue
                    date, log_level, message = log.group(1), log.group(2), log.group(3)
                    local_counts[log_level] += 1
                    local_records.append(
                        {"date": date, "level": log_level, "message": message}
                    )
                except Exception as e:
                    print(f"Unexpected error parsing line {line_num}: {e}")
                    continue
        return {
            "status": "success",
            "log_level": local_counts,
            "malformed": local_malformed,
            "parsed_records": local_records,
        }
    except (PermissionError, FileNotFoundError, UnicodeDecodeError):
        return {
            "status": "failed",
            "log_level": Counter(),
            "malformed": [],
            "parsed_records": [],
        }


def generate_cli_dashboard(total_files, log_counts, malformed_records, parsed_records):
    """Channel 1: Prints a clean, human-readable terminal summary. Designed for triage
    engineers needing immediate system insight."""
    print("=" * 60)
    print("                CLI METRICS SUMMARY                 ")
    print("=" * 60)
    print(f"Total Files Processed Successfully: {total_files}")
    print("-" * 60)
    print("LOG LEVEL METRICS TOTALS:")
    for level, count in log_counts.items():
        print(f"  - {level}: {count}")
    print("-" * 60)
    print(f"Total Malformed Rows Flagged: {len(malformed_records)}")
    print("=" * 60 + "\n")

    print("=" * 60)
    print("             CRITICAL INCIDENT TIMELINE FEED            ")
    print("=" * 60)

    for record in parsed_records:
        if record["level"] in ["ERROR", "CRITICAL", "WARNING"]:
            print(f"[{record['date']}] LOG_LEVEL: {record['level']}")
            print(f" └── ALERT MESSAGE: {record['message']}")
            print("-" * 60)


def generate_json_payload(
    output_filename,
    total_files_processed,
    global_log_counts,
    global_malformed_records,
    global_parsed_records,
):
    """Channel 2: Exports structured telemetry optimized for
    downstream ingestion engines."""
    current_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    telemetry_payload = {
        "system_name": platform.node(),
        "timestamp": current_timestamp,
        "incident_telemetry": global_parsed_records,
        "summary": {
            "files_scanned": total_files_processed,
            "total_logs_by_level": dict(global_log_counts),
            "total_malformed_count": len(global_malformed_records),
        },
        "malformed_telemetry": global_malformed_records,
    }

    with open(output_filename, "w") as json_file:
        json.dump(telemetry_payload, json_file, indent=4)
        print(f"Successfully generated '{output_filename}' ")


if __name__ == "__main__":
    total_files_processed = 0
    global_log_counts = Counter()
    global_malformed_records = []
    global_parsed_records = []

    path, output = parse_cli_arguments()

    print("---Ingestion Pipeline Active---\n")

    for path_to_parse in directory_sweeper(path):
        file_metrics = parsing_gate(path_to_parse)

        if file_metrics["status"] == "success":
            total_files_processed += 1
        global_log_counts.update(file_metrics["log_level"])
        global_malformed_records.extend(file_metrics["malformed"])
        global_parsed_records.extend(file_metrics["parsed_records"])

    generate_cli_dashboard(
        total_files_processed,
        global_log_counts,
        global_malformed_records,
        global_parsed_records,
    )

    folder_context = os.path.basename(os.path.normpath(path))
    time_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if output is None:
        output_filename = f"triage_{folder_context}_{time_stamp}.json"
    else:
        os.makedirs(output, exist_ok=True)
        folder_location = output
        file_name = f"triage_{folder_context}_{time_stamp}.json"
        output_filename = os.path.join(folder_location, file_name)

    generate_json_payload(
        output_filename,
        total_files_processed,
        global_log_counts,
        global_malformed_records,
        global_parsed_records,
    )

    print("\n--- Pipeline Complete ---")
