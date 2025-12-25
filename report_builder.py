"""
Report builder for creating custom reports with field selection and grouping
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QGroupBox, QComboBox,
                             QCheckBox, QLineEdit, QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt
from database import DatabaseManager
from storage import StorageManager
import json


class ReportBuilderDialog(QDialog):
    """Dialog for building custom reports"""

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
        self.selected_fields = []
        self.group_by_field = None
        self.sort_by_field = None
        self.sort_order = 'ASC'
        self.report_title = ""
        self.include_totals = False

        self.setWindowTitle(f"Report Builder - {table_display_name}")
        self.resize(700, 600)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Report title
        title_group = QGroupBox("Report Title")
        title_layout = QVBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(f"{self.table_display_name} Report")
        self.title_input.setText(f"{self.table_display_name} Report")
        title_layout.addWidget(self.title_input)
        layout.addWidget(title_group)

        # Field selection
        fields_group = QGroupBox("Select Fields to Include")
        fields_layout = QVBoxLayout(fields_group)

        fields_info = QLabel("Select the fields you want to include in the report:")
        fields_layout.addWidget(fields_info)

        self.fields_list = QListWidget()
        self.fields_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        # Add all fields except ID
        for field in self.fields:
            if field['name'] != 'id':
                item_text = f"{field['display_name']} ({field['field_type']})"
                self.fields_list.addItem(item_text)
                # Select by default if show_in_list is True
                if field.get('show_in_list', True):
                    self.fields_list.item(self.fields_list.count() - 1).setSelected(True)

        fields_layout.addWidget(self.fields_list)

        # Quick select buttons
        select_btns = QHBoxLayout()
        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self.select_all_fields)
        select_btns.addWidget(btn_select_all)

        btn_select_none = QPushButton("Select None")
        btn_select_none.clicked.connect(self.select_no_fields)
        select_btns.addWidget(btn_select_none)

        fields_layout.addLayout(select_btns)
        layout.addWidget(fields_group)

        # Grouping and sorting options
        options_layout = QHBoxLayout()

        # Group by
        group_box = QGroupBox("Group By")
        group_layout = QVBoxLayout(group_box)
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("None", None)
        for field in self.fields:
            if field['field_type'] in ['text', 'dropdown', 'boolean', 'reference', 'date']:
                self.group_by_combo.addItem(field['display_name'], field['name'])
        group_layout.addWidget(self.group_by_combo)
        options_layout.addWidget(group_box)

        # Sort by
        sort_box = QGroupBox("Sort By")
        sort_layout = QVBoxLayout(sort_box)
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItem("ID", "id")
        for field in self.fields:
            if field['name'] != 'id':
                self.sort_by_combo.addItem(field['display_name'], field['name'])
        sort_layout.addWidget(self.sort_by_combo)

        # Sort order
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItem("Ascending", "ASC")
        self.sort_order_combo.addItem("Descending", "DESC")
        sort_layout.addWidget(self.sort_order_combo)
        options_layout.addWidget(sort_box)

        layout.addLayout(options_layout)

        # Additional options
        additional_group = QGroupBox("Additional Options")
        additional_layout = QVBoxLayout(additional_group)

        self.totals_checkbox = QCheckBox("Include record count totals")
        self.totals_checkbox.setChecked(True)
        additional_layout.addWidget(self.totals_checkbox)

        self.summary_checkbox = QCheckBox("Include summary statistics for number fields")
        additional_layout.addWidget(self.summary_checkbox)

        layout.addWidget(additional_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_preview = QPushButton("Generate Report")
        btn_preview.clicked.connect(self.generate_report)
        btn_preview.setDefault(True)
        btn_layout.addWidget(btn_preview)

        layout.addLayout(btn_layout)

    def select_all_fields(self):
        """Select all fields"""
        for i in range(self.fields_list.count()):
            self.fields_list.item(i).setSelected(True)

    def select_no_fields(self):
        """Deselect all fields"""
        self.fields_list.clearSelection()

    def generate_report(self):
        """Generate the report with selected options"""
        # Get selected fields
        selected_items = self.fields_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Fields Selected",
                              "Please select at least one field to include in the report.")
            return

        # Build list of selected field names
        self.selected_fields = []
        for item in selected_items:
            # Extract field name from item text (remove the type suffix)
            field_display = item.text().split(' (')[0]
            # Find the field by display name
            for field in self.fields:
                if field['display_name'] == field_display:
                    self.selected_fields.append(field['name'])
                    break

        # Get other options
        self.report_title = self.title_input.text().strip() or f"{self.table_display_name} Report"
        self.group_by_field = self.group_by_combo.currentData()
        self.sort_by_field = self.sort_by_combo.currentData()
        self.sort_order = self.sort_order_combo.currentData()
        self.include_totals = self.totals_checkbox.isChecked()
        self.include_summary = self.summary_checkbox.isChecked()

        self.accept()

    def get_report_config(self) -> dict:
        """Get the report configuration"""
        return {
            'title': self.report_title,
            'fields': self.selected_fields,
            'group_by': self.group_by_field,
            'sort_by': self.sort_by_field,
            'sort_order': self.sort_order,
            'include_totals': self.include_totals,
            'include_summary': self.include_summary
        }
