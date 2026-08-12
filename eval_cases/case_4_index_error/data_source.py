"""
Data source module for case 4
"""

def fetch_data():
    """Fetch sample data arrays"""
    return [
        [1, 2, 3],
        [4, 5],  # This array is shorter than expected
        [6, 7, 8, 9],
        [],  # Empty array will cause issues
        [10, 11, 12]
    ]
