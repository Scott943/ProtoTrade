class HalfQuote:
   def __init__(self, volume, price, order_side):
      self._volume = volume
      self._price = price
      self._order_side = order_side.lower()
   
   @property
   def volume(self):
      """Volume at the corresponding price in the order book
      """
      return self._volume
   
   @property
   def price(self):
      """Price in the order book
      """
      return self._price

   @property
   def order_side(self):
      """The side of the order book
      """
      return self._order_side

   def __str__(self):
      return f"{self.order_side} \n volume: {self._volume} \n price: {self._price}"

# Our order book is composed of two half books (one for the bid and another for the ask)
class Quote:
   def __init__(self, bid_volume, bid_price, ask_volume, ask_price, timestamp):
      self._bid = HalfQuote(bid_volume, bid_price, "bid")
      self._ask = HalfQuote(ask_volume, ask_price, "ask")
      self._timestamp = timestamp

   @property
   def bid(self):
      """Half Quote object corresponding to the bid side of the Quote
      """
      return self._bid

   @property
   def ask(self):
      """Half Quote object corresponding to the ask side of the Quote
      """
      return self._ask

   @property
   def timestamp(self):
      """Timestamp of when the framework received the Quote.
      """
      return self._timestamp

   def __str__(self):
      return f"{str(self._bid)}\n {str(self._ask)} \n Timestamp: {self._timestamp}"