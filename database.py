"""
Database manager for pyCruds application
Handles all SQLite operations and schema management
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import config


class DatabaseManager:
    def __init__(self, db_file: str = config.DB_FILE):
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.connect()
        self.initialize_schema()

    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_file)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        # Create custom LOWER function for Unicode support (Greek, etc.)
        def unicode_lower(text):
            return text.lower() if text else text

        self.connection.create_function("UNICODE_LOWER", 1, unicode_lower)

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

    def initialize_schema(self):
        """Create the meta-schema tables"""
        # Tables metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS _tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Fields metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS _fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                field_type TEXT NOT NULL,
                is_required BOOLEAN DEFAULT 0,
                is_unique BOOLEAN DEFAULT 0,
                show_in_list BOOLEAN DEFAULT 1,
                options TEXT,
                reference_table_id INTEGER,
                reference_display_field TEXT,
                position INTEGER DEFAULT 0,
                FOREIGN KEY (table_id) REFERENCES _tables(id) ON DELETE CASCADE,
                FOREIGN KEY (reference_table_id) REFERENCES _tables(id) ON DELETE SET NULL,
                UNIQUE(table_id, name)
            )
        """)

        self.connection.commit()

    def create_table(self, name: str, display_name: str) -> int:
        """Create a new CRUD table"""
        # Insert table metadata
        self.cursor.execute(
            "INSERT INTO _tables (name, display_name) VALUES (?, ?)",
            (name, display_name)
        )
        table_id = self.cursor.lastrowid

        # Create the actual data table
        self.cursor.execute(f"""
            CREATE TABLE {name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()
        return table_id

    def delete_table(self, table_id: int):
        """Delete a CRUD table and its metadata"""
        # Get table name
        self.cursor.execute("SELECT name FROM _tables WHERE id = ?", (table_id,))
        row = self.cursor.fetchone()
        if not row:
            return

        table_name = row['name']

        # Drop the actual table
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # Delete fields metadata
        self.cursor.execute("DELETE FROM _fields WHERE table_id = ?", (table_id,))

        # Delete table metadata
        self.cursor.execute("DELETE FROM _tables WHERE id = ?", (table_id,))

        self.connection.commit()

    def get_all_tables(self) -> List[Dict[str, Any]]:
        """Get all CRUD tables"""
        self.cursor.execute("SELECT * FROM _tables ORDER BY name")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_table(self, table_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific table"""
        self.cursor.execute("SELECT * FROM _tables WHERE id = ?", (table_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def add_field(self, table_id: int, name: str, display_name: str,
                  field_type: str, is_required: bool = False,
                  is_unique: bool = False, show_in_list: bool = True,
                  options: str = None, reference_table_id: int = None,
                  reference_display_field: str = None, position: int = 0):
        """Add a field to a table"""
        # Get table name
        table = self.get_table(table_id)
        if not table:
            return

        # Check if column already exists in the actual table
        self.cursor.execute(f"PRAGMA table_info({table['name']})")
        existing_columns = [row['name'] for row in self.cursor.fetchall()]

        # Insert field metadata
        self.cursor.execute("""
            INSERT INTO _fields (table_id, name, display_name, field_type,
                                is_required, is_unique, show_in_list, options, reference_table_id,
                                reference_display_field, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (table_id, name, display_name, field_type, is_required,
              is_unique, show_in_list, options, reference_table_id, reference_display_field, position))

        # Only add column to actual table if it doesn't exist
        if name not in existing_columns:
            sql_type = self._get_sql_type(field_type)
            self.cursor.execute(f"ALTER TABLE {table['name']} ADD COLUMN {name} {sql_type}")

        self.connection.commit()

    def delete_field(self, field_id: int):
        """Delete a field (note: SQLite doesn't support DROP COLUMN easily)"""
        # For now, just delete the metadata
        # In production, you'd need to recreate the table without the column
        self.cursor.execute("DELETE FROM _fields WHERE id = ?", (field_id,))
        self.connection.commit()

    def get_fields(self, table_id: int) -> List[Dict[str, Any]]:
        """Get all fields for a table"""
        self.cursor.execute("""
            SELECT * FROM _fields
            WHERE table_id = ?
            ORDER BY position, id
        """, (table_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def _get_sql_type(self, field_type: str) -> str:
        """Map field type to SQL type"""
        type_mapping = {
            'text': 'TEXT',
            'number': 'REAL',
            'date': 'TEXT',
            'boolean': 'BOOLEAN',
            'email': 'TEXT',
            'url': 'TEXT',
            'phone': 'TEXT',
            'richtext': 'TEXT',
            'dropdown': 'TEXT',
            'multiselect': 'TEXT',
            'image': 'TEXT',
            'file': 'TEXT',
            'reference': 'INTEGER',
            'multireference': 'TEXT'
        }
        return type_mapping.get(field_type, 'TEXT')

    def insert_record(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert a record into a table"""
        # Filter out id, created_at, updated_at
        data = {k: v for k, v in data.items() if k not in ['id', 'created_at', 'updated_at']}

        if not data:
            self.cursor.execute(f"INSERT INTO {table_name} DEFAULT VALUES")
        else:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())

            self.cursor.execute(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                values
            )

        record_id = self.cursor.lastrowid
        self.connection.commit()
        return record_id

    def update_record(self, table_name: str, record_id: int, data: Dict[str, Any]):
        """Update a record"""
        # Filter out id, created_at
        data = {k: v for k, v in data.items() if k not in ['id', 'created_at']}
        data['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [record_id]

        self.cursor.execute(
            f"UPDATE {table_name} SET {set_clause} WHERE id = ?",
            values
        )
        self.connection.commit()

    def delete_record(self, table_name: str, record_id: int):
        """Delete a record"""
        self.cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        self.connection.commit()

    def get_records(self, table_name: str, limit: int = None, offset: int = 0,
                   order_by: str = 'id', order_dir: str = 'ASC',
                   where_clause: str = None, where_params: tuple = None) -> List[Dict[str, Any]]:
        """Get records from a table"""
        query = f"SELECT * FROM {table_name}"
        params = []

        if where_clause:
            query += f" WHERE {where_clause}"
            if where_params:
                params.extend(where_params)

        query += f" ORDER BY {order_by} {order_dir}"

        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_record(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific record"""
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def count_records(self, table_name: str, where_clause: str = None,
                     where_params: tuple = None) -> int:
        """Count records in a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        params = []

        if where_clause:
            query += f" WHERE {where_clause}"
            if where_params:
                params.extend(where_params)

        self.cursor.execute(query, params)
        return self.cursor.fetchone()['count']

    def search_records(self, table_name: str, fields: List[str],
                      search_term: str) -> List[Dict[str, Any]]:
        """Search records across multiple fields (case-insensitive with Unicode support)"""
        if not fields or not search_term:
            return self.get_records(table_name)

        where_parts = [f"UNICODE_LOWER({field}) LIKE UNICODE_LOWER(?)" for field in fields]
        where_clause = ' OR '.join(where_parts)
        where_params = tuple([f"%{search_term}%" for _ in fields])

        return self.get_records(table_name, where_clause=where_clause,
                               where_params=where_params)
