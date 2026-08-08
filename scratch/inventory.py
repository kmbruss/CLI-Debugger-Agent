class Warehouse:
    def __init__(self):
        self.stock = {"widgets": 10, "gadgets": 5}

    def remove_stock(self, item, qty):
        self.stock[item] -= qty
        return self.stock[item]