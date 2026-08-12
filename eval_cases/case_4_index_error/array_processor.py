"""
Array processor module for case 4
This module contains the IndexError - accessing indices beyond array bounds
"""

from calculations import calculate_stats

def process_arrays(arrays):
    """Process multiple arrays - will fail with IndexError"""
    results = []

    for arr in arrays:
        # Assuming all arrays have at least 3 elements - this is the bug!
        first = arr[0]
        second = arr[1]
        third = arr[2]  # This will cause IndexError for shorter arrays

        stats = calculate_stats(first, second, third)
        results.append(stats)

    return results
