class HalfBook:
   def __init__(self, volume, price, side_str):
      self._volume = volume
      self._price = price
      self._side_str = side_str.capitalize()
   
   @property
   def volume(self):
      return self._volume
   
   @property
   def price(self):
      return self._price

   @property
   def side_str(self):
      return self._side_str

   def __str__(self):
      return f"{self._side_str} volume: {self._volume} \n {self._side_str} price: {self._price}"

class OrderBook:
   def __init__(self, bid_volume, bid_price, ask_volume, ask_price, timestamp):
      self._bid = HalfBook(bid_volume, bid_price, "bid")
      self._ask = HalfBook(ask_volume, ask_price, "ask")
      self._timestamp = timestamp

   @property
   def bid(self):
      return self._bid

   @property
   def ask(self):
      return self._ask

   @property
   def timestamp(self):
      return self._timestamp

   def __str__(self):
      return f"{str(self._bid)}\n {str(self._ask)} \n Timestamp: {self._timestamp}"