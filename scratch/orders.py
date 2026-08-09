from inventory import Warehouse
from config import build_order

def process_order(warehouse, order):
    for item, qty in order.items():
        remaining = warehouse.remove_stock(item, qty)
        print(f"{item}: {remaining} left")

def fulfill(warehouse):
    pending_order = build_order()
    process_order(warehouse, pending_order)