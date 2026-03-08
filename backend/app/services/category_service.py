"""
Category extension service
Manages treatment category-specific fields
"""
import json
import os
from typing import Dict, List
from app.config import get_settings

settings = get_settings()


class CategoryService:
    """Service for managing category extensions"""
    
    def __init__(self):
        """Load category extensions from JSON file"""
        category_path = os.path.join('data', 'category_extensions_v1.json')
        
        with open(category_path, 'r') as f:
            self.categories = json.load(f)
    
    def get_all_categories(self) -> Dict:
        """
        Get all category definitions
        
        Returns:
            Complete category extensions dictionary
        """
        return self.categories
    
    def get_category_fields(self, category_name: str) -> Dict:
        """
        Get fields for a specific category
        
        Args:
            category_name: Category name (icu, emergency, etc.)
        
        Returns:
            Category field definitions
        """
        if category_name not in self.categories['categories']:
            return {}
        
        return self.categories['categories'][category_name]['fields']
    
    def get_all_category_names(self) -> List[str]:
        """
        Get list of all available categories
        
        Returns:
            List of category names
        """
        return list(self.categories['categories'].keys())
    
    def get_category_info(self, category_name: str) -> Dict:
        """
        Get category information
        
        Args:
            category_name: Category name
        
        Returns:
            Category name, description, and fields
        """
        if category_name not in self.categories['categories']:
            return {}
        
        category_data = self.categories['categories'][category_name]
        
        return {
            'category_id': category_name,
            'name': category_data['name'],
            'description': category_data['description'],
            'num_fields': len(category_data['fields']),
            'fields': category_data['fields']
        }
    
    def get_prefixed_field_name(self, category: str, field: str) -> str:
        """
        Get prefixed field name for category
        
        Args:
            category: Category name
            field: Field name
        
        Returns:
            Prefixed field name (e.g., icu_ventilator_usage)
        """
        return f"{category}_{field}"
    
    def parse_prefixed_field(self, prefixed_field: str) -> tuple:
        """
        Parse prefixed field name into category and field
        
        Args:
            prefixed_field: Prefixed field name
        
        Returns:
            Tuple of (category, field_name)
        """
        parts = prefixed_field.split('_', 1)
        
        if len(parts) == 2 and parts[0] in self.get_all_category_names():
            return parts[0], parts[1]
        
        return None, prefixed_field
    
    def get_category_field_list(self, category: str) -> List[str]:
        """
        Get list of all prefixed field names for a category
        
        Args:
            category: Category name
        
        Returns:
            List of prefixed field names
        """
        if category not in self.categories['categories']:
            return []
        
        fields = self.categories['categories'][category]['fields'].keys()
        
        return [self.get_prefixed_field_name(category, field) for field in fields]
    
    def validate_category_data(self, category: str, data: Dict) -> Dict:
        """
        Validate category-specific data
        
        Args:
            category: Category name
            data: Data dictionary with category fields
        
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        category_fields = self.get_category_fields(category)
        
        if not category_fields:
            errors.append(f"Unknown category: {category}")
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        for field_name, field_spec in category_fields.items():
            prefixed_name = self.get_prefixed_field_name(category, field_name)
            
            if prefixed_name not in data:
                if field_spec.get('required', False):
                    errors.append(f"Missing required field: {prefixed_name}")
                continue
            
            value = data[prefixed_name]
            
            # Type validation
            field_type = field_spec.get('type')
            
            if field_type == 'integer':
                if not isinstance(value, int):
                    try:
                        value = int(value)
                    except:
                        warnings.append(f"Field {prefixed_name} should be integer")
            
            elif field_type == 'float':
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except:
                        warnings.append(f"Field {prefixed_name} should be float")
            
            # Range validation
            if 'min' in field_spec and value < field_spec['min']:
                errors.append(f"Field {prefixed_name} value {value} below minimum {field_spec['min']}")
            
            if 'max' in field_spec and value > field_spec['max']:
                errors.append(f"Field {prefixed_name} value {value} above maximum {field_spec['max']}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
