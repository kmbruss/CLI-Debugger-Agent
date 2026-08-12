#!/usr/bin/env python3
"""
Case 2: TypeError
This script has a type error when processing data.
The error occurs in the data_processor module.
"""

from models import DataModel
from data_processor import process_records

def main():
    print("Loading data...")

    # Create some data records
    records = [
        {"id": 1, "value": 100},
        {"id": 2, "value": 200},
        {"id": 3, "value": "invalid"},  # This will cause issues
    ]

    model = DataModel(records)
    result = process_records(model)
    print(f"Processing complete: {result}")

if __name__ == "__main__":
    main()
