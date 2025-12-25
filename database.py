"""
Database manager for pyCruds application
Handles all SQLite operations and schema management
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import unicodedata
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

        # Create custom function to remove accents/tonos for Greek text search
        def remove_accents(text):
            if not text:
                return text
            # Normalize to NFD (decomposed form) and remove combining marks
            nfd = unicodedata.normalize('NFD', text)
            return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

        # Create combined function for case-insensitive, accent-insensitive search
        def normalize_search(text):
            if not text:
                return text
            # First remove accents, then lowercase
            no_accents = remove_accents(text)
            return no_accents.lower()

        self.connection.create_function("UNICODE_LOWER", 1, unicode_lower)
        self.connection.create_function("REMOVE_ACCENTS", 1, remove_accents)
        self.connection.create_function("NORMALIZE_SEARCH", 1, normalize_search)

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

        # Migration: Add cascade_delete column if it doesn't exist
        try:
            self.cursor.execute("SELECT cascade_delete FROM _fields LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            self.cursor.execute("""
                ALTER TABLE _fields ADD COLUMN cascade_delete BOOLEAN DEFAULT 0
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
                  reference_display_field: str = None, position: int = 0,
                  cascade_delete: bool = False):
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
                                reference_display_field, position, cascade_delete)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (table_id, name, display_name, field_type, is_required,
              is_unique, show_in_list, options, reference_table_id, reference_display_field, position, cascade_delete))

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
        """Delete a record and handle cascade deletes"""
        # Get the table ID
        table = self.cursor.execute("SELECT id FROM _tables WHERE name = ?", (table_name,)).fetchone()
        if not table:
            return

        table_id = table['id']

        # Find all reference fields in other tables that point to this table with cascade delete enabled
        all_tables = self.get_tables()

        for other_table in all_tables:
            other_table_id = other_table['id']
            other_table_name = other_table['name']

            # Get fields for this table
            fields = self.get_fields(other_table_id)

            # Find reference fields pointing to our table with cascade_delete=True
            for field in fields:
                if (field['field_type'] == 'reference' and
                    field.get('reference_table_id') == table_id and
                    field.get('cascade_delete', False)):

                    # Find records in this table that reference our record
                    where_clause = f"{field['name']} = ?"
                    where_params = (record_id,)

                    referencing_records = self.get_records(
                        other_table_name,
                        where_clause=where_clause,
                        where_params=where_params
                    )

                    # Delete each referencing record (recursively handles their cascade deletes)
                    for ref_record in referencing_records:
                        self.delete_record(other_table_name, ref_record['id'])

        # Delete the record itself
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
        """Search records across multiple fields (case-insensitive, accent-insensitive with Unicode support)"""
        if not fields or not search_term:
            return self.get_records(table_name)

        where_parts = [f"NORMALIZE_SEARCH({field}) LIKE NORMALIZE_SEARCH(?)" for field in fields]
        where_clause = ' OR '.join(where_parts)
        where_params = tuple([f"%{search_term}%" for _ in fields])

        return self.get_records(table_name, where_clause=where_clause,
                               where_params=where_params)

    def filter_records(self, table_name: str, filters: dict) -> List[Dict[str, Any]]:
        """Filter records based on advanced filter criteria"""
        if not filters:
            return self.get_records(table_name)

        where_parts = []
        where_params = []

        for field_name, filter_config in filters.items():
            filter_type = filter_config['type']

            if filter_type == 'text':
                where_parts.append(f"NORMALIZE_SEARCH({field_name}) LIKE NORMALIZE_SEARCH(?)")
                where_params.append(f"%{filter_config['value']}%")

            elif filter_type == 'number_range':
                if filter_config.get('min') is not None:
                    where_parts.append(f"{field_name} >= ?")
                    where_params.append(filter_config['min'])
                if filter_config.get('max') is not None:
                    where_parts.append(f"{field_name} <= ?")
                    where_params.append(filter_config['max'])

            elif filter_type == 'date_range':
                if filter_config.get('from') is not None:
                    where_parts.append(f"{field_name} >= ?")
                    where_params.append(filter_config['from'])
                if filter_config.get('to') is not None:
                    where_parts.append(f"{field_name} <= ?")
                    where_params.append(filter_config['to'])

            elif filter_type == 'boolean':
                where_parts.append(f"{field_name} = ?")
                where_params.append(1 if filter_config['value'] else 0)

            elif filter_type == 'dropdown':
                where_parts.append(f"{field_name} = ?")
                where_params.append(filter_config['value'])

            elif filter_type == 'reference':
                # Handle reference field by searching in the referenced table
                search_value = filter_config['value']
                field_metadata = filter_config.get('field')

                if field_metadata and field_metadata.get('reference_table_id'):
                    # Get the referenced table
                    ref_table = self.get_table(field_metadata['reference_table_id'])
                    if ref_table:
                        ref_table_name = ref_table['name']

                        # Find matching IDs in the referenced table
                        # Search across all text-like fields in the referenced table
                        ref_fields = self.get_fields(field_metadata['reference_table_id'])
                        searchable_ref_fields = [f['name'] for f in ref_fields
                                                if f['field_type'] in ['text', 'email', 'url', 'phone', 'richtext']]

                        if searchable_ref_fields:
                            # Build search query for referenced table (accent-insensitive)
                            ref_where_parts = [f"NORMALIZE_SEARCH({f}) LIKE NORMALIZE_SEARCH(?)"
                                             for f in searchable_ref_fields]
                            ref_where_clause = ' OR '.join(ref_where_parts)
                            ref_where_params = tuple([f"%{search_value}%" for _ in searchable_ref_fields])

                            # Get matching records from referenced table
                            matching_refs = self.get_records(ref_table_name,
                                                            where_clause=ref_where_clause,
                                                            where_params=ref_where_params)

                            if matching_refs:
                                # Get all matching IDs
                                matching_ids = [str(r['id']) for r in matching_refs]
                                # Create IN clause
                                placeholders = ','.join(['?' for _ in matching_ids])
                                where_parts.append(f"{field_name} IN ({placeholders})")
                                where_params.extend(matching_ids)
                            else:
                                # No matches found, add impossible condition
                                where_parts.append("1 = 0")

        where_clause = ' AND '.join(where_parts) if where_parts else None
        where_params_tuple = tuple(where_params) if where_params else None

        return self.get_records(table_name, where_clause=where_clause,
                               where_params=where_params_tuple)
