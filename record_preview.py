"""
Record preview dialog with print functionality
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QUrl, QMarginsF
from PyQt6.QtGui import QTextDocument, QFont, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from database import DatabaseManager
from storage import StorageManager
import json
import os


class RecordPreviewDialog(QDialog):
    """Dialog for previewing and printing a record"""

    def __init__(self, db: DatabaseManager, storage: StorageManager,
                 table_id: int, table_name: str, table_display_name: str,
                 fields: list, record_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.storage = storage
        self.table_id = table_id
        self.table_name = table_name
        self.table_display_name = table_display_name
        self.fields = fields
        self.record_id = record_id

        self.setWindowTitle(f"Preview: {table_display_name} - Record #{record_id}")
        self.resize(700, 600)

        self.init_ui()
        # Ensure local resources resolve consistently (print/PDF too)
        try:
            base = QUrl.fromLocalFile(os.path.abspath(self.storage.base_dir))
            self.preview_text.document().setBaseUrl(base)
        except Exception:
            pass

        self.load_record_preview()

    def get_reference_display_name(self, record: dict, table_id: int, display_field_name: str = None) -> str:
        """Return a human-friendly name for a referenced record.
        Tries the configured display field, then common text-like fields, then any non-id value, else ID.
        """
        # If a specific display field is specified, use that
        if display_field_name:
            value = record.get(display_field_name)
            if value:
                return str(value)

        # Get fields for the referenced table
        ref_fields = self.db.get_fields(table_id)

        # Try to find a good display field (text, email, phone, url)
        for ref_field in ref_fields:
            field_type = ref_field['field_type']
            field_name = ref_field['name']
            if field_name == 'id':
                continue
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

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        font = QFont("Monospace", 10)
        self.preview_text.setFont(font)
        layout.addWidget(self.preview_text)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_print = QPushButton("Print")
        btn_print.clicked.connect(self.print_record)
        btn_layout.addWidget(btn_print)

        btn_export_pdf = QPushButton("Export PDF")
        btn_export_pdf.clicked.connect(self.export_pdf)
        btn_layout.addWidget(btn_export_pdf)

        btn_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_close.setDefault(True)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def load_record_preview(self):
        """Load and format the record for preview"""
        record = self.db.get_record(self.table_name, self.record_id)
        if not record:
            self.preview_text.setPlainText("Record not found.")
            return

        # Build HTML preview
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'DejaVu Sans', Arial, sans-serif; padding: 12px 16px; color: #222; }}
                .container {{ max-width: 900px; margin: 0 auto; }}
                h1 {{ color: #222; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 14px; font-size: 20pt; }}
                .record-info {{ margin-bottom: 18px; color: #555; font-size: 10pt; }}
                .field {{ margin-bottom: 12px; page-break-inside: avoid; border: 1px solid #e0e0e0; border-radius: 4px; padding: 8px 10px; background: #fafafa; }}
                .field-label {{ font-weight: bold; color: #333; margin-bottom: 4px; }}
                .field-value {{ color: #111; padding: 6px 8px; background-color: #fff; border-left: 3px solid #777; margin-top: 4px; }}
                .image-block {{ text-align: center; margin: 6px 0 4px 0; }}
                .image-block img {{ max-width: 600px; width: 100%; height: auto; border: 1px solid #ccc; }}
                .image-info {{ color: #666; font-style: italic; font-size: 9pt; margin-top: 4px; }}
                @media print {{ body {{ padding: 0; }} .field {{ background: #fff; }} .image-block img {{ max-width: 700px; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self.table_display_name}</h1>
                <div class="record-info">
                    Record ID: {record['id']}<br>
                    Created: {record.get('created_at', 'N/A')}<br>
                    Updated: {record.get('updated_at', 'N/A')}
                </div>
        """

        # Add fields
        for field in self.fields:
            field_name = field['name']
            field_display = field['display_name']
            field_type = field['field_type']
            value = record.get(field_name)

            if value is None or value == '':
                value_display = '<em>(empty)</em>'
            else:
                value_display = self.format_field_value(field, value)

            html += f"""
            <div class="field">
                <div class="field-label">{field_display}:</div>
                <div class="field-value">{value_display}</div>
            </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        self.preview_text.setHtml(html)

    def format_field_value(self, field: dict, value) -> str:
        """Format field value for HTML display"""
        field_type = field['field_type']

        if field_type == 'boolean':
            return 'Yes' if value else 'No'

        elif field_type == 'multiselect':
            try:
                items = json.loads(value) if isinstance(value, str) else value
                if items:
                    return '<br>'.join([f"• {item}" for item in items])
                return '<em>(none selected)</em>'
            except:
                return str(value)

        elif field_type == 'image':
            if value:
                abs_path = self.storage.get_file_path(value)
                filename = os.path.basename(abs_path)
                if os.path.exists(abs_path):
                    # Display the image inline with a max width for readability
                    safe_src = QUrl.fromLocalFile(abs_path).toString()
                    return (
                        f'<div class="image-block">'
                        f'<img src="{safe_src}" alt="{filename}" />'
                        f'<div class="image-info">📷 {filename}</div>'
                        f'</div>'
                    )
                return f'<span class="image-info">📷 {filename} (file not found)</span>'
            return '<em>(no image)</em>'

        elif field_type == 'file':
            if value:
                abs_path = self.storage.get_file_path(value)
                filename = os.path.basename(abs_path)
                if os.path.exists(abs_path):
                    return f'<span class="image-info">📎 {filename}</span>'
                return f'<span class="image-info">📎 {filename} (file not found)</span>'
            return '<em>(no file)</em>'

        elif field_type == 'reference':
            if value:
                # Get referenced table and record to show a friendly label
                ref_table_id = field.get('reference_table_id')
                if ref_table_id:
                    ref_table = self.db.get_table(ref_table_id)
                    if ref_table:
                        ref_record = self.db.get_record(ref_table['name'], value)
                        if ref_record:
                            display_field = field.get('reference_display_field')
                            display_name = self.get_reference_display_name(ref_record, ref_table_id, display_field)
                            return f"→ {ref_table['display_name']}: {display_name}"
                        return f"→ {ref_table['display_name']} (ID: {value})"
                return f"→ Record ID: {value}"
            return '<em>(no reference)</em>'

        elif field_type == 'multireference':
            try:
                ids = json.loads(value) if isinstance(value, str) else value
                if ids:
                    ref_table_id = field.get('reference_table_id')
                    if ref_table_id:
                        ref_table = self.db.get_table(ref_table_id)
                        if ref_table:
                            labels = []
                            for rid in ids:
                                ref_record = self.db.get_record(ref_table['name'], rid)
                                if ref_record:
                                    display_field = field.get('reference_display_field')
                                    labels.append(self.get_reference_display_name(ref_record, ref_table_id, display_field))
                                else:
                                    labels.append(f"ID: {rid}")
                            return '<br>'.join([f"• {lbl}" for lbl in labels])
                    # Fallback: just show IDs
                    return '<br>'.join([f"• ID: {rid}" for rid in ids])
                return '<em>(no references)</em>'
            except:
                return str(value)

        elif field_type == 'richtext':
            # Preserve line breaks
            return str(value).replace('\n', '<br>')

        else:
            # Escape HTML and preserve formatting
            return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')

    def print_record(self):
        """Print the record"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        try:
            # High quality, A4 portrait with comfortable margins
            printer.setResolution(300)
            layout = printer.pageLayout()
            layout.setOrientation(QPageLayout.Orientation.Portrait)
            layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            layout.setMargins(QMarginsF(12, 12, 12, 12))  # millimeters by default
            printer.setPageLayout(layout)
        except Exception:
            pass
        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.preview_text.document().print(printer)

    def export_pdf(self):
        """Export record to PDF"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            f"{self.table_name}_record_{self.record_id}.pdf",
            "PDF Files (*.pdf)"
        )

        if file_path:
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            try:
                # High quality, A4 portrait with comfortable margins
                printer.setResolution(300)
                layout = printer.pageLayout()
                layout.setOrientation(QPageLayout.Orientation.Portrait)
                layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                layout.setMargins(QMarginsF(12, 12, 12, 12))
                printer.setPageLayout(layout)
            except Exception:
                pass

            self.preview_text.document().print(printer)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Record exported to:\n{file_path}"
            )
