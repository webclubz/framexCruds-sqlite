"""
File storage manager for handling images and files
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import config


class StorageManager:
    def __init__(self, base_dir: str = config.STORAGE_DIR):
        self.base_dir = base_dir
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        """Ensure the base storage directory exists"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def get_record_dir(self, table_name: str, record_id: int) -> str:
        """Get the storage directory for a specific record"""
        record_dir = os.path.join(self.base_dir, table_name, str(record_id))
        if not os.path.exists(record_dir):
            os.makedirs(record_dir)
        return record_dir

    def save_file(self, table_name: str, record_id: int,
                  field_name: str, source_path: str) -> str:
        """
        Save a file to storage
        Returns the relative path to the saved file
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        record_dir = self.get_record_dir(table_name, record_id)

        # Get original filename and extension
        original_filename = os.path.basename(source_path)
        name, ext = os.path.splitext(original_filename)

        # Create filename: fieldname_originalname.ext
        new_filename = f"{field_name}_{original_filename}"
        dest_path = os.path.join(record_dir, new_filename)

        # Copy file
        shutil.copy2(source_path, dest_path)

        # Return relative path
        return os.path.relpath(dest_path, self.base_dir)

    def get_file_path(self, relative_path: str) -> str:
        """Get absolute path from relative storage path"""
        return os.path.join(self.base_dir, relative_path)

    def delete_file(self, relative_path: str):
        """Delete a file from storage"""
        abs_path = self.get_file_path(relative_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)

    def delete_record_files(self, table_name: str, record_id: int):
        """Delete all files for a record"""
        record_dir = os.path.join(self.base_dir, table_name, str(record_id))
        if os.path.exists(record_dir):
            shutil.rmtree(record_dir)

    def get_file_size(self, relative_path: str) -> int:
        """Get file size in bytes"""
        abs_path = self.get_file_path(relative_path)
        if os.path.exists(abs_path):
            return os.path.getsize(abs_path)
        return 0

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists"""
        abs_path = self.get_file_path(relative_path)
        return os.path.exists(abs_path)
