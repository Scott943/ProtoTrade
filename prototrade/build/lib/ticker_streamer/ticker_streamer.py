import alpaca_trade_api as tradeapi
import threading
from models.books import OrderBook
import time

BASE_URL = "https://api.alpaca.markets"
class AlpacaDataStreamer:

   def __init__(self, api_key, secret_key, order_books_dict, order_books_dict_semaphore, num_strategies, data_feed = "iex"):
      self.alpaca_api_key = api_key
      self.alpaca_secret_key = secret_key
      self.order_books_dict = order_books_dict
      self.order_books_dict_semaphore = order_books_dict_semaphore
      self.num_strategies = num_strategies
      self.data_feed = data_feed
      self._connect()

   def _connect(self):
      self.secondary_thread = threading.Thread(target=self._create_and_run_connection)
      self.secondary_thread.start()
      time.sleep(4) #wait for connection to be established

   def _create_and_run_connection(self):
      global conn

      conn = tradeapi.stream.Stream(key_id=self.alpaca_api_key, secret_key=self.alpaca_secret_key, base_url=BASE_URL, data_feed=self.data_feed
      )
      
      print("Connection established")

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
      print("New quote")
      new_book = OrderBook(q.bid_size, q.bid_price, q.ask_size, q.ask_price, q.timestamp)
      # this should push the new_book to the price updater
      
      for _ in range(self.num_strategies):
         self.order_books_dict_semaphore.acquire()

      self.order_books_dict[q.symbol] = new_book
      print("Streamer writes", q.symbol)
      # print(self.order_books_dict[q.symbol])

      for _ in range(self.num_strategies):
         # print(self.order_books_dict_semaphore)
         self.order_books_dict_semaphore.release()