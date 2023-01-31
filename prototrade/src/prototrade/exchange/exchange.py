import copy
from prototrade.models.subscription_event import SubscriptionEvent, SubscribeType
import time
from prototrade.exceptions.exceptions import UnavailableSymbolException, SubscriptionException
import logging
from prototrade.position_management.position_manager import PositionManager
from copy import deepcopy

SYMBOL_REQUEST_TIMEOUT = 8
class Exchange:

    def __init__(self, order_books_dict, order_books_dict_semaphore, subscription_queue, error_queue, exchange_num, stop_event, shared_rest_api, save_data_location):
        self._order_books_dict = order_books_dict
        self._order_books_dict_semaphore = order_books_dict_semaphore
        self._subscription_queue = subscription_queue
        self._error_queue = error_queue
        self.exchange_num = exchange_num
        self._stop_event = stop_event
        self.historical = shared_rest_api
        self._save_data_location = save_data_location

        self._position_manager = None
        self._subscribed_symbols = set()

    def get_subscribed_books(self):
        quote_dict = {}
        self._order_books_dict_semaphore.acquire()

        for symbol in self._subscribed_symbols:

            # If the symbol has been subscribed to but has not arrived, then wait
            if symbol not in self._order_books_dict:
                self._wait_for_symbol_to_arrive(symbol)

            # Transfer quote for symbol over to quote_dict
            quote_dict[symbol] = copy.deepcopy(self._order_books_dict[symbol])

        self._order_books_dict_semaphore.release()
        return quote_dict

    def _wait_for_symbol_to_arrive(self, symbol):
        start_time = time.time()
        while symbol not in self._order_books_dict:
            self._order_books_dict_semaphore.release()
            time.sleep(0.2)
            logging.info(f"{self.exchange_num} Waiting for {symbol} to come in")
            self._order_books_dict_semaphore.acquire()

            if time.time() - start_time > SYMBOL_REQUEST_TIMEOUT:
                raise UnavailableSymbolException(
                    f"Symbol request timeout: strategy number {self.exchange_num + 1} cannot find requested symbol '{symbol}' from exchange. Check symbol exists & exchange is open.")

            if self._stop_event.is_set():
                raise UnavailableSymbolException(
                    f"Interrupt while waiting for symbol '{symbol}' to arrive in strategy number {self.exchange_num + 1}")

    def get_subscriptions(self):
        return deepcopy(self._subscribed_symbols)

    def subscribe(self, symbol):
        self._subscription_queue.put(
            SubscriptionEvent(symbol, SubscribeType.SUBSCRIBE, self.exchange_num))
        self._subscribed_symbols.add(symbol)

    def unsubscribe(self, symbol):
        if symbol in self._subscribed_symbols:
            self._subscription_queue.put(
                SubscriptionEvent(symbol, SubscribeType.UNSUBSCRIBE, self.exchange_num))
            self._subscribed_symbols.remove(symbol)
        else:
            raise SubscriptionException(
                f"Strategy {self.exchange_num + 1} attempted to unsubscribe from a symbol that was not subscribed to")

    def is_running(self):
        return not self._stop_event.is_set()

    # Have to create pos manager after passing exchange to process as pos manager contains an unpickleable object
    def position_manager_decorator(func):
        def wrapper(self, *args):
            if not self._position_manager:
                logging.info("L:DSJF:LDSFJL:DSFJ:LSF")
                self._position_manager = PositionManager(self._order_books_dict, self._order_books_dict_semaphore, self._stop_event, self._error_queue, self.exchange_num, self._subscribed_symbols, self._save_data_location)
            return func(self, *args)
        return wrapper

    @position_manager_decorator
    def create_order(self, *args):
        return self._position_manager.create_order(*args)

    @position_manager_decorator
    def get_orders(self, *args):
        return self._position_manager.get_orders(*args)

    @position_manager_decorator
    def print_heap(self, *args):
        self._position_manager.print_heap(*args)

    @position_manager_decorator
    def get_strategy_best_bid(self, *args):
        return self._position_manager.get_strategy_best_bid(*args)

    @position_manager_decorator
    def get_strategy_best_ask(self, *args):
        return self._position_manager.get_strategy_best_ask(*args)

    @position_manager_decorator
    def cancel_order(self, *args):
        self._position_manager.cancel_order(*args)

    @position_manager_decorator
    def get_positions(self, *args):
        return self._position_manager.get_positions(*args)

    @position_manager_decorator
    def get_transactions(self, *args):
        return self._position_manager.get_transactions(*args)

    @position_manager_decorator
    def get_pnl(self, *args):
        return self._position_manager.get_pnl(*args)

    @position_manager_decorator
    def get_pnl_over_time(self, *args):
        return self._position_manager.get_pnl_over_time(*args)

    @position_manager_decorator
    def get_positions_over_time(self, *args):
        return self._position_manager.get_positions_over_time(*args)

    