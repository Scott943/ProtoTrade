# Create new thread that pulls from central data and checks if can execute open order
# every x seconds

import logging
import heapq
from models.dual_heap import DualHeap
class PositionManager:
    def __init__(self):
        self._positions_map = dict()
        self._open_orders = dict() # symbol name -> (bid heap, ask heap)
        self._transaction_history = []

    def create_order(self, symbol, side, order_type):
        # FOC: check if order can be executed immediately (don't add to open orders)
        # Limit: add order with limit price to open orders
        # Market: add order with inf bid price / 0 ask price
        if symbol not in self._open_orders:
            self._open_orders[symbol] = DualHeap()

    
# Thread that pseudo-executes orders must give a transaction price of the corresponding bid/ask price, not the limit price 

# MATCHING ORDERS AGAINST OWN ORDERS?