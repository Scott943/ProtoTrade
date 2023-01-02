import alpaca_trade_api as tradeapi
import threading
from models.books import Quote
import time

BASE_URL = "https://api.alpaca.markets"

class AlpacaDataStreamer:

    def __init__(self, api_key, secret_key, price_updater, data_feed="iex"):
        self.alpaca_api_key = api_key
        self.alpaca_secret_key = secret_key
        self.data_feed = data_feed
        self.price_updater = price_updater
        self._connect()

    def _connect(self):
        self.secondary_thread = threading.Thread(
            target=self._create_and_run_connection)
        self.secondary_thread.start()
        time.sleep(4)  # wait for connection to be established

    def _create_and_run_connection(self):
        global conn

        conn = tradeapi.stream.Stream(key_id=self.alpaca_api_key, secret_key=self.alpaca_secret_key, base_url=BASE_URL, data_feed=self.data_feed
                                      )
        print("Establishing Connection")
        conn.run()

    def subscribe(self, ticker):
        # adds ticker to subscribe instruments and sets handler for conn (in secondary thread)
        conn.subscribe_quotes(self._on_quote, ticker)

    def unsubscribe(self, ticker):
        conn.unsubscribe_quotes(ticker)

    # Stops the incoming data stream and collects the processing thread
    def stop(self):
        conn.stop()
        self.secondary_thread.join()
        print("Alpaca connection stopped & receiver thread joined")

    async def _on_quote(self, q):
        print("Streamer receives quote")
        quote = Quote(q.bid_size, q.bid_price, q.ask_size,
                      q.ask_price, q.timestamp)
        self.price_updater.update_price(q.symbol, quote)
        # this should push the new_book to the price updater


