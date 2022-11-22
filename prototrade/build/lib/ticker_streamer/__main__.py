import alpaca_trade_api as tradeapi
import threading
import time
from multiprocessing import Process, Manager
import signal
from models.books import HalfBook, OrderBook


class AlpacaDataStreamer:

   def __init__(self, api_key, secret_key, order_books_dict, data_feed = "iex"):
      self.BASE_URL = "https://api.alpaca.markets"
      self.ALPACA_API_KEY = api_key
      self.ALPACA_SECRET_KEY = secret_key
      self.order_books_dict = order_books_dict
      self.data_feed = data_feed
      self._connect()

   def _connect(self):
      self.secondary_thread = threading.Thread(target=self._create_and_run_connection)
      self.secondary_thread.start()
      time.sleep(4) #wait for connection to be established

   def _create_and_run_connection(self):
      global conn

      conn = tradeapi.stream.Stream(
         key_id=self.ALPACA_API_KEY,
         secret_key=self.ALPACA_SECRET_KEY,
         base_url=self.BASE_URL,
         data_feed=self.data_feed
      )

      conn.run()

   def subscribe(self, ticker):
      conn.subscribe_quotes(self._on_quote, ticker) # adds ticker to subscribe instruments and sets handler for conn (in secondary thread)

   def unsubscribe(self, ticker):
      conn.unsubscribe_quotes(ticker)

   # Stops the incoming data stream and collects the processing thread
   def stop(self):
      conn.stop()
      self.secondary_thread.join()
      print("Receiver thread joined")

   async def _on_quote(self, q):
      new_book = OrderBook(HalfBook(q.bid_size, q.bid_price, "bid"), HalfBook(q.ask_size, q.ask_price, "ask"), q.timestamp)

      self.order_books_dict[q.symbol] = new_book
      print("\n", q.symbol, self.order_books_dict[q.symbol])


def main():
   signal.signal(signal.SIGINT, handler)
   manager = Manager()
   shared_order_books_dict = manager.dict()

   global streamer
   streamer = AlpacaDataStreamer("AKFA6O7FWKEQ30SFPB9H", "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs", shared_order_books_dict, "iex")
   print("Connetion established")
   streamer.subscribe("AAPL")
   time.sleep(5)
   streamer.unsubscribe("AAPL")
   streamer.subscribe("GOOG")

   time.sleep(3)
   streamer.stop()

   time.sleep(2)
   for symbol, book in shared_order_books_dict.items():
      print(symbol)
      print(book)
      print()



def handler(signum, _):
   if signum == signal.SIGINT:
      streamer.stop()
      exit(1)
 

if __name__ == "__main__":
   main()