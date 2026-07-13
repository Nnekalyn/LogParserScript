#Log Parser
import argparse
import datetime
import json
import os
import platform
import re
from collections import Counter

def dir_validation(path):
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"{path} does not exist")
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"{path} is not a directory")
    return path

def parse_cli_arguments():
    parser = argparse.ArgumentParser(
        description = "Flat Directory Log Parser"
    )
    parser.add_argument("target_dir", help = "Path to the unorganized target dir "
                                             "to sweep for logs", type = dir_validation
                        )
    parser.add_argument("-o", "--output", help = "Optional destination path to"
                                                 " write structured JSON report",
                        default = None
                        )
    args = parser.parse_args()
    path = args.target_dir
    output = args.output
    return path, output


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
    local_records = []
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
                    local_records.append({
                        "date": date,
                        "level": log_level,
                        "message": message
                    })
                except Exception as e:
                    print(f"Unexpected error parsing line {line_num}: {e}")
                    continue
        return {
            "status": "success",
            "log_level": local_counts,
            "malformed": local_malformed,
            "parsed_records": local_records
        }
    except PermissionError:
        return {"status": "failed", "log_level": Counter(),
                "malformed": [],"parsed_records": []
                }
    except FileNotFoundError:
        return {"status": "failed", "log_level": Counter(),
                "malformed": [],"parsed_records": []
                }

def generate_cli_dashboard(total_files, log_counts, malformed_records, parsed_records):
    """Channel 1: Prints a clean, human-readable terminal summary."""
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


def generate_json_payload(output_filename, total_files_processed,global_log_counts,
                          global_malformed_records, global_parsed_records):
    """Channel 2: Exports structured telemetry for ServiceNow ingestion."""
    current_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    service_now_payload = {
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
        json.dump(service_now_payload, json_file, indent=4)
        print(f"Successfully generated '{output_filename}' for ServiceNow ingestion.")

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
        global_parsed_records
    )



    folder_context = os.path.basename(os.path.normpath(path))
    time_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if output == None:
        output_filename = f"triage_{folder_context}_{time_stamp}.json"

    else:
        folder_location = output
        file_name = f"triage_{folder_context}_{time_stamp}.json"
        output_filename = os.path.join(folder_location, file_name)

    """folder_location = os.path.dirname(output)
    folder_context = os.path.basename(os.path.normpath(path))
    time_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"triage_{folder_context}_{time_stamp}.json"
    """

    generate_json_payload(
        output_filename,
        total_files_processed,
        global_log_counts,
        global_malformed_records,
        global_parsed_records,
    )

    print("\n--- Pipeline Complete ---")
