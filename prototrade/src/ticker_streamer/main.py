import alpaca_trade_api as tradeapi
import threading
import asyncio
import time



class AlpacaDataStreamer:

   def __init__(self, api_key, secret_key, data_feed = "iex"):
      self.BASE_URL = "https://api.alpaca.markets"
      self.ALPACA_API_KEY = api_key
      self.ALPACA_SECRET_KEY = secret_key
      self.data_feed = data_feed
      self._connect()

   def _connect(self):
      self.quote_thread = threading.Thread(target=self.quote_receiver)
      self.quote_thread.start()
      time.sleep(4) #wait for connection to be established


   def quote_receiver(self):
      global conn
      try:
         conn = tradeapi.stream.Stream(
            key_id=self.ALPACA_API_KEY,
            secret_key=self.ALPACA_SECRET_KEY,
            base_url=self.BASE_URL,
            data_feed=self.data_feed
         )
      except Exception as e:
         print("Error logging into alpaca: ", e)
         exit()

      conn.run()

   def subscribe(self, ticker):
      conn.subscribe_quotes(self._on_quote, ticker)

   def unsubscribe(self, ticker):
      conn.unsubscribe_quotes(ticker)

   def stop(self):
      conn.stop()
      self.quote_thread.join()
      print("Receiver thread joined")

   async def _on_quote(self, quote):
      print('quote', quote)

streamer = AlpacaDataStreamer("AKFA6O7FWKEQ30SFPB9H", "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs", "iex")
print("Connetion established")
streamer.subscribe("AAPL")
time.sleep(5)
streamer.unsubscribe("AAPL")
streamer.subscribe("GOOG")

time.sleep(5)
streamer.stop()