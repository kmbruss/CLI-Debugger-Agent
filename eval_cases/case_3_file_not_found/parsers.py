"""
Parser functions for case 3
"""

def parse_csv_data(raw_data):
    """Parse CSV data into structured format"""
    lines = raw_data.strip().split('\n')
    result = []

    for line in lines[1:]:  # Skip header
        values = line.split(',')
        result.append({
            "id": values[0],
            "value": values[1]
        })

    return result
