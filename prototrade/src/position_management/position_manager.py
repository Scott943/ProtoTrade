# Create new thread that pulls from central data and checks if can execute open order
# every x seconds

import logging
import heapq
from models.dual_heap import DualHeap
from exceptions.exceptions import InvalidOrderTypeException, InvalidOrderSideException
from models.order import Order
import math
class PositionManager:
    def __init__(self):
        self._positions_map = dict()
        self._open_orders = dict() # symbol name -> (bid heap, ask heap)
        self._transaction_history = []
        self._order_dict = dict() # order_id -> heap object
        self._largest_order_id = -1 #Initally no orders placed

    def create_order(self, symbol, order_side, order_type, volume, price = None):
        # FOC: check if order can be executed immediately (don't add to open orders)
        # Limit: add order with limit price to open orders
        # Market: add order with inf bid price / 0 ask price
        if symbol not in self._open_orders:
            # Create dual heap if this is the 1st order
            self._open_orders[symbol] = DualHeap()

        if order_side == "bid":
            heap_to_use = self._open_orders[symbol].bid_heap
        elif order_side == "ask":
            heap_to_use = self._open_orders[symbol].ask_heap
        else:
            raise InvalidOrderSideException(f"'{order_side}' is an invalid order side. Accepted order sides: 'bid', 'ask'")

        if order_type == "fok":
            self._handle_fok(symbol, order_side, volume, price)
        elif order_type == "limit":
            self._handle_limit_order(heap_to_use, symbol, order_side, order_type, volume, price)
        elif order_type == "market":
            self._handle_market_order(heap_to_use, symbol, order_side, order_type, volume)
        else:
            raise InvalidOrderTypeException(f"'{order_type}' is an invalid order type. Accepted order types: 'market', 'limit', 'fok'")

        # Need to add the order to dual heap, then add a entry in the _order_dict to that new object
        # As the key for the entry, create a new order_id

        # return newly created order_id

    def _insert_order(self, heap_to_use, symbol, order_side, order_type, volume, price):
        # test that price is an int etc
        order = Order(symbol, order_side, order_type, volume, price)
        heapq.heappush(heap_to_use, order)
        self._order_dict[self._get_next_order_id()] = order

    def _handle_limit_order(self, heap_to_use, symbol, order_side, order_type, volume, price):
        self._insert_order(heap_to_use, symbol, order_side, order_type, volume, price)

    def _handle_market_order(self, heap_to_use, symbol, order_side, order_type, volume):
        if order_side == "bid":
            self._insert_order(heap_to_use, symbol, order_side, order_type, volume, math.inf)
        else:
            self._insert_order(heap_to_use, symbol, order_side, order_type, volume, 0)


    def cancel_order_by_id(self, id, volume = "ALL"):
        # remove volume from order
        # if volume_requested > order_volume -> remove entire order
        pass

    def get_orders(self, symbol = None):
        # dictionary of order_id -> Order Object
        if not symbol:
            return self._order_dict

        # handle if a symbol is specified
        

    def _handle_fok(self, order_side, volume, price): 
        pass

    def _get_next_order_id(self):
        self._largest_order_id += 1
        return self._largest_order_id



    # dict of id -> order object

    # to return orders for a symbol, filter orders for symbol

    # prioritise checking heap every x seconds




    
# Thread that pseudo-executes orders must give a transaction price of the corresponding bid/ask price, not the limit price 

# MATCHING ORDERS AGAINST OWN ORDERS?