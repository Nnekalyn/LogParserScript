# Log Parser

A command-line tool that sweeps a flat directory of log files, parses each line against a standard log format, and produces both a human-readable CLI summary and a structured JSON telemetry report.

## Features

- Recursively-free (flat) directory sweep for `.txt`, `.log`, and extensionless files
- Regex-based extraction of date, log level, and message from each line
- Aggregated counts per log level across all files
- Malformed line tracking (file + line number) for anything that doesn't match the expected format
- CLI dashboard highlighting `ERROR`, `CRITICAL`, and `WARNING` entries
- JSON export suitable for downstream ingestion pipelines

## DFD
```text
( User / CLI Invocation )
                                         |
                                         | target_dir, -o output
                                         v
                    +----------------------------------------+
                    | P1: parse_cli_arguments / dir_validation|
                    |  - validate target_dir exists & is dir |
                    +----------------------------------------+
                                         |
                                         | validated path
                                         v
                    +----------------------------------------+
                    | P2: directory_sweeper                  |
                    |  - scan directory entries               |
                    |  - filter by .txt/.log or no extension  |
                    +----------------------------------------+
                                         |
                                         | file_path (per qualifying file)
                                         v
                    +----------------------------------------+
                    | P3: parsing_gate                        |
                    |  - open file                            |
                    |  - match line against DATE [LEVEL] MSG  |
                    |  - split into matched / malformed        |
                    +----------------------------------------+
                       |            |              |
          success/fail |   match    |  no match    |
                       v            v              v
              +----------------+ +----------------+ +---------------------+
              | [Data Store]   | | [Data Store]   | | [Data Store]        |
              | total_files_   | | global_log_    | | global_parsed_      |
              | processed      | | counts         | | records             |
              +----------------+ +----------------+ +---------------------+
                                                              ^
                                                              |
                                                    +---------------------+
                                                    | [Data Store]        |
                                                    | global_malformed_   |
                                                    | records             |
                                                    +---------------------+
                        |            |                |            |
                        +------------+--------+--------+------------+
                                              |
                    +-------------------------+-------------------------+
                    |                                                   |
                    v                                                   v
    +----------------------------------+          +----------------------------------+
    | P4: generate_cli_dashboard       |          | P5: generate_json_payload         |
    |  - format summary + level counts |          |  - build telemetry_payload dict   |
    |  - print incident timeline feed  |          |  - write triage_*.json to disk    |
    +----------------------------------+          +----------------------------------+
                    |                                                   |
                    v                                                   v
        ( Terminal Output )                              ( triage_*.json File )
```

## Requirements

- Python 3.6+
- No third-party dependencies (uses only the standard library: `argparse`, `datetime`, `json`, `platform`, `os`, `re`, `collections`)

## Usage

```bash
python log_parser.py <target_dir> [-o OUTPUT_DIR]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `target_dir` | Yes | Path to the directory containing log files to sweep. Must exist and be a directory. |
| `-o`, `--output` | No | Destination directory for the JSON report. If omitted, the report is written to the current working directory. |

### Examples

Parse logs in `./logs` and write the JSON report to the current directory:

```bash
python log_parser.py ./logs
```

Parse logs and write the JSON report to a specific output folder (created if it doesn't exist):

```bash
python log_parser.py ./logs -o ./reports
```

## Expected Log Line Format

Each line in a log file is matched against:

```
YYYY-MM-DD [LEVEL] message text
```

Example:

```
2026-07-15 [ERROR] Database connection timed out
2026-07-15 [INFO] Health check passed
```

Lines that don't match this pattern are recorded as **malformed** (file + line number) rather than dropped silently.

## Which Files Get Parsed

`directory_sweeper` scans the target directory (non-recursively) and includes a file if either is true:

1. The filename ends in `.txt` or `.log` (case-insensitive), **or**
2. The filename has no extension at all (no `.` in the name)

Symlinks are skipped. Files with any other extension (e.g. `.csv`, `.json`) are ignored.

Whether a file can actually be *opened and read* as text is not checked at this stage — that responsibility belongs to `parsing_gate`, which handles `PermissionError`, `FileNotFoundError`, and `UnicodeDecodeError` for files it can't process, and reports them as failed rather than crashing the pipeline.

## Output

### 1. CLI Dashboard

Printed to the terminal after processing completes:

- Total files processed successfully
- Total count per log level
- Total malformed row count
- A timeline feed of every `ERROR`, `CRITICAL`, and `WARNING` record, in the order encountered

### 2. JSON Report

Written to `triage_<folder_name>_<timestamp>.json`, containing:

```json
{
  "system_name": "hostname",
  "timestamp": "ISO-8601 UTC timestamp",
  "incident_telemetry": [ /* every successfully parsed record */ ],
  "summary": {
    "files_scanned": 0,
    "total_logs_by_level": { "INFO": 0, "ERROR": 0 },
    "total_malformed_count": 0
  },
  "malformed_telemetry": [ /* file + line number for each malformed row */ ]
}
```

The filename is derived from the swept folder's basename and the run timestamp, e.g. `triage_logs_20260715_143000.json`.

## Exit Behavior

- If `target_dir` doesn't exist or isn't a directory, the script exits with status code 2 (via `argparse`) before any processing occurs.
- A file that fails to open (permission denied, not found, or undecodable) does not stop the pipeline — it's counted as failed and processing continues with the next file.

## Known Limitations

- The sweep is **flat only** — it does not recurse into subdirectories.
- Files are opened without an explicit encoding, so behavior may vary slightly across platforms with different default encodings.
- A `UnicodeDecodeError` encountered partway through a file (after some lines were already parsed successfully) discards that file's partial results rather than keeping what was parsed before the error.
## Authors

- [@NnekaLyn](https://www.github.com/nnekalyn)

