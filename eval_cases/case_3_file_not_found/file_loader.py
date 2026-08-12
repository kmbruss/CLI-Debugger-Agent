"""
File loader module for case 3
This module will cause a FileNotFoundError when trying to read a missing file
"""

from settings import Settings
from parsers import parse_csv_data

def load_all_data():
    """Load all data files - will fail with FileNotFoundError"""
    settings = Settings()
    data_path = settings.get_data_path()

    # This file doesn't exist and will cause FileNotFoundError
    with open(data_path, 'r') as f:
        raw_data = f.read()

    return parse_csv_data(raw_data)
