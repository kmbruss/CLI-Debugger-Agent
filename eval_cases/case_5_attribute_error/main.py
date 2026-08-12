#!/usr/bin/env python3
"""
Case 5: AttributeError
This script attempts to access attributes that don't exist on objects.
The error occurs in the service layer.
"""

from database import Database
from service import UserService
from reporter import generate_report

def main():
    print("Initializing database connection...")

    db = Database("sqlite:///:memory:")
    db.connect()

    print("Creating user service...")
    user_service = UserService(db)

    # This will trigger an AttributeError
    users = user_service.get_all_users()

    print(f"Found {len(users)} users")

    report = generate_report(users)
    print(f"Report: {report}")

if __name__ == "__main__":
    main()
