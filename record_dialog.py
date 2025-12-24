"""
Dialog for adding and editing records with dynamic form fields
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QLabel, QPushButton, QMessageBox,
                             QScrollArea, QWidget, QTextEdit, QCheckBox,
                             QComboBox, QDateEdit, QFileDialog, QListWidget,
                             QSpinBox, QDoubleSpinBox, QGroupBox, QListWidgetItem,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap, QImage
from database import DatabaseManager
from storage import StorageManager
from datetime import datetime
import json
import os


class RecordDialog(QDialog):
    def __init__(self, db: DatabaseManager, storage: StorageManager,
                 table_id: int, table_name: str, fields: list,
                 record_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.storage = storage
        self.table_id = table_id
        self.table_name = table_name
        self.fields = fields
        self.record_id = record_id
        self.is_edit_mode = record_id is not None
        self.field_widgets = {}

        self.setWindowTitle(f"Edit Record #{record_id}" if self.is_edit_mode else "New Record")
        self.resize(600, 700)

        self.init_ui()

        if self.is_edit_mode:
            self.load_record_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)

        # Form widget
        form_widget = QWidget()
        scroll.setWidget(form_widget)

        # Simple vertical layout with direct label and widget additions
        self.form_layout = QVBoxLayout(form_widget)
        self.form_layout.setSpacing(0)
        self.form_layout.setContentsMargins(15, 15, 15, 15)

        # Create form fields
        for field in self.fields:
            widget = self.create_field_widget(field)
            self.field_widgets[field['name']] = {
                'field': field,
                'widget': widget
            }

            label_text = field['display_name']
            if field['is_required']:
                label_text += " *"

            label = QLabel(label_text)
            label.setObjectName('FormFieldLabel')

            # Add label and widget directly to form
            self.form_layout.addWidget(label)
            self.form_layout.addWidget(widget)

            # Add spacing after each field group
            self.form_layout.addSpacing(12)

        # Add stretch at the end to push all fields to the top
        self.form_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        btn_layout.setContentsMargins(5, 5, 5, 5)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_record)
        btn_save.setDefault(True)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def get_record_display_name(self, record: dict, table_id: int, display_field_name: str = None) -> str:
        """Get a meaningful display name for a record"""
        # If a specific display field is specified, use that
        if display_field_name:
            value = record.get(display_field_name)
            if value:
                return str(value)

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

    def create_field_widget(self, field: dict) -> QWidget:
        """Create appropriate widget for field type"""
        field_type = field['field_type']

        if field_type == 'text':
            widget = QLineEdit()
            widget.setPlaceholderText(f"Enter {field['display_name'].lower()}")
            return widget

        elif field_type == 'number':
            widget = QDoubleSpinBox()
            widget.setRange(-999999999, 999999999)
            widget.setDecimals(2)
            return widget

        elif field_type == 'date':
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            widget.setDisplayFormat("yyyy-MM-dd")
            return widget

        elif field_type == 'boolean':
            widget = QCheckBox()
            return widget

        elif field_type == 'email':
            widget = QLineEdit()
            widget.setPlaceholderText("example@email.com")
            return widget

        elif field_type == 'url':
            widget = QLineEdit()
            widget.setPlaceholderText("https://example.com")
            return widget

        elif field_type == 'phone':
            widget = QLineEdit()
            widget.setPlaceholderText("+1234567890")
            return widget

        elif field_type == 'richtext':
            widget = QTextEdit()
            widget.setMinimumHeight(100)
            widget.setMaximumHeight(150)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            return widget

        elif field_type == 'dropdown':
            widget = QComboBox()
            widget.setEditable(False)
            widget.addItem("-- Select --", None)
            if field.get('options'):
                try:
                    options = json.loads(field['options'])
                    for option in options:
                        widget.addItem(option, option)
                except:
                    pass
            return widget

        elif field_type == 'multiselect':
            widget = QListWidget()
            widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            widget.setMaximumHeight(150)
            if field.get('options'):
                try:
                    options = json.loads(field['options'])
                    for option in options:
                        item = QListWidgetItem(option)
                        widget.addItem(item)
                except:
                    pass
            return widget

        elif field_type == 'image':
            return ImageFieldWidget(self.storage, self.table_name)

        elif field_type == 'file':
            return FileFieldWidget(self.storage, self.table_name)

        elif field_type == 'reference':
            widget = QComboBox()
            widget.addItem("-- Select --", None)

            # Load referenced table records
            if field.get('reference_table_id'):
                ref_table = self.db.get_table(field['reference_table_id'])
                if ref_table:
                    records = self.db.get_records(ref_table['name'], limit=1000)
                    display_field = field.get('reference_display_field')
                    for record in records:
                        display_name = self.get_record_display_name(record, field['reference_table_id'], display_field)
                        widget.addItem(display_name, record['id'])
            return widget

        elif field_type == 'multireference':
            widget = QListWidget()
            widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            widget.setMaximumHeight(150)

            # Load referenced table records
            if field.get('reference_table_id'):
                ref_table = self.db.get_table(field['reference_table_id'])
                if ref_table:
                    records = self.db.get_records(ref_table['name'], limit=1000)
                    display_field = field.get('reference_display_field')
                    for record in records:
                        display_name = self.get_record_display_name(record, field['reference_table_id'], display_field)
                        item = QListWidgetItem(display_name)
                        item.setData(Qt.ItemDataRole.UserRole, record['id'])
                        widget.addItem(item)
            return widget

        else:
            # Default to text input
            return QLineEdit()

    def load_record_data(self):
        """Load existing record data into form"""
        record = self.db.get_record(self.table_name, self.record_id)
        if not record:
            return

        for field_name, field_data in self.field_widgets.items():
            field = field_data['field']
            widget = field_data['widget']
            value = record.get(field_name)

            if value is None:
                continue

            field_type = field['field_type']

            if field_type == 'text' or field_type == 'email' or field_type == 'url' or field_type == 'phone':
                widget.setText(str(value))

            elif field_type == 'number':
                widget.setValue(float(value) if value else 0)

            elif field_type == 'date':
                try:
                    date = QDate.fromString(str(value), "yyyy-MM-dd")
                    widget.setDate(date)
                except:
                    pass

            elif field_type == 'boolean':
                widget.setChecked(bool(value))

            elif field_type == 'richtext':
                widget.setText(str(value))

            elif field_type == 'dropdown':
                index = widget.findData(value)
                if index >= 0:
                    widget.setCurrentIndex(index)

            elif field_type == 'multiselect':
                try:
                    selected = json.loads(value) if isinstance(value, str) else value
                    if selected:
                        for i in range(widget.count()):
                            item = widget.item(i)
                            if item.text() in selected:
                                item.setSelected(True)
                except:
                    pass

            elif field_type == 'image' or field_type == 'file':
                widget.set_file(value, self.record_id)

            elif field_type == 'reference':
                index = widget.findData(value)
                if index >= 0:
                    widget.setCurrentIndex(index)

            elif field_type == 'multireference':
                try:
                    selected_ids = json.loads(value) if isinstance(value, str) else value
                    if selected_ids:
                        for i in range(widget.count()):
                            item = widget.item(i)
                            item_id = item.data(Qt.ItemDataRole.UserRole)
                            if item_id in selected_ids:
                                item.setSelected(True)
                except:
                    pass

    def validate_record(self) -> bool:
        """Validate the form data"""
        for field_name, field_data in self.field_widgets.items():
            field = field_data['field']
            widget = field_data['widget']

            if field['is_required']:
                field_type = field['field_type']
                value = self.get_field_value(field, widget)

                if value is None or value == '' or value == []:
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        f"{field['display_name']} is required"
                    )
                    return False

        return True

    def get_field_value(self, field: dict, widget: QWidget):
        """Extract value from widget based on field type"""
        field_type = field['field_type']

        if field_type in ['text', 'email', 'url', 'phone']:
            return widget.text().strip()

        elif field_type == 'number':
            return widget.value()

        elif field_type == 'date':
            return widget.date().toString("yyyy-MM-dd")

        elif field_type == 'boolean':
            return widget.isChecked()

        elif field_type == 'richtext':
            return widget.toPlainText().strip()

        elif field_type == 'dropdown':
            return widget.currentData()

        elif field_type == 'multiselect':
            selected = []
            for item in widget.selectedItems():
                selected.append(item.text())
            return json.dumps(selected) if selected else None

        elif field_type == 'image' or field_type == 'file':
            return widget.get_value()

        elif field_type == 'reference':
            return widget.currentData()

        elif field_type == 'multireference':
            selected = []
            for item in widget.selectedItems():
                selected.append(item.data(Qt.ItemDataRole.UserRole))
            return json.dumps(selected) if selected else None

        return None

    def save_record(self):
        """Save the record"""
        if not self.validate_record():
            return

        try:
            # Collect data
            data = {}
            for field_name, field_data in self.field_widgets.items():
                field = field_data['field']
                widget = field_data['widget']
                value = self.get_field_value(field, widget)

                if value is not None:
                    data[field_name] = value

            if self.is_edit_mode:
                # Update existing record
                self.db.update_record(self.table_name, self.record_id, data)

                # Handle file uploads and update DB with new paths (if any)
                updated_paths = {}
                for field_name, field_data in self.field_widgets.items():
                    field = field_data['field']
                    widget = field_data['widget']

                    if field['field_type'] in ['image', 'file']:
                        # Save and compare against the value we just sent to DB
                        previous_value = data.get(field_name)
                        saved_path = widget.save_file(self.record_id, field_name)
                        if saved_path and saved_path != previous_value:
                            updated_paths[field_name] = saved_path

                if updated_paths:
                    self.db.update_record(self.table_name, self.record_id, updated_paths)

            else:
                # Insert new record
                record_id = self.db.insert_record(self.table_name, data)

                # Handle file uploads
                for field_name, field_data in self.field_widgets.items():
                    field = field_data['field']
                    widget = field_data['widget']

                    if field['field_type'] in ['image', 'file']:
                        file_path = widget.save_file(record_id, field_name)
                        if file_path:
                            # Update record with file path
                            self.db.update_record(self.table_name, record_id, {field_name: file_path})

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save record: {str(e)}")


class ImageFieldWidget(QWidget):
    """Widget for image upload with preview"""

    def __init__(self, storage: StorageManager, table_name: str, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.table_name = table_name
        self.file_path = None
        self.current_value = None
        self.record_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(200, 200)
        self.preview_label.setScaledContents(True)
        self.preview_label.setObjectName('ImagePreview')
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setText("No image")
        layout.addWidget(self.preview_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_upload = QPushButton("Upload Image")
        self.btn_upload.clicked.connect(self.upload_image)
        btn_layout.addWidget(self.btn_upload)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_image)
        btn_layout.addWidget(self.btn_clear)

        layout.addLayout(btn_layout)

    def upload_image(self):
        """Upload an image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )

        if file_path:
            self.file_path = file_path
            self.show_preview(file_path)

    def show_preview(self, file_path: str):
        """Show image preview"""
        print(f"[show_preview] Attempting to load image from: {file_path}")
        print(f"[show_preview] File exists: {os.path.exists(file_path)}")

        if os.path.exists(file_path):
            # Check file permissions
            import stat
            st = os.stat(file_path)
            print(f"[show_preview] File permissions: {oct(st.st_mode)}")
            print(f"[show_preview] File size: {st.st_size} bytes")

        pixmap = QPixmap(file_path)
        print(f"[show_preview] QPixmap loaded, isNull: {pixmap.isNull()}")

        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            print(f"[show_preview] Image displayed successfully")
        else:
            print(f"[show_preview] ERROR: QPixmap is null, cannot display image")

    def clear_image(self):
        """Clear the image"""
        self.file_path = None
        self.current_value = None
        self.preview_label.clear()
        self.preview_label.setText("No image")

    def set_file(self, value: str, record_id: int):
        """Set existing file"""
        self.current_value = value
        self.record_id = record_id

        if value:
            # Support both relative storage paths and absolute paths
            abs_path = value if os.path.isabs(value) else self.storage.get_file_path(value)
            if os.path.exists(abs_path):
                self.show_preview(abs_path)
            else:
                # Debug: File not found
                self.preview_label.clear()
                self.preview_label.setText("Image not found")
                print(f"Image file not found: {abs_path}")
                print(f"Looking for relative path: {value}")
                print(f"Storage base dir: {self.storage.base_dir}")

    def save_file(self, record_id: int, field_name: str) -> str:
        """Save the file and return relative path"""
        if self.file_path:
            saved_path = self.storage.save_file(self.table_name, record_id, field_name, self.file_path)
            print(f"[ImageFieldWidget] Saved image to: {saved_path}")
            print(f"[ImageFieldWidget] Storage base dir: {self.storage.base_dir}")
            # Update current_value so subsequent reads reflect new path
            self.current_value = saved_path
            return saved_path
        return self.current_value

    def get_value(self) -> str:
        """Get the current value"""
        return self.current_value


class FileFieldWidget(QWidget):
    """Widget for file upload"""

    def __init__(self, storage: StorageManager, table_name: str, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.table_name = table_name
        self.file_path = None
        self.current_value = None
        self.record_id = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.file_label = QLabel("No file selected")
        layout.addWidget(self.file_label)

        self.btn_upload = QPushButton("Upload File")
        self.btn_upload.clicked.connect(self.upload_file)
        layout.addWidget(self.btn_upload)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_file)
        layout.addWidget(self.btn_clear)

    def upload_file(self):
        """Upload a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )

        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))

    def clear_file(self):
        """Clear the file"""
        self.file_path = None
        self.current_value = None
        self.file_label.setText("No file selected")

    def set_file(self, value: str, record_id: int):
        """Set existing file"""
        self.current_value = value
        self.record_id = record_id

        if value:
            filename = value.split('/')[-1]
            self.file_label.setText(filename)

    def save_file(self, record_id: int, field_name: str) -> str:
        """Save the file and return relative path"""
        if self.file_path:
            return self.storage.save_file(self.table_name, record_id, field_name, self.file_path)
        return self.current_value

    def get_value(self) -> str:
        """Get the current value"""
        return self.current_value
