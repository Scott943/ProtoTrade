
class PriceUpdater:
    def __init__(self, order_books_dict, order_books_dict_semaphore, num_strategies, stop_event):
        self.order_books_dict = order_books_dict
        self.order_books_dict_semaphore = order_books_dict_semaphore
        self.num_strategies = num_strategies
        self.stop_event = stop_event

    def update_price(self, symbol, quote):
        if self.stop_event.is_set():
            return

        for _ in range(self.num_strategies):
            # acquire all so no readers can access
            self.order_books_dict_semaphore.acquire()

        self.order_books_dict[symbol] = quote
        # logging.info("PriceUpdater writes", symbol)

        for _ in range(self.num_strategies):
            # release all
            self.order_books_dict_semaphore.release()
    
    # on quote:
    # add new order book to order book list
    # if time.time() - time_last > 0.3s
        # acquire locks
        # write all order books to map
        # release locks
        # clear list
