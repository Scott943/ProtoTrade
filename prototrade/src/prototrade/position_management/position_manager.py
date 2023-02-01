# Create new thread that pulls from central data and checks if can execute open order
# every x seconds

import logging
import heapq
import traceback
from prototrade.models.dual_heap import DualHeap
from prototrade.exceptions.exceptions import InvalidOrderTypeException, InvalidOrderSideException, UnknownOrderIdException, MissingParameterException, ExtraneousParameterException, UnavailableSymbolException, InvalidPriceException, InvalidVolumeException
from prototrade.models.order import Order
import math
from threading import Thread
from copy import deepcopy
from prototrade.models.transaction import Transaction
import time
from collections import defaultdict
from threading import Lock
import datetime
import numpy as np

from prototrade.models.error_event import ErrorEvent

SYMBOL_REQUEST_TIMEOUT = 5
class PositionManager:
    def __init__(self, order_books_dict, order_books_dict_semaphore, stop_event, error_queue, exchange_num, subscribed_symbols, save_data_location):
        logging.info("L:DSJF:LDSFJL:DSFJ:LSF")
        self._order_books_dict = order_books_dict
        self._order_books_dict_semaphore = order_books_dict_semaphore
        self._stop_event = stop_event
        self._error_queue = error_queue
        self._exchange_num = exchange_num
        self._subscribed_symbols = subscribed_symbols
        self._save_data_location = save_data_location

        self._open_orders_polling_thread = None
        self._positions_map = defaultdict(int)
        self._open_orders = dict() # symbol name -> (bid heap, ask heap)
        self._transaction_history = []
        self._order_dict = dict() # order_id -> heap object
        self._largest_order_id = -1 #Initally no orders placed
        self._transaction_pnl = 0

        self._open_orders_polling_thread = None

        self._rolling_pnl_list = []
        self._rolling_position_dict = defaultdict(list)

        self._order_objects_lock = Lock() # have to acquire lock whenever accessing order_dict or open_orders
        self._rolling_pnl_list_lock = Lock() 
        self._positions_map_lock = Lock()
        self._transaction_pnl_lock = Lock()
        self._transaction_history_lock = Lock()
        self._rolling_position_dict_lock = Lock()
        

    def create_order(self, symbol, order_side, order_type, volume, price = None):
        # FOC: check if order can be executed immediately (don't add to open orders)
        # Limit: add order with limit price to open orders
        # Market: add order with inf bid price / 0 ask price
        if not self._open_orders_polling_thread:
            self._create_thread_to_poll_open_orders() #Start thread to poll open orders

        self._order_objects_lock.acquire()
        if symbol not in self._open_orders:
            # Create dual heap if this is the 1st order
            self._open_orders[symbol] = DualHeap()
            logging.info(f"Creating heap for {symbol}")

        dual_heap = self._open_orders[symbol]
        
        if price and not np.isreal(price):
            self.release_locks()
            raise TypeError(f"The price parameter given, {price}, must be an integer or float. {type(price)}")

        if not isinstance(volume,(int, np.integer)):
            self.release_locks()
            raise TypeError(f"The volume parameter given, {volume}, must be an integer.")

        if volume <= 0:
            raise InvalidVolumeException("Order volume must be greater than zero")

        if price and price < 0:
            raise InvalidPriceException("Order price must be zero or greater")

        if order_side == "bid":
            heap_to_use = dual_heap.bid_heap
        elif order_side == "ask":
            heap_to_use = dual_heap.ask_heap
        else:
            self.release_locks()
            raise InvalidOrderSideException(f"'{order_side}' is an invalid order side. Valid order sides: 'bid', 'ask'")

        if order_type in ["fok", "limit"] and not price:
            self.release_locks()
            raise MissingParameterException(f"Must include price as a parameter when inserting a {order_type} order in create_order")

        elif order_type == "market" and price:
            self.release_locks()
            raise ExtraneousParameterException("Price cannot be used as parameter when a market order type is specified in create_order")
            
        if symbol not in self._subscribed_symbols: # needs live data for symbol as otherwise cannot simulate execution 
            raise UnavailableSymbolException(f"Subscribe to symbol '{symbol}' before creating an order for '{symbol}'")

        if order_type == "fok":
            self.release_locks() # fok doesn't use heap so can release lock
            return self._handle_fok(symbol, order_side, volume, price)
        elif order_type == "limit":
            return self._handle_limit_order(heap_to_use, symbol, order_side, order_type, volume, price)
        elif order_type == "market":
            return self._handle_market_order(heap_to_use, symbol, order_side, order_type, volume)
        else:
            self.release_locks()
            raise InvalidOrderTypeException(f"'{order_type}' is an invalid order type. Valid order types: 'market', 'limit', 'fok'")

        # Need to add the order to dual heap, then add a entry in the _order_dict to that new object
        # As the key for the entry, create a new order_id
        # return newly created order_id

    def _insert_order(self, heap_to_use, symbol, order_side, order_type, volume, price):
        order_id = self._get_next_order_id()
        order = Order(order_id, symbol, order_side, order_type, volume, price)
        heapq.heappush(heap_to_use, order)
        self._order_dict[order_id] = order
        self._order_objects_lock.release()
        logging.info(f"Order with order_id {order_id} inserted")

        return order_id

    def _handle_fok(self, symbol, order_side, volume, price):
        self._order_books_dict_semaphore.acquire()

        if symbol not in self._order_books_dict:
            self._wait_for_symbol_to_arrive(symbol)

        quote_for_symbol = deepcopy(self._order_books_dict[symbol]) # get a copy of the current prices
        self._order_books_dict_semaphore.release()
        if order_side == "bid":
            best_ask_half_quote = quote_for_symbol.ask #match strategy bid against real ask
            if price >= best_ask_half_quote.price:
                return self._register_new_transaction(symbol, order_side, "fok", volume, best_ask_half_quote.price, time.time())
        else:
            best_bid_half_quote = quote_for_symbol.bid #match strategy bid against real ask
            if price <= best_bid_half_quote.price:
                return self._register_new_transaction(symbol, order_side, "fok", volume, best_bid_half_quote.price, time.time())
        
        return None # None if FOK order was killed

    def _handle_limit_order(self, heap_to_use, symbol, order_side, order_type, volume, price):
        return self._insert_order(heap_to_use, symbol, order_side, order_type, volume, price)

    def _handle_market_order(self, heap_to_use, symbol, order_side, order_type, volume):
        if order_side == "bid":
            return self._insert_order(heap_to_use, symbol, order_side, order_type, volume, math.inf)
        else:
            return self._insert_order(heap_to_use, symbol, order_side, order_type, volume, 0)


    def _wait_for_symbol_to_arrive(self, symbol):
        if symbol not in self._subscribed_symbols:
            self._order_books_dict_semaphore.release()
            self.release_locks()
            raise UnavailableSymbolException(f"In strategy {self._exchange_num + 1} requesting live data on symbol '{symbol}', but strategy is not subscribed to '{symbol}'")
        
        start_time = time.time()
        while symbol not in self._order_books_dict:
            self._order_books_dict_semaphore.release()
            time.sleep(0.2)
            logging.info(f"PM Waiting for {symbol} to come in")
            self._order_books_dict_semaphore.acquire()

            if time.time() - start_time > SYMBOL_REQUEST_TIMEOUT:
                self._order_books_dict_semaphore.release()
                self.release_locks()
                raise UnavailableSymbolException(
                    f"Symbol request timeout: strategy number {self._exchange_num + 1} cannot find requested symbol '{symbol}' from exchange. Check symbol exists & exchange is open.")

            if self._stop_event.is_set():
                self._order_books_dict_semaphore.release()
                self.release_locks()
                raise UnavailableSymbolException(
                    f"Interrupt while waiting for symbol '{symbol}' to arrive in strategy number {self._exchange_num + 1}")

    def cancel_order(self, order_id, volume_requested = None):
        # remove volume from order
        # if volume_requested > order_volume -> remove entire order
        if type(order_id) != int:
            raise TypeError(f"The order_id parameter given, {order_id}, must be an integer.")

        if volume_requested and type(volume_requested) != int:
            raise TypeError(f"The volume_requested parameter given, {volume_requested}, must be an integer.")

        self._order_objects_lock.acquire()
        if order_id not in self._order_dict:
            self.release_locks()
            raise UnknownOrderIdException(f"Order ID {order_id} unknown")
        
        order = self._order_dict[order_id]
        dual_heap = self._open_orders[order.symbol]

        if order.order_side == "bid":
            heap_to_use = dual_heap.bid_heap
        else:
            heap_to_use = dual_heap.ask_heap

        if not volume_requested or volume_requested >= order.volume:
            self._remove_from_heap(heap_to_use, order) #Remove from heap
            del self._order_dict[order_id] #Remove from order dict
            logging.info(f"{order_id} deleted")
        else:
            order.volume -= volume_requested
        
        self._order_objects_lock.release()

    def _remove_from_heap(self, heap_to_use, order):
        # Remove order from heap and re-heapify
        heap_to_use.remove(order)
        heapq.heapify(heap_to_use)

    def get_orders(self, symbol = None):
        # dictionary of order_id -> Order Object

        self._order_objects_lock.acquire()
        if symbol:
            # Only return orders for requested symbol
            ret = {k:v for k,v in self._order_dict.items() if v.symbol == symbol} 
        else:
            ret = self._order_objects_lock.acquire()

        self._order_objects_lock.release()
        return ret 

    # Next order ID to assign
    def _get_next_order_id(self):
        self._largest_order_id += 1
        return self._largest_order_id

    def _get_heap(self, symbol):
        self._order_objects_lock.acquire()
        heap = str(self._open_orders[symbol])
        self._order_objects_lock.release()
        return heap

    def get_strategy_best_bid(self, symbol):
        self._order_objects_lock.acquire()
        if symbol not in self._open_orders:
            self._order_objects_lock.release()
            return None #If no orders ever placed, we can just return None

        bid_heap = self._open_orders[symbol].bid_heap
        if bid_heap:
            best_bid = deepcopy(bid_heap[0])
        else:
            best_bid = None

        self._order_objects_lock.release()
        return best_bid

    def get_strategy_best_ask(self, symbol):
        self._order_objects_lock.acquire()
        if symbol not in self._open_orders:
            self._order_objects_lock.release()
            return None #If no orders ever placed, we can just return None

        ask_heap = self._open_orders[symbol].ask_heap
        if ask_heap:
            best_ask = deepcopy(ask_heap[0])
        else:
            best_ask = None

        self._order_objects_lock.release()
        return best_ask

    def _create_thread_to_poll_open_orders(self):
        self._open_orders_polling_thread = Thread(
            target=self._start_thread)  
        self._open_orders_polling_thread.start()

    def _start_thread(self):
        try:
            self._check_for_executable_orders()
        except Exception as e: # if exception in thread then release all locks and place error on queue
            self.release_locks() 
            handle_error(self._error_queue, self._exchange_num)

    def release_locks(self):
        logging.info("Releasing all PM locks")
        if self._order_objects_lock.locked():
            self._order_objects_lock.release()

        if self._rolling_pnl_list_lock.locked():
            self._rolling_pnl_list_lock.release()
        
        if self._positions_map_lock.locked():
            self._positions_map_lock.release()
        
        if self._transaction_pnl_lock.locked():
            self._transaction_pnl_lock.release
        
        if self._transaction_history_lock.locked():
            self._transaction_history_lock.release()

    def _check_for_executable_orders(self):
        logging.info("Starting open order polling thread")
        last_pnl_time = time.time()
        while not self._stop_event.is_set():
            self._order_books_dict_semaphore.acquire()
            for symbol in self._open_orders:
                if symbol not in self._order_books_dict: 
                    self._wait_for_symbol_to_arrive(symbol) 
            order_books_snapshot = deepcopy(self._order_books_dict) # get a copy of the current prices
            self._order_books_dict_semaphore.release()

            self._order_objects_lock.acquire()
            for symbol, dual_heap in self._open_orders.items(): # look through every symbol's dual heap 
                symbol_quote = order_books_snapshot[symbol]
                self.execute_any_bid_orders(symbol, dual_heap.bid_heap, symbol_quote.ask)
                self.execute_any_ask_orders(symbol, dual_heap.ask_heap, symbol_quote.bid)
            self._order_objects_lock.release()

            if time.time() - last_pnl_time > 1:
                timestamp = datetime.datetime.now()
                pnl = self.get_pnl()
                positions = deepcopy(self._positions_map)
                self._rolling_pnl_list_lock.acquire()
                self._rolling_pnl_list.append([timestamp, pnl])
                self._rolling_pnl_list_lock.release()
                self._rolling_position_dict_lock.acquire()
                self._rolling_position_dict[symbol].append([timestamp, positions[symbol]])
                self._rolling_position_dict_lock.release()
                last_pnl_time = time.time()

            time.sleep(0.3)
  
        logging.info("Open order polling thread finished")

    def get_pnl_over_time(self):
        self._rolling_pnl_list_lock.acquire()
        pnl = deepcopy(self._rolling_pnl_list)
        self._rolling_pnl_list_lock.release()
        return pnl

    def get_positions_over_time(self, symbol = None):
        self._rolling_position_dict_lock.acquire()
        if symbol:
            positions = deepcopy(self._rolling_position_dict[symbol])
        else:
            positions = deepcopy(self._rolling_position_dict)
        self._rolling_position_dict_lock.release()
        return positions

    def _register_new_transaction(self, symbol, order_side, order_type, volume, price, time):
        transaction = Transaction(symbol, order_side, order_type, volume, price, time)
        self._transaction_history_lock.acquire()
        self._transaction_history.append(transaction)
        self._transaction_history_lock.release()
        self._positions_map_lock.acquire()
        if order_side == "bid":
            self._positions_map[symbol] += volume
        else:
            self._positions_map[symbol] -= volume
        self._positions_map_lock.release()

        transaction_amount = transaction.price * transaction.volume

        self._transaction_pnl_lock.acquire()
        if transaction.order_side == "bid":
            self._transaction_pnl -= transaction_amount # bid side so lost money and gained assets
        else:
            self._transaction_pnl += transaction_amount # ask side so gained money and lost assets

        self._transaction_pnl_lock.release()
        return transaction

    def execute_any_bid_orders(self, symbol, bid_heap, live_best_ask_half_quote):
        while bid_heap and bid_heap[0].price >= live_best_ask_half_quote.price:
            executed = heapq.heappop(bid_heap)

            logging.info(f"EXECUTED bid order at price {live_best_ask_half_quote.price}: {executed}")

            self._register_new_transaction(symbol, executed.order_side, executed.order_type, executed.volume, live_best_ask_half_quote.price, time.time())
            del self._order_dict[executed.order_id]

    def execute_any_ask_orders(self, symbol, ask_heap, live_best_bid_half_quote):
        while ask_heap and ask_heap[0].price <= live_best_bid_half_quote.price:
            executed = heapq.heappop(ask_heap)

            logging.info(f"EXECUTED ask order at price {live_best_bid_half_quote.price}: {executed}")
            
            self._register_new_transaction(symbol, executed.order_side, executed.order_type, executed.volume, live_best_bid_half_quote.price, time.time())
            del self._order_dict[executed.order_id]

    def get_positions(self, symbol_filter = None):
        self._positions_map_lock.acquire()
        if symbol_filter:
            pos = self._positions_map[symbol_filter] # int of positions
        else:
            pos = deepcopy(self._positions_map)
        self._positions_map_lock.release()
        return pos

    def get_transactions(self, symbol_filter = None):
        self._transaction_history_lock.acquire()
        if symbol_filter:
            trans =  deepcopy([trans for trans in self._transaction_history if trans.symbol == symbol_filter])
        else:
            trans = deepcopy(self._transaction_history)
        self._transaction_history_lock.release()
        return trans

    def get_realised_pnl(self):
        self._transaction_pnl_lock.acquire()
        val = self._transaction_pnl
        self._transaction_pnl_lock.release()
        return val

    def get_pnl(self):
        # for each transaction: price * -volume if bid (lost money gained assets). price * volume if ask (gained money lost assets)
        # for each current position: if position_vol > 0: best_ask * position_vol, if position_vol < 0: best_bid * position_vol
        
        pnl = self._transaction_pnl # pnl acquired by the transaction history
        # atomic so doesn't need a lock

        self._order_books_dict_semaphore.acquire()
        for symbol in self._positions_map:
            if symbol not in self._order_books_dict:
                self._wait_for_symbol_to_arrive(symbol)
        order_books_snapshot = deepcopy(self._order_books_dict) # get a copy of the current prices

        self._order_books_dict_semaphore.release()

        # add all unrealised pnl from current positions
        self._positions_map_lock.acquire()
        positions = self._positions_map.items()
        self._positions_map_lock.release()
        for symbol, amount in positions:
            if amount > 0:
                pnl += order_books_snapshot[symbol].bid.price * amount # the money obtained if all shares were sold at best bid price
            elif amount < 0:
                pnl += order_books_snapshot[symbol].ask.price * amount # the money spent to obtain all shares back at best ask price

        return pnl

    def hack_out(self):
        self._order_objects_lock.acquire()
        for order_id in self._order_dict:
            self.cancel_order(order_id)
        self._order_objects_lock.release()
    
# Thread that pseudo-executes orders must give a transaction price of the corresponding bid/ask price, not the limit price 
# MATCHING ORDERS AGAINST OWN ORDERS?

def handle_error(error_queue, exchange_num):
    exception_info = traceback.format_exc() # Get a string with full original stack trace
    error_queue.put(ErrorEvent(exchange_num, exception_info))
    logging.error(f"Process PM {exchange_num} EXCEPTION")