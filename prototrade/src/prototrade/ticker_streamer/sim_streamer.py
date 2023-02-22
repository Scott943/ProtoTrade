import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import time
import threading
import random
from prototrade.models.quotes import Quote

BASE_URL = "https://api.alpaca.markets"

class SimulatedStreamer:

    def __init__(self, price_updater):
        self.symbol_list = dict()
        self._price_updater = price_updater
        self.keep_running = True
        self._connect()

    def _connect(self):
        self._secondary_thread = threading.Thread(
            target=self._generate_prices)
        self._secondary_thread.start()
        time.sleep(3)  # wait for connection to be established

    def _generate_prices(self):
      while self.keep_running:
         for symbol in self.symbol_list:
            quote = self.symbol_list[symbol]
            quote.bid.price += random.uniform(-1,1)
            quote.ask.price += random.uniform(-1,1)
            spread = quote.ask.price - quote.bid.price
            while quote.ask.price < quote.bid.price:
               print(quote.bid.price, quote.ask.price)
               quote.ask.price = quote.ask.price + abs(random.uniform(spread/2, 3*spread/2))
            quote.bid.volume += round(random.gauss(0, 10))
            quote.ask.volume += round(random.gauss(0, 10))
            quote.bid.volume = max(quote.bid.volume, 1)
            quote.ask.volume = max(quote.ask.volume, 1)
            self._price_updater.update_price(symbol, quote)
         time.sleep(0.5)
      

    def subscribe(self, symbol):
        # adds ticker to subscribe instruments and sets handler for self.conn (in secondary thread)
        if symbol not in self.symbol_list:
            bid_price = random.uniform(1, 500)
            ask_price = bid_price + random.uniform(0.1,2)
            self.symbol_list[symbol] = Quote(random.randrange(1,100), bid_price, random.randrange(1,100),
                      ask_price, time.time())

    def unsubscribe(self, symbol):
        del self.symbol_list[symbol]

    # Stops the incoming data stream and collects the processing thread
    def stop(self):
        logger.debug("Stopping conn")
        self.keep_running = False
        self._secondary_thread.join()
        logger.debug("Simulated connection stopped & receiver thread joined")


    def get_rest_api(self):
        return None

    def is_market_open(self):
        return True # simulated market always open
