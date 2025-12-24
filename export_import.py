"""
Export and import functionality for data
"""
import json
import csv
from typing import List, Dict, Any
from database import DatabaseManager


class DataExporter:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def export_to_json(self, table_name: str, file_path: str):
        """Export table data to JSON"""
        records = self.db.get_records(table_name, limit=None)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, default=str)

    def export_to_csv(self, table_name: str, table_id: int, file_path: str):
        """Export table data to CSV"""
        records = self.db.get_records(table_name, limit=None)
        if not records:
            return

        # Get fields
        fields = self.db.get_fields(table_id)
        field_names = ['id'] + [f['name'] for f in fields]

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()

            for record in records:
                # Filter only the fields we want
                row = {k: v for k, v in record.items() if k in field_names}
                writer.writerow(row)


class DataImporter:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def import_from_json(self, table_name: str, file_path: str) -> int:
        """Import data from JSON file. Returns number of records imported."""
        with open(file_path, 'r', encoding='utf-8') as f:
            records = json.load(f)

        count = 0
        for record in records:
            # Remove id, created_at, updated_at to let DB generate new ones
            data = {k: v for k, v in record.items()
                   if k not in ['id', 'created_at', 'updated_at']}

            self.db.insert_record(table_name, data)
            count += 1

        return count

    def import_from_csv(self, table_name: str, file_path: str) -> int:
        """Import data from CSV file. Returns number of records imported."""
        count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Remove id, created_at, updated_at
                data = {k: v for k, v in row.items()
                       if k and k not in ['id', 'created_at', 'updated_at'] and v}

                self.db.insert_record(table_name, data)
                count += 1

        return count
