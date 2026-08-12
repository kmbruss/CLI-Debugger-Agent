"""
Database module for case 5
"""

class Database:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connected = False

    def connect(self):
        """Establish database connection"""
        print(f"Connecting to {self.connection_string}")
        self.connected = True

    def disconnect(self):
        """Close database connection"""
        self.connected = False

    def query(self, sql):
        """Execute a query"""
        if not self.connected:
            raise Exception("Database not connected")
        # Mock query results
        return [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
