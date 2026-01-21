"""
Waste Tracker
--------------
A command-line tool for logging and
analyzing kitchen waste.
Initial version built for personal use in 
a working restaurant.
Author: Reggie
Date: 2026-12-28
"""
# Ok, Copilot, let's build this Waste Tracker! I'm going to give you some specs to work with. 

# Scope for v1.0:
# 1. CLI
# 2. Log waste entries with validation
# 3. Persist entries to disk (JSONL format)
# 4. Basic roporting summaries
# 5. CSV export

# Stations to use: 
# Pasta, grill, middle(fry and plancha), salumi, pasta_prep, other_prep

# Waste types to use:
# trim(primary), spoilage(secondary), overproduction(tertiary), other(rare, optional)

# Quantity units to use:
# -If weight-based: pounds (lbs), ounces (oz)
# -If count-based: portions (po)
# -If volume-based: quarts (qt)

# No cost tracking for v1.0

# Item Identification:
# -Free-text description of wasted item (v1.0)
# -V 1.5: standardized item list with categories

# Data Model (logical):
# -id: unique identifier (UUID)
# -timestamp: date and time of waste entry
# -station: station where waste occurred (from predefined list)
# -waste_type: type of waste (from predefined list)
# -item_name: description of wasted item
# -quantity_type: unit of measurement (from predefined list)
# -quantity_value: numeric value of wasted quantity
# -notes: optional free-text notes

#Storage & Export:
# -Primary storage: JSONL file (one JSON object per line)
# -Export format: CSV for spreadsheet analysis
# -Design allows for future cost fields without schema breakage

# Reporting:
# -Total waste by station
# -Total waste by waste type
# -Counts vs. weights/volumes breakdown
# -Date-range filtering

#Engineering Principles: Demonstrated
# -Input validation and defensive programming
# -Separation of concerns (data model, storage, reporting)
# -Incremental development with future extensibility in mind
# -Real-world applicability for restaurant kitchen operations

# Important notes for both of us, Copilot:
#     This project is intentionally practical. It reflects real constraints, real data, and real workflows. It is designed to be discussed
#      interviews with confidence, including trade-offs and future extensions.
#     Focus on clarity, maintainability, and usability. Avoid over-engineering.

# Must have a menu (for GPT5.1 Codex!):
# 1. Log new waste entry
# 2. View summary report
# 3. Export data to CSV
# 4. Exit

# Start of Waste Tracker code  #

import csv
import json
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
DATA_DIR = Path("Projects/Waste_Tracker")
JSONL_FILE = DATA_DIR / "data/waste_log.jsonl"
CSV_EXPORT_FILE = DATA_DIR / "reports/waste_log_export.csv"

VALID_STATIONS = [
    "pasta",
    "grill",
    "middle",
    "salumi",
    "pasta_prep",
    "other_prep",
]

VALID_WASTE_TYPES = [
    "trim",
    "spoilage",
    "overproduction",
    "other",
]

VALID_QUANTITY_TYPES = ["lbs", "oz", "po", "qt"]

# Data Model
class WasteEntry:
    def __init__(self, station, waste_type, item_name, quantity_type, quantity_value, notes=""):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.station = station
        self.waste_type = waste_type
        self.item_name = item_name
        self.quantity_type = quantity_type
        self.quantity_value = quantity_value
        self.notes = notes

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "station": self.station,
            "waste_type": self.waste_type,
            "item_name": self.item_name,
            "quantity_type": self.quantity_type,
            "quantity_value": self.quantity_value,
            "notes": self.notes
        }

    def to_json(self):
        return json.dumps(self.to_dict())
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        entry = WasteEntry(
            station=data["station"],
            waste_type=data["waste_type"],
            item_name=data["item_name"],
            quantity_type=data["quantity_type"],
            quantity_value=data["quantity_value"],
            notes=data.get("notes", "")
        )
        entry.id = data["id"]
        entry.timestamp = data["timestamp"]
        return entry


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_entry(entry, filename=JSONL_FILE):
    ensure_data_dir()
    with open(filename, "a", encoding="utf-8") as f:
        f.write(entry.to_json() + "\n")


def load_entries(filename=JSONL_FILE):
    entries = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = WasteEntry.from_json(line)
                except json.JSONDecodeError:
                    print("Warning: Skipping malformed log line.")
                    continue
                entries.append(entry)
    except FileNotFoundError:
        pass
    return entries


def prompt_choice(prompt, choices):
    normalized = {choice.lower(): choice for choice in choices}
    choices_display = ", ".join(choices)
    while True:
        response = input(f"{prompt} ({choices_display}): ").strip().lower()
        if response in normalized:
            return normalized[response]
        print("Invalid option. Please choose from the list above.")


def prompt_quantity_value():
    while True:
        raw_value = input("Enter quantity value: ").strip()
        try:
            value = float(raw_value)
            if value <= 0:
                print("Quantity must be greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a numeric quantity.")


def log_new_waste_entry():
    print("\n-- Log New Waste Entry --")
    station = prompt_choice("Enter station", VALID_STATIONS)
    waste_type = prompt_choice("Enter waste type", VALID_WASTE_TYPES)
    item_name = input("Enter item name/description: ").strip()
    while not item_name:
        print("Item description cannot be empty.")
        item_name = input("Enter item name/description: ").strip()
    quantity_type = prompt_choice("Enter quantity type", VALID_QUANTITY_TYPES)
    quantity_value = prompt_quantity_value()
    notes = input("Enter any additional notes (optional): ").strip()

    entry = WasteEntry(
        station=station,
        waste_type=waste_type,
        item_name=item_name,
        quantity_type=quantity_type,
        quantity_value=quantity_value,
        notes=notes,
    )

    save_entry(entry)
    print("Entry saved.\n")


def generate_summary(entries):
    summary = {
        "total_entries": len(entries),
        "totals_by_station": defaultdict(float),
        "totals_by_waste_type": defaultdict(float),
        "quantity_by_unit": defaultdict(float),
    }
    for entry in entries:
        summary["totals_by_station"][entry.station] += entry.quantity_value
        summary["totals_by_waste_type"][entry.waste_type] += entry.quantity_value
        summary["quantity_by_unit"][entry.quantity_type] += entry.quantity_value
    return summary


def view_summary_report():
    print("\n-- Summary Report --")
    entries = load_entries()
    if not entries:
        print("No entries logged yet.\n")
        return

    summary = generate_summary(entries)
    print(f"Total entries: {summary['total_entries']}")

    print("\nWaste by station:")
    for station in VALID_STATIONS:
        total = summary["totals_by_station"].get(station, 0)
        print(f"  {station}: {total:.2f}")

    print("\nWaste by type:")
    for waste_type in VALID_WASTE_TYPES:
        total = summary["totals_by_waste_type"].get(waste_type, 0)
        print(f"  {waste_type}: {total:.2f}")

    print("\nQuantity by unit:")
    for unit in VALID_QUANTITY_TYPES:
        total = summary["quantity_by_unit"].get(unit, 0)
        print(f"  {unit}: {total:.2f}")
    print("")


def export_data_to_csv():
    print("\n-- Export to CSV --")
    entries = load_entries()
    if not entries:
        print("No entries available to export.\n")
        return

    ensure_data_dir()
    with open(CSV_EXPORT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "id",
            "timestamp",
            "station",
            "waste_type",
            "item_name",
            "quantity_type",
            "quantity_value",
            "notes",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.to_dict())
    print(f"Data exported to {CSV_EXPORT_FILE}.\n")


def display_menu():
    print("Waste Tracker Menu")
    print("1. Log new waste entry")
    print("2. View summary report")
    print("3. Export data to CSV")
    print("4. Delete an entry (coming soon)")
    print("5. Exit")


def main():
    print("Welcome to Waste Tracker!\n")
    while True:
        display_menu()
        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            log_new_waste_entry()
        elif choice == "2":
            view_summary_report()
        elif choice == "3":
            export_data_to_csv()
        elif choice == "4":
            print("Coming soon: Delete Entry feature!\n")
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid selection. Please enter a number between 1 and 5.\n")


if __name__ == "__main__":
    main()

#  End of Waste Tracker code  #

# Future enhancements:
# - Refined Summary Reports: More detailed breakdowns, trends over time, visualizations.
# - Delete Entry Functionality: Allow users to remove incorrect entries.
# - User Authentication: Add login functionality to offer limited station access and track entries by user.
# - Data Visualization: Graphs and charts for waste trends over time.
# - Mobile App Integration: Sync data with a mobile app for easier logging.