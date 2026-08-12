"""
Service layer for case 5
This module contains the AttributeError - accessing non-existent attributes
"""

from models import User

class UserService:
    def __init__(self, database):
        self.database = database

    def get_all_users(self):
        """Fetch all users - will fail with AttributeError"""
        # Query the database
        results = self.database.query("SELECT * FROM users")

        users = []
        for row in results:
            user = User(row["id"], row["name"])
            users.append(user)

        # This will cause AttributeError - database doesn't have close() method
        self.database.close()  # Should be disconnect()!

        return users
