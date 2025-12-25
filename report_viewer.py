"""
Report viewer for displaying and printing custom reports
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, QUrl, QMarginsF
from PyQt6.QtGui import QFont, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from database import DatabaseManager
from storage import StorageManager
from datetime import datetime
import json


class ReportViewerDialog(QDialog):
    """Dialog for viewing and printing reports"""

    def __init__(self, db: DatabaseManager, storage: StorageManager,
                 table_id: int, table_name: str, table_display_name: str,
                 fields: list, config: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.storage = storage
        self.table_id = table_id
        self.table_name = table_name
        self.table_display_name = table_display_name
        self.fields = fields
        self.config = config

        self.setWindowTitle(f"Report: {config['title']}")
        self.resize(900, 700)

        self.init_ui()
        self.generate_report()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Report preview
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        font = QFont("Monospace", 10)
        self.report_text.setFont(font)
        layout.addWidget(self.report_text)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_print = QPushButton("Print")
        btn_print.clicked.connect(self.print_report)
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

    def get_field_by_name(self, field_name: str) -> dict:
        """Get field metadata by name"""
        for field in self.fields:
            if field['name'] == field_name:
                return field
        return None

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

        elif field_type == 'reference':
            if value:
                ref_table_id = field.get('reference_table_id')
                if ref_table_id:
                    ref_table = self.db.get_table(ref_table_id)
                    if ref_table:
                        ref_record = self.db.get_record(ref_table['name'], value)
                        if ref_record:
                            display_field = field.get('reference_display_field')
                            if display_field and ref_record.get(display_field):
                                return str(ref_record[display_field])
                            # Fallback to first text field
                            ref_fields = self.db.get_fields(ref_table_id)
                            for rf in ref_fields:
                                if rf['field_type'] in ['text', 'email', 'url', 'phone'] and rf['name'] != 'id':
                                    val = ref_record.get(rf['name'])
                                    if val:
                                        return str(val)
                return f"ID: {value}"
            return ''

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
                                    if display_field and ref_record.get(display_field):
                                        labels.append(str(ref_record[display_field]))
                                    else:
                                        labels.append(f"ID: {rid}")
                            return ', '.join(labels)
                return ''
            except:
                return str(value)

        elif field_type in ['image', 'file']:
            return f"[{field_type.title()}]" if value else ''

        else:
            return str(value)

    def generate_report(self):
        """Generate the report HTML"""
        # Get all records with sorting
        sort_by = self.config.get('sort_by', 'id')
        sort_order = self.config.get('sort_order', 'ASC')
        records = self.db.get_records(self.table_name,
                                      order_by=sort_by,
                                      order_dir=sort_order,
                                      limit=999999)

        # Build selected fields metadata
        selected_fields = []
        for field_name in self.config['fields']:
            field = self.get_field_by_name(field_name)
            if field:
                selected_fields.append(field)

        # Start HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'DejaVu Sans', Arial, sans-serif; padding: 16px; color: #222; font-size: 11pt; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #222; border-bottom: 3px solid #444; padding-bottom: 10px; margin-bottom: 10px; font-size: 22pt; }}
                .report-meta {{ margin-bottom: 20px; color: #666; font-size: 10pt; }}
                .section-title {{ font-size: 14pt; font-weight: bold; color: #333; margin: 20px 0 10px 0; padding: 5px 0; border-bottom: 2px solid #888; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; page-break-inside: auto; }}
                th {{ background: #f5f5f5; padding: 8px; text-align: left; border: 1px solid #ddd; font-weight: bold; font-size: 10pt; }}
                td {{ padding: 6px 8px; border: 1px solid #e0e0e0; font-size: 10pt; }}
                tr {{ page-break-inside: avoid; page-break-after: auto; }}
                tr:nth-child(even) {{ background: #fafafa; }}
                .summary {{ background: #f0f0f0; padding: 10px; margin: 15px 0; border-left: 4px solid #666; }}
                .summary-title {{ font-weight: bold; margin-bottom: 5px; }}
                .group-header {{ background: #e8e8e8; font-weight: bold; padding: 8px; margin-top: 15px; border-left: 5px solid #555; }}
                @media print {{
                    body {{ padding: 0; font-size: 10pt; }}
                    .no-print {{ display: none; }}
                    h1 {{ font-size: 20pt; }}
                    th, td {{ font-size: 9pt; padding: 4px 6px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self.config['title']}</h1>
                <div class="report-meta">
                    Table: {self.table_display_name}<br>
                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    Total Records: {len(records)}
                </div>
        """

        # Group by field if specified
        group_by_field = self.config.get('group_by')
        if group_by_field:
            # Group records
            groups = {}
            group_field = self.get_field_by_name(group_by_field)

            for record in records:
                group_value = record.get(group_by_field)
                group_display = self.format_field_value(group_field, group_value) or '(Empty)'

                if group_display not in groups:
                    groups[group_display] = []
                groups[group_display].append(record)

            # Generate grouped output
            for group_name, group_records in groups.items():
                html += f"""
                <div class="group-header">
                    {group_field['display_name']}: {group_name} ({len(group_records)} record{'s' if len(group_records) != 1 else ''})
                </div>
                """
                html += self.generate_table(selected_fields, group_records)

        else:
            # No grouping - single table
            html += self.generate_table(selected_fields, records)

        # Summary statistics
        if self.config.get('include_summary'):
            html += self.generate_summary(selected_fields, records)

        # Total count
        if self.config.get('include_totals'):
            html += f"""
            <div class="summary">
                <div class="summary-title">Report Summary</div>
                Total Records: {len(records)}
            </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        self.report_text.setHtml(html)

    def generate_table(self, fields: list, records: list) -> str:
        """Generate HTML table for records"""
        if not records:
            return "<p><em>No records to display</em></p>"

        html = "<table>"

        # Table header
        html += "<thead><tr>"
        html += "<th>#</th>"  # Row number
        for field in fields:
            html += f"<th>{field['display_name']}</th>"
        html += "</tr></thead>"

        # Table body
        html += "<tbody>"
        for idx, record in enumerate(records, 1):
            html += "<tr>"
            html += f"<td>{idx}</td>"
            for field in fields:
                value = record.get(field['name'])
                display_value = self.format_field_value(field, value)
                html += f"<td>{display_value}</td>"
            html += "</tr>"
        html += "</tbody>"

        html += "</table>"
        return html

    def generate_summary(self, fields: list, records: list) -> str:
        """Generate summary statistics for number fields"""
        number_fields = [f for f in fields if f['field_type'] == 'number']

        if not number_fields or not records:
            return ""

        html = """
        <div class="section-title">Summary Statistics</div>
        <div class="summary">
        """

        for field in number_fields:
            values = []
            for record in records:
                val = record.get(field['name'])
                if val is not None and val != '':
                    try:
                        values.append(float(val))
                    except:
                        pass

            if values:
                total = sum(values)
                avg = total / len(values)
                min_val = min(values)
                max_val = max(values)

                html += f"""
                <div style="margin-bottom: 10px;">
                    <strong>{field['display_name']}:</strong><br>
                    &nbsp;&nbsp;Sum: {total:,.2f}<br>
                    &nbsp;&nbsp;Average: {avg:,.2f}<br>
                    &nbsp;&nbsp;Min: {min_val:,.2f}<br>
                    &nbsp;&nbsp;Max: {max_val:,.2f}<br>
                    &nbsp;&nbsp;Count: {len(values)}
                </div>
                """

        html += "</div>"
        return html

    def print_report(self):
        """Print the report"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        try:
            printer.setResolution(300)
            layout = printer.pageLayout()
            layout.setOrientation(QPageLayout.Orientation.Portrait)
            layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            layout.setMargins(QMarginsF(15, 15, 15, 15))
            printer.setPageLayout(layout)
        except Exception:
            pass

        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.report_text.document().print(printer)

    def export_pdf(self):
        """Export report to PDF"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            f"{self.table_name}_report.pdf",
            "PDF Files (*.pdf)"
        )

        if file_path:
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            try:
                printer.setResolution(300)
                layout = printer.pageLayout()
                layout.setOrientation(QPageLayout.Orientation.Portrait)
                layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                layout.setMargins(QMarginsF(15, 15, 15, 15))
                printer.setPageLayout(layout)
            except Exception:
                pass

            self.report_text.document().print(printer)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Report exported to:\n{file_path}"
            )
