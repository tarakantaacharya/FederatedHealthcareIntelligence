"""
Schema validation service
Validates data against canonical schema
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from app.config import get_settings

settings = get_settings()


class SchemaValidationService:
    """Service for validating data against canonical schema"""
    
    def __init__(self):
        """Load canonical schema from JSON file"""
        schema_path = os.path.join('data', 'canonical_schema_v1.json')
        
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def get_schema(self) -> Dict:
        """
        Get canonical schema definition
        
        Returns:
            Schema dictionary
        """
        return self.schema
    
    def get_field_categories(self) -> Dict:
        """
        Get all field categories
        
        Returns:
            Dictionary of field categories
        """
        return self.schema['field_categories']
    
    def get_required_fields(self) -> List[str]:
        """
        Get list of all required fields across all categories
        
        Returns:
            List of required field names
        """
        required = []
        
        for category_name, category_data in self.schema['field_categories'].items():
            if 'fields' in category_data:
                for field_name, field_spec in category_data['fields'].items():
                    if field_spec.get('required', False):
                        required.append(field_name)
        
        return required
    
    def get_all_fields(self) -> Dict[str, Dict]:
        """
        Get all fields with their specifications
        
        Returns:
            Dictionary of {field_name: field_spec}
        """
        all_fields = {}
        
        for category_name, category_data in self.schema['field_categories'].items():
            if 'fields' in category_data:
                for field_name, field_spec in category_data['fields'].items():
                    all_fields[field_name] = {
                        **field_spec,
                        'category': category_name
                    }
        
        return all_fields
    
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate DataFrame against canonical schema
        
        Args:
            df: Pandas DataFrame to validate
        
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        
        all_fields = self.get_all_fields()
        required_fields = self.get_required_fields()
        
        # Check required fields
        missing_required = []
        for req_field in required_fields:
            if req_field not in df.columns:
                missing_required.append(req_field)
        
        if missing_required:
            errors.append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Validate field types and constraints
        for col in df.columns:
            if col in all_fields:
                field_spec = all_fields[col]
                field_type = field_spec.get('type')
                
                # Type validation
                if field_type == 'integer':
                    if not pd.api.types.is_integer_dtype(df[col]):
                        try:
                            df[col] = df[col].astype(int)
                        except:
                            warnings.append(f"Field '{col}' should be integer")
                
                elif field_type == 'float':
                    if not pd.api.types.is_float_dtype(df[col]):
                        try:
                            df[col] = df[col].astype(float)
                        except:
                            warnings.append(f"Field '{col}' should be float")
                
                elif field_type == 'datetime':
                    if not pd.api.types.is_datetime64_any_dtype(df[col]):
                        warnings.append(f"Field '{col}' should be datetime")
                
                # Range validation
                if 'min' in field_spec:
                    min_val = field_spec['min']
                    if (df[col] < min_val).any():
                        errors.append(f"Field '{col}' has values below minimum {min_val}")
                
                if 'max' in field_spec:
                    max_val = field_spec['max']
                    if (df[col] > max_val).any():
                        errors.append(f"Field '{col}' has values above maximum {max_val}")
        
        # Overall validation result
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'num_rows': len(df),
            'num_columns': len(df.columns),
            'validated_at': datetime.now().isoformat()
        }
    
    def get_field_synonyms(self) -> Dict[str, List[str]]:
        """
        Get field mapping hints (synonyms)
        
        Returns:
            Dictionary of {canonical_field: [synonyms]}
        """
        return self.schema.get('field_mapping_hints', {})
    
    def suggest_field_mapping(self, column_name: str) -> List[Dict[str, Any]]:
        """
        Suggest canonical field mapping for a column name
        
        Args:
            column_name: Original column name
        
        Returns:
            List of suggestions with confidence scores
        """
        suggestions = []
        column_lower = column_name.lower().strip()
        
        synonyms = self.get_field_synonyms()
        
        # Exact match
        if column_lower in self.get_all_fields():
            suggestions.append({
                'canonical_field': column_lower,
                'confidence': 1.0,
                'reason': 'exact_match'
            })
            return suggestions
        
        # Synonym match
        for canonical_field, synonym_list in synonyms.items():
            if column_lower in [s.lower() for s in synonym_list]:
                suggestions.append({
                    'canonical_field': canonical_field.replace('_synonyms', ''),
                    'confidence': 0.9,
                    'reason': 'synonym_match'
                })
        
        # Fuzzy match (simple contains check)
        all_fields = self.get_all_fields()
        for canonical_field in all_fields.keys():
            if canonical_field in column_lower or column_lower in canonical_field:
                suggestions.append({
                    'canonical_field': canonical_field,
                    'confidence': 0.7,
                    'reason': 'fuzzy_match'
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:3]  # Top 3 suggestions
