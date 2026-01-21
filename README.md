# Waste Tracker (CLI)

A command-line waste tracking tool designed for real restaurant workflows.

This project replaces pen-and-paper waste logs with structured data collection
and simple reporting to support operational decision-making.

---

## Why This Project Exists

Restaurant waste is often tracked manually, which makes it difficult to answer
questions such as:

- Which station produces the most waste?
- Is waste primarily trim or spoilage?
- How much waste is tracked by weight vs portion?
- Are there patterns across days or stations?

This tool captures waste data in a structured format and provides basic summaries
that can be exported for further analysis.

---

## Features (V1)

- Interactive command-line interface
- Log waste entries with:
  - Station
  - Waste category (trim, spoilage, etc.)
  - Item name
  - Quantity type (weight or portion)
- Append-only data storage using JSON Lines (`.jsonl`)
- CSV export for reporting
- Basic summaries by station and waste category

---

## Project Structure

```text
Waste_Tracker/
├── data/
│   └── waste_log.jsonl        # Raw append-only waste log
├── reports/
│   └── waste_log_export.csv   # Generated CSV report
├── src/
│   └── waste_tracker.py       # Main application logic
└── README.md
└── waste_tr.gitignore

```

---

## Example Use Case

A line cook or manager logs daily waste during service.
At the end of the week, the exported CSV can be reviewed
to identify waste patterns by station or category.

