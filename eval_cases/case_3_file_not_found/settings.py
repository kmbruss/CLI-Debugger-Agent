"""
Settings module for case 3
"""

class Settings:
    def __init__(self):
        self.config = {
            "data_path": "data/input.csv",
            "output_path": "data/output.json",
            "log_level": "INFO"
        }

    def get_config(self):
        return self.config

    def get_data_path(self):
        return self.config["data_path"]
