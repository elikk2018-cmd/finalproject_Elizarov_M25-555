"""Enhanced DatabaseManager with transactions and backup support."""
import json
import os
import shutil
import threading
from datetime import datetime
from typing import Any, Dict, List

from ..core.exceptions import DatabaseError


class DatabaseManager:
    """
    Enhanced Singleton for managing JSON database operations
    with transactions, backups, and thread safety.
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                from .settings import settings
                self.data_dir = settings.get('data_dir', 'data')
                self.backup_dir = settings.get('backup_dir', 'backups')
                self._ensure_directories()
                self._transaction_stack = []
                self._transaction_lock = threading.RLock()
                self._initialized = True

    def _ensure_directories(self):
        """Ensure data and backup directories exist."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            if self.backup_dir:  # Only create backup dir if specified
                os.makedirs(self.backup_dir, exist_ok=True)
        except OSError as e:
            raise DatabaseError(
                "Failed to create data directories",
                {"data_dir": self.data_dir, "backup_dir": self.backup_dir, "error": str(e)}
            )

    def _get_file_path(self, entity: str) -> str:
        """Get file path for entity."""
        return os.path.join(self.data_dir, f"{entity}.json")

    def _get_backup_path(self, entity: str, timestamp: str = None) -> str:
        """Get backup file path."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.backup_dir:
            return os.path.join(self.backup_dir, f"{entity}_{timestamp}.json")
        else:
            # If no backup dir specified, use data dir with backup suffix
            return os.path.join(self.data_dir, f"{entity}_{timestamp}.backup.json")

    def _create_backup(self, entity: str):
        """Create backup of entity file."""
        file_path = self._get_file_path(entity)
        if os.path.exists(file_path):
            try:
                backup_path = self._get_backup_path(entity)
                # Ensure backup directory exists
                backup_dir = os.path.dirname(backup_path)
                if backup_dir and not os.path.exists(backup_dir):
                    os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                # Log backup failure but don't stop the operation
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Backup creation failed", extra={
                    "entity": entity,
                    "backup_path": backup_path,
                    "error": str(e)
                })

    def read_data(self, entity: str) -> List[Dict[str, Any]]:
        """Read data from JSON file with comprehensive error handling."""
        file_path = self._get_file_path(entity)
        try:
            if not os.path.exists(file_path):
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise DatabaseError(
                    f"Invalid data format in {file_path}",
                    {"entity": entity, "file": file_path, "data_type": type(data).__name__}
                )

            return data

        except json.JSONDecodeError as e:
            # Attempt to recover by creating backup and returning empty data
            self._create_backup(entity)
            raise DatabaseError(
                f"Corrupted JSON data in {file_path}",
                {
                    "entity": entity,
                    "file": file_path,
                    "error": str(e),
                    "action": "Backup created, returning empty data"
                }
            )
        except IOError as e:
            raise DatabaseError(
                f"Error reading data from {file_path}",
                {"entity": entity, "file": file_path, "error": str(e)}
            )

    def write_data(self, entity: str, data: List[Dict[str, Any]]):
        """Write data to JSON file atomically with backup."""
        file_path = self._get_file_path(entity)

        # Validate data
        if not isinstance(data, list):
            raise DatabaseError(
                "Data must be a list",
                {"entity": entity, "data_type": type(data).__name__}
            )

        try:
            # Create backup before writing
            self._create_backup(entity)

            # Write to temporary file first
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Replace original file
            os.replace(temp_path, file_path)

        except IOError as e:
            raise DatabaseError(
                f"Error writing data to {file_path}",
                {"entity": entity, "file": file_path, "error": str(e)}
            )

    def update_entity(self, entity: str, key: str, value: Any, data: Dict[str, Any]):
        """Update or create entity in database."""
        entities = self.read_data(entity)

        # Find existing entity
        found_index = -1
        for i, item in enumerate(entities):
            if item.get(key) == value:
                found_index = i
                break

        if found_index >= 0:
            entities[found_index] = data
        else:
            entities.append(data)

        self.write_data(entity, entities)

    def find_entity(self, entity: str, key: str, value: Any) -> Dict[str, Any]:
        """Find entity by key-value pair."""
        entities = self.read_data(entity)
        for item in entities:
            if item.get(key) == value:
                return item
        return {}

    def delete_entity(self, entity: str, key: str, value: Any):
        """Delete entity by key-value pair."""
        entities = self.read_data(entity)
        initial_count = len(entities)
        entities = [item for item in entities if item.get(key) != value]

        if len(entities) < initial_count:
            self.write_data(entity, entities)

    def transaction(self):
        """Context manager for database transactions."""
        return DatabaseTransaction(self)


class DatabaseTransaction:
    """Database transaction context manager."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.operations = []
        self.committed = False

    def __enter__(self):
        self.db_manager._transaction_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_manager._transaction_stack.pop()

        if exc_type is not None:
            # Transaction failed, don't commit
            return False

        if not self.committed:
            # Auto-commit if not explicitly committed
            self.commit()

        return True

    def add_operation(self, operation: Dict[str, Any]):
        """Add operation to transaction."""
        self.operations.append(operation)

    def commit(self):
        """Commit all operations in transaction."""
        if self.committed:
            raise DatabaseError("Transaction already committed")

        try:
            # Group operations by entity for efficiency
            operations_by_entity = {}
            for op in self.operations:
                entity = op['entity']
                if entity not in operations_by_entity:
                    operations_by_entity[entity] = []
                operations_by_entity[entity].append(op)

            # Execute operations
            for entity, ops in operations_by_entity.items():
                self._execute_operations(entity, ops)

            self.committed = True

        except Exception as e:
            raise DatabaseError(
                "Transaction commit failed",
                {"operations_count": len(self.operations), "error": str(e)}
            )

    def _execute_operations(self, entity: str, operations: List[Dict[str, Any]]):
        """Execute operations for a specific entity."""
        # Read current data
        current_data = self.db_manager.read_data(entity)

        # Apply operations
        for op in operations:
            op_type = op['type']

            if op_type == 'update':
                key = op['key']
                value = op['value']
                new_data = op['data']

                # Find and update
                for i, item in enumerate(current_data):
                    if item.get(key) == value:
                        current_data[i] = new_data
                        break
                else:
                    # Not found, add new
                    current_data.append(new_data)

            elif op_type == 'delete':
                key = op['key']
                value = op['value']
                current_data = [item for item in current_data if item.get(key) != value]

        # Write back
        self.db_manager.write_data(entity, current_data)


# Global singleton instance
db = DatabaseManager()
