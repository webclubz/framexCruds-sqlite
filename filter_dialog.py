"""
Advanced filter dialog for filtering records by multiple criteria
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QLabel, QPushButton, QComboBox,
                             QDateEdit, QDoubleSpinBox, QScrollArea, QWidget,
                             QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
import json


class FilterDialog(QDialog):
    def __init__(self, fields: list, parent=None):
        super().__init__(parent)
        self.fields = fields
        self.filters = {}
        self.filter_widgets = {}

        self.setWindowTitle("Advanced Filters")
        self.resize(500, 600)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Instructions
        info_label = QLabel("Set filters for one or more fields. Leave empty to ignore.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Scroll area for filters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)

        # Filter widget
        filter_widget = QWidget()
        scroll.setWidget(filter_widget)

        self.filter_layout = QVBoxLayout(filter_widget)
        self.filter_layout.setSpacing(15)
        self.filter_layout.setContentsMargins(10, 10, 10, 10)

        # Create filter widgets for each field
        for field in self.fields:
            filter_group = self.create_filter_widget(field)
            if filter_group:
                self.filter_layout.addWidget(filter_group)

        # Add stretch at the end
        self.filter_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self.clear_filters)
        btn_layout.addWidget(btn_clear)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_apply = QPushButton("Apply Filters")
        btn_apply.clicked.connect(self.apply_filters)
        btn_apply.setDefault(True)
        btn_layout.addWidget(btn_apply)

        layout.addLayout(btn_layout)

    def create_filter_widget(self, field: dict) -> QWidget:
        """Create appropriate filter widget for field type"""
        field_type = field['field_type']
        field_name = field['name']

        # Skip ID field
        if field_name == 'id':
            return None

        # Create group box for this field
        group = QGroupBox(field['display_name'])
        layout = QVBoxLayout(group)
        layout.setSpacing(5)

        if field_type in ['text', 'email', 'url', 'phone', 'richtext']:
            # Text filter: contains
            widget = QLineEdit()
            widget.setPlaceholderText("Contains text...")
            layout.addWidget(widget)
            self.filter_widgets[field_name] = {'type': 'text', 'widget': widget}

        elif field_type == 'number':
            # Number filter: min and max
            min_layout = QHBoxLayout()
            min_layout.addWidget(QLabel("Min:"))
            min_widget = QDoubleSpinBox()
            min_widget.setRange(-999999999, 999999999)
            min_widget.setSpecialValueText("No minimum")
            min_widget.setValue(-999999999)
            min_layout.addWidget(min_widget)
            layout.addLayout(min_layout)

            max_layout = QHBoxLayout()
            max_layout.addWidget(QLabel("Max:"))
            max_widget = QDoubleSpinBox()
            max_widget.setRange(-999999999, 999999999)
            max_widget.setSpecialValueText("No maximum")
            max_widget.setValue(999999999)
            max_layout.addWidget(max_widget)
            layout.addLayout(max_layout)

            self.filter_widgets[field_name] = {
                'type': 'number_range',
                'min': min_widget,
                'max': max_widget
            }

        elif field_type == 'date':
            # Date filter: from and to
            from_layout = QHBoxLayout()
            from_layout.addWidget(QLabel("From:"))
            from_widget = QDateEdit()
            from_widget.setCalendarPopup(True)
            from_widget.setDisplayFormat("yyyy-MM-dd")
            from_widget.setDate(QDate(2000, 1, 1))
            from_check = QCheckBox("Enable")
            from_layout.addWidget(from_widget)
            from_layout.addWidget(from_check)
            layout.addLayout(from_layout)

            to_layout = QHBoxLayout()
            to_layout.addWidget(QLabel("To:"))
            to_widget = QDateEdit()
            to_widget.setCalendarPopup(True)
            to_widget.setDisplayFormat("yyyy-MM-dd")
            to_widget.setDate(QDate.currentDate())
            to_check = QCheckBox("Enable")
            to_layout.addWidget(to_widget)
            to_layout.addWidget(to_check)
            layout.addLayout(to_layout)

            self.filter_widgets[field_name] = {
                'type': 'date_range',
                'from': from_widget,
                'from_check': from_check,
                'to': to_widget,
                'to_check': to_check
            }

        elif field_type == 'boolean':
            # Boolean filter: Any/True/False
            widget = QComboBox()
            widget.addItem("Any", None)
            widget.addItem("Yes", True)
            widget.addItem("No", False)
            layout.addWidget(widget)
            self.filter_widgets[field_name] = {'type': 'boolean', 'widget': widget}

        elif field_type == 'dropdown':
            # Dropdown filter: show all options
            widget = QComboBox()
            widget.addItem("Any", None)
            if field.get('options'):
                try:
                    options = json.loads(field['options'])
                    for option in options:
                        widget.addItem(option, option)
                except:
                    pass
            layout.addWidget(widget)
            self.filter_widgets[field_name] = {'type': 'dropdown', 'widget': widget}

        elif field_type == 'reference':
            # For reference fields, allow text search of the display value
            widget = QLineEdit()
            widget.setPlaceholderText("Search referenced value...")
            layout.addWidget(widget)
            self.filter_widgets[field_name] = {
                'type': 'reference',
                'widget': widget,
                'field': field  # Store field metadata for reference table info
            }

        else:
            # For other types, use text filter
            widget = QLineEdit()
            widget.setPlaceholderText("Contains text...")
            layout.addWidget(widget)
            self.filter_widgets[field_name] = {'type': 'text', 'widget': widget}

        return group

    def clear_filters(self):
        """Clear all filter inputs"""
        for field_name, filter_data in self.filter_widgets.items():
            filter_type = filter_data['type']

            if filter_type == 'text':
                filter_data['widget'].clear()
            elif filter_type == 'number_range':
                filter_data['min'].setValue(-999999999)
                filter_data['max'].setValue(999999999)
            elif filter_type == 'date_range':
                filter_data['from_check'].setChecked(False)
                filter_data['to_check'].setChecked(False)
            elif filter_type in ['boolean', 'dropdown']:
                filter_data['widget'].setCurrentIndex(0)
            elif filter_type == 'reference':
                filter_data['widget'].clear()

    def apply_filters(self):
        """Collect filter values and close dialog"""
        self.filters = {}

        for field_name, filter_data in self.filter_widgets.items():
            filter_type = filter_data['type']

            if filter_type == 'text':
                value = filter_data['widget'].text().strip()
                if value:
                    self.filters[field_name] = {'type': 'text', 'value': value}

            elif filter_type == 'number_range':
                min_val = filter_data['min'].value()
                max_val = filter_data['max'].value()
                if min_val > -999999999 or max_val < 999999999:
                    self.filters[field_name] = {
                        'type': 'number_range',
                        'min': min_val if min_val > -999999999 else None,
                        'max': max_val if max_val < 999999999 else None
                    }

            elif filter_type == 'date_range':
                from_enabled = filter_data['from_check'].isChecked()
                to_enabled = filter_data['to_check'].isChecked()
                if from_enabled or to_enabled:
                    self.filters[field_name] = {
                        'type': 'date_range',
                        'from': filter_data['from'].date().toString("yyyy-MM-dd") if from_enabled else None,
                        'to': filter_data['to'].date().toString("yyyy-MM-dd") if to_enabled else None
                    }

            elif filter_type == 'boolean':
                value = filter_data['widget'].currentData()
                if value is not None:
                    self.filters[field_name] = {'type': 'boolean', 'value': value}

            elif filter_type == 'dropdown':
                value = filter_data['widget'].currentData()
                if value is not None:
                    self.filters[field_name] = {'type': 'dropdown', 'value': value}

            elif filter_type == 'reference':
                value = filter_data['widget'].text().strip()
                if value:
                    # Pass the search text and field metadata
                    self.filters[field_name] = {
                        'type': 'reference',
                        'value': value,
                        'field': filter_data.get('field')
                    }

        self.accept()

    def get_filters(self) -> dict:
        """Get the collected filters"""
        return self.filters
