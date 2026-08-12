"""
Validation functions for case 2
"""

def validate_record(record):
    """Validate a record has required fields"""
    if "id" not in record:
        raise ValueError("Record missing 'id' field")
    if "value" not in record:
        raise ValueError("Record missing 'value' field")
    return True
