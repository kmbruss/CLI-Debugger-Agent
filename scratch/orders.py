from inventory import Warehouse

def process_order(warehouse, order):
    for item, qty in order.items():
        remaining = warehouse.remove_stock(item, qty)
        print(f"{item}: {remaining} left")

def fulfill(warehouse):
    pending_order = {"widgets": 3, "sprockets": 2}
    process_order(warehouse, pending_order)

if __name__ == "__main__":
    wh = Warehouse()
    fulfill(wh)