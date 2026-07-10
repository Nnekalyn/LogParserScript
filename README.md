# Resilient Log Telemetry & API Payload Pipeline

This memory-efficient script parses logs from a directory using regex groups, isolates binary files, aggregates cross-file analytics, and outputs notable logs in both a CLI summary and an API-ready .json file (for, as an example, ServiceNow). 



## DFD
```
                [ Raw Target Directory ]
                          │
            ▲             ▼
 MODULE 1   │   ┌───────────────────┐
Sweeper Gate│   │ directory_sweeper │ ──(Drops hidden binary traps)
            │   └───────────────────┘
                          │  (Yields 1 Clean File Path at a time)
                          ▼
 MODULE 2   │   ┌───────────────────┐
Parser Gate │   │   parsing_gate    │ ──(Catches Permission/Line Errors)
            ▼   └───────────────────┘
                          │  (Returns Local Metric Dicts)
                          ▼
            ┌───────────────────────────┐
 MODULE 3   │ Global Accumulator Ledger │ ──(Orchestrator Management)
            └───────────────────────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
   ┌───────────────────┐     ┌───────────────────┐
   │   CLI Dashboard   │     │ API JSON Payload  │
   │ (Manual Triage)   │     │ (ServiceNow Ingest)
   └───────────────────┘     └───────────────────┘

   ```
## Features
Zero-Memory Footprint Streamer: Implements a Python generator framework via os.scandir(), allowing the engine to sweep millions of files without overloading system RAM.

Binary Trap Mitigation: Inspects the initial byte headers of extensionless files (file.read(1)) to trap and bypass compressed binaries, completely avoiding fatal runtime parsing crashes.

Decoupled Local/Global State Architecture: Isolates file-level analytics within local tracking scopes (Counter) to ensure runtime faults within one file never corrupt the system metrics ledger.

Data Formatting: ISO 8601 dynamic UTC timestamps

Language: Python 3.10+ (Zero external third-party dependencies required)




## Output Example


### CLI Dashboard
When executed, the pipeline prints a real-time, human-readable triage feed directly to the terminal:

```text
============================================================
                CLI METRICS SUMMARY                 
============================================================
Total Files Processed Successfully: 4
------------------------------------------------------------
LOG LEVEL METRICS TOTALS:
  - INFO: 24
  - WARNING: 3
  - ERROR: 2
  - CRITICAL: 1
------------------------------------------------------------
Total Malformed Rows Flagged: 1
============================================================

============================================================
             CRITICAL INCIDENT TIMELINE FEED            
============================================================
[2026-07-10] LOG_LEVEL: CRITICAL
 └── ALERT MESSAGE: Core temperature exceeds threshold.
------------------------------------------------------------
```

### ServiceNow API Target Payload
The pipeline automatically generates an API-ready JSON artifact mapping the global system telemetry:

```json
{
    "system_name": "production-app-srv-02",
    "timestamp": "2026-07-10T14:28:05.109283+00:00",
    "incident_telemetry": [
        {
            "date": "2026-07-10",
            "level": "CRITICAL",
            "message": "Core temperature exceeds threshold."
        }
    ],
    "summary": {
        "files_scanned": 4,
        "total_logs_by_level": {
            "INFO": 24,
            "WARNING": 3,
            "ERROR": 2,
            "CRITICAL": 1
        },
        "total_malformed_count": 1
    },
    "malformed_telemetry": [
        {"file": "/var/log/tests/mixed_payload.txt", "line": 2}
    ]
}
```
## Next Steps

Currently, this program uses hard-coded paths. The next steps are to remove the hardcoded paths and inject configuration data using CLI arguments and environment variables.

## Authors

- [@NnekaLyn](https://www.github.com/nnekalyn)

