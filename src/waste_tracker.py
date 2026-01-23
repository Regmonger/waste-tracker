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


import csv
import json
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("Projects") / "Waste_Tracker"
JSONL_FILE = DATA_DIR / "data" / "waste_log.jsonl"
CSV_EXPORT_FILE = DATA_DIR / "reports" / "waste_log_export.csv"


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
    "burnt/overcooked",
]

VALID_QUANTITY_TYPES = ["lbs", "oz", "po", "qt"]

# Data Model
class WasteEntry:
    """ The WasteEntry class represents a single waste log entry. 
    The attributes include:
    - id: Unique identifier for the entry
    - timestamp: Date and time of the entry
    - station: Station where the waste occurred
    - waste_type: Type of waste
    - item_name: Description of the wasted item
    - quantity_type: Unit of measurement for the quantity
    - quantity_value: Numeric value of the quantity
    - notes: Additional notes about the entry

    Methods:
    - to_dict(): Convert the entry to a dictionary
    - to_json(): Convert the entry to a JSON string
    - from_json(json_str): Create an entry from a JSON string.
    """
    def __init__(self, station: str, waste_type: str, item_name: str, quantity_type: str, quantity_value: float, notes: str = ""):
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
    JSONL_FILE.parent.mkdir(parents=True, exist_ok=True)
    CSV_EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


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


def search_entries_by_item(search_term: str, entries: list[WasteEntry]) -> list[WasteEntry]:
    """Return entries where item_name contains the search ter (case-insensitive)."""
    search_term = search_term.lower()
    return [entry for entry in entries if search_term in entry.item_name.lower()]


def display_entries_for_selections(entries: list[WasteEntry]):
    """Display entries with numbers for user selection. Returns the list for reference."""
    for i, entry in enumerate(entries, start=1):
        date = entry.timestamp[:10]
        print(f" {i}. [{date}] {entry.item_name} - {entry.quantity_value} {entry.quantity_type} ({entry.station})")
    return entries


def delete_entry():
    """Allow user to search for and delete an entry."""
    print("\n-- Delete Entry --")

    entries = load_entries()
    if not entries:
        print("No entries to delete.\n")
        return

    search_term = input("Enter item name to search (or 'list' to show all): ").strip()
    if not search_term:
        print("Search cancelled!")
        return
    
    if search_term.lower() == 'list':
        matches = entries

    else:
        matches = search_entries_by_item(search_term, entries)

    if not matches:
        print(f"No matches were found match '{search_term}'.\n")
        return
    
    # Selection phase
    print(f"\nFound {len(matches)} matching entries:")
    display_entries_for_selections(matches)

    try:
        choice = int(input("\nEnter number to delete (or 0 to cancel): ").strip())
    except ValueError:
        print("Invalid input. Deletion cancelled!\n")
        return
    
    if choice == 0:
        print("Deletion cancelled.\n")
        return
    
    if choice < 1 or choice > len(matches):
        print("Invalid selection. Deletion Cancelled!\n")
        return
    
    #Confirmation of deletion
    selected = matches[choice - 1]
    print(f"\nAbout to delete: {selected.item_name} - {selected.quantity_value} {selected.quantity_type} ({selected.station})")
    confirm = input("Are you sure (y/n): ").strip().lower()

    if confirm != 'y':
        print("Deletion cancelled!\n")
        return
    
    #Delete phase. Filter out and rewrite file
    updated_entries = [e for e in entries if e.id != selected.id]

    with open(JSONL_FILE, 'w', encoding='utf-8') as f:
        for entry in updated_entries:
            f.write(entry.to_json() + "\n")

    print("Entry deleted.\n")

    




def prompt_choice(prompt: str, choices: list[str]) -> str:
    """Function to prompt user to select from a list of choices."""
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
    """Function to log a new waste entry via user prompts.
    If the user enters quantity in ounces, it is converted to pounds.
    """
    print("\n-- Log New Waste Entry --")
    station = prompt_choice("Enter station", VALID_STATIONS)
    waste_type = prompt_choice("Enter waste type", VALID_WASTE_TYPES)
    item_name = input("Enter item name/description: ").strip()
    while not item_name:
        print("Item description cannot be empty.")
        item_name = input("Enter item name/description: ").strip()
    quantity_type = prompt_choice("Enter quantity type", VALID_QUANTITY_TYPES)
    quantity_value = prompt_quantity_value()
    if quantity_type == "oz":
        quantity_value /= 16.0
        quantity_type = "lbs"
        print(f"  (Converted to {quantity_value:.2f} lbs)")
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
    """Generate summary statistics from entries."""
    summary = {
        "total_entries": len(entries),
        "weight_lbs": 0.0,
        "portions": 0.0,
        "volume_qt": 0.0,
        "by_station": defaultdict(lambda: {"weight": 0.0, "portions": 0.0, "volume": 0.0}),
        "by_waste_type": defaultdict(lambda: {"weight": 0.0, "portions": 0.0, "volume": 0.0}),
        "item_frequency": defaultdict(int),
    }
    for entry in entries:
        # Track item frequency
        summary["item_frequency"][entry.item_name] += 1
        
        # Route to correct unit bucket
        if entry.quantity_type == "lbs":
            summary["weight_lbs"] += entry.quantity_value
            summary["by_station"][entry.station]["weight"] += entry.quantity_value
            summary["by_waste_type"][entry.waste_type]["weight"] += entry.quantity_value
        elif entry.quantity_type == "po":
            summary["portions"] += entry.quantity_value
            summary["by_station"][entry.station]["portions"] += entry.quantity_value
            summary["by_waste_type"][entry.waste_type]["portions"] += entry.quantity_value
        elif entry.quantity_type == "qt":
            summary["volume_qt"] += entry.quantity_value
            summary["by_station"][entry.station]["volume"] += entry.quantity_value
            summary["by_waste_type"][entry.waste_type]["volume"] += entry.quantity_value
    
    return summary


def view_summary_report():
    """Display summary report with actionable insights."""
    print("\n-- Summary Report --")
    entries = load_entries()
    if not entries:
        print("No entries logged yet.\n")
        return

    summary = generate_summary(entries)

    # Overview
    print(f"Total entries: {summary['total_entries']}")
    print(f"\nTotal waste by unit")
    print(f"  Weight: {summary['weight_lbs']:.2f} lbs")
    print(f"  Portions: {summary['portions']:.0f}")
    print(f"  Volume: {summary['volume_qt']:.2f} qt")
    
    # Problem waste (excluding trim)
    problem_types = ["spoilage", "overproduction", "burnt/overcooked"]
    problem_weight = sum(summary["by_waste_type"] [wt] ["weight"] for wt in problem_types)
    problem_portions = sum(summary["by_waste_type"] [wt] ["portions"] for wt in problem_types)
    problem_volume = sum(summary["by_waste_type"] [wt] ["volume"] for wt in problem_types)

    print(f"\n** Problem Waste (excluding trim) **")
    print(f"  Weight: {problem_weight:.2f} lbs")
    if problem_portions > 0:
        print(f"  Portions: {problem_portions:.0f}")
    if problem_volume > 0:
        print(f"  Volume: {problem_volume:.2f} qt")
    
    # Breakdown by waste type
    print(f"\nBy waste type:")
    for waste_type in VALID_WASTE_TYPES:
        data = summary["by_waste_type"][waste_type]
        if data["weight"] > 0 or data["portions"] > 0 or data["volume"] > 0:
            parts = []
            if data["weight"] > 0:
                parts.append(f"{data['weight']:.2f} lbs")
            if data["portions"] > 0:
                parts.append(f"{data['portions']:.0f} po")
            if data["volume"] > 0:
                parts.append(f"{data['volume']:.2f} qt")
            print(f"  {waste_type}: {', '.join(parts)}")
    
    # Station breakdown for problem waste only
    print(f"\nProblem waste by station:")
    for station in VALID_STATIONS:
        station_data = {"lbs": 0.0, "po": 0.0, "qt": 0.0}
        for entry in entries:
            if entry.station == station and entry.waste_type in problem_types:
                if entry.quantity_type == "lbs":
                    station_data["lbs"] += entry.quantity_value
                elif entry.quantity_type == "po":
                    station_data["po"] += entry.quantity_value
                elif entry.quantity_type == "qt":
                    station_data["qt"] += entry.quantity_value                
        parts = []
        if station_data["lbs"] > 0:
            parts.append(f"{station_data['lbs']:.2f} lbs")
        if station_data["po"] > 0:
            parts.append(f"{station_data['po']:.0f} po")
        if station_data["qt"] > 0:
            parts.append(f"{station_data['qt']:.2f} qt")
        if parts:
            print(f"  {station}: {', '.join(parts)}")


    # Top items by frequency with waste type breakdown
    print(f"\nTop items by frequency:")
    item_detail = defaultdict(lambda: defaultdict(lambda: {"count": 0, "lbs": 0.0, "po": 0.0, "qt": 0.0}))
    for entry in entries:
        item_detail[entry.item_name][entry.waste_type]["count"] += 1
        if entry.quantity_type == "lbs":
            item_detail[entry.item_name][entry.waste_type]["lbs"] += entry.quantity_value
        elif entry.quantity_type == "po":
            item_detail[entry.item_name][entry.waste_type]["po"] += entry.quantity_value
        elif entry.quantity_type == "qt":
            item_detail[entry.item_name][entry.waste_type]["qt"] += entry.quantity_value
    
    sorted_items = sorted(summary["item_frequency"].items(), key=lambda x: x[1], reverse=True)
    for item, count in sorted_items[:5]:
        breakdown_parts = []
        for waste_type in VALID_WASTE_TYPES:
            wt_data = item_detail[item][waste_type]
            if wt_data["count"] > 0:
                qty_parts = []
                if wt_data["lbs"] > 0:
                    qty_parts.append(f"{wt_data['lbs']:.2f} lbs")
                if wt_data["po"] > 0:
                    qty_parts.append(f"{wt_data['po']:.0f} po")
                if wt_data["qt"] > 0:
                    qty_parts.append(f"{wt_data['qt']:.2f} qt")
                breakdown_parts.append(f"{', '.join(qty_parts)} {waste_type}")
        print(f"  {item}: {count} entries ({'; '.join(breakdown_parts)})")
    
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
    print("4. Delete an entry")
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
            delete_entry()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid selection. Please enter a number between 1 and 5.\n")


if __name__ == "__main__":
    main()

#  End of Waste Tracker code  #

# Future enhancements:
# - User Authentication: Add login functionality to offer limited station access and track entries by user.
# - Data Visualization: Graphs and charts for waste trends over time.
# - Mobile App Integration: Sync data with a mobile app for easier logging.