import copy 

class Exchange:

    def __init__(self, order_books_dict, order_books_dict_semaphore, position_manager):
        self.order_books_dict = order_books_dict
        self.order_books_dict_semaphore = order_books_dict_semaphore
        self.position_manager = position_manager
        self.subscribed_symbols = set()

    def get_subscribed_books(self):
        quote_dict = {}
        self.order_books_dict_semaphore.acquire()

        for symbol in self.subscribed_symbols:
            quote_dict[symbol] = copy.deepcopy(self.order_books_dict[symbol])

        self.order_books_dict_semaphore.release()

        return quote_dict

    def get_subscriptions(self):
        return self.subscribed_symbols

    def subscribe(self, symbol):
        self.subscribed_symbols.add(symbol)

    def unsubscribe(self, symbol):
        if symbol in self.subscribed_symbols:
            self.subscribed_symbols.remove(symbol)
