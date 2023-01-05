import alpaca_trade_api as tradeapi
import threading
from models.books import Quote
import time

BASE_URL = "https://api.alpaca.markets"

class AlpacaDataStreamer:

    def __init__(self, api_key, secret_key, price_updater, exchange_name):
        self._alpaca_api_key = api_key
        self._alpaca_secret_key = secret_key
        self._exchange_name = exchange_name
        self._price_updater = price_updater
        self._connect()

    def _connect(self):
        self._secondary_thread = threading.Thread(
            target=self._create_and_run_connection)
        self._secondary_thread.start()
        time.sleep(4)  # wait for connection to be established

    def _create_and_run_connection(self):
        self._conn = tradeapi.stream.Stream(key_id=self._alpaca_api_key, secret_key=self._alpaca_secret_key, base_url=BASE_URL, data_feed=self._exchange_name
                                      )
        print("Establishing Connection")
        self._conn.run()

    def subscribe(self, symbol):
        # adds ticker to subscribe instruments and sets handler for self.conn (in secondary thread)
        print(f"Alpaca subscribes to {symbol}")
        self._conn.subscribe_quotes(self._on_quote, symbol)

    def unsubscribe(self, symbol):
        self._conn.unsubscribe_quotes(symbol)

    # Stops the incoming data stream and collects the processing thread
    def stop(self):
        self._conn.stop()
        print("Attempting to join secondary thread")
        self._secondary_thread.join()
        print("Alpaca connection stopped & receiver thread joined")

    async def _on_quote(self, q):
        quote = Quote(q.bid_size, q.bid_price, q.ask_size,
                      q.ask_price, q.timestamp)
        self._price_updater.update_price(q.symbol, quote)
        # this should push the new_book to the price updater


