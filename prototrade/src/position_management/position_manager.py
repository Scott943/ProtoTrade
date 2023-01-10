# Create new thread that pulls from central data and checks if can execute open order
# every x seconds

import logging
import heapq
from models.dual_heap import DualHeap
from exceptions.exceptions import InvalidOrderTypeException, InvalidOrderSideException, UnknownOrderIdException
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
            logging.info(f"Creating heap for {symbol}")

        dual_heap = self._open_orders[symbol]

        if order_side == "bid":
            heap_to_use = dual_heap.bid_heap
        elif order_side == "ask":
            heap_to_use = dual_heap.ask_heap
        else:
            raise InvalidOrderSideException(f"'{order_side}' is an invalid order side. Accepted order sides: 'bid', 'ask'")

        if order_type == "fok":
            return self._handle_fok(symbol, order_side, volume, price)
        elif order_type == "limit":
            return self._handle_limit_order(heap_to_use, symbol, order_side, order_type, volume, price)
        elif order_type == "market":
            return self._handle_market_order(heap_to_use, symbol, order_side, order_type, volume)
        else:
            raise InvalidOrderTypeException(f"'{order_type}' is an invalid order type. Accepted order types: 'market', 'limit', 'fok'")

        # Need to add the order to dual heap, then add a entry in the _order_dict to that new object
        # As the key for the entry, create a new order_id

        # return newly created order_id

    def _insert_order(self, heap_to_use, symbol, order_side, order_type, volume, price):
        # test that price is an int etc
        order = Order(symbol, order_side, order_type, volume, price)
        heapq.heappush(heap_to_use, order)
        order_id = self._get_next_order_id()
        self._order_dict[order_id] = order
        logging.info(f"Order with order_id {order_id} inserted")

        return order_id

    def _handle_limit_order(self, heap_to_use, symbol, order_side, order_type, volume, price):
        return self._insert_order(heap_to_use, symbol, order_side, order_type, volume, price)

    def _handle_market_order(self, heap_to_use, symbol, order_side, order_type, volume):
        if order_side == "bid":
            return self._insert_order(heap_to_use, symbol, order_side, order_type, volume, math.inf)
        else:
            return self._insert_order(heap_to_use, symbol, order_side, order_type, volume, 0)

    def cancel_order(self, order_id, volume_requested = None):
        # remove volume from order
        # if volume_requested > order_volume -> remove entire order
        if order_id not in self._order_dict:
            raise UnknownOrderIdException(f"Order ID {order_id} unknown")
        
        order = self._order_dict[order_id]
        dual_heap = self._open_orders[order.symbol]

        if order.order_side == "bid":
            heap_to_use = dual_heap.bid_heap
        else:
            heap_to_use = dual_heap.ask_heap

        if not volume_requested or volume_requested >= order.volume:
            self._remove_from_heap(self, heap_to_use, order) #Remove from heap
            del self._order_dict[order_id] #Remove from order dict
        else:
            order.volume -= volume_requested

    def _remove_from_heap(self, heap_to_use, order):
        # Remove order from heap and re-heapify
        heap_to_use.remove(order)
        heapq.heapify(heap_to_use)

    def get_orders(self, symbol = None):
        # dictionary of order_id -> Order Object
        if symbol:
            return self._get_heap(symbol)
        return self._order_dict.items()

        # handle if a symbol is specified
        
    def _handle_fok(self, order_side, volume, price): 
        pass

    def _get_next_order_id(self):
        self._largest_order_id += 1
        return self._largest_order_id

    def _get_heap(self, symbol):
        return str(self._open_orders[symbol])

    def get_strategy_best_bid(self, symbol):
        return self._open_orders[symbol].bid_heap[0]

    def get_strategy_best_ask(self, symbol):
        return self._open_orders[symbol].ask_heap[0]


    # dict of id -> order object

    # to return orders for a symbol, filter orders for symbol

    # prioritise checking heap every x seconds




    
# Thread that pseudo-executes orders must give a transaction price of the corresponding bid/ask price, not the limit price 

# MATCHING ORDERS AGAINST OWN ORDERS?