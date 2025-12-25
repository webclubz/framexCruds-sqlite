"""
Main window with sidebar navigation
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QStackedWidget, QLabel,
                             QMessageBox, QListWidgetItem, QSplitter, QFileDialog,
                             QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
import os
import config
from config import ConfigManager
from database import DatabaseManager
from storage import StorageManager
from export_import import DataExporter, DataImporter
from backup import BackupManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.current_db_path = None
        self.db = None
        self.storage = None
        self.exporter = None
        self.importer = None
        self.backup_manager = None
        self.current_table_id = None

        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        self.init_ui()

        # Load last database or show welcome
        last_db = self.config_manager.get_last_database()
        if last_db:
            self.open_database(last_db)
        else:
            # Try default database
            if os.path.exists(config.DB_FILE):
                self.open_database(config.DB_FILE)
            else:
                self.update_window_title()

    def init_ui(self):
        """Initialize the user interface"""
        # Create menu bar
        self.create_menu_bar()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for resizable sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left sidebar
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)

        # Right content area
        self.content_stack = QStackedWidget()
        splitter.addWidget(self.content_stack)

        # Set initial splitter sizes
        splitter.setSizes([config.SIDEBAR_WIDTH, config.WINDOW_WIDTH - config.SIDEBAR_WIDTH])

        # Welcome screen (shown when no table is selected)
        welcome = QWidget()
        welcome_layout = QVBoxLayout(welcome)
        welcome_label = QLabel("Select a table from the sidebar or create a new one")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        self.content_stack.addWidget(welcome)

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Database submenu
        new_db_action = QAction("New Database...", self)
        new_db_action.setShortcut("Ctrl+Shift+N")
        new_db_action.triggered.connect(self.new_database)
        file_menu.addAction(new_db_action)

        open_db_action = QAction("Open Database...", self)
        open_db_action.setShortcut("Ctrl+O")
        open_db_action.triggered.connect(self.open_database_dialog)
        file_menu.addAction(open_db_action)

        # Recent databases submenu
        self.recent_menu = file_menu.addMenu("Recent Databases")
        self.update_recent_menu()

        file_menu.addSeparator()

        new_table_action = QAction("New Table", self)
        new_table_action.setShortcut("Ctrl+N")
        new_table_action.triggered.connect(self.create_new_table)
        file_menu.addAction(new_table_action)

        file_menu.addSeparator()

        import_action = QAction("Import Data from CSV...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_csv_data)
        file_menu.addAction(import_action)

        export_template_action = QAction("Export Import Template...", self)
        export_template_action.setShortcut("Ctrl+Shift+T")
        export_template_action.triggered.connect(self.export_import_template)
        file_menu.addAction(export_template_action)

        file_menu.addSeparator()

        export_action = QAction("Export Database", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        import_db_action = QAction("Import Database", self)
        import_db_action.triggered.connect(self.import_data)
        file_menu.addAction(import_db_action)

        file_menu.addSeparator()

        backup_action = QAction("Backup Database", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)

        restore_action = QAction("Restore Database", self)
        restore_action.triggered.connect(self.restore_database)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_sidebar(self) -> QWidget:
        """Create the left sidebar with table list"""
        sidebar = QWidget()
        sidebar.setFixedWidth(config.SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("Tables")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        sidebar_layout.addWidget(header)

        # Table list
        self.table_list = QListWidget()
        self.table_list.itemClicked.connect(self.on_table_selected)
        sidebar_layout.addWidget(self.table_list)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(5)

        self.btn_new_table = QPushButton("New Table")
        self.btn_new_table.clicked.connect(self.create_new_table)
        btn_layout.addWidget(self.btn_new_table)

        self.btn_edit_table = QPushButton("Edit Table")
        self.btn_edit_table.clicked.connect(self.edit_table)
        self.btn_edit_table.setEnabled(False)
        btn_layout.addWidget(self.btn_edit_table)

        self.btn_delete_table = QPushButton("Delete Table")
        self.btn_delete_table.clicked.connect(self.delete_table)
        self.btn_delete_table.setEnabled(False)
        btn_layout.addWidget(self.btn_delete_table)

        sidebar_layout.addLayout(btn_layout)

        return sidebar

    def load_tables(self):
        """Load all tables into the sidebar"""
        if not self.db:
            return

        self.table_list.clear()
        tables = self.db.get_all_tables()

        for table in tables:
            item = QListWidgetItem(table['display_name'])
            item.setData(Qt.ItemDataRole.UserRole, table['id'])
            self.table_list.addItem(item)

    def on_table_selected(self, item: QListWidgetItem):
        """Handle table selection"""
        table_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_table_id = table_id

        self.btn_edit_table.setEnabled(True)
        self.btn_delete_table.setEnabled(True)

        # Show table view
        self.show_table_view(table_id)

    def show_table_view(self, table_id: int):
        """Display the record view for a table"""
        # Import here to avoid circular imports
        from record_view import RecordView

        # Remove old view if exists
        while self.content_stack.count() > 1:
            widget = self.content_stack.widget(1)
            self.content_stack.removeWidget(widget)
            widget.deleteLater()

        # Create new view
        table = self.db.get_table(table_id)
        if table:
            view = RecordView(self.db, self.storage, table_id, table['name'])
            self.content_stack.addWidget(view)
            self.content_stack.setCurrentIndex(1)

    def create_new_table(self):
        """Create a new table"""
        from table_dialog import TableDialog

        dialog = TableDialog(self.db, parent=self)
        if dialog.exec():
            self.load_tables()

    def edit_table(self):
        """Edit the selected table"""
        if not self.current_table_id:
            return

        from table_dialog import TableDialog

        dialog = TableDialog(self.db, table_id=self.current_table_id, parent=self)
        if dialog.exec():
            self.load_tables()
            # Refresh current view
            self.show_table_view(self.current_table_id)

    def delete_table(self):
        """Delete the selected table"""
        if not self.current_table_id:
            return

        table = self.db.get_table(self.current_table_id)
        if not table:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete table '{table['display_name']}'?\n\n"
            "This will delete all records and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_table(self.current_table_id)
            self.current_table_id = None
            self.load_tables()
            self.content_stack.setCurrentIndex(0)
            self.btn_edit_table.setEnabled(False)
            self.btn_delete_table.setEnabled(False)

    def export_data(self):
        """Export data to CSV/JSON"""
        if not self.current_table_id:
            QMessageBox.warning(self, "Export", "Please select a table first")
            return

        table = self.db.get_table(self.current_table_id)
        if not table:
            return

        # Ask for format
        format_choice, ok = QInputDialog.getItem(
            self,
            "Export Format",
            "Select export format:",
            ["JSON", "CSV"],
            0,
            False
        )

        if not ok:
            return

        # Get file path
        if format_choice == "JSON":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export to JSON",
                f"{table['name']}.json",
                "JSON Files (*.json)"
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export to CSV",
                f"{table['name']}.csv",
                "CSV Files (*.csv)"
            )

        if not file_path:
            return

        try:
            if format_choice == "JSON":
                self.exporter.export_to_json(table['name'], file_path)
            else:
                self.exporter.export_to_csv(table['name'], self.current_table_id, file_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Data exported successfully to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export data:\n{str(e)}")

    def import_data(self):
        """Import data from CSV/JSON"""
        if not self.current_table_id:
            QMessageBox.warning(self, "Import", "Please select a table first")
            return

        table = self.db.get_table(self.current_table_id)
        if not table:
            return

        # Get file path
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "Data Files (*.json *.csv);;JSON Files (*.json);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                count = self.importer.import_from_json(table['name'], file_path)
            elif file_path.endswith('.csv'):
                count = self.importer.import_from_csv(table['name'], file_path)
            else:
                QMessageBox.warning(self, "Import", "Unsupported file format")
                return

            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported {count} records"
            )

            # Refresh current view
            self.show_table_view(self.current_table_id)

        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Failed to import data:\n{str(e)}")

    def import_csv_data(self):
        """Import data from CSV with field mapping"""
        if not self.db:
            QMessageBox.warning(self, "No Database", "Please open or create a database first")
            return

        if not self.current_table_id:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first")
            return

        # Get current view to call import
        current_view = self.content_stack.currentWidget()
        if hasattr(current_view, 'import_data'):
            current_view.import_data()
        else:
            QMessageBox.warning(self, "Import Not Available",
                              "Please select a table to import data into")

    def export_import_template(self):
        """Export a CSV template for easy data entry"""
        if not self.db:
            QMessageBox.warning(self, "No Database", "Please open or create a database first")
            return

        if not self.current_table_id:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first")
            return

        # Get current view to call export template
        current_view = self.content_stack.currentWidget()
        if hasattr(current_view, 'export_template'):
            current_view.export_template()
        else:
            QMessageBox.warning(self, "Export Not Available",
                              "Please select a table to export a template for")

    def backup_database(self):
        """Backup the database"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Database",
            f"pycruds_backup.db",
            "Database Files (*.db)"
        )

        if not file_path:
            return

        try:
            if self.backup_manager.create_backup(file_path):
                QMessageBox.information(
                    self,
                    "Backup Successful",
                    f"Database backed up successfully to:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "Backup Failed", "Failed to create backup")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", f"Failed to backup database:\n{str(e)}")

    def restore_database(self):
        """Restore the database"""
        reply = QMessageBox.warning(
            self,
            "Confirm Restore",
            "Restoring a backup will replace the current database.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            "",
            "Database Files (*.db)"
        )

        if not file_path:
            return

        try:
            # Close current connection
            self.db.close()

            if self.backup_manager.restore_backup(file_path):
                # Reconnect to database
                self.db.connect()
                self.load_tables()
                self.content_stack.setCurrentIndex(0)
                self.current_table_id = None

                QMessageBox.information(
                    self,
                    "Restore Successful",
                    "Database restored successfully"
                )
            else:
                QMessageBox.critical(self, "Restore Failed", "Failed to restore backup")
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", f"Failed to restore database:\n{str(e)}")

    def new_database(self):
        """Create a new database"""
        # Default to data directory
        default_path = os.path.join(config.DATA_DIR, "new_database.db")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create New Database",
            default_path,
            "Database Files (*.db)"
        )

        if not file_path:
            return

        # Ensure .db extension
        if not file_path.endswith('.db'):
            file_path += '.db'

        # Check if file already exists
        if os.path.exists(file_path):
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"Database already exists. Open it instead?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.open_database(file_path)
            return

        # Create new database
        self.open_database(file_path)

    def open_database_dialog(self):
        """Open an existing database"""
        # Default to data directory
        default_dir = config.DATA_DIR

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database",
            default_dir,
            "Database Files (*.db);;All Files (*)"
        )

        if file_path:
            self.open_database(file_path)

    def open_database(self, db_path):
        """Open a database file"""
        try:
            # Close current database if open
            if self.db:
                self.db.close()

            # Open new database
            self.current_db_path = db_path
            self.db = DatabaseManager(db_path)

            # Use storage directory organized by database name
            # Structure: storage/<db_name>/<table>/<record>/
            db_name = os.path.splitext(os.path.basename(db_path))[0]
            storage_dir = os.path.join(config.STORAGE_DIR, db_name)

            self.storage = StorageManager(storage_dir)
            self.exporter = DataExporter(self.db)
            self.importer = DataImporter(self.db)
            self.backup_manager = BackupManager(db_path, storage_dir)

            # Add to recent databases
            self.config_manager.add_recent_database(db_path)
            self.update_recent_menu()

            # Update UI
            self.update_window_title()
            self.load_tables()
            self.content_stack.setCurrentIndex(0)
            self.current_table_id = None
            self.btn_edit_table.setEnabled(False)
            self.btn_delete_table.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Opening Database",
                f"Failed to open database:\n{str(e)}"
            )

    def update_recent_menu(self):
        """Update the recent databases menu"""
        self.recent_menu.clear()

        recent_dbs = self.config_manager.get_recent_databases()

        if not recent_dbs:
            no_recent = QAction("(No recent databases)", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
            return

        for db_path in recent_dbs:
            db_name = os.path.basename(db_path)
            action = QAction(db_name, self)
            action.setToolTip(db_path)
            action.triggered.connect(lambda checked, path=db_path: self.open_database(path))
            self.recent_menu.addAction(action)

    def update_window_title(self):
        """Update window title with current database name"""
        if self.current_db_path:
            db_name = os.path.basename(self.current_db_path)
            self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION} - {db_name}")
        else:
            self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            f"About {config.APP_NAME}",
            f"{config.APP_NAME} v{config.APP_VERSION}\n\n"
            "A modular CRUD application builder\n"
            "Built with PyQt6 and SQLite"
        )

    def closeEvent(self, event):
        """Handle window close"""
        if self.db:
            self.db.close()
        event.accept()
