# Quick Start Guide

## Installation

1. Open terminal in the pyCruds directory
2. Run the installation script:
   ```bash
   ./install.sh
   ```

This will:
- Create a Python virtual environment
- Install PyQt6 and dependencies
- Set up the project

## Running the Application

```bash
./run.sh
```

## First Time Usage

### Step 0: Managing Databases (NEW!)

pyCruds now supports multiple databases! You can create separate database files for different projects.

**Create a New Database:**
- File → New Database...
- Choose location and name (e.g., `my_inventory.db`)
- Each database has its own storage folder (e.g., `my_inventory_storage/`)

**Open an Existing Database:**
- File → Open Database...
- Select the .db file

**Recent Databases:**
- File → Recent Databases
- Quick access to your last 10 databases

**Current Database:**
- The window title shows which database is currently open
- Example: "pyCruds v1.0.0 - my_inventory.db"

### Step 1: Create Your First Table

1. Click the **"New Table"** button in the left sidebar
2. Fill in:
   - **Table Name**: `customers` (lowercase, no spaces)
   - **Display Name**: `Customers` (human-readable)
3. Click **"Add Field"** to add fields:

   **Field 1:**
   - Field Name: `name`
   - Display Name: `Full Name`
   - Type: `Text`
   - Required: ✓

   **Field 2:**
   - Field Name: `email`
   - Display Name: `Email`
   - Type: `Email`
   - Required: ✓
   - Unique: ✓

   **Field 3:**
   - Field Name: `phone`
   - Display Name: `Phone Number`
   - Type: `Phone`

   **Field 4:**
   - Field Name: `status`
   - Display Name: `Status`
   - Type: `Dropdown`
   - Click **"Edit"** for Options and enter:
     ```
     Active
     Inactive
     Pending
     ```

   **Field 5:**
   - Field Name: `notes`
   - Display Name: `Notes`
   - Type: `Richtext`

4. Click **"Create"**

### Step 2: Add Your First Record

1. Select "Customers" from the sidebar
2. Click **"Add Record"**
3. Fill in the form:
   - Full Name: `John Doe`
   - Email: `john@example.com`
   - Phone Number: `+1234567890`
   - Status: `Active`
   - Notes: `VIP customer`
4. Click **"Save"**

### Step 3: Try More Features

**Search:**
- Type in the search box and press Enter

**Sort:**
- Click any column header to sort

**Edit:**
- Double-click a record or select it and click "Edit"

**Delete:**
- Select a record and click "Delete"

**Export:**
- Go to File → Export Data
- Choose JSON or CSV
- Select save location

## Example: E-commerce Database

### Products Table

```
Table Name: products
Fields:
- name (Text, Required)
- sku (Text, Required, Unique)
- description (Richtext)
- price (Number, Required)
- stock_quantity (Number)
- category (Dropdown: Electronics, Clothing, Books, Food)
- is_active (Boolean)
- product_image (Image)
```

### Customers Table

```
Table Name: customers
Fields:
- full_name (Text, Required)
- email (Email, Required, Unique)
- phone (Phone)
- address (Richtext)
- customer_since (Date)
- status (Dropdown: Active, Inactive)
- profile_picture (Image)
```

### Orders Table

```
Table Name: orders
Fields:
- order_number (Text, Required, Unique)
- customer (Reference → customers)
- products (Multireference → products)
- order_date (Date, Required)
- total_amount (Number, Required)
- status (Dropdown: Pending, Processing, Shipped, Delivered)
- notes (Richtext)
- invoice (File)
```

## Tips

1. **Always use lowercase table names** with underscores (e.g., `my_table`)
2. **Create referenced tables first** before adding reference fields
3. **Backup regularly** using File → Backup Database
4. **Use required fields** to ensure data integrity
5. **Unique fields** prevent duplicate entries

## Keyboard Shortcuts

- `Ctrl+N` - New Table
- `Ctrl+E` - Export Data
- `Ctrl+I` - Import Data
- `Ctrl+Q` - Exit

## Need Help?

See the full [README.md](README.md) for detailed documentation.

## Common Issues

**Can't run install.sh**
```bash
chmod +x install.sh run.sh
```

**ModuleNotFoundError**
- Run `./install.sh` first
- Make sure you're using `./run.sh` not `python main.py`

**Database locked**
- Close all instances of the app
- Only run one instance at a time
