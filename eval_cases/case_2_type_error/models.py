"""
Data models for case 2
"""

class DataModel:
    def __init__(self, records):
        self.records = records
        self.total = 0

    def get_records(self):
        return self.records

    def calculate_total(self):
        for record in self.records:
            self.total += record["value"]
        return self.total
