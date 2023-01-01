class PriceUpdater:
    def __init__(self, order_books_dict, order_books_dict_semaphore, num_strategies):
        self.order_books_dict = order_books_dict
        self.order_books_dict_semaphore = order_books_dict_semaphore
        self.num_strategies = num_strategies

    def update_price(self, symbol, quote):
        for _ in range(self.num_strategies):
            # acquire all so no readers can access
            self.order_books_dict_semaphore.acquire()

        self.order_books_dict[symbol] = quote
        print("PriceUpdater writes", symbol)

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
