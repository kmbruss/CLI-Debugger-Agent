"""
Calculation functions for case 4
"""

def calculate_stats(a, b, c):
    """Calculate statistics from three values"""
    return {
        "sum": a + b + c,
        "average": (a + b + c) / 3,
        "max": max(a, b, c),
        "min": min(a, b, c)
    }
