# pyCruds

A modular CRUD application builder with PyQt6 and SQLite. Create custom database tables with dynamic fields, manage records, and handle files - all through a clean, minimal interface.

## Features

### Core Functionality
- **Multiple Databases**: Create and manage multiple database files, easily switch between projects
- **Multiple Tables**: Create unlimited custom CRUD tables (Products, Customers, Projects, etc.)
- **Dynamic Fields**: Add custom fields to each table with 14 different field types
- **File Management**: Image and file uploads with organized storage by record ID
- **Search & Filter**: Search across records and filter results (case-insensitive, Unicode-aware)
- **Sort & Pagination**: Sort by any column, paginate large datasets
- **Export/Import**: Export to CSV/JSON and import data back
- **Backup/Restore**: Full database backup with storage files
- **Recent Databases**: Quick access to recently opened databases

### Supported Field Types

1. **Text** - Single-line text input
2. **Number** - Numeric values with decimals
3. **Date** - Date picker
4. **Boolean** - Checkbox (Yes/No)
5. **Email** - Email address field
6. **URL** - Web address field
7. **Phone** - Phone number field
8. **Rich Text** - Multi-line text editor
9. **Dropdown** - Single selection from predefined options
10. **Multiselect** - Multiple selections from predefined options
11. **Image** - Image upload with preview
12. **File** - File upload
13. **Reference** - Link to a record in another table (foreign key)
14. **Multi-reference** - Link to multiple records in another table

### Field Validation
- Required fields
- Unique constraints
- Field-specific format validation

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

### Quick Start Guide

1. **Database Management**
   - **New Database**: File → New Database (creates a new .db file)
   - **Open Database**: File → Open Database (opens an existing .db file)
   - **Recent Databases**: File → Recent Databases (quick access to recent files)
   - The window title shows the current database name
   - Each database has its own storage folder (e.g., `mydb_storage/`)

2. **Create a Table**
   - Click "New Table" button in the sidebar
   - Enter table name (e.g., "products") and display name (e.g., "Products")
   - Add fields by clicking "Add Field"
   - Configure each field (name, type, validation)
   - Click "Create"

3. **Add Records**
   - Select a table from the sidebar
   - Click "Add Record"
   - Fill in the form fields
   - For images/files, click "Upload" buttons
   - Click "Save"

4. **Manage Records**
   - Double-click a record to edit
   - Select a record and click "Delete" to remove
   - Use search box to find records (supports Greek and other Unicode characters)
   - Click column headers to sort
   - Use pagination controls for large datasets

5. **Export/Import Data**
   - Select a table
   - File → Export Data (choose JSON or CSV)
   - File → Import Data (select JSON or CSV file)

6. **Backup/Restore**
   - File → Backup Database (saves .db file and storage folder)
   - File → Restore Database (replaces current database)

## Project Structure

```
pyCruds/
├── main.py              # Application entry point
├── config.py            # Configuration settings
├── database.py          # Database manager (SQLite)
├── storage.py           # File storage manager
├── main_window.py       # Main application window
├── table_dialog.py      # Table creation/editing dialog
├── record_view.py       # Record list view
├── record_dialog.py     # Record creation/editing dialog
├── export_import.py     # Data export/import functionality
├── backup.py            # Backup/restore functionality
├── requirements.txt     # Python dependencies
├── pycruds.db          # SQLite database (created on first run)
└── storage/            # File storage directory (created on first run)
    └── [table_name]/
        └── [record_id]/
            └── [files]
```

## Database Schema

The application uses a meta-schema approach:

- `_tables` - Stores table definitions
- `_fields` - Stores field definitions for each table
- Dynamic tables created based on user configuration

## File Storage

Files and images are stored in the `storage/` directory:
- Organized by table name and record ID
- Original filenames preserved with field name prefix
- Automatically deleted when records are removed

## Examples

### Example 1: Product Catalog

Table: `products`
Fields:
- Name (Text, Required)
- Description (Rich Text)
- Price (Number, Required)
- Stock (Number)
- Category (Dropdown: Electronics, Clothing, Food)
- Product Image (Image)
- Is Active (Boolean)

### Example 2: Customer Database

Table: `customers`
Fields:
- Full Name (Text, Required)
- Email (Email, Required, Unique)
- Phone (Phone)
- Address (Rich Text)
- Registration Date (Date)
- Status (Dropdown: Active, Inactive, Pending)
- Profile Picture (Image)

### Example 3: Project Management

Table: `projects`
Fields:
- Project Name (Text, Required)
- Description (Rich Text)
- Start Date (Date)
- End Date (Date)
- Client (Reference → clients table)
- Team Members (Multi-reference → employees table)
- Status (Dropdown: Planning, In Progress, Completed)
- Budget (Number)
- Documents (File)

## Tips

1. **Table Names**: Use lowercase with underscores (e.g., `my_table`)
2. **Field Names**: Use descriptive names without spaces
3. **References**: Create the referenced table before adding reference fields
4. **Backups**: Regular backups recommended before major changes
5. **Large Datasets**: Use pagination and search for better performance
6. **File Size**: Be mindful of large image/file uploads

## Keyboard Shortcuts

- `Ctrl+Shift+N` - New Database
- `Ctrl+O` - Open Database
- `Ctrl+N` - New Table
- `Ctrl+E` - Export Data
- `Ctrl+I` - Import Data
- `Ctrl+Q` - Exit Application

## Troubleshooting

**Database locked error**
- Close other instances of the application
- Check file permissions

**Files not showing**
- Verify storage/ directory exists
- Check file paths in database

**Import fails**
- Ensure CSV/JSON format matches table structure
- Check for required field violations

## Future Enhancements

Potential features for future versions:
- Custom themes and styling
- Advanced filtering with multiple criteria
- Relationship visualization
- Formula fields
- Automated workflows
- Multi-user support
- Cloud sync

## License

This project is provided as-is for local usage.

## Credits

Built with:
- PyQt6 - GUI framework
- SQLite - Database engine
- Python 3 - Programming language
