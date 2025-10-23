"""Singleton DatabaseManager for JSON data storage."""
import json
import os
from typing import Any, Dict, List
from ..core.exceptions import DatabaseError


class DatabaseManager:
    """Singleton for managing JSON database operations."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            from .settings import settings
            self.data_dir = settings.get('data_dir', 'data')
            self._ensure_data_dir()
            self._initialized = True
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_file_path(self, entity: str) -> str:
        """Get file path for entity."""
        return os.path.join(self.data_dir, f"{entity}.json")
    
    def read_data(self, entity: str) -> List[Dict[str, Any]]:
        """Read data from JSON file."""
        file_path = self._get_file_path(entity)
        try:
            if not os.path.exists(file_path):
                return []
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise DatabaseError(f"Ошибка чтения данных из {file_path}: {e}")
    
    def write_data(self, entity: str, data: List[Dict[str, Any]]):
        """Write data to JSON file atomically."""
        file_path = self._get_file_path(entity)
        try:
            # Write to temporary file first
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            # Replace original file
            os.replace(temp_path, file_path)
        except IOError as e:
            raise DatabaseError(f"Ошибка записи данных в {file_path}: {e}")
    
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
        entities = [item for item in entities if item.get(key) != value]
        self.write_data(entity, entities)


# Global singleton instance
db = DatabaseManager()
