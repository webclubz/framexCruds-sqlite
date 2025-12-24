"""
Dialog for creating and editing tables and their fields
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QCheckBox, QMessageBox, QHeaderView,
                             QWidget, QTabWidget, QFormLayout, QGroupBox,
                             QTextEdit)
from PyQt6.QtCore import Qt
import json
import config
from database import DatabaseManager


class TableDialog(QDialog):
    def __init__(self, db: DatabaseManager, table_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.table_id = table_id
        self.is_edit_mode = table_id is not None
        self.fields = []

        self.setWindowTitle("Edit Table" if self.is_edit_mode else "New Table")
        self.resize(800, 600)

        self.init_ui()

        if self.is_edit_mode:
            self.load_table_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Table name section
        name_group = QGroupBox("Table Information")
        name_layout = QVBoxLayout(name_group)

        # Table Name (label above input)
        table_name_label = QLabel("Table Name:")
        table_name_label.setObjectName('FormFieldLabel')
        name_layout.addWidget(table_name_label)

        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("e.g., products")
        if self.is_edit_mode:
            self.table_name_input.setEnabled(False)  # Can't change table name after creation
        name_layout.addWidget(self.table_name_input)

        # Display Name (label above input)
        display_name_label = QLabel("Display Name:")
        display_name_label.setObjectName('FormFieldLabel')
        name_layout.addWidget(display_name_label)

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("e.g., Products")
        name_layout.addWidget(self.display_name_input)

        layout.addWidget(name_group)

        # Fields section
        fields_group = QGroupBox("Fields")
        fields_layout = QVBoxLayout(fields_group)

        # Field table
        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(8)
        self.fields_table.setHorizontalHeaderLabels([
            "Field Name", "Display Name", "Type", "Required", "Unique", "Show in List", "Options", "Actions"
        ])
        self.fields_table.horizontalHeader().setStretchLastSection(False)
        self.fields_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.fields_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.fields_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        fields_layout.addWidget(self.fields_table)

        # Add field button
        btn_add_field = QPushButton("Add Field")
        btn_add_field.clicked.connect(self.add_field_row)
        fields_layout.addWidget(btn_add_field)

        layout.addWidget(fields_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save" if self.is_edit_mode else "Create")
        btn_save.clicked.connect(self.save_table)
        btn_save.setDefault(True)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def add_field_row(self, field_data: dict = None):
        """Add a row to the fields table"""
        row = self.fields_table.rowCount()
        self.fields_table.insertRow(row)

        # Field name
        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., price")
        if field_data:
            name_input.setText(field_data.get('name', ''))
        self.fields_table.setCellWidget(row, 0, name_input)

        # Display name
        display_input = QLineEdit()
        display_input.setPlaceholderText("e.g., Price")
        if field_data:
            display_input.setText(field_data.get('display_name', ''))
        self.fields_table.setCellWidget(row, 1, display_input)

        # Type
        type_combo = QComboBox()
        for field_type in config.FIELD_TYPES:
            type_combo.addItem(field_type.capitalize(), field_type)
        if field_data:
            index = type_combo.findData(field_data.get('field_type'))
            if index >= 0:
                type_combo.setCurrentIndex(index)
        type_combo.currentIndexChanged.connect(lambda: self.on_type_changed(row))
        self.fields_table.setCellWidget(row, 2, type_combo)

        # Required
        required_check = QCheckBox()
        required_check.setStyleSheet("margin-left: 50%;")
        if field_data:
            required_check.setChecked(field_data.get('is_required', False))
        self.fields_table.setCellWidget(row, 3, required_check)

        # Unique
        unique_check = QCheckBox()
        unique_check.setStyleSheet("margin-left: 50%;")
        if field_data:
            unique_check.setChecked(field_data.get('is_unique', False))
        self.fields_table.setCellWidget(row, 4, unique_check)

        # Show in List
        show_in_list_check = QCheckBox()
        show_in_list_check.setStyleSheet("margin-left: 50%;")
        if field_data:
            show_in_list_check.setChecked(field_data.get('show_in_list', True))
        else:
            show_in_list_check.setChecked(True)  # Default to checked
        self.fields_table.setCellWidget(row, 5, show_in_list_check)

        # Options (for dropdown, multiselect, reference)
        options_widget = QWidget()
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 0, 0, 0)

        # Hidden input to store the options data
        options_input = QLineEdit()
        options_input.setVisible(False)
        if field_data:
            # Preserve any stored options (dropdown/multiselect JSON)
            if field_data.get('options'):
                options_input.setText(field_data.get('options', ''))

            # For reference/multireference, options are not used; metadata lives in separate columns.
            # Populate the hidden input with a JSON blob so a subsequent Save round-trips these values.
            if field_data.get('field_type') in ['reference', 'multireference'] and not options_input.text():
                ref_data = {
                    'table_id': field_data.get('reference_table_id'),
                    'display_field': field_data.get('reference_display_field')
                }
                try:
                    import json as _json
                    options_input.setText(_json.dumps(ref_data))
                except Exception:
                    # Fallback: simple string for table id if JSON fails
                    if ref_data.get('table_id') is not None:
                        options_input.setText(str(ref_data['table_id']))
        options_layout.addWidget(options_input)

        options_btn = QPushButton("Edit")
        options_btn.clicked.connect(lambda: self.edit_field_options(row))
        options_layout.addWidget(options_btn)

        self.fields_table.setCellWidget(row, 6, options_widget)

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        btn_delete = QPushButton("Remove")
        btn_delete.clicked.connect(lambda: self.remove_field_row(row))
        actions_layout.addWidget(btn_delete)

        self.fields_table.setCellWidget(row, 7, actions_widget)

        # Update options visibility
        self.on_type_changed(row)

    def on_type_changed(self, row: int):
        """Handle field type change"""
        type_combo = self.fields_table.cellWidget(row, 2)
        field_type = type_combo.currentData()

        options_widget = self.fields_table.cellWidget(row, 6)

        # Show options only for dropdown, multiselect, reference, multireference
        needs_options = field_type in ['dropdown', 'multiselect', 'reference', 'multireference']
        options_widget.setVisible(needs_options)

    def edit_field_options(self, row: int):
        """Edit field options"""
        type_combo = self.fields_table.cellWidget(row, 2)
        field_type = type_combo.currentData()

        options_widget = self.fields_table.cellWidget(row, 6)
        options_input = options_widget.findChild(QLineEdit)

        if field_type in ['dropdown', 'multiselect']:
            dialog = OptionsDialog(options_input.text(), parent=self)
            if dialog.exec():
                options_input.setText(dialog.get_options())
        elif field_type in ['reference', 'multireference']:
            # Parse current options (might be old format: just table_id, or new format: JSON)
            current_table_id = None
            current_display_field = None
            if options_input.text():
                try:
                    import json
                    data = json.loads(options_input.text())
                    current_table_id = str(data.get('table_id', ''))
                    current_display_field = data.get('display_field')
                except:
                    # Old format - just table ID
                    current_table_id = options_input.text()

            dialog = ReferenceDialog(self.db, current_table_id, current_display_field, parent=self)
            if dialog.exec():
                # Store as JSON with both table_id and display_field
                import json
                ref_data = {
                    'table_id': dialog.get_table_id(),
                    'display_field': dialog.get_display_field()
                }
                options_input.setText(json.dumps(ref_data))

    def remove_field_row(self, row: int):
        """Remove a field row"""
        self.fields_table.removeRow(row)

    def load_table_data(self):
        """Load existing table data"""
        table = self.db.get_table(self.table_id)
        if table:
            self.table_name_input.setText(table['name'])
            self.display_name_input.setText(table['display_name'])

        fields = self.db.get_fields(self.table_id)
        for field in fields:
            self.add_field_row(field)

    def validate_input(self) -> bool:
        """Validate the form input"""
        if not self.table_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Table name is required")
            return False

        if not self.display_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Display name is required")
            return False

        # Validate table name format (alphanumeric and underscore only)
        table_name = self.table_name_input.text().strip()
        if not table_name.replace('_', '').isalnum():
            QMessageBox.warning(self, "Validation Error",
                              "Table name can only contain letters, numbers, and underscores")
            return False

        return True

    def save_table(self):
        """Save the table"""
        if not self.validate_input():
            return

        table_name = self.table_name_input.text().strip()
        display_name = self.display_name_input.text().strip()

        try:
            if self.is_edit_mode:
                # Update table metadata
                self.db.cursor.execute(
                    "UPDATE _tables SET display_name = ? WHERE id = ?",
                    (display_name, self.table_id)
                )

                # Get existing fields
                existing_fields = {f['name']: f for f in self.db.get_fields(self.table_id)}

                # Track current field names to identify removed fields
                current_field_names = set()

                # Process fields
                for row in range(self.fields_table.rowCount()):
                    field_name = self.fields_table.cellWidget(row, 0).text().strip()
                    if not field_name:
                        continue

                    current_field_names.add(field_name)

                    field_display = self.fields_table.cellWidget(row, 1).text().strip()
                    field_type = self.fields_table.cellWidget(row, 2).currentData()
                    is_required = self.fields_table.cellWidget(row, 3).isChecked()
                    is_unique = self.fields_table.cellWidget(row, 4).isChecked()
                    show_in_list = self.fields_table.cellWidget(row, 5).isChecked()

                    options_widget = self.fields_table.cellWidget(row, 6)
                    options_input = options_widget.findChild(QLineEdit)
                    options = options_input.text() if options_input.text() else None

                    reference_table_id = None
                    reference_display_field = None
                    if field_type in ['reference', 'multireference']:
                        if options:
                            try:
                                # Try to parse as JSON (new format)
                                import json
                                ref_data = json.loads(options)
                                reference_table_id = ref_data.get('table_id')
                                reference_display_field = ref_data.get('display_field')
                            except:
                                # Old format - just table ID
                                try:
                                    reference_table_id = int(options)
                                except Exception:
                                    reference_table_id = None
                            # Options are not stored for reference types
                            options = None
                        else:
                            # No options came back from UI (user didn't open the dialog). Preserve existing.
                            existing = existing_fields.get(field_name)
                            if existing:
                                reference_table_id = existing.get('reference_table_id')
                                reference_display_field = existing.get('reference_display_field')

                    # Check if field already exists
                    if field_name not in existing_fields:
                        # New field - add it
                        self.db.add_field(
                            self.table_id, field_name, field_display,
                            field_type, is_required, is_unique, show_in_list,
                            options, reference_table_id, reference_display_field, row
                        )
                    else:
                        # Update existing field metadata
                        field_id = existing_fields[field_name]['id']
                        self.db.cursor.execute("""
                            UPDATE _fields
                            SET display_name = ?, field_type = ?, is_required = ?, is_unique = ?,
                                show_in_list = ?, options = ?, reference_table_id = ?,
                                reference_display_field = ?, position = ?
                            WHERE id = ?
                        """, (field_display, field_type, is_required, is_unique, show_in_list,
                              options, reference_table_id, reference_display_field, row, field_id))
                        self.db.connection.commit()

                # Delete fields that were removed from the UI
                for field_name, field_data in existing_fields.items():
                    if field_name not in current_field_names:
                        self.db.delete_field(field_data['id'])

            else:
                # Create new table
                table_id = self.db.create_table(table_name, display_name)

                # Add fields
                for row in range(self.fields_table.rowCount()):
                    field_name = self.fields_table.cellWidget(row, 0).text().strip()
                    if not field_name:
                        continue

                    field_display = self.fields_table.cellWidget(row, 1).text().strip()
                    field_type = self.fields_table.cellWidget(row, 2).currentData()
                    is_required = self.fields_table.cellWidget(row, 3).isChecked()
                    is_unique = self.fields_table.cellWidget(row, 4).isChecked()
                    show_in_list = self.fields_table.cellWidget(row, 5).isChecked()

                    options_widget = self.fields_table.cellWidget(row, 6)
                    options_input = options_widget.findChild(QLineEdit)
                    options = options_input.text() if options_input.text() else None

                    reference_table_id = None
                    reference_display_field = None
                    if field_type in ['reference', 'multireference']:
                        if options:
                            try:
                                # Try to parse as JSON (new format)
                                import json
                                ref_data = json.loads(options)
                                reference_table_id = ref_data.get('table_id')
                                reference_display_field = ref_data.get('display_field')
                            except:
                                # Old format - just table ID
                                try:
                                    reference_table_id = int(options)
                                except Exception:
                                    reference_table_id = None
                            # Options are not stored for reference types
                            options = None

                    self.db.add_field(
                        table_id, field_name, field_display,
                        field_type, is_required, is_unique, show_in_list,
                        options, reference_table_id, reference_display_field, row
                    )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save table: {str(e)}")


class OptionsDialog(QDialog):
    """Dialog for editing dropdown/multiselect options"""

    def __init__(self, current_options: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Options")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        label = QLabel("Enter options (one per line):")
        layout.addWidget(label)

        self.text_edit = QTextEdit()
        if current_options:
            # Parse JSON array
            try:
                options = json.loads(current_options)
                self.text_edit.setText('\n'.join(options))
            except:
                self.text_edit.setText(current_options)
        layout.addWidget(self.text_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

    def get_options(self) -> str:
        """Get options as JSON array string"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            return ""

        options = [line.strip() for line in text.split('\n') if line.strip()]
        return json.dumps(options)


class ReferenceDialog(QDialog):
    """Dialog for selecting reference table and display field"""

    def __init__(self, db: DatabaseManager, current_table_id: str, current_display_field: str = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Select Reference Table")
        self.resize(350, 200)

        layout = QVBoxLayout(self)

        # Table selection
        label = QLabel("Select the table to reference:")
        layout.addWidget(label)

        self.table_combo = QComboBox()
        tables = self.db.get_all_tables()
        for table in tables:
            self.table_combo.addItem(table['display_name'], table['id'])

        if current_table_id:
            try:
                index = self.table_combo.findData(int(current_table_id))
                if index >= 0:
                    self.table_combo.setCurrentIndex(index)
            except:
                pass

        # Connect table selection change to update fields
        self.table_combo.currentIndexChanged.connect(self.on_table_changed)

        layout.addWidget(self.table_combo)

        # Display field selection
        field_label = QLabel("Select the field to display:")
        layout.addWidget(field_label)

        self.field_combo = QComboBox()
        layout.addWidget(self.field_combo)

        # Store current display field for later selection
        self.current_display_field = current_display_field

        # Populate fields for initially selected table
        self.on_table_changed()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

    def on_table_changed(self):
        """Update field dropdown when table selection changes"""
        self.field_combo.clear()

        table_id = self.table_combo.currentData()
        if table_id:
            fields = self.db.get_fields(table_id)
            for field in fields:
                # Only show text-like fields that make sense for display
                if field['field_type'] in ['text', 'email', 'phone', 'url', 'number']:
                    self.field_combo.addItem(field['display_name'], field['name'])

            # Try to select the current display field if it exists
            if self.current_display_field:
                index = self.field_combo.findData(self.current_display_field)
                if index >= 0:
                    self.field_combo.setCurrentIndex(index)

    def get_table_id(self) -> int:
        """Get selected table ID"""
        return self.table_combo.currentData()

    def get_display_field(self) -> str:
        """Get selected display field name"""
        return self.field_combo.currentData()
