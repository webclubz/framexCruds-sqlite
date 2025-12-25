"""
Record view for displaying and managing records in a table
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QMessageBox, QHeaderView, QComboBox, QSpinBox,
                             QFileDialog)
from PyQt6.QtCore import Qt
from database import DatabaseManager
from storage import StorageManager
import json
import csv


class RecordView(QWidget):
    def __init__(self, db: DatabaseManager, storage: StorageManager,
                 table_id: int, table_name: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.storage = storage
        self.table_id = table_id
        self.table_name = table_name
        self.fields = []
        self.current_page = 0
        self.page_size = 50
        self.total_records = 0
        self.sort_column = 'id'
        self.sort_order = 'ASC'
        self.active_filters = {}

        self.init_ui()
        self.load_fields()
        self.load_records()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Top toolbar
        toolbar = QHBoxLayout()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.returnPressed.connect(self.search_records)
        toolbar.addWidget(QLabel("Search:"))
        toolbar.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_records)
        toolbar.addWidget(search_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        toolbar.addWidget(clear_btn)

        # Advanced filter button
        filter_btn = QPushButton("Advanced Filter")
        filter_btn.clicked.connect(self.show_filter_dialog)
        toolbar.addWidget(filter_btn)

        toolbar.addStretch()

        # Add record button
        self.btn_add = QPushButton("Add Record")
        self.btn_add.clicked.connect(self.add_record)
        toolbar.addWidget(self.btn_add)

        layout.addLayout(toolbar)

        # Records table
        self.records_table = QTableWidget()
        self.records_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.records_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.records_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.records_table.itemDoubleClicked.connect(self.edit_record)
        layout.addWidget(self.records_table)

        # Bottom toolbar (pagination and actions)
        bottom_toolbar = QHBoxLayout()

        # Pagination
        self.btn_prev = QPushButton("Previous")
        self.btn_prev.clicked.connect(self.previous_page)
        bottom_toolbar.addWidget(self.btn_prev)

        self.page_label = QLabel("Page 1 of 1")
        bottom_toolbar.addWidget(self.page_label)

        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self.next_page)
        bottom_toolbar.addWidget(self.btn_next)

        bottom_toolbar.addStretch()

        # Page size
        bottom_toolbar.addWidget(QLabel("Records per page:"))
        self.page_size_combo = QComboBox()
        for size in [25, 50, 100, 200]:
            self.page_size_combo.addItem(str(size), size)
        self.page_size_combo.setCurrentIndex(1)  # 50
        self.page_size_combo.currentIndexChanged.connect(self.on_page_size_changed)
        bottom_toolbar.addWidget(self.page_size_combo)

        # Record actions
        self.btn_preview = QPushButton("Preview")
        self.btn_preview.clicked.connect(self.preview_record)
        bottom_toolbar.addWidget(self.btn_preview)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.edit_record)
        bottom_toolbar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_record)
        bottom_toolbar.addWidget(self.btn_delete)

        bottom_toolbar.addSpacing(10)

        # Export button
        self.btn_export = QPushButton("Export to CSV")
        self.btn_export.clicked.connect(self.export_to_csv)
        bottom_toolbar.addWidget(self.btn_export)

        # Report button
        self.btn_report = QPushButton("Generate Report")
        self.btn_report.clicked.connect(self.generate_report)
        bottom_toolbar.addWidget(self.btn_report)

        layout.addLayout(bottom_toolbar)

    def load_fields(self):
        """Load table fields"""
        self.fields = self.db.get_fields(self.table_id)

        # Filter fields to only show those with show_in_list = True
        self.visible_fields = [f for f in self.fields if f.get('show_in_list', True)]

        # Set up table columns (only visible fields)
        columns = ['ID'] + [f['display_name'] for f in self.visible_fields]
        self.records_table.setColumnCount(len(columns))
        self.records_table.setHorizontalHeaderLabels(columns)
        self.records_table.horizontalHeader().setStretchLastSection(True)

    def load_records(self):
        """Load records from database"""
        # Count total records
        self.total_records = self.db.count_records(self.table_name)

        # Calculate total pages
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)

        # Ensure current page is valid
        self.current_page = min(self.current_page, total_pages - 1)
        self.current_page = max(0, self.current_page)

        # Load records
        offset = self.current_page * self.page_size
        records = self.db.get_records(
            self.table_name,
            limit=self.page_size,
            offset=offset,
            order_by=self.sort_column,
            order_dir=self.sort_order
        )

        # Populate table
        self.records_table.setRowCount(len(records))

        for row_idx, record in enumerate(records):
            # ID column
            id_item = QTableWidgetItem(str(record['id']))
            id_item.setData(Qt.ItemDataRole.UserRole, record['id'])
            self.records_table.setItem(row_idx, 0, id_item)

            # Field columns (only visible fields)
            for col_idx, field in enumerate(self.visible_fields):
                value = record.get(field['name'], '')
                display_value = self.format_field_value(field, value)

                item = QTableWidgetItem(display_value)
                self.records_table.setItem(row_idx, col_idx + 1, item)

        # Update pagination UI
        self.update_pagination_ui(total_pages)

    def get_reference_display_name(self, record: dict, table_id: int) -> str:
        """Get a meaningful display name for a referenced record"""
        # Get fields for the referenced table
        ref_fields = self.db.get_fields(table_id)

        # Try to find a good display field (text, email, or first string field)
        for ref_field in ref_fields:
            field_type = ref_field['field_type']
            field_name = ref_field['name']

            # Skip non-text fields and ID
            if field_name == 'id':
                continue

            # Prioritize text-like fields
            if field_type in ['text', 'email', 'phone', 'url']:
                value = record.get(field_name)
                if value:
                    return str(value)

        # If no text field found, try any field with a value
        for ref_field in ref_fields:
            field_name = ref_field['name']
            if field_name != 'id':
                value = record.get(field_name)
                if value:
                    return str(value)

        # Fallback to ID
        return f"ID: {record['id']}"

    def format_field_value(self, field: dict, value) -> str:
        """Format field value for display"""
        if value is None or value == '':
            return ''

        field_type = field['field_type']

        if field_type == 'boolean':
            return 'Yes' if value else 'No'
        elif field_type == 'multiselect':
            try:
                items = json.loads(value) if isinstance(value, str) else value
                return ', '.join(items) if items else ''
            except:
                return str(value)
        elif field_type in ['image', 'file']:
            return '📎 ' + str(value).split('/')[-1] if value else ''
        elif field_type == 'reference':
            if not value:
                return ''
            # Get the referenced record and display the appropriate field
            if field.get('reference_table_id'):
                ref_table = self.db.get_table(field['reference_table_id'])
                if ref_table:
                    ref_record = self.db.get_record(ref_table['name'], value)
                    if ref_record:
                        display_field = field.get('reference_display_field')
                        if display_field and display_field in ref_record:
                            return str(ref_record[display_field])
                        # Fallback to auto-detection
                        return self.get_reference_display_name(ref_record, field['reference_table_id'])
            return f"ID: {value}"
        elif field_type == 'multireference':
            if not value:
                return ''
            try:
                ids = json.loads(value) if isinstance(value, str) else value
                if not ids:
                    return ''
                # Get referenced records and display their values
                if field.get('reference_table_id'):
                    ref_table = self.db.get_table(field['reference_table_id'])
                    if ref_table:
                        display_names = []
                        for record_id in ids:
                            ref_record = self.db.get_record(ref_table['name'], record_id)
                            if ref_record:
                                display_field = field.get('reference_display_field')
                                if display_field and display_field in ref_record:
                                    display_names.append(str(ref_record[display_field]))
                                else:
                                    # Fallback to auto-detection
                                    display_names.append(self.get_reference_display_name(ref_record, field['reference_table_id']))
                        return ', '.join(display_names) if display_names else ''
                return f"IDs: {', '.join(map(str, ids))}"
            except:
                return str(value)
        else:
            return str(value)

    def update_pagination_ui(self, total_pages: int):
        """Update pagination controls"""
        current_display = self.current_page + 1
        self.page_label.setText(f"Page {current_display} of {total_pages} ({self.total_records} records)")

        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < total_pages - 1)

    def on_header_clicked(self, logical_index: int):
        """Handle column header click for sorting"""
        if logical_index == 0:
            column_name = 'id'
        else:
            field = self.visible_fields[logical_index - 1]
            column_name = field['name']

        # Toggle sort order if same column
        if self.sort_column == column_name:
            self.sort_order = 'DESC' if self.sort_order == 'ASC' else 'ASC'
        else:
            self.sort_column = column_name
            self.sort_order = 'ASC'

        self.load_records()

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_records()

    def next_page(self):
        """Go to next page"""
        total_pages = (self.total_records + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_records()

    def on_page_size_changed(self):
        """Handle page size change"""
        self.page_size = self.page_size_combo.currentData()
        self.current_page = 0
        self.load_records()

    def search_records(self):
        """Search records"""
        search_term = self.search_input.text().strip()
        if not search_term:
            self.load_records()
            return

        # Search across all text-based fields
        searchable_fields = [f['name'] for f in self.fields
                            if f['field_type'] in ['text', 'email', 'url', 'phone', 'richtext']]

        if not searchable_fields:
            QMessageBox.information(self, "Search", "No searchable fields in this table")
            return

        records = self.db.search_records(self.table_name, searchable_fields, search_term)

        # Display results
        self.records_table.setRowCount(len(records))

        for row_idx, record in enumerate(records):
            id_item = QTableWidgetItem(str(record['id']))
            id_item.setData(Qt.ItemDataRole.UserRole, record['id'])
            self.records_table.setItem(row_idx, 0, id_item)

            for col_idx, field in enumerate(self.fields):
                value = record.get(field['name'], '')
                display_value = self.format_field_value(field, value)

                item = QTableWidgetItem(display_value)
                self.records_table.setItem(row_idx, col_idx + 1, item)

        # Disable pagination during search
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.page_label.setText(f"{len(records)} results found")

    def clear_search(self):
        """Clear search and reload all records"""
        self.search_input.clear()
        self.active_filters = {}
        self.current_page = 0
        self.load_records()

    def show_filter_dialog(self):
        """Show advanced filter dialog"""
        from filter_dialog import FilterDialog

        dialog = FilterDialog(self.fields, parent=self)
        if dialog.exec():
            self.active_filters = dialog.get_filters()
            self.apply_filters()

    def apply_filters(self):
        """Apply active filters to records"""
        if not self.active_filters:
            self.load_records()
            return

        # Clear search input when using filters
        self.search_input.clear()

        # Get filtered records
        records = self.db.filter_records(self.table_name, self.active_filters)

        # Display results
        self.records_table.setRowCount(len(records))

        for row_idx, record in enumerate(records):
            id_item = QTableWidgetItem(str(record['id']))
            id_item.setData(Qt.ItemDataRole.UserRole, record['id'])
            self.records_table.setItem(row_idx, 0, id_item)

            for col_idx, field in enumerate(self.visible_fields):
                value = record.get(field['name'], '')
                display_value = self.format_field_value(field, value)

                item = QTableWidgetItem(display_value)
                self.records_table.setItem(row_idx, col_idx + 1, item)

        # Disable pagination during filter
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        filter_count = len(self.active_filters)
        self.page_label.setText(f"{len(records)} results ({filter_count} filter{'s' if filter_count > 1 else ''} active)")

    def add_record(self):
        """Add a new record"""
        from record_dialog import RecordDialog

        dialog = RecordDialog(self.db, self.storage, self.table_id,
                             self.table_name, self.fields, parent=self)
        if dialog.exec():
            self.load_records()

    def edit_record(self):
        """Edit the selected record"""
        current_row = self.records_table.currentRow()
        if current_row < 0:
            return

        record_id = self.records_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        from record_dialog import RecordDialog

        dialog = RecordDialog(self.db, self.storage, self.table_id,
                             self.table_name, self.fields, record_id, parent=self)
        if dialog.exec():
            self.load_records()

    def preview_record(self):
        """Preview the selected record"""
        current_row = self.records_table.currentRow()
        if current_row < 0:
            return

        record_id = self.records_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        from record_preview import RecordPreviewDialog

        # Get table display name
        table = self.db.get_table(self.table_id)
        table_display_name = table['display_name'] if table else self.table_name

        dialog = RecordPreviewDialog(
            self.db, self.storage, self.table_id,
            self.table_name, table_display_name,
            self.fields, record_id, parent=self
        )
        dialog.exec()

    def delete_record(self):
        """Delete the selected record"""
        current_row = self.records_table.currentRow()
        if current_row < 0:
            return

        record_id = self.records_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete record #{record_id}?\n\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete files associated with this record
            self.storage.delete_record_files(self.table_name, record_id)

            # Delete record
            self.db.delete_record(self.table_name, record_id)

            self.load_records()

    def export_to_csv(self):
        """Export current records to CSV file"""
        # Get the current records to export
        if self.active_filters:
            # Export filtered records
            records = self.db.filter_records(self.table_name, self.active_filters)
            default_filename = f"{self.table_name}_filtered_export.csv"
        elif self.search_input.text().strip():
            # Export search results
            search_term = self.search_input.text().strip()
            searchable_fields = [f['name'] for f in self.fields
                                if f['field_type'] in ['text', 'email', 'url', 'phone', 'richtext']]
            records = self.db.search_records(self.table_name, searchable_fields, search_term)
            default_filename = f"{self.table_name}_search_export.csv"
        else:
            # Export all records
            records = self.db.get_records(self.table_name, limit=999999)
            default_filename = f"{self.table_name}_export.csv"

        if not records:
            QMessageBox.information(self, "Export", "No records to export")
            return

        # Ask user for file location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            default_filename,
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Use visible fields for export
                field_names = ['ID'] + [f['display_name'] for f in self.visible_fields]
                writer = csv.DictWriter(csvfile, fieldnames=field_names)

                # Write header
                writer.writeheader()

                # Write records
                for record in records:
                    row = {'ID': record['id']}
                    for field in self.visible_fields:
                        value = record.get(field['name'], '')
                        # Format the value for CSV
                        display_value = self.format_field_value(field, value)
                        row[field['display_name']] = display_value

                    writer.writerow(row)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(records)} record(s) to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export records:\n{str(e)}"
            )

    def generate_report(self):
        """Generate a custom report"""
        from report_builder import ReportBuilderDialog
        from report_viewer import ReportViewerDialog

        # Get table display name
        table = self.db.get_table(self.table_id)
        table_display_name = table['display_name'] if table else self.table_name

        # Show report builder dialog
        builder = ReportBuilderDialog(
            self.db,
            self.storage,
            self.table_id,
            self.table_name,
            table_display_name,
            self.fields,
            parent=self
        )

        if builder.exec():
            # Get report configuration
            config = builder.get_report_config()

            # Show report viewer
            viewer = ReportViewerDialog(
                self.db,
                self.storage,
                self.table_id,
                self.table_name,
                table_display_name,
                self.fields,
                config,
                parent=self
            )
            viewer.exec()

    def export_template(self):
        """Export a blank CSV template for data entry"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Import Template",
            f"{self.table_name}_template.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Use all non-ID fields for template
                template_fields = [f for f in self.fields if f['name'] != 'id']
                field_names = [f['display_name'] for f in template_fields]
                writer = csv.DictWriter(csvfile, fieldnames=field_names)

                # Write header
                writer.writeheader()

                # Write one example row with field type hints
                example_row = {}
                for field in template_fields:
                    field_type = field['field_type']
                    if field_type == 'text':
                        example_row[field['display_name']] = 'Example text'
                    elif field_type == 'number':
                        example_row[field['display_name']] = '123.45'
                    elif field_type == 'date':
                        example_row[field['display_name']] = '2025-12-25'
                    elif field_type == 'boolean':
                        example_row[field['display_name']] = 'true'
                    elif field_type == 'email':
                        example_row[field['display_name']] = 'example@email.com'
                    elif field_type == 'phone':
                        example_row[field['display_name']] = '+1234567890'
                    elif field_type == 'url':
                        example_row[field['display_name']] = 'https://example.com'
                    elif field_type == 'dropdown':
                        example_row[field['display_name']] = 'Option1'
                    elif field_type == 'multiselect':
                        example_row[field['display_name']] = 'Option1, Option2'
                    else:
                        example_row[field['display_name']] = f'({field_type})'

                writer.writerow(example_row)

            QMessageBox.information(
                self,
                "Template Exported",
                f"Import template exported to:\n{file_path}\n\n"
                "The first row contains example data showing the expected format.\n"
                "Delete the example row and add your data below the header."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export template:\n{str(e)}"
            )

    def import_data(self):
        """Import data from CSV file"""
        from import_dialog import ImportDialog

        # Get table display name
        table = self.db.get_table(self.table_id)
        table_display_name = table['display_name'] if table else self.table_name

        # Show import dialog
        dialog = ImportDialog(
            self.db,
            self.storage,
            self.table_id,
            self.table_name,
            table_display_name,
            self.fields,
            parent=self
        )

        if dialog.exec():
            # Reload records after import
            self.load_records()
