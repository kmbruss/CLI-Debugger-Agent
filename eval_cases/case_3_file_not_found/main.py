#!/usr/bin/env python3
"""
Case 3: FileNotFoundError
This script attempts to read files that don't exist.
The error occurs in the file_loader module.
"""

from settings import Settings
from file_loader import load_all_data

def main():
    print("Initializing application...")

    settings = Settings()
    print(f"Settings loaded: {settings.get_config()}")

    # This will trigger a FileNotFoundError
    data = load_all_data()
    print(f"Data loaded: {data}")

if __name__ == "__main__":
    main()
