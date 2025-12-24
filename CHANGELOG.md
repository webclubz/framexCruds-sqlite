# Changelog

## Version 1.0.0 - 2025-12-23

### Added Features

#### Multiple Database Support
- **New Database**: Create separate database files for different projects
  - File → New Database (Ctrl+Shift+N)
  - Choose custom location and filename
  - Each database has its own storage folder

- **Open Database**: Open existing database files
  - File → Open Database (Ctrl+O)
  - Switch between different databases easily

- **Recent Databases**: Quick access menu
  - File → Recent Databases
  - Shows last 10 opened databases
  - Click to quickly switch

- **Database Indicator**: Window title shows current database
  - Example: "pyCruds v1.0.0 - my_project.db"
  - Always know which database you're working with

- **Separate Storage**: Each database has its own storage folder
  - Format: `{database_name}_storage/`
  - Example: `inventory.db` → `inventory_storage/`
  - Keeps files organized by project

#### Record Preview & Printing
- **Preview Dialog**: View formatted record details before printing
  - Clean, readable layout with all field information
  - Shows field labels and formatted values
  - Metadata display (ID, created/updated timestamps)

- **Print Support**: Direct printing from preview dialog
  - Print button for immediate printing
  - High-resolution print output
  - Print dialog with printer selection

- **PDF Export**: Export individual records to PDF
  - Export PDF button in preview dialog
  - Professional formatting
  - Preserves all field data and formatting

#### Search Improvements
- **Unicode Support**: Fixed case-insensitive search for Greek and other Unicode characters
  - Search "φωτο" now finds "Φωτοτυπικό" ✓
  - Works with all languages and character sets
  - Custom UNICODE_LOWER function for proper Unicode handling

#### UI Improvements
- **Compact Form Spacing**: Reduced spacing in add/edit record dialogs
  - Vertical spacing reduced to 4px between fields
  - More compact, professional appearance
  - Better use of screen space

- **Field Visibility Control**: Choose which fields appear in the main table list
  - New "Show in List" checkbox when creating/editing fields
  - Hide lengthy fields (rich text, files, etc.) from table view
  - Reduces horizontal scrolling in tables with many fields
  - All fields still editable and visible in record details

### Technical Changes

#### New Files
- `config.py`: Added `ConfigManager` class for managing application configuration
  - Tracks recent databases
  - Stores last opened database
  - JSON-based configuration file (`pycruds_config.json`)

- `record_preview.py`: New dialog for previewing and printing records
  - HTML-based formatting
  - Print and PDF export functionality
  - Professional layout with proper formatting

#### Modified Files
- `main_window.py`:
  - Added database management methods
  - Updated menu bar with database options
  - Window title now shows current database
  - Recent databases submenu
  - Database switching support

- `database.py`:
  - Added custom `UNICODE_LOWER` SQL function
  - Fixed search to support Unicode characters
  - Case-insensitive search for all languages

- `record_view.py`:
  - Added Preview button to toolbar
  - New preview_record() method
  - Integration with preview dialog

- `record_dialog.py`:
  - Reduced form spacing for compact layout
  - Improved label alignment
  - Better use of dialog space

- `.gitignore`:
  - Added `pycruds_config.json` to ignore list
  - Added `*_storage/` pattern for database-specific storage folders

#### Documentation Updates
- `README.md`: Updated with multiple database features
- `QUICK_START.md`: Added Step 0 for database management
- `CHANGELOG.md`: Created this file

### Keyboard Shortcuts Added
- `Ctrl+Shift+N` - New Database
- `Ctrl+O` - Open Database

### Use Cases
This update enables:
1. **Project Separation**: Different database for each project
   - `personal_contacts.db` - Personal contacts
   - `business_inventory.db` - Business inventory
   - `recipe_collection.db` - Recipe collection

2. **Client Management**: Separate database per client
   - Easy to backup and share individual client data
   - Keep client data isolated

3. **Testing**: Create test databases without affecting production
   - `production.db` - Live data
   - `testing.db` - Test data

### Migration Notes
- Existing `pycruds.db` will continue to work
- On first launch, if `pycruds.db` exists, it will be opened automatically
- No action required for existing users
- New databases can be created at any time

### Configuration File
A new configuration file `pycruds_config.json` is created automatically:
```json
{
  "recent_databases": [
    "/path/to/project1.db",
    "/path/to/project2.db"
  ],
  "last_database": "/path/to/project1.db"
}
```

### Known Issues
None

### Future Improvements
- Database templates (pre-configured table structures)
- Database comparison tools
- Merge databases functionality
- Cloud sync for databases
