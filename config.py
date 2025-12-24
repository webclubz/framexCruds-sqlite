"""
Configuration settings for pyCruds application
"""
import os
import json

# Application settings
APP_NAME = "pyCruds"
APP_VERSION = "1.0.0"

# Database settings
DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "pycruds.db")
CONFIG_FILE = "pycruds_config.json"
MAX_RECENT_DBS = 10

# Storage settings
STORAGE_DIR = "storage"

# UI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 250

# Field types
FIELD_TYPES = [
    "text",
    "number",
    "date",
    "boolean",
    "email",
    "url",
    "phone",
    "richtext",
    "dropdown",
    "multiselect",
    "image",
    "file",
    "reference",
    "multireference"
]

# Ensure directories exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)


class ConfigManager:
    """Manager for application configuration and recent databases"""

    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return {
            'recent_databases': [],
            'last_database': None
        }

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def add_recent_database(self, db_path):
        """Add database to recent list"""
        db_path = os.path.abspath(db_path)

        # Remove if already in list
        if db_path in self.config['recent_databases']:
            self.config['recent_databases'].remove(db_path)

        # Add to front of list
        self.config['recent_databases'].insert(0, db_path)

        # Keep only MAX_RECENT_DBS
        self.config['recent_databases'] = self.config['recent_databases'][:MAX_RECENT_DBS]

        # Update last database
        self.config['last_database'] = db_path

        self.save_config()

    def get_recent_databases(self):
        """Get list of recent databases (only existing files)"""
        recent = []
        for db_path in self.config['recent_databases']:
            if os.path.exists(db_path):
                recent.append(db_path)

        # Update config if some files don't exist anymore
        if len(recent) != len(self.config['recent_databases']):
            self.config['recent_databases'] = recent
            self.save_config()

        return recent

    def get_last_database(self):
        """Get last opened database"""
        last_db = self.config.get('last_database')
        if last_db and os.path.exists(last_db):
            return last_db
        return None
