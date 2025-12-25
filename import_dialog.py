"""
Import data from CSV/Excel files with field mapping and validation
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QComboBox,
                             QGroupBox, QFileDialog, QMessageBox, QProgressBar,
                             QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt
from database import DatabaseManager
from storage import StorageManager
import csv
import json


class ImportDialog(QDialog):
    """Dialog for importing data from CSV files"""

    def __init__(self, db: DatabaseManager, storage: StorageManager,
                 table_id: int, table_name: str, table_display_name: str,
                 fields: list, parent=None):
        super().__init__(parent)
        self.db = db
        self.storage = storage
        self.table_id = table_id
        self.table_name = table_name
        self.table_display_name = table_display_name
        self.fields = fields
        self.csv_headers = []
        self.csv_data = []
        self.field_mapping = {}
        self.file_path = None

        self.setWindowTitle(f"Import Data - {table_display_name}")
        self.resize(900, 700)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("1. Select CSV File")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)

        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(btn_browse)

        layout.addWidget(file_group)

        # Field mapping
        mapping_group = QGroupBox("2. Map CSV Columns to Database Fields")
        mapping_layout = QVBoxLayout(mapping_group)

        mapping_info = QLabel("Match each CSV column to a database field. Unmapped columns will be ignored.")
        mapping_info.setWordWrap(True)
        mapping_layout.addWidget(mapping_info)

        # Mapping table
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(['CSV Column', 'Sample Data', 'Database Field'])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        mapping_layout.addWidget(self.mapping_table)

        layout.addWidget(mapping_group)

        # Options
        options_group = QGroupBox("3. Import Options")
        options_layout = QVBoxLayout(options_group)

        self.skip_first_row = QCheckBox("Skip first row (header row)")
        self.skip_first_row.setChecked(True)
        options_layout.addWidget(self.skip_first_row)

        self.auto_create_fields = QCheckBox("Auto-create missing fields from CSV columns")
        self.auto_create_fields.setChecked(True)
        options_layout.addWidget(self.auto_create_fields)

        self.validate_before_import = QCheckBox("Validate data before importing")
        self.validate_before_import.setChecked(True)
        options_layout.addWidget(self.validate_before_import)

        layout.addWidget(options_group)

        # Progress and errors
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setMaximumHeight(150)
        self.error_log.setVisible(False)
        layout.addWidget(self.error_log)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        self.btn_import = QPushButton("Import Data")
        self.btn_import.clicked.connect(self.import_data)
        self.btn_import.setEnabled(False)
        self.btn_import.setDefault(True)
        btn_layout.addWidget(self.btn_import)

        layout.addLayout(btn_layout)

    def browse_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            self.file_path = file_path
            self.load_csv_file(file_path)

    def load_csv_file(self, file_path: str):
        """Load and preview CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.csv_data = list(reader)

            if not self.csv_data:
                QMessageBox.warning(self, "Empty File", "The selected CSV file is empty.")
                return

            # Get headers (first row)
            self.csv_headers = self.csv_data[0]
            self.file_label.setText(f"Selected: {file_path}")

            # Build field mapping UI
            self.build_mapping_table()

            self.btn_import.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error Loading File",
                               f"Failed to load CSV file:\n{str(e)}")

    def build_mapping_table(self):
        """Build the field mapping table"""
        self.mapping_table.setRowCount(len(self.csv_headers))

        # Get sample data (from second row if available)
        sample_row = self.csv_data[1] if len(self.csv_data) > 1 else []

        for idx, header in enumerate(self.csv_headers):
            # CSV column name
            col_item = QTableWidgetItem(header)
            col_item.setFlags(col_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping_table.setItem(idx, 0, col_item)

            # Sample data
            sample_data = sample_row[idx] if idx < len(sample_row) else ""
            sample_item = QTableWidgetItem(sample_data[:50])  # Truncate long samples
            sample_item.setFlags(sample_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping_table.setItem(idx, 1, sample_item)

            # Database field dropdown
            field_combo = QComboBox()
            field_combo.addItem("(Skip this column)", None)

            # Add option to create new field
            field_combo.addItem(f"✨ Create new field: {header}", f"__CREATE__{header}")

            # Add all database fields
            for field in self.fields:
                if field['name'] != 'id':  # Skip ID field
                    field_combo.addItem(f"{field['display_name']} ({field['field_type']})", field['name'])

            # Try to auto-match by name
            header_lower = header.lower().strip()
            matched = False
            for i in range(2, field_combo.count()):  # Start from 2 to skip "Create new" option
                field_name = field_combo.itemData(i)
                field = next((f for f in self.fields if f['name'] == field_name), None)
                if field:
                    field_display_lower = field['display_name'].lower().strip()
                    if header_lower == field_display_lower or header_lower == field_name:
                        field_combo.setCurrentIndex(i)
                        matched = True
                        break

            # If auto-create is enabled and no match found, default to "Create new"
            if not matched and self.auto_create_fields.isChecked():
                field_combo.setCurrentIndex(1)  # Select "Create new field" option

            self.mapping_table.setCellWidget(idx, 2, field_combo)

        self.mapping_table.resizeColumnsToContents()

    def get_field_mapping(self) -> dict:
        """Get the current field mapping"""
        mapping = {}
        for row in range(self.mapping_table.rowCount()):
            combo = self.mapping_table.cellWidget(row, 2)
            if combo:
                field_name = combo.currentData()
                if field_name:  # Not skipped
                    mapping[row] = field_name
        return mapping

    def validate_data(self) -> tuple:
        """Validate import data and return (is_valid, errors)"""
        errors = []
        field_mapping = self.get_field_mapping()

        if not field_mapping:
            errors.append("No fields are mapped. Please map at least one CSV column to a database field.")
            return False, errors

        # Get data rows (skip header if option is checked)
        start_row = 1 if self.skip_first_row.isChecked() else 0
        data_rows = self.csv_data[start_row:]

        if not data_rows:
            errors.append("No data rows to import.")
            return False, errors

        # Build field metadata lookup
        field_meta = {f['name']: f for f in self.fields}

        # Validate each row
        for row_idx, row_data in enumerate(data_rows, start=start_row + 1):
            for csv_col_idx, db_field_name in field_mapping.items():
                if csv_col_idx >= len(row_data):
                    continue

                value = row_data[csv_col_idx].strip()
                field = field_meta.get(db_field_name)

                if not field:
                    continue

                # Check required fields
                if field['is_required'] and not value:
                    errors.append(f"Row {row_idx}: Required field '{field['display_name']}' is empty")

                # Type validation
                field_type = field['field_type']

                if value:  # Only validate non-empty values
                    if field_type == 'number':
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Row {row_idx}: '{field['display_name']}' must be a number, got '{value}'")

                    elif field_type == 'boolean':
                        valid_bool = value.lower() in ['true', 'false', 'yes', 'no', '1', '0', 'on', 'off']
                        if not valid_bool:
                            errors.append(f"Row {row_idx}: '{field['display_name']}' must be true/false, got '{value}'")

                    elif field_type == 'date':
                        # Basic date format check (accept YYYY-MM-DD)
                        if '-' not in value or len(value.split('-')) != 3:
                            errors.append(f"Row {row_idx}: '{field['display_name']}' must be in YYYY-MM-DD format, got '{value}'")

        # Limit errors shown
        if len(errors) > 50:
            errors = errors[:50]
            errors.append(f"... and {len(errors) - 50} more errors")

        return len(errors) == 0, errors

    def import_data(self):
        """Import the data"""
        # Get field mapping
        field_mapping = self.get_field_mapping()

        if not field_mapping:
            QMessageBox.warning(self, "No Mapping",
                              "Please map at least one CSV column to a database field.")
            return

        # Check for fields to create
        fields_to_create = {}
        for csv_col_idx, db_field_name in field_mapping.items():
            if db_field_name.startswith("__CREATE__"):
                field_name = db_field_name.replace("__CREATE__", "")
                # Infer field type from sample data
                sample_value = self.csv_data[1][csv_col_idx] if len(self.csv_data) > 1 and csv_col_idx < len(self.csv_data[1]) else ""
                field_type = self.infer_field_type(sample_value)
                fields_to_create[csv_col_idx] = {
                    'name': self.sanitize_field_name(field_name),
                    'display_name': field_name,
                    'field_type': field_type
                }

        # Create new fields if any
        if fields_to_create:
            reply = QMessageBox.question(
                self,
                "Create New Fields",
                f"The following {len(fields_to_create)} field(s) will be created:\n\n" +
                "\n".join([f"• {f['display_name']} ({f['field_type']})" for f in fields_to_create.values()]) +
                "\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.No:
                return

            # Create the fields
            for csv_col_idx, field_info in fields_to_create.items():
                try:
                    # Get current max position
                    max_position = max([f.get('position', 0) for f in self.fields], default=0)

                    # Create field using add_field method
                    self.db.add_field(
                        self.table_id,
                        field_info['name'],
                        field_info['display_name'],
                        field_info['field_type'],
                        is_required=False,
                        show_in_list=True,
                        position=max_position + 1
                    )

                    # Add to fields list
                    new_field = {
                        'name': field_info['name'],
                        'display_name': field_info['display_name'],
                        'field_type': field_info['field_type'],
                        'is_required': False,
                        'show_in_list': True
                    }
                    self.fields.append(new_field)

                    # Update mapping to use the actual field name
                    field_mapping[csv_col_idx] = field_info['name']

                except Exception as e:
                    QMessageBox.critical(self, "Field Creation Failed",
                                       f"Failed to create field '{field_info['display_name']}':\n{str(e)}")
                    return

        # Validate if option is checked
        if self.validate_before_import.isChecked():
            is_valid, errors = self.validate_data()
            if not is_valid:
                self.error_log.setVisible(True)
                self.error_log.setPlainText("Validation Errors:\n\n" + "\n".join(errors))
                QMessageBox.warning(self, "Validation Failed",
                                  f"Found {len(errors)} validation error(s). Please fix them and try again.\n\n"
                                  "See the error log below for details.")
                return

        # Get data rows
        start_row = 1 if self.skip_first_row.isChecked() else 0
        data_rows = self.csv_data[start_row:]

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(data_rows))
        self.btn_import.setEnabled(False)

        # Import data
        imported_count = 0
        errors = []

        for row_idx, row_data in enumerate(data_rows):
            try:
                # Build record data
                record_data = {}

                for csv_col_idx, db_field_name in field_mapping.items():
                    if csv_col_idx >= len(row_data):
                        continue

                    value = row_data[csv_col_idx].strip()

                    # Get field metadata
                    field = next((f for f in self.fields if f['name'] == db_field_name), None)
                    if not field:
                        continue

                    # Convert value based on field type
                    converted_value = self.convert_value(value, field)
                    if converted_value is not None or not field['is_required']:
                        record_data[db_field_name] = converted_value

                # Create record
                if record_data:
                    self.db.insert_record(self.table_name, record_data)
                    imported_count += 1

                self.progress_bar.setValue(row_idx + 1)

            except Exception as e:
                errors.append(f"Row {start_row + row_idx + 1}: {str(e)}")

        # Show results
        self.progress_bar.setVisible(False)

        if errors:
            self.error_log.setVisible(True)
            self.error_log.setPlainText("Import Errors:\n\n" + "\n".join(errors[:50]))

        result_msg = f"Successfully imported {imported_count} record(s)."
        if errors:
            result_msg += f"\n\n{len(errors)} record(s) failed to import. See error log for details."

        QMessageBox.information(self, "Import Complete", result_msg)

        if imported_count > 0:
            self.accept()
        else:
            self.btn_import.setEnabled(True)

    def convert_value(self, value: str, field: dict):
        """Convert CSV value to appropriate type for field"""
        if not value:
            return None

        field_type = field['field_type']

        try:
            if field_type == 'number':
                return float(value)

            elif field_type == 'boolean':
                return value.lower() in ['true', 'yes', '1', 'on']

            elif field_type == 'multiselect':
                # Assume comma-separated values
                items = [item.strip() for item in value.split(',') if item.strip()]
                return json.dumps(items)

            elif field_type in ['text', 'email', 'url', 'phone', 'richtext', 'date', 'dropdown']:
                return value

            else:
                return value

        except Exception:
            return value

    def infer_field_type(self, sample_value: str) -> str:
        """Infer field type from sample data"""
        if not sample_value:
            return 'text'

        sample_value = sample_value.strip()

        # Try to detect number
        try:
            float(sample_value)
            return 'number'
        except ValueError:
            pass

        # Try to detect boolean
        if sample_value.lower() in ['true', 'false', 'yes', 'no', '1', '0']:
            return 'boolean'

        # Try to detect date (YYYY-MM-DD format)
        if '-' in sample_value and len(sample_value.split('-')) == 3:
            try:
                parts = sample_value.split('-')
                if len(parts[0]) == 4 and len(parts[1]) <= 2 and len(parts[2]) <= 2:
                    return 'date'
            except:
                pass

        # Try to detect email
        if '@' in sample_value and '.' in sample_value.split('@')[-1]:
            return 'email'

        # Try to detect URL
        if sample_value.startswith(('http://', 'https://', 'www.')):
            return 'url'

        # Default to text
        return 'text'

    def sanitize_field_name(self, display_name: str) -> str:
        """Convert display name to a valid field name"""
        import re
        # Convert to lowercase
        name = display_name.lower()
        # Replace spaces and special chars with underscore
        name = re.sub(r'[^\w]+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = 'field_' + name
        # Ensure it's not empty
        if not name:
            name = 'field'
        return name
