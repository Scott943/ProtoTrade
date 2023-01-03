import copy 

class Exchange:

    def __init__(self, order_books_dict, order_books_dict_semaphore, position_manager):
        self._order_books_dict = order_books_dict
        self._order_books_dict_semaphore = order_books_dict_semaphore
        self._position_manager = position_manager
        self._subscribed_symbols = set()

    def get_subscribed_books(self):
        quote_dict = {}
        self._order_books_dict_semaphore.acquire()

        for symbol in self._subscribed_symbols:
            quote_dict[symbol] = copy.deepcopy(self._order_books_dict[symbol])

        self._order_books_dict_semaphore.release()

        return quote_dict

    def get_subscriptions(self):
        return self._subscribed_symbols

    def subscribe(self, symbol):
        self._subscribed_symbols.add(symbol)

    def unsubscribe(self, symbol):
        if symbol in self._subscribed_symbols:
            self._subscribed_symbols.remove(symbol)
