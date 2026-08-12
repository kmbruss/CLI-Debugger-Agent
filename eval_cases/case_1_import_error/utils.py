"""
Utility functions for case 1
This file has an import error - importing a non-existent module
"""

import non_existent_module  # This will cause an ImportError
from helpers import format_output

def process_data(data):
    """Process data using non-existent module"""
    processed = non_existent_module.transform(data)
    return format_output(processed)
