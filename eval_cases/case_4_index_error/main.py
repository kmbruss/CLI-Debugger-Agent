#!/usr/bin/env python3
"""
Case 4: IndexError
This script attempts to access list indices that don't exist.
The error occurs in the array_processor module.
"""

from data_source import fetch_data
from array_processor import process_arrays
from output_formatter import format_results

def main():
    print("Fetching data from source...")

    data_arrays = fetch_data()
    print(f"Fetched {len(data_arrays)} arrays")

    # This will trigger an IndexError
    results = process_arrays(data_arrays)

    formatted = format_results(results)
    print(f"Results: {formatted}")

if __name__ == "__main__":
    main()
