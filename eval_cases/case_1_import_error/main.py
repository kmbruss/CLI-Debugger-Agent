#!/usr/bin/env python3
"""
Case 1: ImportError
This script attempts to import a module that doesn't exist.
The error is in utils.py which is imported here.
"""

from config import CONFIG
from utils import process_data

def main():
    print(f"Starting application with config: {CONFIG}")
    data = [1, 2, 3, 4, 5]
    result = process_data(data)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
