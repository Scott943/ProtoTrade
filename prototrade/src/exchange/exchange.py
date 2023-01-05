import copy 
from models.subscription_event import SubscriptionEvent, SubscribeType
import time
from exceptions.exceptions import UnavailableSymbolException, SubscriptionException

class Exchange:

    def __init__(self, order_books_dict, order_books_dict_semaphore, position_manager, subscription_queue, exchange_num):
        self._order_books_dict = order_books_dict
        self._order_books_dict_semaphore = order_books_dict_semaphore
        self._position_manager = position_manager
        self._subscription_queue = subscription_queue
        self._exchange_num = exchange_num

        self._subscribed_symbols = set()

    def get_subscribed_books(self):
        quote_dict = {}
        self._order_books_dict_semaphore.acquire()

        for symbol in self._subscribed_symbols:

            # If the symbol has been subscribed to but has not arrived, 
            if symbol not in self._order_books_dict:
                self._busy_wait_for_symbol_to_arrive(symbol)

            quote_dict[symbol] = copy.deepcopy(self._order_books_dict[symbol])

        self._order_books_dict_semaphore.release()

        return quote_dict

    def _busy_wait_for_symbol_to_arrive(self, symbol):
        start_time = time.time()
        while symbol not in self._order_books_dict:
            self._order_books_dict_semaphore.release()
            time.sleep(0.2)
            print(f"{self._exchange_num} Waiting for {symbol} to come in")
            self._order_books_dict_semaphore.acquire()

            if time.time() - start_time > 4:
                raise UnavailableSymbolException(
                    f"Cannot find {symbol} from exchange")

    def get_subscriptions(self):
        return self._subscribed_symbols

    def subscribe(self, symbol):
        self._subscription_queue.put(
            SubscriptionEvent(symbol, SubscribeType.SUBSCRIBE, self._exchange_num))
        self._subscribed_symbols.add(symbol)

    def unsubscribe(self, symbol):
        # THROW if no subscribed to symbol?
        if symbol in self._subscribed_symbols:
            self._subscription_queue.put(
                SubscriptionEvent(symbol, SubscribeType.UNSUBSCRIBE, self._exchange_num))
            self._subscribed_symbols.remove(symbol)
        else:
            raise SubscriptionException(
                f"Strategy {self._exchange_num} attempted to unsubscribe from a symbol that was not subscribed to")
        
        
