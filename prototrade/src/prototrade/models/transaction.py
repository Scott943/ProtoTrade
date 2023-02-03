

class Transaction:
   def __init__(self, symbol, order_side, order_type, volume, price, timestamp):
      self._symbol = symbol
      self._order_side = order_side
      self._order_type = order_type
      self._volume = volume
      self._price = price
      self._timestamp = timestamp

   @property
   def symbol(self):
      """The symbol that the transaction pertains to
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
      """Volume (number of lots) for the Transaction
      """
      return self._volume
   
   @property
   def price(self):
      """Price in the Transaction was executed at"""
      return self._price

   @property
   def timestamp(self):
      """Timestamp of when the Transaction was made
      """
      return self._timestamp

   def __repr__(self):
      return f"Transaction(symbol={self.symbol}, side={self.order_side}, type={self.order_type}, vol={self.volume}, price={self.price}, timestamp={self.timestamp})"

   
