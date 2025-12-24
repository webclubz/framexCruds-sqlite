"""
Backup and restore functionality for the database
"""
import shutil
import os
from datetime import datetime
from pathlib import Path
import config


class BackupManager:
    def __init__(self, db_file: str = config.DB_FILE,
                 storage_dir: str = config.STORAGE_DIR):
        self.db_file = db_file
        self.storage_dir = storage_dir

    def create_backup(self, backup_path: str) -> bool:
        """
        Create a backup of the database and storage files
        Returns True if successful
        """
        try:
            # If backup_path is a directory, create a timestamped backup file
            if os.path.isdir(backup_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_path, f"pycruds_backup_{timestamp}.db")

            # Copy database file
            shutil.copy2(self.db_file, backup_path)

            # Also backup storage directory if it exists
            if os.path.exists(self.storage_dir):
                storage_backup = backup_path.replace('.db', '_storage')
                if os.path.exists(storage_backup):
                    shutil.rmtree(storage_backup)
                shutil.copytree(self.storage_dir, storage_backup)

            return True

        except Exception as e:
            print(f"Backup failed: {e}")
            return False

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup
        Returns True if successful
        """
        try:
            if not os.path.exists(backup_path):
                return False

            # Restore database
            shutil.copy2(backup_path, self.db_file)

            # Restore storage if exists
            storage_backup = backup_path.replace('.db', '_storage')
            if os.path.exists(storage_backup):
                if os.path.exists(self.storage_dir):
                    shutil.rmtree(self.storage_dir)
                shutil.copytree(storage_backup, self.storage_dir)

            return True

        except Exception as e:
            print(f"Restore failed: {e}")
            return False
