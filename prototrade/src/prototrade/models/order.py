from prototrade.exceptions.exceptions import InvalidOrderSideException

class Order:
   def __init__(self, order_id, symbol, order_side, order_type, volume, price):
      self._order_id = order_id
      self._symbol = symbol
      self._order_side = order_side
      self._order_type = order_type
      self._volume = volume
      self._price = price

   @property
   def order_id(self):
      """The integer order id of the Order object
      """
      return self._order_id

   @property
   def symbol(self):
      """The symbol that the order pertains to
      """
      return self._symbol

   @property
   def order_side(self):
      """Side of the order book. Either 'bid' or 'ask'
      """
      return self._order_side

   @property
   def order_type(self):
      """Type of order e.g. 'market', 'limit' or 'fok'
      """
      return self._order_type

   @property
   def volume(self):
      """Volume at the corresponding price in the order book
      """
      return self._volume
   
   @property
   def price(self):
      """Price in the order book"""
      return self._price

   def __lt__(self, other):
      if self.order_side != other.order_side:
         raise InvalidOrderSideException("Two objects in same heap have different order side types")
      
      if self.order_side == "bid":
         return self.price > other.price # max bid at the top of heap

      return self.price < other.price # min ask at the top of heap

   def __repr__(self):
      return f"Order(symbol={self.symbol}, side={self.order_side}, type={self.order_type}, vol={self.volume}, price={self.price})"