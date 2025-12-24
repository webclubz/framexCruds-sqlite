# pyCruds Architecture

## Overview

pyCruds is a modular CRUD application builder with a clean separation of concerns. The application follows the MVC pattern with PyQt6 for the UI layer and SQLite for data persistence.

## Project Statistics

- **Total Python Files**: 10
- **Total Lines of Code**: ~2,238
- **External Dependencies**: PyQt6 (+ Qt dependencies)
- **Database**: SQLite3 (built-in)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│                    (Entry Point)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    main_window.py                            │
│              (Main Application Window)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Sidebar    │  │ Content Area │  │  Menu Bar    │      │
│  │ (Table List) │  │(Stacked Views)│  │   (Actions)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───┬─────────────────────┬───────────────────┬───────────────┘
    │                     │                   │
    ▼                     ▼                   ▼
┌───────────┐      ┌────────────┐      ┌──────────────┐
│table_     │      │record_     │      │export_import │
│dialog.py  │      │view.py     │      │backup.py     │
│           │      │            │      │              │
│- Create   │      │- List      │      │- Export CSV  │
│- Edit     │      │- Search    │      │- Export JSON │
│- Fields   │      │- Sort      │      │- Import      │
│           │      │- Paginate  │      │- Backup      │
└─────┬─────┘      └──────┬─────┘      └──────────────┘
      │                   │
      ▼                   ▼
┌─────────────────────────────┐
│     record_dialog.py        │
│  (Add/Edit Record Dialog)   │
│                             │
│  ┌─────────────────────┐   │
│  │ Dynamic Form Fields │   │
│  │ - Text, Number, etc.│   │
│  │ - Image/File Upload │   │
│  │ - References        │   │
│  └─────────────────────┘   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│          Backend Layer                   │
│  ┌──────────────┐  ┌──────────────┐    │
│  │ database.py  │  │ storage.py   │    │
│  │              │  │              │    │
│  │ - SQLite Ops │  │ - File Mgmt  │    │
│  │ - Meta Schema│  │ - Images     │    │
│  │ - CRUD Ops   │  │ - Documents  │    │
│  └──────┬───────┘  └──────┬───────┘    │
│         │                 │             │
│         ▼                 ▼             │
│  ┌──────────────┐  ┌──────────────┐    │
│  │pycruds.db    │  │storage/      │    │
│  │(SQLite DB)   │  │(Files)       │    │
│  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────┘
              ▲
              │
              ▼
      ┌──────────────┐
      │  config.py   │
      │(Settings)    │
      └──────────────┘
```

## Component Breakdown

### 1. Entry Point
**File**: [main.py](main.py)
- Application initialization
- QApplication setup
- Window creation and display

### 2. Main Window
**File**: [main_window.py](main_window.py)
- Main application window with sidebar navigation
- Menu bar (File, Help)
- Table list management
- View switching between tables
- Export/Import/Backup coordination

### 3. Table Management
**File**: [table_dialog.py](table_dialog.py)
- Create new tables
- Edit table structure
- Field definition UI
- Field types configuration
- Options editor for dropdown/multiselect
- Reference table selector

### 4. Record Management

**File**: [record_view.py](record_view.py)
- Display records in table format
- Search functionality
- Sorting by columns
- Pagination controls
- Record selection and actions

**File**: [record_dialog.py](record_dialog.py)
- Dynamic form generation based on fields
- 14 different field type widgets
- Image upload with preview
- File upload handling
- Reference field selection
- Validation on save

### 5. Database Layer
**File**: [database.py](database_py)
- SQLite connection management
- Meta-schema for tables and fields
- Dynamic table creation
- CRUD operations
- Search and filtering
- Transaction management

**Schema**:
```sql
_tables (
    id, name, display_name,
    created_at, updated_at
)

_fields (
    id, table_id, name, display_name,
    field_type, is_required, is_unique,
    options, reference_table_id, position
)

{dynamic_tables} (
    id, created_at, updated_at,
    {custom_fields...}
)
```

### 6. Storage Layer
**File**: [storage.py](storage.py)
- File and image storage management
- Organized by table/record ID
- File operations (save, delete, get)
- Path management

**Structure**:
```
storage/
├── products/
│   ├── 1/
│   │   ├── image_product.jpg
│   │   └── manual_document.pdf
│   └── 2/
│       └── image_photo.png
└── customers/
    └── 1/
        └── profile_avatar.jpg
```

### 7. Data Import/Export
**File**: [export_import.py](export_import.py)
- Export to JSON format
- Export to CSV format
- Import from JSON
- Import from CSV
- Data transformation

### 8. Backup/Restore
**File**: [backup.py](backup.py)
- Database backup with timestamp
- Storage directory backup
- Database restoration
- Storage restoration

### 9. Configuration
**File**: [config.py](config.py)
- Application settings
- Field type definitions
- UI dimensions
- File paths

## Data Flow

### Creating a Record
```
User Input (record_dialog.py)
    ↓
Validation
    ↓
Database Insert (database.py)
    ↓
File Upload (storage.py)
    ↓
Database Update (file paths)
    ↓
Refresh View (record_view.py)
```

### Loading Records
```
User Selects Table (main_window.py)
    ↓
Load Table Metadata (database.py)
    ↓
Load Fields (database.py)
    ↓
Query Records (database.py)
    ↓
Format Display (record_view.py)
    ↓
Render Table Widget
```

## Field Types Implementation

Each field type has:
1. **Widget** - UI component for input
2. **Validation** - Rules for valid data
3. **Storage** - How it's saved in SQLite
4. **Display** - How it's shown in the table

| Field Type     | Widget          | Storage    | Example                |
|----------------|-----------------|------------|------------------------|
| Text           | QLineEdit       | TEXT       | "John Doe"             |
| Number         | QDoubleSpinBox  | REAL       | 123.45                 |
| Date           | QDateEdit       | TEXT       | "2025-12-22"           |
| Boolean        | QCheckBox       | BOOLEAN    | true/false             |
| Email          | QLineEdit       | TEXT       | "user@example.com"     |
| URL            | QLineEdit       | TEXT       | "https://example.com"  |
| Phone          | QLineEdit       | TEXT       | "+1234567890"          |
| RichText       | QTextEdit       | TEXT       | "Multi-line\ntext"     |
| Dropdown       | QComboBox       | TEXT       | "Option A"             |
| Multiselect    | QListWidget     | TEXT (JSON)| ["A", "B", "C"]        |
| Image          | Custom Widget   | TEXT       | "products/1/img.jpg"   |
| File           | Custom Widget   | TEXT       | "docs/1/file.pdf"      |
| Reference      | QComboBox       | INTEGER    | 5 (foreign key)        |
| Multireference | QListWidget     | TEXT (JSON)| [1, 3, 7]              |

## Key Design Decisions

### 1. Meta-Schema Approach
- Store table/field definitions in the database
- Allows dynamic table creation without schema migration
- User-defined structures

### 2. File Storage Organization
- Separate files by table and record ID
- Easy cleanup when records deleted
- Supports multiple files per record

### 3. Reference Implementation
- Single reference: Direct foreign key (INTEGER)
- Multi-reference: JSON array of IDs
- Trade-off: Simplicity vs. strict relational integrity

### 4. Validation Layer
- Client-side validation in dialogs
- Required/Unique constraints
- Format validation for email, URL, etc.

### 5. Pagination
- Prevents loading huge datasets
- Configurable page size
- Efficient queries with LIMIT/OFFSET

## Extension Points

Want to add features? Here are the extension points:

### Adding a New Field Type

1. Add to [config.py](config.py:19) `FIELD_TYPES`
2. Update [database.py](database.py:158) `_get_sql_type()`
3. Create widget in [record_dialog.py](record_dialog.py:77) `create_field_widget()`
4. Handle loading in [record_dialog.py](record_dialog.py:207) `load_record_data()`
5. Handle saving in [record_dialog.py](record_dialog.py:270) `get_field_value()`
6. Format display in [record_view.py](record_view.py:128) `format_field_value()`

### Adding Validation Rules

1. Extend [record_dialog.py](record_dialog.py:254) `validate_record()`
2. Add validation logic per field type
3. Update UI to show validation errors

### Adding Export Formats

1. Add methods to [export_import.py](export_import.py)
2. Update [main_window.py](main_window.py:243) menu handlers
3. Add file dialog filters

## Performance Considerations

- **Pagination**: Large tables use LIMIT/OFFSET
- **Lazy Loading**: Records loaded on-demand
- **Connection Pool**: Single DB connection per session
- **File Streaming**: Large files handled efficiently

## Security Notes

- SQL injection prevented by parameterized queries
- File uploads validated by extension
- No authentication (local desktop app)
- Backup encryption not implemented

## Testing Checklist

- [ ] Create table with all field types
- [ ] Add/Edit/Delete records
- [ ] Upload images and files
- [ ] Search across fields
- [ ] Sort by different columns
- [ ] Pagination with large dataset
- [ ] Export to JSON/CSV
- [ ] Import from JSON/CSV
- [ ] Create backup
- [ ] Restore from backup
- [ ] Reference fields between tables
- [ ] Multi-reference fields
- [ ] Required field validation
- [ ] Unique field validation
