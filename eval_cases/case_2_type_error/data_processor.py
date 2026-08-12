"""
Data processor for case 2
This module contains the TypeError - attempting to add string to int
"""

from validators import validate_record

def process_records(model):
    """Process records and calculate statistics"""
    records = model.get_records()

    # Validate each record
    for record in records:
        validate_record(record)

    # This will fail when it encounters the string value
    total = model.calculate_total()

    return {
        "total": total,
        "count": len(records)
    }
