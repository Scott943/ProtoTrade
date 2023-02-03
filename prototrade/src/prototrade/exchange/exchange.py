import copy
from prototrade.models.subscription_event import SubscriptionEvent, SubscribeType
import time
from prototrade.exceptions.exceptions import UnavailableSymbolException, SubscriptionException
import logging
from prototrade.position_management.position_manager import PositionManager
from copy import deepcopy
from functools import wraps

SYMBOL_REQUEST_TIMEOUT = 8
class Exchange:
    """
    To interact with the framework, the user calls functions in the Exchange object.
    Allows user to place orders, retrieve information on transactions/positions, (un)subscribe to stock data, and retrieve the latest prices for subscribed stocks.
    """

    def __init__(self, order_books_dict, order_books_dict_semaphore, subscription_queue, error_queue, exchange_num, stop_event, shared_rest_api, save_data_location):
        """
        Initalises an exchange object (initialisation performed automatically in the VirutalExchange class)
        """
        
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

    def get_subscribed_quotes(self):
        """Retrieves the latest quotes for the symbols that are subscribed to.
        e.g. to access latest bid price for AAPL, use exchange.get_subscribed_quotes()["AAPL"].bid.price
        e.g. to access latest volume at ask price for AAPL, use exchange.get_subscribed_quotes()["AAPL"].ask.volume

        :return: A dictionary where the key is a symbol and the value is the corresponding quote object.
        :rtype: *dict*\ (\ *str* -> :py:class:`Quote<prototrade.models.quotes.Quote>`)
        """
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
        """Returns a set symbols that the strategy is currently subscribed to

        :return: set of symbols that the strategy is currently subscribed to
        :rtype: *set*
        """
        return deepcopy(self._subscribed_symbols)

    def subscribe(self, symbol):
        """Subscribes to the specified symbol.
        Once a symbol is subscribed to, market data for that symbol will be avaiable using the get_subscribed_quotes() member function

        :param symbol: The symbol to subscribe to
        :type symbol: *str*
        """
        self._subscription_queue.put(
            SubscriptionEvent(symbol, SubscribeType.SUBSCRIBE, self.exchange_num))
        self._subscribed_symbols.add(symbol)

    def unsubscribe(self, symbol):
        """Unsubscribes from a symbol. Data for the specified symbol will no longer be subscribed to.

        :param symbol: The symbol to unsubscribe from
        :type symbol: *str*
        :raises SubscriptionException: If the strategy is not currently subscribed to the specified symbol, this exception will be thrown
        """
        if symbol in self._subscribed_symbols:
            self._subscription_queue.put(
                SubscriptionEvent(symbol, SubscribeType.UNSUBSCRIBE, self.exchange_num))
            self._subscribed_symbols.remove(symbol)
        else:
            raise SubscriptionException(
                f"Strategy {self.exchange_num + 1} attempted to unsubscribe from a symbol that was not subscribed to")

    def is_running(self):
        """Check whether the framework is still running. If the user exits or any strategy encounters an exception, this will return 'False'
        This should be used in the main 'while' loop condition for the user strategy. This way, the user can perform clearup operations or data analysis 
        operations after their strategy has finished execution.

        :return: A boolean value representing whether the framework is still running
        :rtype: *bool*
        """
        return not self._stop_event.is_set()

    # Have to create pos manager after passing exchange to process as pos manager contains an unpickleable object
    def position_manager_decorator(func):
        @wraps(func) # ensures docstrings correctly updated
        def wrapper(self, *args):
            if not self._position_manager:
                self._position_manager = PositionManager(self._order_books_dict, self._order_books_dict_semaphore, self._stop_event, self._error_queue, self.exchange_num, self._subscribed_symbols, self._save_data_location)
            return func(self, *args)
        
        return wrapper

    # We could use *args here, but we include the complete function signature for documentation reasons

    @position_manager_decorator
    def create_order(self, symbol, order_side, order_type, volume, price = None):
        """Submit an order to the framework. When a *'market'* or *'limit'* order is submitted, the framework will repeatedly check whether it can be executed.
        When a *'fok'* (Fill-Or-Kill) order is submitted, the framework will check whether it can be executed once. If it cannot be executed at the specified price, the order will be cancelled.

        :param symbol: The symbol to place the order for
        :type symbol: *str*
        :param order_side: The side of the order book to place the order in. Either *'bid'* or *'ask'*.
        :type order_side: *str*
        :param order_type: The type of order to submit. One of *'market'*, *'limit'*, *'fok'*. If *'limit'* or *'fok'* specified, then the price parameter must also be specified
        :type order_type: *str*
        :param volume: The volume of the order. Must be > 0
        :type volume: *int*
        :param price: The limit price / Fill-Or-Kill price, defaults to *None*
        :type price: *float* | *int*, optional
        :return: The ID of the order created
        :rtype: *int*
        """
        return self._position_manager.create_order(symbol, order_side, order_type, volume, price)

    @position_manager_decorator
    def get_orders(self, symbol = None):
        """Retrive the open orders for a strategy. If the symbol argument is specified, then only retrieves orders for that particular symbol.
        Otherwise, all open orders for the strategy are returned.

        :param symbol: The symbol to retrieve open orders for, defaults to *None*
        :type symbol: *str*, optional
        :return: The dictionary where the key is the order_id and the value is the corresponding :py:class:`Order<prototrade.models.order.Order>` object
        :rtype: *dict*\ (\ *int* -> :py:class:`Order<prototrade.models.order.Order>`)
        """
        return self._position_manager.get_orders(symbol)

    @position_manager_decorator
    def get_strategy_best_bid(self, symbol):
        """Get the current best bid in the strategy's open orders for a specified symbol. Simply, this is the highest price that the strategy is 'willing to pay' for a particular stock.
        In the framework implementation, this reads the top of bid heap for the particular symbol.

        :param symbol: symbol
        :type symbol: *str*
        :return: A :py:class:`Order<prototrade.models.order.Order>` object corresponding to the best bid for the calling strategy
        :rtype: :py:class:`Order<prototrade.models.order.Order>`
        """
        return self._position_manager.get_strategy_best_bid(symbol)

    @position_manager_decorator
    def get_strategy_best_ask(self, symbol):
        """Get the current best ask in the strategy's open orders for a specified symbol. Simply, this is the lowest price that the strategy is 'willing to sell' a particular stock at.
        In the framework implementation, this reads the top of ask heap for the particular symbol.

        :param symbol: symbol
        :type symbol: *str*
        :return: A :py:class:`Order<prototrade.models.order.Order>` object corresponding to the best ask for the calling strategy
        :rtype: :py:class:`Order<prototrade.models.order.Order>`
        """
        return self._position_manager.get_strategy_best_ask(symbol)

    @position_manager_decorator
    def cancel_order(self, order_id, volume_requested = None):
        """Removes the order with order_id from the list of open orders.

        :param order_id: The id of the order to remove
        :type order_id: *int*
        :param volume_requested: The amount of the order to cancel (allows for partial cancellation). If parameter not specified, the entire order will be cancelled, defaults to *None*
        :type volume_requested: *int*\ , optional
        """
        self._position_manager.cancel_order(order_id, volume_requested)

    @position_manager_decorator
    def get_positions(self, symbol_filter = None):
        """Retrieve a dictionary of the strategy's current positions held. Here, a negative value in the dictionary implies a short position is being held.

        :param symbol_filter: The symbol to retrieve positions data for. If not symbol specified, retrieves positions for all stocks held, defaults to *None*
        :type symbol_filter: *int*, optional
        :return: A dictionary where the key is a symbol and the value is the corresponding number of lots held
        :rtype: *dict*\ (\ *str* -> *int*)
        """
        return self._position_manager.get_positions(symbol_filter)

    @position_manager_decorator
    def get_transactions(self, symbol_filter = None):
        """Get a list of all previous transactions made (for a particular symbol)

        :param symbol_filter: If specified, returns transactions for a particular symbol. Otherwise returns all transactions in chronological order, defaults to *None*
        :type symbol_filter: *str*, optional
        :return: A list of transactions
        :rtype: *list*\ (:py:class:`Transaction<prototrade.models.transaction.Transaction>`)
        """
        return self._position_manager.get_transactions(symbol_filter)

    @position_manager_decorator
    def get_pnl(self):
        """Retrieves the Profit-And-Loss for the calling strategy.

        :return: PnL
        :rtype: *int*
        """
        return self._position_manager.get_pnl()

    @position_manager_decorator
    def get_pnl_over_time(self):
        """Retrieves the PnL for a strategy over several time-intervals (since the strategy started)

        :return: A list of (*timestamp*, *int*) where each entry indicated the PnL at the specified timestamp
        :rtype: *list*\ (\ *tuple*\ (\ *timestamp*\ , \ *int*\ ))
        """
        return self._position_manager.get_pnl_over_time()

    @position_manager_decorator
    def get_positions_over_time(self, symbol = None):
        """Retrieves the positions dictionary over several time-intervals (since the strategy started)

        :param symbol: The symbol to return positions over time for. If not specified, returns a dictionary of every symbol, defaults to *None*
        :type symbol: *str*, optional
        :return: a dictionary where the key is a symbol and the value is a list of positions over time
        :rtype: *dict*\ (\ *str*\ , *list*\ (\ *tuple*\ (\ *timestamp*\ , *int*\ )))
        """
        return self._position_manager.get_positions_over_time(symbol)

    